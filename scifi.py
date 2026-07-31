#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "1.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import sys, os, time
from loguru import logger
from Xlib.display import Display
import epics

##
from PyQt6.QtCore import (QUrl, Qt, QThread, QThreadPool, QRunnable,  
                          pyqtSlot, pyqtSignal, 
                          QObject, QSignalBlocker, QRect)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QSizePolicy,
                             QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                             QGroupBox, QSpinBox)
from PyQt6.QtGui import QFont, QPixmap

##
sys.path.append('package')
# from gui_env import ensure_gui_environment
# ensure_gui_environment()

from mncl_logger      import MnclLogger

from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager
from ssh_commander    import SSHCommander
from mbs_browser      import MBSBrowser

# # GUI
# sys.path.append('gui')

# Constants
BOARD_CHANNEL_NUMBER = 128
BOARDS_UP = 6
BOARDS_DOWN = 6
BOARDS_RIGHT = 2
BOARDS_LEFT = 2
BOARDS_TOTAL = BOARDS_UP + BOARDS_DOWN + BOARDS_RIGHT + BOARDS_LEFT
CHANNEL_TOTAL = BOARD_CHANNEL_NUMBER * BOARDS_TOTAL

SCIFI_BOARD_MAPPING = {
    0:  {'sfp': 0, 'dev': 0, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 1
    1:  {'sfp': 0, 'dev': 1, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 2
    2:  {'sfp': 0, 'dev': 2, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 3
    3:  {'sfp': 0, 'dev': 3, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 4
    4:  {'sfp': 0, 'dev': 4, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 5
    5:  {'sfp': 0, 'dev': 5, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 6
 
    6:  {'sfp': 1, 'dev': 0, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0}, # Board 7
    7:  {'sfp': 1, 'dev': 1, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0}, # Board 8
 
    8:  {'sfp': 2, 'dev': 0, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 9
    9:  {'sfp': 2, 'dev': 1, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 10
    10: {'sfp': 2, 'dev': 2, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0}, # Board 11
    11: {'sfp': 2, 'dev': 3, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0}, # Board 12
    12: {'sfp': 2, 'dev': 4, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 13
    13: {'sfp': 2, 'dev': 5, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},  # Board 14

    14: {'sfp': 3, 'dev': 0, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},   # Board 15
    15: {'sfp': 3, 'dev': 1, 'pv_fpga':None, 'fpga_temp': 0.0, 'pv_sipm': None, 'sipm_temp': 0.0},   # Board 16
    # Add more boards as needed
}

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
                for board_id, board in SCIFI_BOARD_MAPPING.items():
                    sfp = board['sfp']
                    dev = board['dev']
                    fpga_temp = None
                    sipm_temp = None

                    if board['pv_fpga'].wait_for_connection(timeout=1.0):
                        fpga_temp = board['pv_fpga'].get()
                    else:
                        fpga_temp = 0.0

                    if board['pv_sipm'].wait_for_connection(timeout=1.0):
                        sipm_temp = board['pv_sipm'].get()
                    else:
                        sipm_temp = 0.0

                    if board['pv_bias_set'].wait_for_connection(timeout=1.0):
                        bias_set = board['pv_bias_set'].get()
                    else:
                        bias_set = 0.0

                    if board['pv_bias_rbv'].wait_for_connection(timeout=1.0):
                        bias_rbv = board['pv_bias_rbv'].get()
                    else:
                        bias_rbv = 0.0

                    if board['pv_bias_state'].wait_for_connection(timeout=1.0):
                        bias_state = board['pv_bias_state'].get()
                    else:
                        bias_state = 0

                    self.datadict[f'board_{sfp}_{dev}_fpga_temp'] = fpga_temp
                    self.datadict[f'board_{sfp}_{dev}_sipm_temp'] = sipm_temp
                    self.datadict[f'board_{sfp}_{dev}_bias_set'] = bias_set
                    self.datadict[f'board_{sfp}_{dev}_bias_rbv'] = bias_rbv
                    self.datadict[f'board_{sfp}_{dev}_bias_state'] = bias_state
            
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

    def __init__(self, channel: int, sfp: int = 0, dev: int = 0):
        self.channel = channel
        self.sfp = sfp
        self.dev = dev

    def setupUi(self, SciFiChannel):
        SciFiChannel.setObjectName(f"SciFiChannel_{self.channel}")
        # SciFiChannel.resize(10, 10)

        self.layoutWidget = QWidget(parent=SciFiChannel)
        # self.layoutWidget.setGeometry(.QRect(5, 10, 50, 30))

        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        # self.horizontalLayout.setContentsMargins(2,2,2,2)

        self.groupBox = QGroupBox(parent=self.layoutWidget)
        self.groupBox.setTitle(f"CH {self.channel+1}")
        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBoxLayout = QHBoxLayout(self.groupBox)
        # self.groupBoxLayout.setContentsMargins(2,2,2,2)

        self.isb_dac = QSpinBox(parent=self.groupBox)
        self.isb_dac.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.isb_dac.setMaximum(1023)
        self.isb_dac.setProperty("value", 0)
        self.groupBoxLayout.addWidget(self.isb_dac)


#==============================================================================
## Threshold Channel Widget
#==============================================================================
class Ui_BoardInfo(object):

    def __init__(self, board: int, sfp: int = 0, dev: int = 0):
        self.board = board
        self.sfp = sfp
        self.dev = dev

    def setupUi(self, BoardInfo):
        BoardInfo.setObjectName(f"BoardInfo_{self.board}")

        self.layoutWidget = QWidget(parent=BoardInfo)
        self.layoutWidget.setGeometry(QRect(5, 10, 50, 30))

        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        # self.horizontalLayout.setContentsMargins(2,2,2,2)

        self.groupBox = QGroupBox(parent=self.layoutWidget)
        self.groupBox.setTitle(f"Board {self.board+1}")
        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBoxLayout = QGridLayout(self.groupBox)
        # self.groupBoxLayout.setContentsMargins(2,2,2,2)

        # Temperatures in deg C
        # SciFi_652 FPGA: 42.2
        # SciFi_652 SiPM sensor: 37.9
        # SciFi FEB sensor: 0.0
        fpga_temp = 0.0
        SiPM_temp = 0.0
        fontBold = QFont("Arial", 12, QFont.Weight.Bold)
        lable_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        self.lab_sfp_dev = QLabel(parent=self.groupBox)
        self.lab_sfp_dev.setText(f"SFP {self.sfp}, DEV {self.dev}")
        self.lab_sfp_dev.setFont(QFont("Courier", 12, QFont.Weight.Normal))
        self.lab_sfp_dev.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_sfp_dev, 0, 0)

        self.lab_fpga = QLabel(parent=self.groupBox)
        self.lab_fpga.setText(f"FPGA {fpga_temp:.1f} °C")
        self.lab_fpga.setFont(fontBold)
        self.lab_fpga.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_fpga, 1, 0) # row, column, rowspan, colspan

        self.lab_sipm = QLabel(parent=self.groupBox)
        self.lab_sipm.setText(f"SiPM {SiPM_temp:.1f} °C")
        self.lab_sipm.setFont(fontBold)
        self.lab_sipm.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_sipm, 2, 0) # row, column, rowspan, colspan

        self.lab_bias_title = QLabel(parent=self.groupBox)
        self.lab_bias_title.setText(f"Bias Set | RBV | STATE")
        self.lab_bias_title.setFont(fontBold)
        self.lab_bias_title.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_bias_title, 3, 0) # row, column, rowspan, colspan

        self.lab_bias_display = QLabel(parent=self.groupBox)
        self.lab_bias_display.setText(f" 00.0 V | 00.0 V | 0")
        self.lab_bias_display.setFont(QFont("Courier", 12, QFont.Weight.Normal))
        self.lab_bias_display.setAlignment(lable_alignment)
        self.groupBoxLayout.addWidget(self.lab_bias_display, 4, 0) # row, column, rowspan, colspan

#==============================================================================
## SciFi Main Window
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

        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        SSHCommander.__init__(self, hostname='x86l-253') # initialize SSHCommander with node_host

        self.init_epics()

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
        SciFi_svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.tab_main_layout.addWidget(SciFi_svg, 1, 1, 2, 6) # add to grid layout

        self.browser_window = MBSBrowser(url=f"")

        self.board = [None]*BOARDS_TOTAL # 
        # self.board = [None]*16 # 

        # draw the boards in the layout according to the SciFi detector layout
        layout = [(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), 
                  (0,2), (0,1), 
                  (6,3), (5,3), (4,3), (3,3), (2,3), (1,3),
                  (7,1), (7,2)]
        for board_id, board in SCIFI_BOARD_MAPPING.items():
            sfp = board['sfp']
            dev = board['dev']
            self.board[board_id] = Ui_BoardInfo(board_id, sfp, dev)
            self.board[board_id].setupUi(self)
            self.board[board_id].lab_fpga.mousePressEvent = lambda event, sfp=sfp, dev=dev: self.show_hide_dashboard("FPGA:TEMP", sfp, dev)
            self.board[board_id].lab_sipm.mousePressEvent = lambda event, sfp=sfp, dev=dev: self.show_hide_dashboard("SIPM:TEMP", sfp, dev)
            self.board[board_id].lab_bias_title.mousePressEvent = lambda event, sfp=sfp, dev=dev: self.show_hide_dashboard("SIPM:BIAS_SET", sfp, dev)
            self.board[board_id].lab_bias_display.mousePressEvent = lambda event, sfp=sfp, dev=dev: self.show_hide_dashboard("SIPM:BIAS_RBV", sfp, dev)
            self.tab_main_layout.addWidget(self.board[board_id].layoutWidget, layout[board_id][1], layout[board_id][0]) # add to grid layout

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
    def init_epics(self):
        logger.debug("Initializing EPICS PVs")
        for board_id, board in SCIFI_BOARD_MAPPING.items():
            sfp = board['sfp']
            dev = board['dev']
            board['pv_fpga']=epics.PV(f"SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:FPGA:TEMP")
            board['pv_sipm']=epics.PV(f"SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:SIPM:TEMP")
            # SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:BIAS_SET
            # SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:BIAS_RBV
            # SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:BIAS_STATE
            board['pv_bias_set']=epics.PV(f"SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:SIPM:BIAS_SET")
            board['pv_bias_rbv']=epics.PV(f"SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:SIPM:BIAS_RBV")
            board['pv_bias_state']=epics.PV(f"SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:SIPM:BIAS_STATE")


    #==========================================================================
    def show_hide_dashboard(self, sensor="FPGA:TEMP", sfp=0, dev=0):


        if self.browser_window.isVisible() and self.shown_sensor==sensor and self.shown_sfp==sfp and self.shown_dev==dev:
            self.browser_window.close() # close the existing window before opening a new one
        else:
            url=f"http://dtlpc019.gsi.de:17665/retrieval/ui/viewer/archViewer.html?pv=SFRS:FHF1:SCIFI3:SFP{sfp}:DEV{dev}:{sensor}"
            self.browser_window.view.load(QUrl(url))
            self.shown_sensor = sensor
            self.shown_sfp = sfp
            self.shown_dev = dev
            self.browser_window.move(200, 20) # move the window to a specific position on the screen
            self.browser_window.resize(900, 600) # resize the window to a specific size
            self.browser_window.show()
            self.browser_window.raise_()
            self.browser_window.activateWindow()

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
        for board_id, board_dict in SCIFI_BOARD_MAPPING.items():
            sfp = board_dict['sfp']
            dev = board_dict['dev']
            fpga_temp = data_dict.get(f'board_{sfp}_{dev}_fpga_temp', 0.0)
            sipm_temp = data_dict.get(f'board_{sfp}_{dev}_sipm_temp', 0.0)
            self.board[board_id].lab_fpga.setText(f"FPGA {fpga_temp:.1f} °C")
            self.board[board_id].lab_sipm.setText(f"SiPM {sipm_temp:.1f} °C")

            bias_state = int(data_dict.get(f'board_{sfp}_{dev}_bias_state', 0))
            bias_text = f"{data_dict.get(f'board_{sfp}_{dev}_bias_set', 0.0):4.1f} V | {data_dict.get(f'board_{sfp}_{dev}_bias_rbv', 0.0):.1f} V"
            self.board[board_id].lab_bias_display.setText(bias_text)
            
            if bias_state == 0:
                self.board[board_id].lab_bias_display.setStyleSheet("color: gray;")
            elif bias_state == 1:
                self.board[board_id].lab_bias_display.setStyleSheet("color: darkgreen;")
            elif bias_state == 2:
                self.board[board_id].lab_bias_display.setStyleSheet("color: red;")

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

        # close browser if open
        if self.browser_window.isVisible():
            self.browser_window.close()

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
