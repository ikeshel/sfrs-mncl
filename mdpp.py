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
# import mncl_logger

from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager
from ssh_commander    import SSHCommander

# GUI
sys.path.append('gui')

# Constants
MUSIC_CHANNEL_NUMBER = 16

###############################################################################
class MdppWorkerSignals(QObject):
    """ Signals to be emitted from the worker thread """
    data = pyqtSignal(dict)

###############################################################################
class MdppWorker(QRunnable):
    """ Worker thread that performs a task in the background. """

    def __init__(self, nodes=None):
        super(MdppWorker, self).__init__()

        self.nodes       = nodes
        self.signals     = MdppWorkerSignals()
        self.is_running  = True
        self.datadict    = {}

        logger.debug(f"{__class__.__name__} started")

        self.delay_ms = 1000 # milliseconds
        self.last_time = 0

    #==========================================================================
    def run(self):

        logger.debug("MdppWorker.run()")

        while True:
            if self.is_running == False:
                logger.debug("MdppWorker.run() break")
                break

            QThread.msleep(self.delay_ms)
            
            self.datadict['time'] = time.time() # seconds
            if self.last_time < self.datadict['time']-1: # check every 1 second
                self.last_time = self.datadict['time']
            
            self.signals.data.emit( self.datadict ) # emit the data when it's ready

        logger.debug("MdppWorker.run() finished")

    #==========================================================================
    def stop(self):
        logger.debug("MdppWorker.stop()")
        self.is_running = False


