#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "1.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import sys, os, time
from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6 import QtGui
from loguru import logger
from Xlib.display import Display

##
from PyQt6.QtCore import QSignalBlocker, QThread, Qt, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QGridLayout
from PyQt6.QtCore import QThreadPool, QObject, QRunnable
from PyQt6.QtGui import QFont, QPixmap

##
sys.path.append('package')
# from gui_env import ensure_gui_environment
# ensure_gui_environment()

from mbs_node         import MBSNode
from mncl_logger      import MnclLogger

from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager
from ssh_commander    import SSHCommander

# GUI
sys.path.append('gui')

# Constants
BOARD_CHANNEL_NUMBER = 128
BOARDS_UP = 6
BOARDS_DOWN = 6
BOARDS_RIGHT = 2
BOARDS_LEFT = 2
BOARDS_TOTAL = BOARDS_UP + BOARDS_DOWN + BOARDS_RIGHT + BOARDS_LEFT
CHANNEL_TOTAL = BOARD_CHANNEL_NUMBER * BOARDS_TOTAL

###############################################################################
class SciFiWorkerSignals(QObject):
    """ Signals to be emitted from the worker thread """
    data = pyqtSignal(dict)

###############################################################################
class SciFiWorker(QRunnable):
    """ Worker thread that performs a task in the background. """

    def __init__(self, nodes=None):
        super(SciFiWorker, self).__init__()

        self.nodes       = nodes
        self.signals     = SciFiWorkerSignals()
        self.is_running  = True
        self.datadict    = {}

        logger.debug(f"{__class__.__name__} started")

        self.delay_ms = 1000 # milliseconds
        self.last_time = 0

    #==========================================================================
    def run(self):

        logger.debug("SciFiWorker.run()")

        while True:
            if self.is_running == False:
                logger.debug("SciFiWorker.run() break")
                break

            QThread.msleep(self.delay_ms)
            
            self.datadict['time'] = time.time() # seconds
            if self.last_time < self.datadict['time']-1: # check every 1 second
                self.last_time = self.datadict['time']
            
            self.signals.data.emit( self.datadict ) # emit the data when it's ready

        logger.debug("SciFiWorker.run() finished")

    #==========================================================================
    def stop(self):
        logger.debug("SciFiWorker.stop()")
        self.is_running = False


#==============================================================================
## Threshold Channel Widget
#==============================================================================
class Ui_SciFiChannel(object):

    def __init__(self, channel: int):
        self.channel = channel

    def setupUi(self, SciFiChannel):
        SciFiChannel.setObjectName(f"SciFiChannel_{self.channel}")
        # SciFiChannel.resize(10, 10)

        self.layoutWidget = QtWidgets.QWidget(parent=SciFiChannel)
        # self.layoutWidget.setGeometry(QtCore.QRect(5, 10, 50, 30))

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        # self.horizontalLayout.setContentsMargins(2,2,2,2)

        self.groupBox = QtWidgets.QGroupBox(parent=self.layoutWidget)
        self.groupBox.setTitle(f"CH {self.channel+1}")
        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBoxLayout = QtWidgets.QHBoxLayout(self.groupBox)
        # self.groupBoxLayout.setContentsMargins(2,2,2,2)

        self.isb_dac = QtWidgets.QSpinBox(parent=self.groupBox)
        self.isb_dac.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.isb_dac.setMaximum(1023)
        self.isb_dac.setProperty("value", 0)
        self.groupBoxLayout.addWidget(self.isb_dac)


