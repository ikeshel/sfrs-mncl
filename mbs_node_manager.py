#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import signal
import sys, os, time
from loguru import logger
from Xlib.display import Display

## 
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtGui import QAction, QPainter
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QThreadPool, QObject, QRunnable, QThread, pyqtSlot, pyqtSignal

##
sys.path.append('package')

# from gui_env import ensure_gui_environment
# ensure_gui_environment()
# os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext=false" # supressing the webengine GUI info

from mncl_logger        import MnclLogger
from win_pos_manager    import WindowPositionManager
from menu_bar           import MenuBarManager
from mbs_node           import MBSNode
from yaml_manager       import YamlManager

###############################################################################
class NodeWorkerSignals(QObject):
    """ Signals to be emitted from the worker thread """
    data = pyqtSignal(dict)

###############################################################################
class NodeWorker(QRunnable):
    """ Worker thread that performs a task in the background. """

    def __init__(self, nodes=None):
        super(NodeWorker, self).__init__()

        self.nodes       = nodes
        self.signals     = NodeWorkerSignals()
        self.is_running  = True
        self.datadict    = {}

        logger.debug(f"{__class__.__module__} started")

        self.delay_ms = 1000 # milliseconds
        self.last_time = 0

    #==========================================================================
    def run(self):

        logger.debug("NodeWorker.run()")

        while True:
            if self.is_running == False:
                logger.debug("NodeWorker.run() break")
                break

            QThread.msleep(self.delay_ms)
            
            self.datadict['time'] = time.time() # seconds
            if self.last_time < self.datadict['time']-1: # check every 1 second
                for node in self.nodes:
                    # self.datadict[f"alive_{node.name}"] = node.check_ping()
                    self.datadict[f"alive_{node.name}"] = node.check_ssh()
                self.last_time = self.datadict['time']
            
            self.signals.data.emit( self.datadict ) # emit the data when it's ready

        logger.debug("NodeWorker.run() finished")

    #==========================================================================
    def stop(self):
        logger.debug("NodeWorker.stop()")
        self.is_running = False

#==============================================================================
#==============================================================================
# MBS Node Manager Main Window
#
class MbsNodeManager(   QMainWindow, 
                        MnclLogger,
                        WindowPositionManager, 
                        MenuBarManager):

    #==========================================================================
    def __init__(self):

        super(MbsNodeManager, self).__init__()

        super(MnclLogger, self).__init__()
        self.setup_logger()
    
        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        self.setup_mbs_menu()

        # yaml manager for mbs nodes configuration
        try:
            self.node_yaml = YamlManager("config/mbs_nodes.yaml") # yaml manager for mbs nodes configuration
        except FileNotFoundError as e:
            logger.error(f"Error loading YAML file: {e}")
            QMessageBox.critical(self, "Error", f"Configuration file not found: {e}")
            sys.exit(1)
        
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

        for node_dict in self.node_yaml.get_dict()['nodes']:
            MBSNode(node_dict)
            self.layout.addWidget(MBSNode.list_of_nodes[-1]) # add the last created node to the layout
            MBSNode.list_of_nodes[-1].menu = self.menubar.addMenu(f"{MBSNode.list_of_nodes[-1].name}")
            self.build_node_menu(MBSNode.list_of_nodes[-1]) # build the menu for the last created node
            logger.debug(f"Added Node from YAML: {node_dict}")


        self.nodes = [] # initialize the nodes list in the main window instance
        self.nodes = MBSNode.list_of_nodes.copy() # copy the list of nodes from MBSNode class to the main window instance for easier access    


        # -------------------------------------------------------------------------------------------
        # starting threads
        self.threadpool = QThreadPool()
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.node_worker = NodeWorker(MBSNode.list_of_nodes)
        self.node_worker.signals.data.connect(self.data_received)
        self.threadpool.start(self.node_worker)

        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            # self.resize(self.ww, self.hh)
            self.setFixedWidth(614)

        else:
            # screen = Display(os.environ['DISPLAY']).screen() 
            try:
                screen = Display(os.environ['DISPLAY']).screen() 
            except Exception as e:
                logger.error(f"Cannot connect to X server. Exception: {e}\n")
                screen = type('obj', (object,), {})()  # create empty object
                screen.width_in_pixels = 1920
                screen.height_in_pixels = 1080
            self.move(  int(screen.width_in_pixels/2)+10,
                        int(0.01*screen.height_in_pixels))
        
        self.setWindowTitle("MBS Node Manager")
        self.show()
        self.raise_()

    #==========================================================================
    @pyqtSlot(dict)
    def data_received (self, data_dict):
        ''' timer loop to HMP readout and status check '''
       
        # logger.debug(f"Data received: {data_dict}")

        self.ping_toggling = not getattr(self, 'ping_toggling', False) # invert the toggling value to alternate colors on each check
        for node in MBSNode.list_of_nodes:
            if f"alive_{node.name}" in data_dict:
                if data_dict[f"alive_{node.name}"] == True:
                    if self.ping_toggling:
                        node.status_ping.setStyleSheet(f"background-color: lightgreen; border-radius: {node.radius}px;")
                    else:
                        node.status_ping.setStyleSheet(f"background-color: green; border-radius: {node.radius}px;")
                else:
                    if self.ping_toggling:
                        node.status_ping.setStyleSheet(f"background-color: pink; border-radius: {node.radius}px;")
                    else:
                        node.status_ping.setStyleSheet(f"background-color: red; border-radius: {node.radius}px;")
                del data_dict[f"alive_{node.name}"] # remove the key to avoid processing it again

    #==========================================================================
    def open_external_browsers(self):

        for node in MBSNode.list_of_nodes:
            node_host = node.node_host
            logger.info(f"Opening {node_host} dashboard...")
            node.open_external_browser()
            
    
    #==========================================================================
    def show_all_dashboards(self):

        for node in MBSNode.list_of_nodes:
            logger.info(f"Showing {node.name} dashboard...")
            node.show_window()

    #==========================================================================
    def paintEvent(self, event):
        super().paintEvent(event)
        # painter = QPainter(self)
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # # Draw lines between nodes
        # pen = QtGui.QPen(Qt.GlobalColor.red, 2)
        # painter.setPen(pen)

        # # Get the center points of the nodes
        # node1_center = self.node_TOF.geometry().center()
        # node2_center = self.node_MUSIC.geometry().center()
        # node3_center = self.node_SIFI.geometry().center()
        # node4_center = self.node_TIMESORTER.geometry().center()
        # # Draw lines between nodes
        # painter.drawLine(node1_center, node2_center)
        # painter.drawLine(node2_center, node3_center)
        # painter.drawLine(node3_center, node4_center)
        # painter.drawLine(node4_center, node1_center)
        
    #==========================================================================
    def closeEvent(self, event):
        '''Must stay with Main widget'''
        logger.debug("closeEvent")
        self.save_window_data() # save window position and size on close

        # close all node browser windows
        for node in MBSNode.list_of_nodes:
             node.browser_window.close() # close browser windows

        # stop the worker thread
        self.node_worker.is_running = False  # Stop the worker loop
        self.node_worker.stop()  # Stop the worker
        self.threadpool.waitForDone()

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

    window = MbsNodeManager()

    sys.exit(app.exec())
