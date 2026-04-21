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

##
from PyQt6.QtCore import QSignalBlocker, QThread, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QGridLayout
from PyQt6.QtCore import QThreadPool, QObject, QRunnable

##
sys.path.append('package')
# from gui_env import ensure_gui_environment
# ensure_gui_environment()

from mncl_logger      import MnclLogger
# import mncl_logger

from win_pos_manager  import WindowPositionManager
from menu_bar         import MenuBarManager
from ssh_commander    import SSHCommander

# GUI
sys.path.append('gui')
from tamex_channel import Ui_TamexChannel
from sfp_control   import Ui_SfpControl
from gui_tamex_trigger_tab import Ui_TamexTriggerTab


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

        logger.debug(f"{__class__.__name__} started")

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
                self.last_time = self.datadict['time']
            
            self.signals.data.emit( self.datadict ) # emit the data when it's ready

        logger.debug("TamexWorker.run() finished")

    #==========================================================================
    def stop(self):
        logger.debug("TamexWorker.stop()")
        self.is_running = False

#==============================================================================
## MBS Node Manager Main Window
#==============================================================================
class TamexMainWindow(  QMainWindow, 
                        MnclLogger,
                        WindowPositionManager, 
                        MenuBarManager,
                        SSHCommander):

    #==========================================================================
    def __init__(self):

        super().__init__()

        # MnclLogger.__init__(self)
        self.setup_logger()

        WindowPositionManager.__init__(self)
        MenuBarManager.__init__(self)
        SSHCommander.__init__(self, hostname='x86l-132') # initialize SSHCommander with node_host

        # node widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.v_leyout = QVBoxLayout()
        self.central_widget.setLayout(self.v_leyout)

        # SFP control panel
        self.sfp_control = Ui_SfpControl()
        self.sfp_control.setupUi(self)
        self.sfp_control.layoutWidget.setObjectName("SfpControl")
        self.sfp_control.layoutWidget.setFixedHeight(40)
        self.v_leyout.addWidget(self.sfp_control.layoutWidget)

        self.sfp_control.cob_sfp.currentIndexChanged.connect(self.sfp_selection_changed)

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

        #_/thresholds\_____
        self.tab_widget.addTab(self.tab_thresholds, "Thresholds")
        # Thresholds tab: create a grid layout and add 16 TamexChannel widgets
        # Create a grid layout for two columns and 8 rows
        self.gl_threshold = QGridLayout()
        self.tab_thresholds.setLayout(self.gl_threshold)

        self.tmx_ch = [None]*16
        for i in range(len(self.tmx_ch)):
            self.tmx_ch[i] = Ui_TamexChannel()
            self.tmx_ch[i].setupUi(self)
            self.tmx_ch[i].layoutWidget.setObjectName(f"TamexChannel_{i+1}")
            self.tmx_ch[i].lbl_ch.setText(f"CH {i+1}")
            self.gl_threshold.addWidget(self.tmx_ch[i].layoutWidget, i // 2, i % 2) # add to grid layout

            self.tmx_ch[i].isb_dac.valueChanged.connect(lambda value, ch=i: self.on_dac_value_changed(ch, value))
            self.tmx_ch[i].hsb_dac.valueChanged.connect(lambda value, ch=i: self.on_dac_slider_changed(ch, value))
            self.tmx_ch[i].dsb_mV .valueChanged.connect(lambda value, ch=i: self.on_mv_value_changed(ch, value))

        #_/pulses\_____
        self.tab_widget.addTab(self.tab_pulses, "Trigger")
        self.tamex_trigger_tab = Ui_TamexTriggerTab()
        self.tamex_trigger_tab.setupUi(self.tab_pulses)
        # self.tab_pulses.setLayout(self.tamex_trigger_tab.verticalLayout)
        # self.tab_pulses.setLayout(self.tamex_trigger_tab.layoutWidget.layout())
        self.tamex_trigger_tab.ckbx_ch_all.stateChanged.connect(lambda state, ch=-1: self.on_ckbx_ch_state_changed(ch, state))
        for i in range(8):
            getattr(self.tamex_trigger_tab, f"ckbx_ch_{i}").stateChanged.connect(lambda state, ch=i: self.on_ckbx_ch_state_changed(ch, state))

        #_/clock\_____
        self.tab_widget.addTab(self.tab_clock, "Clock")

        self.tab_widget.setCurrentIndex(2) # set default tab to 

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

        self.setWindowTitle("TAMEX Manager")
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
        self.tmx_ch[ch].dsb_mV.setValue(value * 1000.0 / 1023.0) # update mV

    #==========================================================================
    # DAC value changed by slider
    def on_dac_slider_changed(self, ch, value):
        logger.debug(f"Channel {ch+1} DAC slider changed to {value}")
        self.tmx_ch[ch].isb_dac.setValue(value) # update spinbox
        self.tmx_ch[ch].dsb_mV.setValue(value * 1000.0 / 1023.0) # update mV     

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

    import scripts.CheckForAnotherInstance as check
    if check.CheckForAnotherInstance(sys.argv[0]) != None:
        sys.exit( 0 )


    try:
        window = TamexMainWindow()
        sys.exit(app.exec())
    except Exception as e:
        sys.stderr.write(f"An error occurred: {e}\n")
    
    except KeyboardInterrupt:
        sys.stderr.write("KeyboardInterrupt received. Exiting...\n")
        # window.close() # this will trigger closeEvent and stop the worker thread properly
        sys.exit(app.exec())