#==============================================================================
## Threshold Channel Widget
#==============================================================================
class Ui_BoardInfo(object):

    def __init__(self, board: int):
        self.board = board

    def setupUi(self, BoardInfo):
        BoardInfo.setObjectName(f"BoardInfo_{self.board}")
        BoardInfo.resize(100, 100)

        self.layoutWidget = QtWidgets.QWidget(parent=BoardInfo)
        self.layoutWidget.setGeometry(QtCore.QRect(5, 10, 50, 30))

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        # self.horizontalLayout.setContentsMargins(2,2,2,2)

        self.groupBox = QtWidgets.QGroupBox(parent=self.layoutWidget)
        self.groupBox.setTitle(f"Board {self.board+1}")
        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBoxLayout = QtWidgets.QGridLayout(self.groupBox)
        # self.groupBoxLayout.setContentsMargins(2,2,2,2)

        # Temperatures in deg C
        # SciFi_652 FPGA: 42.2
        # SciFi_652 SiPM sensor: 37.9
        # SciFi FEB sensor: 0.0
        fpga_temp = 43.2
        SiPM_temp = 38.9
        font = QFont("Arial", 12, QFont.Weight.Bold)
        lable_alignment = QtCore.Qt.AlignmentFlag.AlignCenter

        self.lab_fpga = QLabel(parent=self.groupBox)
        self.lab_fpga.setText(f"FPGA {fpga_temp:.1f} °C")
        self.lab_fpga.setFont(font)
        self.lab_fpga.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_fpga, 0, 0) # row, column, rowspan, colspan

        self.lab_sipm = QLabel(parent=self.groupBox)
        self.lab_sipm.setText(f"SiPM {SiPM_temp:.1f} °C")
        self.lab_sipm.setFont(font)
        self.lab_sipm.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_sipm, 1, 0) # row, column, rowspan, colspan