#==============================================================================
## MBS Node Manager Main Window
#==============================================================================
class Ui_MdppChannel(object):

    def __init__(self, channel: int):
        self.channel = channel

    def setupUi(self, MdppChannel):
        MdppChannel.setObjectName(f"MdppChannel_{self.channel}")
        MdppChannel.resize(393, 53)

        self.layoutWidget = QtWidgets.QWidget(parent=MdppChannel)
        self.layoutWidget.setGeometry(QtCore.QRect(5, 10, 381, 31))
        self.layoutWidget.setObjectName(f"layoutWidget_{self.channel}")

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName(f"horizontalLayout_{self.channel}")

        self.lbl_ch = QtWidgets.QLabel(parent=self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_ch.setFont(font)
        self.lbl_ch.setObjectName(f"lbl_ch_{self.channel}")
        self.setText = f"CH {self.channel+1}"
        self.horizontalLayout.addWidget(self.lbl_ch)

        self.isb_dac = QtWidgets.QSpinBox(parent=self.layoutWidget)
        self.isb_dac.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.isb_dac.setMaximum(1023)
        self.isb_dac.setProperty("value", 0)
        self.isb_dac.setObjectName(f"isb_dac_{self.channel}")
        self.horizontalLayout.addWidget(self.isb_dac)

        self.hsb_dac = QtWidgets.QSlider(parent=self.layoutWidget)
        self.hsb_dac.setMaximum(1023)
        self.hsb_dac.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.hsb_dac.setObjectName(f"hsb_dac_{self.channel}")
        self.horizontalLayout.addWidget(self.hsb_dac)

        self.retranslateUi(MdppChannel)
        QtCore.QMetaObject.connectSlotsByName(MdppChannel)

    def retranslateUi(self, MdppChannel):
        _translate = QtCore.QCoreApplication.translate
        MdppChannel.setWindowTitle(_translate("MdppChannel", "Form"))
        self.lbl_ch.setText(_translate("MdppChannel", f"CH {self.channel+1}"))



#==============================================================================
## MBS Node Manager Main Window
#==============================================================================
class MdppMainWindow(  QMainWindow, 
                        MnclLogger,
                        WindowPositionManager, 
                        MenuBarManager,
                        SSHCommander):

    #==========================================================================
    def __init__(self):

        super().__init__()

        MnclLogger.__init__(self)
        self.setup_logger()

        node = {'host_name': 'x86l-170', 'node_name': 'MUSIC', 'directory': 'MUSIC', 'active': True, 'pc_type': 'intel_nuc'}

        self.nodes = []
        self.nodes.append(MBSNode(node))

        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        SSHCommander.__init__(self, hostname='x86l-170') # initialize SSHCommander with node_host


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
        self.tab_pulses = QWidget()
        self.tab_clock = QWidget()

        #_/main\_____
        self.tab_widget.addTab(self.tab_main, "Main")

        self.tab_main_layout = QVBoxLayout()
        self.tab_main_layout.setContentsMargins(0, 0, 0, 0)

        mdpp_svg = QLabel()
        mdpp_svg.setPixmap(QPixmap(f"images/mdpp16.svg"))
        mdpp_svg.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.tab_main_layout.addWidget(mdpp_svg)

        self.tab_main.setLayout(self.tab_main_layout)
       

        #_/thresholds\_____
        self.tab_widget.addTab(self.tab_thresholds, "Thresholds")
        # Thresholds tab: create a grid layout and add 16 MdppChannel widgets
        # Create a grid layout for two columns and 8 rows
        self.tab_thresholds_layout = QVBoxLayout()
        self.tab_thresholds.setLayout(self.tab_thresholds_layout)
               
        # self.tab_thresholds_layout.addWidget(mdpp_svg)
        
        self.gl_threshold = QGridLayout()
        self.tab_thresholds_layout.addLayout(self.gl_threshold)


        self.tmx_ch = [None]*MUSIC_CHANNEL_NUMBER # create a list to hold the MdppChannel widgets
        for i in range(len(self.tmx_ch)):
            self.tmx_ch[i] = Ui_MdppChannel(i)
            self.tmx_ch[i].setupUi(self)
            self.gl_threshold.addWidget(self.tmx_ch[i].layoutWidget, i, 1) # add to grid layout

            self.tmx_ch[i].isb_dac.valueChanged.connect(lambda value, ch=i: self.on_dac_value_changed(ch, value))
            self.tmx_ch[i].hsb_dac.valueChanged.connect(lambda value, ch=i: self.on_dac_slider_changed(ch, value))

        #_/pulses\_____
        self.tab_widget.addTab(self.tab_pulses, "Trigger")
        # self.tamex_trigger_tab = Ui_TamexTriggerTab()
        # self.tamex_trigger_tab.setupUi(self.tab_pulses)
        # # self.tab_pulses.setLayout(self.tamex_trigger_tab.verticalLayout)
        # # self.tab_pulses.setLayout(self.tamex_trigger_tab.layoutWidget.layout())
        # self.tamex_trigger_tab.ckbx_ch_all.stateChanged.connect(lambda state, ch=-1: self.on_ckbx_ch_state_changed(ch, state))
        # for i in range(8):
        #     getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}").stateChanged.connect(lambda state, ch=i: self.on_ckbx_ch_state_changed(ch, state))

        self.tab_widget.setCurrentIndex(1) # set default tab to 

        # -------------------------------------------------------------------------------------------
        # starting threads
        self.threadpool = QThreadPool()
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.tamex_worker = MdppWorker(self)
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

        self.setWindowTitle("MDPP Manager")
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
        logger.debug(f"Channel {ch+1} DAC value changed to {value}")
        self.tmx_ch[ch].hsb_dac.setValue(value) # update slider

    #==========================================================================
    # DAC value changed by slider
    def on_dac_slider_changed(self, ch, value):
        logger.debug(f"Channel {ch+1} DAC slider changed to {value}")
        self.tmx_ch[ch].isb_dac.setValue(value) # update spinbox

    #==========================================================================
    # mV value changed by double spinbox
    def on_mv_value_changed(self, ch, value):
        logger.debug(f"Channel {ch+1} mV value changed to {value}")
        dac_value = int(value * 1023.0 / 1000.0) # convert mV to DAC value
        self.tmx_ch[ch].isb_dac.setValue(dac_value) # update spinbox
        self.tmx_ch[ch].hsb_dac.setValue(dac_value) # update slider       
    
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

    window = MdppMainWindow()
    sys.exit(app.exec())
