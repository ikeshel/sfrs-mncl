#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys, os
from loguru import logger
from Xlib.display import Display


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
##
sys.path.append('package')
from win_pos_manager   import WindowPositionManager
from menu_bar         import MenuBarManager

## MBS Node Manager Main Window
##
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

        self.node_TOF = self.create_node("ToF", "x86l-132")
        self.layout.addWidget(self.node_TOF)

        self.node_MUSIC = self.create_node("MUSIC", "x86l-170")
        self.layout.addWidget(self.node_MUSIC)

        self.node_SIFI = self.create_node("SiFi", "x86l-253")
        self.layout.addWidget(self.node_SIFI)

        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            # self.resize(self.ww, self.hh)
            self.setFixedWidth(self.ww)

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
    def create_node(self, name="Node", link="http://localhost"):

        node = QWidget()
        node.setObjectName(f"node_{name}")
        node.setFixedSize(400, 150)
        node.setStyleSheet("background-color: white; border: 1px solid black;")

        # Create the SVG widget and add it to the container
        from PyQt5.QtSvg import QSvgWidget
        node_svg = QSvgWidget("images/node.svg")

        svg_layout = QtWidgets.QVBoxLayout()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addWidget(node_svg)       
        node.setLayout(svg_layout)

        self.lbl_node_name = QtWidgets.QLabel(node)
        self.lbl_node_name.setObjectName(f"lbl_{name}")
        self.lbl_node_name.setGeometry(QtCore.QRect(10, 5, 70, 35))
        self.lbl_node_name.setAlignment(Qt.AlignCenter)
        self.lbl_node_name.setFont(QFont("Arial", 10, QFont.Bold))
        self.lbl_node_name.setText(f"{name}\n{link}")
        self.lbl_node_name.setCursor(Qt.PointingHandCursor)
        self.lbl_node_name.mousePressEvent = lambda event: os.system(f"xdg-open {link}:8899/MBS/localhost/ControlGUI/")
        self.lbl_node_name.setToolTip(f"Click to open {name} Dashboard")                                

        return node
    
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
        self.save_window_data()

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