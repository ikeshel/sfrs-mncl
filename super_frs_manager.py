#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import signal
import sys, os
from loguru import logger

## 
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

##
sys.path.append('package')

# from gui_env import ensure_gui_environment
# ensure_gui_environment()
# os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext=false" # supressing the webengine GUI info

from mncl_logger        import MnclLogger
from win_pos_manager    import WindowPositionManager
from menu_bar           import MenuBarManager
from yaml_manager       import YamlManager
from detector_map       import DetectorMapWidget
from node_process       import NodeProcessController
from node_groups        import DETECTOR_GROUPS, node_group

#==============================================================================
#==============================================================================
# MBS Node Manager Main Window
#
class SuperFrsManager(   QMainWindow, 
                        MnclLogger,
                        WindowPositionManager, 
                        MenuBarManager):

    #==========================================================================
    def __init__(self):

        super(SuperFrsManager, self).__init__()

        # yaml manager for mbs nodes configuration
        try:
            self.node_yaml = YamlManager("config/mbs_nodes.yaml") # yaml manager for mbs nodes configuration
        except FileNotFoundError as e:
            logger.error(f"Error loading YAML file: {e}")
            QMessageBox.critical(self, "Error", f"Configuration file not found: {e}")
            sys.exit(1)
        logger.debug(f"Loaded MBS nodes configuration from YAML: {self.node_yaml.get_dict()}")
        self.node_configs = {node['directory'].upper(): node
                             for node in self.node_yaml.get_dict()['nodes']}
        self.node_controller = NodeProcessController(self.node_configs.values())
        self.list_node_hosts = [node["host_name"] for node in self.node_configs.values()]

        # yaml manager for mbs screens configuration
        try:
            self.screen_yaml = YamlManager("config/node_screens.yaml") # yaml manager for mbs screens configuration
        except FileNotFoundError as e:
            logger.error(f"Error loading YAML file: {e}")
            QMessageBox.critical(self, "Error", f"Configuration file not found: {e}")
            sys.exit(1)
        logger.debug(f"Loaded node screens configuration from YAML: {self.screen_yaml.get_dict()}")
        self.list_screens = list(self.screen_yaml.get_dict()['screens'].keys())

        ## intialize the parent classes
        MnclLogger.__init__(self)
        self.setup_logger()
    
        WindowPositionManager.__init__(self)

        MenuBarManager.__init__(self)
        self.setup_mbs_menu()
        self.node_menu.setTitle('Opened nodes')
        self.timesorter_action = self.menubar.addAction('Time sorter')
        sorter_directory = next((directory for directory, config in self.node_configs.items()
                                 if node_group(config) == 'TIMESORTER'), None)
        self.timesorter_action.setEnabled(sorter_directory is not None)
        if sorter_directory is not None:
            self.timesorter_action.setToolTip('Open the TimeSorter main window')
            self.timesorter_action.triggered.connect(
                lambda checked=False: self.open_node(sorter_directory)
            )
        self.setup_detector_menus()
        self.node_menu_timer = QTimer(self)
        self.node_menu_timer.setInterval(1000)
        self.node_menu_timer.timeout.connect(self.refresh_node_menus)
        self.node_menu_timer.start()
        self.refresh_node_menus()

        
        # node widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        # add toolbar buttons
        self.btn_show_dashboards = QAction("Show Dashboards", self)
        self.btn_show_dashboards.triggered.connect(self.show_all_dashboards)
        self.toolbar.addAction(self.btn_show_dashboards)

        self.sfrs_svg = DetectorMapWidget('images/SuperFRS.svg', self.node_configs.values(), self)
        self.sfrs_svg.node_clicked.connect(self.open_node)
        self.layout.addWidget(self.sfrs_svg)

        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            self.resize(self.ww, self.hh)
            # self.setFixedSize(self.ww, self.hh)

        else:
            screen = QApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                self.resize(self.sizeHint().boundedTo(area.size()))
                self.move(area.left(), area.top())
        
        self.setWindowTitle("Super FRS Detector Manager")
        self.show()
        self.raise_()

    @property
    def nodes(self):
        return self.node_controller.nodes

    def setup_detector_menus(self):
        self.detector_menus = {}
        self.detector_nodes = {}
        self.node_actions = {}
        for group in DETECTOR_GROUPS:
            directories = [directory for directory, config in self.node_configs.items()
                           if node_group(config) == group]
            self.detector_nodes[group] = directories
            menu = self.menubar.addMenu(group)
            self.detector_menus[group] = menu
            menu.addAction('Open all nodes').triggered.connect(
                lambda checked=False, group=group: self.set_detector_windows_open(group, True)
            )
            menu.addAction('Close all nodes').triggered.connect(
                lambda checked=False, group=group: self.set_detector_windows_open(group, False)
            )
            menu.addSeparator()
            for directory in directories:
                config = self.node_configs[directory]
                action = menu.addAction(config['node_name'])
                action.setCheckable(True)
                action.setToolTip(f"Open or close {config['node_name']} manager ({config['host_name']})")
                action.triggered.connect(
                    lambda checked, directory=directory: self.set_node_window_open(directory, checked)
                )
                self.node_actions[directory] = action
            menu.setEnabled(bool(directories))
            menu.aboutToShow.connect(self.refresh_node_menus)

    def refresh_node_menus(self):
        opened = self.node_controller.open_directories
        for directory, action in self.node_actions.items():
            # Programmatic checks do not trigger the open/close QAction signal.
            action.setChecked(directory in opened)

    def set_node_window_open(self, directory, opened):
        if opened:
            self.open_node(directory)
        else:
            self.node_controller.close_node(self.node_configs[directory])
            self.refresh_node_menus()

    def set_detector_windows_open(self, group, opened):
        for directory in self.detector_nodes[group]:
            self.set_node_window_open(directory, opened)

    def open_node(self, element_id):
        config = self.node_configs.get(element_id.upper())
        if config is None:
            QMessageBox.information(
                self, 'Node not configured',
                f'{element_id} has no node entry in config/mbs_nodes.yaml.\n'
                'Add its directory and host_name to enable this detector.'
            )
            return
        try:
            node = self.node_controller.open_node(config)
            self.refresh_node_menus()
            return node
        except RuntimeError as error:
            logger.error(str(error))
            QMessageBox.critical(self, 'Cannot open node manager', str(error))
            self.refresh_node_menus()

    #==========================================================================
    def open_external_browsers(self):

        for node in self.nodes:
            node_host = node.node_host
            logger.info(f"Opening {node_host} dashboard...")
            node.open_external_browser()
            
    #==========================================================================
    def show_all_dashboards(self):

        for node in self.nodes:
            logger.info(f"Showing {node.name} dashboard...")
            node.show_hide_dashboard()
       
    #==========================================================================
    def closeEvent(self, event):
        '''Must stay with Main widget'''
        logger.debug("closeEvent")
        self.node_menu_timer.stop()
        self.stop_konsole_monitor()
        self.save_window_data() # save window position and size on close

        # accept the close event to allow the window to close
        event.accept() # let the window close

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == "__main__":

    # Check if running in graphical mode
    if not os.environ.get('DISPLAY'):
        sys.stderr.write("No X11 display detected. Exiting.\n")
        sys.exit(1)

    app = QApplication(sys.argv)
    # app.setStyle('Windows')

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # restore default Ctrl+C behavior
    
    import scripts.CheckForAnotherInstance as check
    if check.CheckForAnotherInstance(sys.argv[0]) != None:
        sys.exit( 0 )

    window = SuperFrsManager()

    sys.exit(app.exec())
