"""Console checks must follow named windows without opening remote sessions."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, call

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'package'))

from PyQt6.QtCore import QProcess
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from konsole_status import KonsoleWindowMonitor, console_title, parse_console_windows
import test_node_manager as node_tests


class ConsoleMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_names_match_whole_host_and_screen_tokens(self):
        output = '''0x01  0 desktop ikeshel@x86l-253_mbs — Konsole
0x02 -1 desktop ikeshel@x86l-253_web - Konsole
0x03  1 desktop ikeshel@x86l-253_com
0x04  0 desktop ikeshel@x86l-253_mbs_extra — Konsole
0x05  0 desktop other@x86l-253_com — Konsole
0x06  0 desktop ikeshel@x86l-2530_mbs — Konsole
0x07  0 desktop [ikeshel@x86l-253_com_backup] — Konsole
0x08  0 ikeshel@wrong-host_mbs unrelated window
malformed line'''
        titles = parse_console_windows(output)
        self.assertIn('ikeshel@x86l-253_mbs', titles)
        self.assertIn('ikeshel@x86l-253_web', titles)
        self.assertIn('ikeshel@x86l-253_com', titles)
        self.assertNotIn('ikeshel@wrong-host_mbs', titles)
        only_other_windows = parse_console_windows('\n'.join(output.splitlines()[3:]))
        self.assertNotIn('ikeshel@x86l-253_mbs', only_other_windows)
        self.assertNotIn('ikeshel@x86l-253_com', only_other_windows)

    def test_async_scan_updates_after_window_closes_and_preserves_state_on_error(self):
        monitor = KonsoleWindowMonitor()
        received = []
        monitor.windows_changed.connect(received.append)
        monitor.process.setProgram(sys.executable)
        monitor.process.setArguments(['-c', 'print("0x01 0 desktop ikeshel@test_com — Konsole")'])
        try:
            self.assertEqual(monitor.timer.interval(), 1000)
            monitor.start()
            QTest.qWait(150)
            self.assertEqual(received, [{'ikeshel@test_com'}])
            monitor.process.setArguments(['-c', 'import sys; sys.exit(1)'])
            monitor.poll()
            QTest.qWait(150)
            self.assertEqual(received, [{'ikeshel@test_com'}])
            self.assertEqual(monitor.last_titles, {'ikeshel@test_com'})
            monitor.process.setArguments(['-c', 'print("")'])
            monitor.poll()
            QTest.qWait(150)
            self.assertEqual(received[-1], set())
        finally:
            monitor.stop()

    def test_hung_scan_is_killed_without_overlapping_or_blocking_gui(self):
        monitor = KonsoleWindowMonitor()
        monitor.process.setProgram(sys.executable)
        monitor.process.setArguments(['-c', 'import time; time.sleep(10)'])
        monitor.timeout.setInterval(100)
        received = []
        monitor.windows_changed.connect(received.append)
        try:
            monitor.start()
            QTest.qWait(30)
            pid = monitor.process.processId()
            self.assertGreater(pid, 0)
            monitor.poll()
            self.assertEqual(monitor.process.processId(), pid)
            QTest.qWait(150)
            self.assertEqual(monitor.process.state(), QProcess.ProcessState.NotRunning)
            self.assertEqual(received, [])
            monitor.poll()
            QTest.qWait(30)
            monitor.stop()
            self.assertFalse(monitor.timer.isActive())
            self.assertEqual(monitor.process.state(), QProcess.ProcessState.NotRunning)
        finally:
            monitor.stop()


class ConsoleMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node_tests.NodeManagerTests.setUpClass()

    def setUp(self):
        self.fixture = node_tests.NodeManagerTests()
        self.fixture.setUp()
        self.window = self.fixture.controller.open_group('MUSIC')
        for node in self.window.nodes:
            node.konsole_manager = Mock()

    def tearDown(self):
        self.fixture.tearDown()

    def test_each_node_and_aggregate_follow_actual_console_windows(self):
        first, second = self.window.nodes
        actions = self.window.node_console_actions
        first_titles = {console_title(first, screen) for screen in self.window.list_screens}
        titles = first_titles | {console_title(second, 'web')}
        self.window._update_konsole_actions(titles)
        self.assertTrue(all(action.isChecked() for action in actions[first.directory].values()))
        self.assertTrue(actions[second.directory]['web'].isChecked())
        for key in ('com', 'mbs', 'all'):
            self.assertFalse(actions[second.directory][key].isChecked())
        self.assertFalse(self.window.toggle_all_konsoles.isChecked())

        titles |= {console_title(second, screen) for screen in self.window.list_screens}
        self.window._update_konsole_actions(titles)
        self.assertTrue(self.window.toggle_all_konsoles.isChecked())
        titles.remove(console_title(first, 'mbs'))
        self.window.konsole_monitor.windows_changed.emit(titles)
        self.assertFalse(actions[first.directory]['mbs'].isChecked())
        self.assertFalse(actions[first.directory]['all'].isChecked())
        self.assertFalse(self.window.toggle_all_konsoles.isChecked())
        self.assertTrue(actions[second.directory]['mbs'].isChecked())
        for node in self.window.nodes:
            node.konsole_manager.assert_not_called()

    def test_bulk_actions_keep_correct_command_for_every_node(self):
        self.window.konsole_action(self.window.nodes, ['com', 'mbs'], True)
        for node in self.window.nodes:
            self.assertEqual(node.konsole_manager.call_args_list, [call('com', 'open'), call('mbs', 'open')])
            node.konsole_manager.reset_mock()
        self.window.konsole_action(self.window.nodes, ['com', 'mbs'], False)
        for node in self.window.nodes:
            self.assertEqual(node.konsole_manager.call_args_list, [call('com', 'close'), call('mbs', 'close')])


if __name__ == '__main__':
    unittest.main()
