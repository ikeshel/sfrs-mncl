"""Verify SVG hit regions and single-node navigation without network traffic."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'package'))

import yaml
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from detector_map import DetectorMapWidget
import super_frs_manager as overview
import test_node_manager as node_tests


class DetectorMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_rotated_region_tracks_viewbox_and_letterboxing(self):
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / 'map.svg'
            svg.write_text('''<svg xmlns="http://www.w3.org/2000/svg"
              xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="200" height="100"
              viewBox="10 20 200 100"><g transform="translate(20,30)">
              <rect id="rect1-6" inkscape:label="FPF2_SCIFI1" x="10" y="10" width="20" height="10"
                transform="rotate(30,20,15)" fill="blue"/></g></svg>''')
            configs = [dict(directory='FPF2_SCIFI1', node_name='FPF2 SciFi1', host_name='test-node')]
            widget = DetectorMapWidget(svg, configs)
            clicked = []
            widget.node_clicked.connect(clicked.append)
            try:
                widget.resize(400, 400)
                widget.show()
                self.app.processEvents()
                # SVG center (40,45), viewBox origin (10,20), scale 2, top margin 100.
                center = QPointF(60, 150)
                self.assertEqual(widget.element_at(center), 'FPF2_SCIFI1')
                corner = widget.element_polygon('FPF2_SCIFI1').boundingRect().topLeft() + QPointF(.1, .1)
                self.assertIsNone(widget.element_at(corner))
                self.assertIsNone(widget.element_at(QPointF(60, 50)))
                QTest.mouseMove(widget, center.toPoint())
                self.assertEqual(widget.cursor().shape(), Qt.CursorShape.PointingHandCursor)
                self.assertIn('test-node', widget.toolTip())
                QTest.mouseClick(widget, Qt.MouseButton.RightButton, pos=center.toPoint())
                self.assertEqual(clicked, [])
                QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=center.toPoint())
                self.assertEqual(clicked, ['FPF2_SCIFI1'])
                widget.resize(200, 100)
                self.app.processEvents()
                self.assertEqual(widget.element_at(QPointF(30, 25)), 'FPF2_SCIFI1')

                # Moving a rect's transform to its parent must not change the artwork.
                widget.hovered_id = None
                renderer = QSvgRenderer(str(svg))
                original = QImage(200, 100, QImage.Format.Format_ARGB32)
                original.fill(Qt.GlobalColor.white)
                painter = QPainter(original)
                renderer.render(painter, QRectF(0, 0, 200, 100))
                painter.end()
                self.assertEqual(widget.grab().toImage().convertToFormat(original.format()), original)
            finally:
                widget.close()

    def test_all_real_regions_remain_clickable_after_resizing(self):
        configs = yaml.safe_load((ROOT / 'config/mbs_nodes.yaml').read_text())['nodes']
        widget = DetectorMapWidget(ROOT / 'images/SuperFRS.svg', configs)
        try:
            self.assertIn('FHF1_SCIFI3', widget.hotspots)
            self.assertIn('FPF2_SCIFI1', widget.hotspots)
            self.assertEqual({name for name in widget.hotspots if name.endswith('_PLSCI')},
                             {'FPF2_PLSCI', 'FPF4_PLSCI', 'FMF1_PLSCI', 'FMF2_PLSCI',
                              'FMF3_PLSCI', 'FHF1_PLSCI'})
            for size in ((1600, 600), (800, 600), (1500, 400)):
                widget.resize(*size)
                for element_id in widget.hotspots:
                    with self.subTest(size=size, element_id=element_id):
                        center = widget.element_polygon(element_id).boundingRect().center()
                        self.assertEqual(widget.element_at(center), element_id)
        finally:
            widget.close()


class SuperFrsNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node_tests.NodeManagerTests.setUpClass()

    def setUp(self):
        self.fixture = node_tests.NodeManagerTests()
        self.fixture.setUp()
        configs = yaml.safe_load((ROOT / 'config/mbs_nodes.yaml').read_text())['nodes']
        self.fixture.write_config(configs)
        factory = self.fixture.patches.enter_context(patch.object(overview, 'NodeProcessController', autospec=True))
        self.processes = factory.return_value
        self.processes.nodes = []
        self.processes.open_directories = set()
        self.processes.open_node.side_effect = lambda config: self.processes.open_directories.add(config['directory'])
        self.processes.close_node.side_effect = lambda config: self.processes.open_directories.discard(config['directory'])
        self.window = overview.SuperFrsManager()
        self.app = self.fixture.app
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.fixture.tearDown()

    def click_detector(self, element_id):
        diagram = self.window.sfrs_svg
        point = diagram.element_polygon(element_id).boundingRect().center().toPoint()
        QTest.mouseClick(diagram, Qt.MouseButton.LeftButton, pos=point)
        self.app.processEvents()

    def test_click_launches_only_matching_node(self):
        self.assertEqual(self.window.nodes, [])
        for directory, host in (('FHF1_SCIFI3', 'x86l-253'), ('FMF2_PLSCI', 'x86l-132')):
            with self.subTest(directory=directory):
                self.click_detector(directory)
                self.processes.open_node.assert_called_once_with(self.window.node_configs[directory])
                self.assertEqual(self.processes.open_node.call_args.args[0]['host_name'], host)
                self.processes.open_node.reset_mock()
        self.assertEqual(node_tests.mbs_node.MBSNode.list_of_nodes, [])
        self.fixture.start_mbs.assert_not_called()
        self.fixture.start_web.assert_not_called()

    def test_missing_configuration_never_opens_a_different_node(self):
        for directory in ('FMF3_SCIFI2', 'FPF2_PLSCI'):
            with patch.object(overview.QMessageBox, 'information') as message:
                self.click_detector(directory)
                message.assert_called_once()
                self.assertIn(directory, message.call_args.args[2])
        self.processes.open_node.assert_not_called()

    def test_individual_and_group_windows_have_separate_geometry_and_bulk_scope(self):
        individual = self.fixture.controller.open_node(self.window.node_configs['FHF1_MUSIC'])
        group = self.fixture.controller.open_group('MUSIC')
        self.assertNotEqual(individual.yaml_filename, group.yaml_filename)
        self.assertEqual(individual.yaml_filename, '.size_pos_MbsNodeManager_FHF1_MUSIC.yaml')
        self.assertEqual(len(individual.nodes), 1)
        self.assertEqual(len(group.nodes), 2)

    def test_closing_overview_sends_no_commands_to_node_processes(self):
        self.click_detector('FHF1_SCIFI3')
        before = self.processes.mock_calls.copy()
        self.window.close()
        self.assertEqual(self.processes.mock_calls, before)

    def test_overview_actions_forward_to_running_node_proxies(self):
        node = Mock()
        self.processes.nodes = [node]
        self.window.show_all_dashboards()
        node.show_hide_dashboard.assert_called_once_with()
        self.window.open_external_browsers()
        node.open_external_browser.assert_called_once_with()
        self.window.konsole_action(self.window.nodes, ['com'], True)
        node.konsole_manager.assert_called_once_with('com', 'open')

    def test_launch_error_is_shown(self):
        self.processes.open_node.side_effect = RuntimeError('Cannot start test node')
        with patch.object(overview.QMessageBox, 'critical') as message:
            self.click_detector('FHF1_SCIFI3')
            message.assert_called_once()
            self.assertIn('Cannot start test node', message.call_args.args[2])

    def test_detector_menus_open_and_close_only_their_own_nodes(self):
        self.assertEqual(list(self.window.detector_menus), ['MUSIC', 'PLSCI', 'SCIFI'])
        self.assertNotIn('TIMESORTER', self.window.node_actions)
        for group, menu in self.window.detector_menus.items():
            with self.subTest(group=group):
                expected = self.window.detector_nodes[group]
                self.assertEqual([action.text() for action in menu.actions()[:2]],
                                 ['Open all nodes', 'Close all nodes'])
                self.assertTrue(all(self.window.node_actions[name].isCheckable() for name in expected))
                menu.actions()[0].trigger()
                self.assertEqual([call.args[0]['directory'] for call in self.processes.open_node.call_args_list], expected)
                self.assertEqual({name for name, action in self.window.node_actions.items() if action.isChecked()}, set(expected))
                menu.actions()[1].trigger()
                self.assertEqual([call.args[0]['directory'] for call in self.processes.close_node.call_args_list], expected)
                self.assertFalse(any(action.isChecked() for action in self.window.node_actions.values()))
                self.processes.open_node.reset_mock()
                self.processes.close_node.reset_mock()

    def test_node_checkbox_tracks_external_open_and_close_without_relaunching(self):
        directory = 'FMF2_PLSCI'
        action = self.window.node_actions[directory]
        action.trigger()
        self.assertTrue(action.isChecked())
        self.processes.open_node.assert_called_once_with(self.window.node_configs[directory])
        self.processes.open_node.reset_mock()

        self.processes.open_directories.clear()
        self.window.node_menu_timer.timeout.emit()
        self.assertFalse(action.isChecked())
        self.processes.open_directories.add(directory)
        self.window.detector_menus['PLSCI'].aboutToShow.emit()
        self.assertTrue(action.isChecked())
        self.processes.open_node.assert_not_called()
        self.processes.close_node.assert_not_called()

        action.trigger()
        self.assertFalse(action.isChecked())
        self.processes.close_node.assert_called_once_with(self.window.node_configs[directory])


if __name__ == '__main__':
    unittest.main()
