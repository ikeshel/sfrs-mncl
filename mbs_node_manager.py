#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import argparse
import os
import signal
import sys
from threading import Event

from loguru import logger
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt, QThreadPool, QTimer, QObject, QRunnable, pyqtSlot, pyqtSignal

sys.path.append('package')

from mncl_logger import MnclLogger
from win_pos_manager import WindowPositionManager
from menu_bar import MenuBarManager
from mbs_node import MBSNode
from node_groups import DETECTOR_GROUPS, NODE_GROUPS, node_group
from yaml_manager import YamlManager
from window_aspect import set_x11_aspect_ratio
from node_process import NODE_COMMANDS, NodeInstanceServer


class NodeWorkerSignals(QObject):
    data = pyqtSignal(dict)


class NodeWorker(QRunnable):
    """Poll only the nodes owned by one window, with interruptible pauses."""

    def __init__(self, nodes):
        super().__init__()
        self.nodes = list(nodes)
        self.signals = NodeWorkerSignals()
        self.stopped = Event()

    def run(self):
        while not self.stopped.wait(1):
            data = {}
            for node in self.nodes:
                if self.stopped.is_set():
                    return
                data[f"alive_{node.name}"] = node.check_ssh()
            self.signals.data.emit(data)

    def stop(self):
        self.stopped.set()


class NodeWindowController:
    """Reuse independent windows for detector groups and individual nodes."""

    def __init__(self):
        self.windows = {}

    def open_group(self, group):
        group = group.upper()
        if group not in NODE_GROUPS:
            raise ValueError(f"Unknown node group: {group}")
        window = self.windows.get(group)
        if window is None:
            window = MbsNodeManager(group, controller=self)
        return self._show_window(window)

    def open_node(self, node_config):
        key = f"NODE:{node_config['directory'].upper()}"
        window = self.windows.get(key)
        if window is None:
            window = MbsNodeManager(controller=self, node_config=node_config)
        return self._show_window(window)

    @staticmethod
    def _show_window(window):
        window.showNormal()
        window.enable_native_aspect_ratio()
        window.raise_()
        window.activateWindow()
        return window

    def open_selection(self, selection):
        selections = [selection] if isinstance(selection, str) else selection
        groups = []
        for name in selections:
            groups.extend(NODE_GROUPS if name.upper() == "ALL" else (name.upper(),))
        for group in dict.fromkeys(groups):
            self.open_group(group)

    def close_all(self):
        for window in list(self.windows.values()):
            window.close()


