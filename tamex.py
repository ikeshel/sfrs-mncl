#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

#
import sys, os, time
from loguru import logger
from Xlib.display import Display

# 
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThreadPool, QObject, QRunnable, QThread, pyqtSlot, pyqtSignal

#
sys.path.append('package')
from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager

# GUI
sys.path.append('gui')
from tamex_channel import Ui_TamexChannel

###############################################################################
class TamexWorkerSignals(QObject):
    """ Signals to be emitted from the worker thread """
    data = pyqtSignal(dict)

###############################################################################
class TamexWorker(QRunnable):
    """ Worker thread that performs a task in the background. """

    def __init__(self, nodes=None):
        super(TamexWorker, self).__init__()

        self.nodes       = nodes
        self.signals     = TamexWorkerSignals()
        self.is_running  = True
        self.datadict    = {}

        logger.debug(f"{__class__.__module__} started")

        self.delay_ms = 1000 # milliseconds
        self.last_time = 0

    #==========================================================================
    def run(self):

        logger.debug("TamexWorker.run()")

        while True:
            if self.is_running == False:
                logger.debug("TamexWorker.run() break")
                break

            QThread.msleep(self.delay_ms)
            
            self.datadict['time'] = time.time() # seconds
            if self.last_time < self.datadict['time']-1: # check every 1 second

                #
                #

                self.last_time = self.datadict['time']
            
            self.signals.data.emit( self.datadict ) # emit the data when it's ready

        logger.debug("TamexWorker.run() finished")

    #==========================================================================
    def stop(self):
        logger.debug("TamexWorker.stop()")
        self.is_running = False

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
        self.test_log_file  = "logs/tamex_manager.log"
        self.debug_log_file = "logs/debug_tamex_manager.log"
        self.add_loggers()

        # node widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.tmx_ch = [None]*8
        for i in range(len(self.tmx_ch)):
            self.tmx_ch[i] = Ui_TamexChannel()
            self.tmx_ch[i].setupUi(self)
            self.tmx_ch[i].lbl_ch.setText(f"CH {i+1}")
            self.layout.addWidget(self.tmx_ch[i].widget)

        # self.node_TOF = MBSNode("ToF", "x86l-132")
        # self.layout.addWidget(self.node_TOF)

        # self.node_MUSIC = MBSNode("MUSIC", "x86l-170")
        # self.layout.addWidget(self.node_MUSIC)

        # self.node_SIFI = MBSNode("SiFi", "x86l-253")
        # self.layout.addWidget(self.node_SIFI)

        # # add node menus to the main menu bar
        # for node in MBSNode.list_of_nodes:
        #     logger.debug(f"Added node: {node.name} with host {node.node_host} to main window menu")
        #     node.menu = self.menubar.addMenu(f"{node.name}")
        #     self.build_node_menu(node)

        # -------------------------------------------------------------------------------------------
        # starting threads
        self.threadpool = QThreadPool()
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.tamex_worker = TamexWorker(self)
        self.tamex_worker.signals.data.connect(self.data_received)
        self.threadpool.start(self.tamex_worker)

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
    @pyqtSlot(dict)
    def data_received (self, data_dict):
        ''' timer loop to HMP readout and status check '''
       
        logger.debug(f"Data received: {data_dict}")

        self.ping_toggling = not getattr(self, 'ping_toggling', False) # invert the toggling value to alternate colors on each check

            
    
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


        # stop the worker thread
        self.tamex_worker.is_running = False  # Stop the worker loop
        self.tamex_worker.stop()  # Stop the worker
        self.threadpool.waitForDone()

        # accept the close event to allow the window to close
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