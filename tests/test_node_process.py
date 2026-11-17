"""Verify process isolation, repeated activation and overview command forwarding."""

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'package'))

import yaml
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from node_process import NodeInstanceServer, NodeProcessController, NodeProcessProxy, send_node_command, node_server_name


class NodeProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_socket_reuses_instance_and_forwards_only_supported_commands(self):
        endpoint = NodeInstanceServer('FHF1_SCIFI3', self.project)
        duplicate = NodeInstanceServer('fhf1_scifi3', self.project)
        received = []
        endpoint.command_received.connect(lambda command, args: received.append((command, args)))
        try:
            self.assertTrue(endpoint.start())
            self.assertFalse(duplicate.start())
            QTest.qWait(30)
            self.assertEqual(received, [('activate', [])])
            config = dict(directory='FHF1_SCIFI3', node_name='FHF1 SciFi3', host_name='offline-node')
            proxy = NodeProcessProxy(config, self.project)
            self.assertTrue(proxy.is_running())
            proxy.start_mbs('force')
            proxy.konsole_manager('com', 'open')
            send_node_command(endpoint.name, 'unsupported_method')
            QTest.qWait(30)
            self.assertEqual(received, [('activate', []), ('start_mbs', ['force']),
                                        ('konsole_manager', ['com', 'open'])])
            controller = NodeProcessController([config], self.project)
            self.assertEqual(len(controller.nodes), 1)
            self.assertEqual(controller.open_directories, {'FHF1_SCIFI3'})
            with patch('node_process.QProcess') as launch:
                controller.open_node(config)
                launch.assert_not_called()
            controller.close_node(config)
            self.assertEqual(controller.open_directories, set())
            QTest.qWait(30)
            self.assertEqual(received[-1], ('close', []))
            endpoint.close()
            self.assertFalse(proxy.is_running())
            self.assertTrue(duplicate.start())
        finally:
            endpoint.close()
            duplicate.close()

    def test_failed_launch_is_reported_and_uses_current_interpreter(self):
        config = dict(directory='FHF1_SCIFI3', node_name='FHF1 SciFi3', host_name='offline-node')
        controller = NodeProcessController([config], self.project)
        with patch('node_process.send_node_command', return_value=False), patch('node_process.QProcess') as factory:
            process = factory.return_value
            process.startDetached.return_value = (False, 0)
            process.errorString.return_value = 'test failure'
            with self.assertRaisesRegex(RuntimeError, 'test failure'):
                controller.open_node(config)
            process.setProgram.assert_called_once_with(sys.executable)
            process.setWorkingDirectory.assert_called_once_with(str(self.project))
            self.assertEqual(process.setArguments.call_args.args[0][-2:], ['--node', 'FHF1_SCIFI3'])

    def test_close_during_startup_is_retried_without_relaunching(self):
        config = dict(directory='FHF1_SCIFI3', node_name='FHF1 SciFi3', host_name='offline-node')
        controller = NodeProcessController([config], self.project)
        with patch('node_process.send_node_command', return_value=False) as send, patch('node_process.QProcess') as factory:
            factory.return_value.startDetached.return_value = (True, 123)
            controller.open_node(config)
            controller.open_node(config)
            factory.return_value.startDetached.assert_called_once()
            self.assertEqual(controller.open_directories, {'FHF1_SCIFI3'})
            controller.close_node(config)
            self.assertEqual(controller.open_directories, set())
            send.return_value = True
            controller._refresh_pending()
            self.assertEqual(send.call_args.args[1], 'close')
            send.return_value = False
            controller._refresh_pending()
            self.assertEqual(controller._pending, {})
            self.assertFalse(controller._pending_timer.isActive())

    def test_reopen_waits_for_pending_close_before_starting_new_manager(self):
        config = dict(directory='FHF1_SCIFI3', node_name='FHF1 SciFi3', host_name='offline-node')
        controller = NodeProcessController([config], self.project)
        with patch('node_process.send_node_command', return_value=True) as send, patch('node_process.QProcess') as factory:
            factory.return_value.startDetached.return_value = (True, 123)
            controller.close_node(config)
            controller.open_node(config)
            controller._refresh_pending()
            factory.assert_not_called()
            send.return_value = False
            controller._refresh_pending()
            factory.return_value.startDetached.assert_called_once()
            self.assertEqual(controller.open_directories, {'FHF1_SCIFI3'})
            controller._pending_timer.stop()

    def test_detached_managers_survive_overview_exit_and_reuse_after_reopen(self):
        (self.project / 'config').mkdir()
        (self.project / 'images').symlink_to(ROOT / 'images', target_is_directory=True)
        shutil.copy(ROOT / 'config/node_screens.yaml', self.project / 'config')
        configs = [dict(directory='FHF1_SCIFI3', node_name='FHF1 SciFi3', host_name='offline-scifi', pc_type='intel_x86'),
                   dict(directory='FHF1_MUSIC', node_name='FHF1 MUSIC', host_name='offline-music', pc_type='intel_music')]
        (self.project / 'config/mbs_nodes.yaml').write_text(yaml.safe_dump({'nodes': configs}))
        state_dir = self.project / 'state'
        state_dir.mkdir()
        processes = []
        known_pids = set()
        log = (self.project / 'fixture.log').open('w')

        def start_overview():
            process = subprocess.Popen([sys.executable, str(ROOT / 'tests/node_process_fixture.py'), '--overview'],
                                       cwd=self.project, stdout=log, stderr=log, start_new_session=True)
            processes.append(process)
            return process

        def state(directory):
            path = state_dir / f'{directory}.json'
            return json.loads(path.read_text()) if path.exists() else None

        def wait_until(condition):
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if condition():
                    return
                time.sleep(.04)
            self.fail(f'Process check timed out: {(self.project / "fixture.log").read_text()}')

        def is_running(directory):
            return send_node_command(node_server_name(directory, self.project), 'ping')

        try:
            first = start_overview()
            wait_until(lambda: all(state(config['directory']) for config in configs))
            before = {config['directory']: state(config['directory']) for config in configs}
            known_pids.update(item['pid'] for item in before.values())
            self.assertEqual(len(known_pids), 2)
            for config in configs:
                item = before[config['directory']]
                self.assertNotEqual(item['pid'], first.pid)
                self.assertNotEqual(item['session'], os.getsid(first.pid))
                self.assertEqual(item['hosts'], [config['host_name']])
                self.assertEqual(item['log_file'], f"logs/MbsNodeManager_{config['directory']}.log")
            (state_dir / 'close-overview').touch()
            self.assertEqual(first.wait(timeout=5), 0)
            self.assertTrue(all(is_running(config['directory']) for config in configs))

            # A fresh overview must activate the surviving managers, not duplicate them.
            (state_dir / 'close-overview').unlink()
            second = start_overview()
            wait_until(lambda: all(state(name)['activations'] > item['activations'] for name, item in before.items()))
            for name, item in before.items():
                self.assertEqual(state(name)['pid'], item['pid'])
            (state_dir / 'close-overview').touch()
            self.assertEqual(second.wait(timeout=5), 0)
            self.assertTrue(all(is_running(config['directory']) for config in configs))

            # Closing one node leaves the other alive; the next click starts it again.
            stopped = configs[0]['directory']
            control = NodeProcessController(configs, self.project)
            self.assertTrue(control.close_node(configs[0]))
            wait_until(lambda: not is_running(stopped))
            self.assertTrue(is_running(configs[1]['directory']))
            control._refresh_pending()
            self.assertEqual(control.open_directories, {configs[1]['directory']})
            (state_dir / 'close-overview').unlink()
            third = start_overview()
            wait_until(lambda: state(stopped)['pid'] != before[stopped]['pid'])
            known_pids.add(state(stopped)['pid'])
            (state_dir / 'close-overview').touch()
            self.assertEqual(third.wait(timeout=5), 0)
            self.assertTrue(all(is_running(config['directory']) for config in configs))
        finally:
            (state_dir / 'close-overview').touch()
            for config in configs:
                (state_dir / f"stop-{config['directory']}").touch()
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and any(is_running(c['directory']) for c in configs):
                time.sleep(.04)
            for config in configs:
                if is_running(config['directory']):
                    info = state(config['directory'])
                    if info and info['pid'] in known_pids:
                        os.kill(info['pid'], signal.SIGTERM)
            log.close()


if __name__ == '__main__':
    unittest.main()