class MbsNodeManager(QMainWindow, MnclLogger, WindowPositionManager, MenuBarManager):
    """A TimeSorter launcher, detector-family manager, or single-node manager."""

    def __init__(self, group="TIMESORTER", controller=None, node_config=None):
        super().__init__()
        self.group = node_group(node_config) if node_config is not None else group.upper()
        if self.group not in NODE_GROUPS:
            raise ValueError(f"Unknown node group: {group}")
        geometry_name = node_config['directory'] if node_config is not None else self.group
        self.window_key = f"NODE:{geometry_name.upper()}" if node_config is not None else self.group
        self.controller = controller if controller is not None else NodeWindowController()
        self.nodes = []
        self.closed = False
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        MnclLogger.__init__(self)
        if node_config is not None:
            self.test_log_file = f'logs/MbsNodeManager_{geometry_name}.log'
            self.debug_log_file = f'logs/debug_MbsNodeManager_{geometry_name}.log'
        if not self.controller.windows:
            self.setup_logger()
        WindowPositionManager.__init__(self, node_name=geometry_name)

        try:
            self.node_yaml = YamlManager("config/mbs_nodes.yaml")
            self.screen_yaml = YamlManager("config/node_screens.yaml")
        except FileNotFoundError as error:
            QMessageBox.critical(self, "Configuration error", str(error))
            raise
        node_configs = [node_config] if node_config is not None else []
        if node_config is None:
            for config in self.node_yaml.get_dict()["nodes"]:
                family = node_group(config)
                if family is None:
                    logger.warning(f"Unrecognized node group: {config['node_name']}")
                elif family == self.group:
                    node_configs.append(config)
        self.list_node_hosts = [node["host_name"] for node in node_configs]
        self.list_screens = list(self.screen_yaml.get_dict()["screens"])

        MenuBarManager.__init__(self)
        self.node_menu = None
        label = "TimeSorter" if self.group == "TIMESORTER" else self.group
        if node_config is not None:
            label = node_config['node_name']
        else:
            self.setup_mbs_menu()
            self.node_menu.setTitle(f"{label} nodes")
        if self.group in DETECTOR_GROUPS:
            self.timesorter_action = self.menubar.addAction("TimeSorter")
            self.timesorter_action.setToolTip("Open the TimeSorter main window")
            self.timesorter_action.triggered.connect(
                lambda checked=False: self.controller.open_group("TIMESORTER")
            )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        for config in node_configs:
            try:
                node = MBSNode(config)
            except Exception as error:
                logger.exception(f"Error creating node {config['node_name']}")
                QMessageBox.critical(self, "Node error", str(error))
                continue
            self.nodes.append(node)
            self.layout.addWidget(node)
            node.menu = self.menubar.addMenu(node.name)
            self.build_node_menu(node)

        if not self.nodes:
            self.layout.addWidget(QLabel(f"No {label} nodes available."))
            if self.node_menu is not None:
                self.node_menu.setEnabled(False)

        self.group_buttons = {}
        if self.group == "TIMESORTER":
            buttons = QHBoxLayout()
            for family in DETECTOR_GROUPS:
                button = QPushButton(family)
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                button.setMinimumHeight(36)
                button.clicked.connect(
                    lambda checked=False, selected=family: self.controller.open_group(selected)
                )
                buttons.addWidget(button, 1)
                self.group_buttons[family] = button
            self.layout.addLayout(buttons)

        self.setWindowTitle(f"MBS Node Manager — {label}")
        if self.read_window_data():
            self.resize(self.ww, self.hh)
            self.move(self.xx, self.yy)
        else:
            # Combine native SVG sizes with layout spacing, menus and buttons.
            # adjustSize() caps top-level windows to 2/3 of the screen size.
            self.ensurePolished()
            self.layout.activate()
            self.resize(self.sizeHint())
            screen = QApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                offset = NODE_GROUPS.index(self.group) * 40
                x = min(area.center().x() + offset, area.right() - self.width())
                y = min(area.top() + 20 + offset, area.bottom() - self.height())
                self.move(max(area.left(), x), max(area.top(), y))

        # Keep the restored (or initial layout) proportions for this window.
        self._aspect_ratio = self.width() / self.height()
        self._aspect_reference_size = self.size()
        self._native_aspect = False
        self._last_aspect_size = self.size()
        self._adjusting_aspect = False
        self._aspect_timer = QTimer(self)
        self._aspect_timer.setSingleShot(True)
        self._aspect_timer.timeout.connect(self._constrain_window_size)

        self.threadpool = QThreadPool(self)
        self.node_worker = NodeWorker(self.nodes)
        self.node_worker.signals.data.connect(self.data_received)
        if self.nodes:
            self.threadpool.start(self.node_worker)
        self.controller.windows[self.window_key] = self

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "central_widget"):
            self.central_widget.update()
        # Defer the correction: resizing inside resizeEvent can recurse in Qt.
        if hasattr(self, "_aspect_timer") and not self._adjusting_aspect and not self.closed:
            self._aspect_timer.start(75 if QApplication.platformName().startswith('wayland') else 0)

    def enable_native_aspect_ratio(self):
        if QApplication.platformName() != 'xcb':
            return
        try:
            set_x11_aspect_ratio(int(self.winId()), self._aspect_reference_size.width(),
                                self._aspect_reference_size.height())
            self._native_aspect = True
        except Exception as error:
            logger.warning(f"Cannot set native window aspect ratio: {error}")
            self._native_aspect = False

    def _constrain_window_size(self):
        self._aspect_timer.stop()
        if self._native_aspect:
            # Qt can refresh its size hints after a layout change. Reinstate the
            # constraint without issuing another resize during the user's drag.
            self.enable_native_aspect_ratio()
            self._last_aspect_size = self.size()
            return
        if self.isMaximized() or self.isFullScreen() or self.isMinimized():
            return  # Let the desktop manage these special window states.
        previous = self._last_aspect_size
        width, height = self.width(), self.height()
        width_change = abs(width - previous.width()) / previous.width()
        height_change = abs(height - previous.height()) / previous.height()
        ratio = self._aspect_ratio
        if width_change >= height_change:
            height = width / ratio
        else:
            width = height * ratio

        minimum = self.minimumSizeHint().expandedTo(self.minimumSize())
        scale = max(1.0, minimum.width() / width, minimum.height() / height)
        width, height = round(width * scale), round(height * scale)
        self._adjusting_aspect = True
        try:
            if (width, height) != (self.width(), self.height()):
                self.resize(width, height)
            self._last_aspect_size = self.size()
        finally:
            self._adjusting_aspect = False

    @pyqtSlot(dict)
    def data_received(self, data):
        if self.closed:
            return
        self.ping_toggling = not getattr(self, "ping_toggling", False)
        for node in self.nodes:
            key = f"alive_{node.name}"
            if key in data:
                node.set_connection_status(bool(data[key]), bright=self.ping_toggling)

    def open_external_browsers(self):
        for node in self.nodes:
            node.open_external_browser()

    def show_all_dashboards(self):
        for node in self.nodes:
            node.show_hide_dashboard()

    def closeEvent(self, event):
        if not self.closed:
            self._constrain_window_size()
            self.closed = True
            self.stop_konsole_monitor()
            self.save_window_data()
            self.node_worker.stop()
            self.threadpool.waitForDone()
            for node in self.nodes:
                node.close()
                node.browser_window.deleteLater()
            self.controller.windows.pop(self.window_key, None)
        event.accept()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Open MBS node manager windows by detector group.")
    parser.add_argument(
        "groups", nargs="*", default="TIMESORTER", type=str.upper,
        choices=(*NODE_GROUPS, "ALL"),
        help="windows to open, e.g. MUSIC PLSCI (default: TIMESORTER); ALL opens all four windows",
    )
    parser.add_argument('--node', metavar='DIRECTORY', type=str.upper,
                        help='open one independent node manager, e.g. --node FHF1_SCIFI3')
    args = parser.parse_args(argv)
    if args.node:
        if isinstance(args.groups, list):
            parser.error('--node cannot be combined with detector group names')
        args.groups = []
    # argparse checks a '*' default as one choice, so normalize it after parsing.
    if isinstance(args.groups, str):
        args.groups = [args.groups]
    return args