#==============================================================================
## MBS Node Manager Main Window
#==============================================================================
class SciFiMainWindow(  QMainWindow, 
                        MnclLogger,
                        WindowPositionManager, 
                        MenuBarManager,
                        SSHCommander):

    #==========================================================================
    def __init__(self):

        super().__init__()

        MnclLogger.__init__(self)
        self.setup_logger()

        node = {'host_name': 'x86l-253', 'node_name': 'SciFi', 'directory': 'SiFi', 'active': True, 'pc_type': 'intel_pc'}

        self.nodes = []
        self.nodes.append(MBSNode(node))

        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        SSHCommander.__init__(self, hostname='x86l-253') # initialize SSHCommander with node_host


        # node widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.v_leyout = QVBoxLayout()
        self.central_widget.setLayout(self.v_leyout)

        # Create a tab widget

        self.tab_widget = QTabWidget()
        self.v_leyout.addWidget(self.tab_widget)

        # Create tabs
        self.tab_main = QWidget()
        self.tab_thresholds = QWidget()

        #_/main\_____
        self.tab_widget.addTab(self.tab_main, "Main")

        self.tab_main_layout = QGridLayout()
        # self.tab_main_layout.setContentsMargins(0, 0, 0, 0)

        SciFi_svg = QLabel()
        SciFi_svg.setPixmap(QPixmap(f"images/det_scifi.svg"))
        # SciFi_svg.setScaledContents(True)
        SciFi_svg.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        SciFi_svg.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        
        self.tab_main_layout.addWidget(SciFi_svg, 1, 1, 2, 6) # add to grid layout

        self.board = [None]*BOARDS_TOTAL # 
        # self.board = [None]*16 # 
        layout = [(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), 
                  (0,1), (0,2), 
                  (1,3), (2,3), (3,3), (4,3), (5,3), (6,3), 
                  (7,1), (7,2)]
        for i in range(len(self.board)):
            self.board[i] = Ui_BoardInfo(i)
            self.board[i].setupUi(self)
            self.tab_main_layout.addWidget(self.board[i].layoutWidget, layout[i][1], layout[i][0]) # add to grid layout

        self.tab_main.setLayout(self.tab_main_layout)
       

        #_/thresholds\_____
        self.tab_widget.addTab(self.tab_thresholds, "Thresholds")
        # Thresholds tab: create a grid layout and add 16 SciFiChannel widgets
        # Create a grid layout for two columns and 8 rows
        self.tab_thresholds_layout = QVBoxLayout()
        self.tab_thresholds.setLayout(self.tab_thresholds_layout)
                       
        self.gl_threshold = QGridLayout()
        self.tab_thresholds_layout.addLayout(self.gl_threshold)


        self.scifi_ch = [None]*BOARD_CHANNEL_NUMBER # create a list to hold the SciFiChannel widgets
        for i in range(len(self.scifi_ch)):
            self.scifi_ch[i] = Ui_SciFiChannel(i)
            self.scifi_ch[i].setupUi(self)
            self.gl_threshold.addWidget(self.scifi_ch[i].layoutWidget, i//16, i%16) # add to grid layout

            self.scifi_ch[i].isb_dac.valueChanged.connect(lambda value, ch=i: self.on_dac_value_changed(ch, value))

        #_/default\_____
        self.tab_widget.setCurrentIndex(0) # set default tab to 

        # -------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------------
        # starting threads
        self.threadpool = QThreadPool()
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.tamex_worker = SciFiWorker(self)
        self.tamex_worker.signals.data.connect(self.data_received)
        self.threadpool.start(self.tamex_worker)

        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            self.resize(self.ww, self.hh)
            # self.setFixedWidth(600)

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

        self.setWindowTitle("SciFi Manager")
        self.show()
        self.raise_()

    #==========================================================================
    def on_ckbx_ch_state_changed(self, ch: int, state: int):
        if ch == -1:
            # Handle the "all channels" checkbox
            for i in range(8):
                with QSignalBlocker(getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}")):
                    getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}").setChecked(bool(state))
        else:
            # Handle individual channel checkbox
            with QSignalBlocker(self.tamex_trigger_tab.ckbx_ch_all):
                self.tamex_trigger_tab.ckbx_ch_all.setChecked(False) # uncheck "all channels" if any individual channel is changed

            if all(getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}").isChecked() for i in range(8)):
                self.tamex_trigger_tab.ckbx_ch_all.setChecked(True) # check "all channels" if all individual channels are checked

        self.list_of_trigger_channels = [i for i in range(8) if getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}").isChecked()]
        logger.debug(f"Current list of trigger channels: {self.list_of_trigger_channels}")

        # create bitmask from list of channels and write to TAMEX via GOC
        # only every second channel works. 0, 2, ... 16
        self.trigger_mask = sum(1 << (2*i) for i in self.list_of_trigger_channels) # create bitmask from list of channels
        logger.debug(f"Current trigger mask: {self.trigger_mask:08b}")
        logger.debug(f"Current trigger mask (hex): {self.trigger_mask:02x}")
        # self.goc_format = f"goc -w -x 0 0 0x330010 0x{self.trigger_mask:02x}" # format as hex string for GOC command
        # logger.debug(f"Current trigger mask (GOC format): {self.goc_format}")

        return_code, stdout, stderr = self.goc_write(sfp=0, dev=0, address=0x330010, value=self.trigger_mask) # write the trigger mask to the TAMEX via GOC

        logger.info(f"GOC Read Return code: {return_code}")
        logger.info(f"GOC Read Output: {stdout}")
        if stderr:
            logger.error(f"GOC Read Error: {stderr}")


    #==========================================================================
    @pyqtSlot(dict)
    def data_received (self, data_dict):
        ''' timer loop to HMP readout and status check '''
       
        # logger.debug(f"Data received: {data_dict}")

        self.ping_toggling = not getattr(self, 'ping_toggling', False) # invert the toggling value to alternate colors on each check

    #==========================================================================
    def sfp_selection_changed(self, index):
        logger.debug(f"SFP selection changed to index {index}")
        # Implement the logic to handle the SFP selection change here

    #==========================================================================
    # DAC value changed by spinbox
    def on_dac_value_changed(self, ch, value):
        logger.success(f"Channel {ch+1} DAC value changed to {value}")

   
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

    window = SciFiMainWindow()
    sys.exit(app.exec())
