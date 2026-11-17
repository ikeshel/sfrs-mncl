"""Headless GUI regression tests; no SSH, acquisition, or dashboard traffic."""

import contextlib
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml
from PyQt6.QtCore import QCoreApplication, QEvent, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget

import mbs_node_manager as manager
import mbs_node
from node_groups import NODE_GROUPS, node_group
from loguru import logger


class OfflineBrowser(QWidget):
    def __init__(self, url):
        super().__init__()


class NodeManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
        logger.disable('mbs_node_manager')
        logger.disable('mbs_node')
        logger.disable('yaml_manager')
        logger.disable('win_pos_manager')
        logger.disable('menu_bar')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        self.workdir = Path(self.temp.name)
        (self.workdir / 'config').mkdir()
        (self.workdir / 'images').symlink_to(ROOT / 'images', target_is_directory=True)
        shutil.copy(ROOT / 'config/node_screens.yaml', self.workdir / 'config')
        self.configs = [
            dict(host_name=f'node-{i}', node_name=name, directory=directory,
                 active=True, pc_type='intel_x86')
            for i, (name, directory) in enumerate([
                ('Time Sorter', 'TimeSorter'),
                ('FMF1 MUSIC', 'FMF1_MUSIC'),
                ('FHF1 MUSIC', 'FHF1_MUSIC'),
                ('FMF2 PlSci', 'FMF2_PLSCI'),
                ('FHF1 SciFi3', 'FHF1_SCIFI3'),
                ('FHF1 SciFi4', 'FHF1_SCIFI4'),
            ])
        ]
        self.write_config(self.configs)
        os.chdir(self.workdir)
        self.patches = contextlib.ExitStack()
        self.patches.enter_context(patch('menu_bar.KonsoleWindowMonitor.start'))
        self.patches.enter_context(patch.object(manager.MnclLogger, 'setup_logger'))
        self.patches.enter_context(patch.object(mbs_node, 'MBSBrowser', OfflineBrowser))
        self.patches.enter_context(patch.object(mbs_node.MBSNode, 'check_ssh', return_value=True))
        self.patches.enter_context(patch.object(mbs_node.MBSNode, 'read_node_murx_config'))
        self.start_mbs = self.patches.enter_context(patch.object(mbs_node.MBSNode, 'start_mbs'))
        self.start_web = self.patches.enter_context(patch.object(mbs_node.MBSNode, 'start_webmbs'))
        self.controller = manager.NodeWindowController()

    def tearDown(self):
        self.controller.close_all()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertEqual(mbs_node.MBSNode.list_of_nodes, [])
        self.patches.close()
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def write_config(self, nodes):
        (self.workdir / 'config/mbs_nodes.yaml').write_text(yaml.safe_dump({'nodes': nodes}))

    def test_cli_selection(self):
        self.assertEqual(manager.parse_args([]).groups, ['TIMESORTER'])
        for choice in (*NODE_GROUPS, 'ALL'):
            self.assertEqual(manager.parse_args([choice.lower()]).groups, [choice])
        self.assertEqual(manager.parse_args(['music', 'PlSci']).groups, ['MUSIC', 'PLSCI'])
        selected = manager.parse_args(['--node', 'fhf1_scifi3'])
        self.assertEqual(selected.node, 'FHF1_SCIFI3')
        self.assertEqual(selected.groups, [])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            manager.parse_args(['--node', 'FHF1_SCIFI3', 'music'])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            manager.parse_args(['music', 'unknown'])
        self.assertEqual(error.exception.code, 2)

    def test_default_buttons_equal_width_and_reuse(self):
        self.controller.open_selection(manager.parse_args([]).groups)
        self.assertEqual(set(self.controller.windows), {'TIMESORTER'})
        main = self.controller.windows['TIMESORTER']
        self.assertEqual([n.directory for n in main.nodes], ['TimeSorter'])
        self.app.processEvents()
        widths = [button.width() for button in main.group_buttons.values()]
        self.assertLessEqual(max(widths) - min(widths), 1)
        for family, button in main.group_buttons.items():
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            window = self.controller.windows[family]
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            self.assertIs(self.controller.windows[family], window)
        self.assertEqual(set(self.controller.windows), set(NODE_GROUPS))
        self.start_mbs.assert_not_called()
        self.start_web.assert_not_called()

    def test_all_groups_and_independent_positions(self):
        self.controller.open_selection('all')
        expected = {'TIMESORTER': 1, 'MUSIC': 2, 'PLSCI': 1, 'SCIFI': 2}
        for group, count in expected.items():
            window = self.controller.windows[group]
            self.assertEqual(len(window.nodes), count)
            self.assertEqual(window.node_worker.nodes, window.nodes)
            self.assertTrue(all(node_group({'directory': n.directory}) == group for n in window.nodes))
        filenames = {w.yaml_filename for w in self.controller.windows.values()}
        self.assertEqual(len(filenames), 4)

    def test_explicit_selection_opens_only_requested_group(self):
        for choices in (['music'], ['plsci'], ['scifi'], ['music', 'PlSci'],
                        ['scifi', 'timesorter'], ['music', 'music', 'plsci'], ['music', 'all']):
            self.controller.open_selection(manager.parse_args(choices).groups)
            expected = set(NODE_GROUPS) if 'all' in choices else {name.upper() for name in choices}
            self.assertEqual(set(self.controller.windows), expected)
            self.controller.close_all()

    def test_first_launch_uses_native_svg_dimensions(self):
        for config in self.configs:
            if 'MUSIC' in config['directory'] or config['directory'] == 'TimeSorter':
                config['pc_type'] = 'intel_music'
        self.write_config(self.configs)
        for group in NODE_GROUPS:
            with self.subTest(group=group):
                window = self.controller.open_group(group)
                self.app.processEvents()
                for node in window.nodes:
                    self.assertEqual(node.size(), node.svg_size)
                self.assertEqual(window.size(), window.sizeHint())
                self.assertAlmostEqual(window._aspect_ratio, window.width() / window.height())

    def test_large_svg_is_not_capped_by_adjust_size(self):
        # A wide fixture catches Qt's implicit 2/3-screen limit in adjustSize().
        images = self.workdir / 'images'
        images.unlink()  # Replace the test symlink, leaving repository assets intact.
        images.mkdir()
        (images / 'intel_x86.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="180" '
            'viewBox="0 0 960 180"><rect width="960" height="180" fill="gray"/></svg>'
        )
        window = self.controller.open_group('MUSIC')
        self.app.processEvents()
        for node in window.nodes:
            self.assertEqual((node.width(), node.height()), (960, 180))
        self.assertGreater(window.width(), 960)

    def test_size_and_position_survive_reopening_every_group(self):
        expected = {}
        for index, group in enumerate(NODE_GROUPS):
            window = self.controller.open_group(group)
            window.resize(700 + index * 25, 500 + index * 20)
            window.move(50 + index * 20, 70 + index * 20)
            self.app.processEvents()
            expected[group] = (window.x(), window.y(), window.width(), window.height())
        self.controller.close_all()

        # A fresh controller must restore each group's own saved geometry.
        self.controller = manager.NodeWindowController()
        for group, geometry in expected.items():
            with self.subTest(group=group):
                saved = yaml.safe_load((self.workdir / f'.size_pos_MbsNodeManager_{group}.yaml').read_text())
                self.assertEqual((saved['x_position'], saved['y_position'],
                                  saved['width'], saved['height']), geometry)
                window = self.controller.open_group(group)
                self.app.processEvents()
                self.assertEqual((window.x(), window.y(), window.width(), window.height()), geometry)

    def test_window_ratio_survives_side_and_corner_resizing(self):
        for group in NODE_GROUPS:
            with self.subTest(group=group):
                window = self.controller.open_group(group)
                self.app.processEvents()
                ratio = window.width() / window.height()
                for width, height in [(window.width() + 120, window.height()),
                                      (window.width(), window.height() + 120),
                                      (900, 650), (300, 200)]:
                    window.resize(width, height)
                    self.app.processEvents()
                    self.assertLessEqual(abs(window.width() - ratio * window.height()),
                                         max(1, ratio))
                    stable = window.size()
                    self.app.processEvents()
                    self.assertEqual(window.size(), stable)

    def test_native_aspect_does_not_issue_competing_resize_calls(self):
        window = self.controller.open_group('MUSIC')
        window._native_aspect = True
        window.resize(900, 600)
        with patch.object(window, 'enable_native_aspect_ratio') as refresh, \
                patch.object(window, 'resize', wraps=window.resize) as resize:
            self.app.processEvents()
            refresh.assert_called()
            resize.assert_not_called()
        window._native_aspect = False

    def test_resize_repaints_entire_svg_and_background(self):
        for config in self.configs:
            if 'MUSIC' in config['directory']:
                config['pc_type'] = 'intel_music'
        self.write_config(self.configs)
        window = self.controller.open_group('MUSIC')
        for size in ((1000, 440), (800, 700), (1300, 250), (1012, 442)):
            window.resize(*size)
            QTest.qWait(40)
            displayed = window.screen().grabWindow(int(window.winId())).toImage()
            self.assertFalse(displayed.isNull())
            repainted = window.grab().toImage()
            self.assertEqual(displayed, repainted)

    def test_saved_ratio_is_used_and_pending_resize_is_saved_on_close(self):
        path = self.workdir / '.size_pos_MbsNodeManager_MUSIC.yaml'
        path.write_text(yaml.safe_dump(dict(width=800, height=400, x_position=60, y_position=80)))
        window = self.controller.open_group('MUSIC')
        self.app.processEvents()
        window.resize(1000, 400)
        window.close()  # Close before the deferred resize correction runs.
        saved = yaml.safe_load(path.read_text())
        self.assertEqual((saved['width'], saved['height']), (1000, 500))
        window = self.controller.open_group('MUSIC')
        self.app.processEvents()
        self.assertEqual((window.width(), window.height()), (1000, 500))

    def test_bulk_actions_and_status_stay_in_their_window(self):
        self.controller.open_selection('ALL')
        music = self.controller.windows['MUSIC']
        scifi = self.controller.windows['SCIFI']
        for window in self.controller.windows.values():
            for node in window.nodes:
                node.open_external_browser = Mock()
                node.show_hide_dashboard = Mock()
                node.start_mbs = Mock()
                node.check_screens = Mock()
        music.open_external_browsers()
        music.show_all_dashboards()
        with patch('menu_bar.time.sleep') as sleep:
            music.start_mbs_processes()
            sleep.assert_not_called()
        for window in self.controller.windows.values():
            for node in window.nodes:
                self.assertEqual(node.start_mbs.call_count, int(window is music))
                self.assertEqual(node.open_external_browser.call_count, int(window is music))
                self.assertEqual(node.show_hide_dashboard.call_count, int(window is music))
        with patch.object(music, 'konsole_action') as action:
            music.toggle_all_konsoles.trigger()
            action.assert_called_once_with(music.nodes, music.list_screens, True)
        before = scifi.nodes[0].node_svg.power_led_color
        data = {f'alive_{node.name}': True for node in mbs_node.MBSNode.list_of_nodes}
        original = data.copy()
        music.data_received(data)
        self.assertEqual(data, original)
        self.assertEqual(scifi.nodes[0].node_svg.power_led_color, before)
        self.assertEqual(music.nodes[0].node_svg.power_led_color, 'lightgreen')

    def test_heartbeat_recolors_embedded_led_in_both_illustrations(self):
        self.configs[1]['pc_type'] = 'intel_music'
        self.write_config(self.configs)
        window = self.controller.open_group('MUSIC')
        for node in window.nodes:
            self.assertFalse(hasattr(node, 'status_ping'))
            self.assertEqual(node.node_svg.power_led_color, 'green')
        window.node_worker.stop()
        window.threadpool.waitForDone()
        self.app.processEvents()
        window.ping_toggling = False
        for alive, color in ((True, 'lightgreen'), (True, 'green'),
                             (False, 'pink'), (False, 'red'), (True, 'lightgreen')):
            window.data_received({f'alive_{node.name}': alive for node in window.nodes})
            for node in window.nodes:
                with self.subTest(pc_type=node.pc_type, color=color):
                    renderer = node.node_svg.renderer()
                    self.assertEqual(node.node_svg.power_led_color, color)
                    self.assertEqual(node.status, mbs_node.NodeStatus.ALIVE if alive else mbs_node.NodeStatus.DEAD)
                    self.assertEqual(renderer.defaultSize(), node.svg_size)
                    self.assertEqual(renderer.aspectRatioMode(), Qt.AspectRatioMode.KeepAspectRatio)
                    # Check the actual Qt-rendered LED, including inline CSS fills.
                    image = QImage(64, 64, QImage.Format.Format_ARGB32)
                    image.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(image)
                    renderer.render(painter, 'led_power', QRectF(0, 0, 64, 64))
                    painter.end()
                    self.assertEqual(image.pixelColor(32, 32), QColor(color))

    def test_unreachable_node_starts_with_red_svg_led(self):
        with patch.object(mbs_node.MBSNode, 'check_ssh', return_value=False):
            window = self.controller.open_group('PLSCI')
            self.assertEqual(window.nodes[0].node_svg.power_led_color, 'red')
            self.assertEqual(window.nodes[0].status, mbs_node.NodeStatus.DEAD)

    def test_close_and_reopen_preserves_other_windows(self):
        self.controller.open_selection('ALL')
        music = self.controller.windows['MUSIC']
        scifi = self.controller.windows['SCIFI']
        scifi.nodes[0].browser_window.show()
        music.nodes[0].browser_window.show()
        worker = music.node_worker
        music.move(75, 85)
        music.close()
        self.assertTrue(worker.stopped.is_set())
        self.assertEqual(music.threadpool.activeThreadCount(), 0)
        self.assertNotIn('MUSIC', self.controller.windows)
        self.assertTrue(scifi.isVisible())
        self.assertTrue(scifi.nodes[0].browser_window.isVisible())
        self.assertFalse(scifi.node_worker.stopped.is_set())
        replacement = self.controller.open_group('MUSIC')
        self.assertIsNot(replacement, music)
        self.assertEqual((replacement.x(), replacement.y()), (75, 85))
        self.assertEqual(len(mbs_node.MBSNode.list_of_nodes), 6)
        self.controller.windows['TIMESORTER'].close()
        self.assertTrue(scifi.isVisible())

    def test_empty_group_has_disabled_actions_and_still_closes(self):
        self.write_config(self.configs[:1])
        window = self.controller.open_group('SCIFI')
        self.assertEqual(window.nodes, [])
        self.assertFalse(window.node_menu.isEnabled())
        window.start_mbs_processes()  # also safe if invoked programmatically
        self.start_mbs.assert_not_called()

    def test_polling_updates_only_its_window_and_stops_on_close(self):
        window = self.controller.open_group('MUSIC')
        received = []
        window.node_worker.signals.data.connect(received.append)
        QTest.qWait(1200)
        self.assertTrue(received)
        self.assertEqual(set(received[0]), {f'alive_{n.name}' for n in window.nodes})
        self.assertTrue(all(received[0].values()))
        window.close()
        self.assertEqual(window.threadpool.activeThreadCount(), 0)

    def test_combined_start_keeps_timesorter_last_regardless_of_order(self):
        calls = []
        nodes = [SimpleNamespace(
            name=name, directory=directory, check_screens=Mock(),
            start_mbs=lambda mode, name=name: calls.append(name),
        ) for name, directory in [('MUSIC', 'FMF1_MUSIC'),
                                  ('Time Sorter', 'TimeSorter'),
                                  ('SCIFI', 'FHF1_SCIFI3')]]
        target = SimpleNamespace(nodes=nodes, check_all_screens=Mock())
        with patch('menu_bar.time.sleep') as sleep:
            manager.MenuBarManager.start_mbs_processes(target)
            sleep.assert_called_once_with(10)
        self.assertEqual(calls, ['SCIFI', 'MUSIC', 'Time Sorter'])

    def test_grouping_uses_names_without_specific_hosts(self):
        self.assertEqual(node_group({'node_name': 'Time Sorter'}), 'TIMESORTER')
        self.assertEqual(node_group({'directory': 'FPF2_SCIFI12'}), 'SCIFI')
        self.assertEqual(node_group({'node_name': 'FMF2 PlSci'}), 'PLSCI')
        self.assertIsNone(node_group({'node_name': 'Unknown detector'}))

    def test_dashboard_links_do_not_duplicate_hostnames(self):
        for config in self.configs:
            if config['directory'] != 'TimeSorter':
                config['sfrs_chamber'] = config['directory'].split('_')[0]
        self.write_config(self.configs)
        self.controller.open_selection('ALL')
        for window in self.controller.windows.values():
            for node in window.nodes:
                expected = node.directory if node.directory == 'TimeSorter' else node.directory.split('_')[0]
                self.assertEqual(node.lbl_node_name.text(), expected)
                self.assertIn(node.node_host, node.lbl_node_name.toolTip())


if __name__ == '__main__':
    unittest.main()