def main(argv=None):
    args = parse_args(argv)
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
            or os.environ.get('QT_QPA_PLATFORM') in ('offscreen', 'minimal')):
        sys.stderr.write("No X11 display detected. Exiting.\n")
        return 1

    app = QApplication([sys.argv[0]])
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    controller = NodeWindowController()
    app.aboutToQuit.connect(controller.close_all)
    if args.node:
        configs = YamlManager('config/mbs_nodes.yaml').get_dict()['nodes']
        config = next((node for node in configs if node['directory'].upper() == args.node), None)
        if config is None:
            sys.stderr.write(f'No node with directory {args.node} in config/mbs_nodes.yaml.\n')
            return 2
        endpoint = NodeInstanceServer(args.node, parent=app)
        try:
            if not endpoint.start():
                return 0
            window = controller.open_node(config)
            endpoint.command_received.connect(
                lambda command, values: handle_node_command(window, command, values)
            )
            window.destroyed.connect(endpoint.close)
            app.aboutToQuit.connect(endpoint.close)
            return app.exec()
        finally:
            endpoint.close()
    controller.open_selection(args.groups)
    return app.exec()


def handle_node_command(window, command, args):
    if window.closed:
        return
    if command == 'activate':
        NodeWindowController._show_window(window)
    elif command == 'close':
        window.close()
    elif command in NODE_COMMANDS and window.nodes:
        try:
            getattr(window.nodes[0], command)(*args)
        except Exception:
            logger.exception(f'Node manager command failed: {command}')


if __name__ == "__main__":
    sys.exit(main())
