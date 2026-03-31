#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

#
import sys, os
from loguru import logger
from Xlib.display import Display

# 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtSvg import QSvgWidget

#
sys.path.append('package')
from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager
from mbs_browser      import MBSBrowser

#==============================================================================
#==============================================================================
# MBS Node Widget
class MBSNode(QtWidgets.QWidget):

    list_of_nodes = [] # class variable to keep track of all node instances

    #=========================================================================
    def __init__(self, name="Node", node_host="localhost"):
        super().__init__()
        self.name = name
        self.node_host = node_host
        self.setObjectName(f"node_{name}")
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        self.init_ui()
        MBSNode.list_of_nodes.append(self) # add instance to the class variable list

    #=========================================================================
    def init_ui(self):
        node_svg = QSvgWidget("images/node.svg")
        
        svg_layout = QtWidgets.QVBoxLayout()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addWidget(node_svg)
        self.setLayout(svg_layout)
        
        self.lbl_node_name = QtWidgets.QLabel(self)
        self.lbl_node_name.setObjectName(f"lbl_{self.name}")
        self.lbl_node_name.setText(f"{self.name}\n{self.node_host}")
        self.lbl_node_name.setCursor(Qt.PointingHandCursor)
        self.lbl_node_name.setToolTip(f"Click to open {self.name} Dashboard")
        self.lbl_node_name.setGeometry(QtCore.QRect(10, 5, 90, 40))
        self.lbl_node_name.setAlignment(Qt.AlignCenter)
        self.lbl_node_name.setFont(QFont("Arial", 10, QFont.Bold))
        self.browser_window = MBSBrowser(url=f"http://{self.node_host}:8899/MBS/localhost/ControlGUI/")
        self.lbl_node_name.mousePressEvent = lambda event: self.show_window()      

    #==========================================================================
    def show_window(self):

        if self.browser_window.isVisible():
            logger.debug(f"{self.name} dashboard is already open. Bringing it to front...")
            self.browser_window.close() # close the existing window before opening a new one
        else:
            self.browser_window.show()
            self.browser_window.raise_()
            self.browser_window.activateWindow()
    
    def closeEvent(self, a0):
        logger.debug(f"Closing node {self.name} window...")
        self.browser_window.close() #if hasattr(self, 'browser_window') else None
        MBSNode.list_of_nodes.remove(self) # remove instance from the class variable list
        return super().closeEvent(a0)



#==============================================================================
## MBS Node Manager Main Window
class MainWindow(QMainWindow, 
                 WindowPositionManager, 
                 MenuBarManager):

    #==========================================================================
    def __init__(self):
        super().__init__()
        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        self.setWindowTitle("MBS Node Manager")

        ## logger
        self.test_log_file  = "logs/mbs_node_manager.log"
        self.debug_log_file = "logs/debug_mbs_node_manager.log"
        self.add_loggers()

        # node widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.node_TOF = MBSNode("ToF", "x86l-132")
        self.layout.addWidget(self.node_TOF)
        self.node_menu.addAction(f"Node {self.node_TOF.name}").triggered.connect(self.node_TOF.show_window)

        self.node_MUSIC = MBSNode("MUSIC", "x86l-170")
        self.layout.addWidget(self.node_MUSIC)
        self.node_menu.addAction(f"Node {self.node_MUSIC.name}").triggered.connect(self.node_MUSIC.show_window)

        self.node_SIFI = MBSNode("SiFi", "x86l-253")
        self.layout.addWidget(self.node_SIFI)
        self.node_menu.addAction(f"Node {self.node_SIFI.name}").triggered.connect(self.node_SIFI.show_window)

        for node in MBSNode.list_of_nodes:
            logger.debug(f"Added node: {node.name} with host {node.node_host} to main window menu")
            self.node_menu.addAction(f"Node {node.name}")


        # self.node_menu.triggered.connect(self.open_external_browser)


        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            # self.resize(self.ww, self.hh)
            self.setFixedWidth(600)

        else:
            # screen = Display(os.environ['DISPLAY']).screen() 
            try:
                screen = Display(os.environ['DISPLAY']).screen() 
            except Exception as e:
                print(f"Cannot connect to X server. Exception: {e}")
                screen = type('obj', (object,), {})()  # create empty object
                screen.width_in_pixels = 1920
                screen.height_in_pixels = 1080
            self.move(  int(screen.width_in_pixels/2)+10,
                        int(0.01*screen.height_in_pixels))
        self.show()
        self.raise_()

    #==========================================================================
    def open_external_browser(self):

        for node in MBSNode.list_of_nodes:
            node_host = node.node_host
            logger.info(f"Opening {node_host} dashboard...")
            os.system(f"xdg-open {node_host}:8899/MBS/localhost/ControlGUI/")
    
    #==========================================================================
    def show_all_dashboards(self):

        for node in MBSNode.list_of_nodes:
            logger.info(f"Showing {node.name} dashboard...")
            node.show_window()

    #==========================================================================
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw lines between nodes
        pen = QtGui.QPen(Qt.black, 2)
        painter.setPen(pen)

        # Get the center points of the nodes
        node1_center = self.node_TOF.geometry().center()
        node2_center = self.node_MUSIC.geometry().center()
        node3_center = self.node_SIFI.geometry().center()

        # Draw lines between nodes
        painter.drawLine(node1_center, node2_center)
        painter.drawLine(node2_center, node3_center)

    #==========================================================================
    def add_loggers(self):
        ## logger loguru settings 
        logger.remove() #remove the old handler.

        logger.add( sys.stdout, 
                    level = "INFO",
                    format = "{time:HH:mm:ss}|{level: >8}| {message}")

        log_fmt =   "<green>{time:YY-MM-DD HH:mm:ss}</green> | "\
                    "<level>{level: <8}</level> | "\
                    "<magenta>{module}</magenta>:<cyan>{function}</cyan>:"\
                    "<yellow>{line}</yellow> - <level>{message}</level>"

        ## for quasi-permanent log file
        logger.add( self.debug_log_file,
                    level       = "DEBUG",
                    mode        = "a", 
                    format      = log_fmt,
                    rotation    = "50 MB",   # rotate after
                    retention   = "3 month", # keep logs for
                    compression = "zip")     # compress rotated logs

        ## for test log file
        logger.add( self.test_log_file,
                    mode="w",
                    level = "DEBUG",
                    format = "<green>{time:YY-MM-DD HH:mm:ss}</green> | "\
                            "<level>{level: <8}</level> | "\
                            "<magenta>{module}</magenta>:<cyan>{function}</cyan>:"\
                            "<yellow>{line}</yellow> - <level>{message}</level>")


    #==========================================================================
    def closeEvent(self, event):
        '''Must stay with Main widget'''
        logger.debug("closeEvent")
        self.save_window_data() # save window position and size on close

        self.node_TOF.close() # close node windows
        self.node_MUSIC.close()
        self.node_SIFI.close()

        event.accept() # let the window close

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == "__main__":

    app = QApplication(sys.argv)
    # app.setStyle('Windows')

    import scripts.CheckForAnotherInstance as check
    if check.CheckForAnotherInstance(sys.argv[0]) != None:
        sys.exit( 0 )

    window = MainWindow()

    sys.exit(app.exec_())