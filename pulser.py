#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "1.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import argparse
import sys, os
import signal
from loguru import logger
from Xlib.display import Display

##
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QCheckBox, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox)

##
sys.path.append('package')
from mncl_logger      import MnclLogger
from win_pos_manager  import WindowPositionManager
from ssh_commander    import SSHCommander

# /frs/usr/ikeshel/Pulser10Hz/clk-gen-standalone dev/ttyUSB0 IO3 15 0.1 0
#
PULSER_COMMAND_TEMPLATE = "/frs/usr/ikeshel/Pulser10Hz/clk-gen-standalone {device} IO3 {freq} {high_phase} {phase_shift}"

#==============================================================================
class PulserWindow( QMainWindow, 
                    MnclLogger,
                    WindowPositionManager,
                    SSHCommander):
    
    #==========================================================================
    def __init__(self):

        super().__init__()

        WindowPositionManager.__init__(self)

        SSHCommander.__init__(self, PULSER_NODE)  # Where the pulser is connected, for now hardcoded, can be made dynamic later

        MnclLogger.__init__(self)
        self.setup_logger() 

        self.init_ui()
    
    #==========================================================================
    def init_ui(self) -> None:
        widget = QWidget()
        main_layout = QVBoxLayout()
        
        col1 = QVBoxLayout()
        col1.addWidget(QLabel(f"Node: {PULSER_NODE}"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Row 1: USB Device, Set Button, and empty space
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("USB Device:"))

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Select the USB device for the pulser")
        self.device_combo.setDisabled(True) # disable until devices are populated
        self.populate_usb_devices() # needs to be implemented to detect available /dev/ttyUSB* devices
        row1.addWidget(self.device_combo)
        col1.addLayout(row1)
        main_layout.addLayout(col1)

        row12 = QHBoxLayout()
        chkb_IO=[]
        for i in range(3):
            chkb_IO.append(QCheckBox(f"IO{i+1}"))
            chkb_IO[i].setChecked(i==2) # only IO3 is checked by default
            chkb_IO[i].setDisabled(True) # IO1 is disabled
            row12.addWidget(chkb_IO[i])
        main_layout.addLayout(row12)

        # Row 2: Frequency label and spinbox
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Frequency:"))
        self.spbx_freq = QSpinBox()
        self.spbx_freq.setSuffix(" [Hz]")
        self.spbx_freq.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spbx_freq.setRange(0, 1_000_000)
        self.spbx_freq.setValue(10)
        self.spbx_freq.setToolTip("Set the frequency of the pulser in Hz")
        row2.addWidget(self.spbx_freq)
        main_layout.addLayout(row2)
        
        # Row 3: High-phase label and spinbox
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("High-phase:"))
        self.spbx_highPhase = QSpinBox()
        self.spbx_highPhase.setSuffix(" [ns]")
        self.spbx_highPhase.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spbx_highPhase.setRange(0, 1_000_000) # allow up to 1 second high-phase
        self.spbx_highPhase.setValue(100)
        self.spbx_highPhase.setToolTip("Set the high-phase of the pulser in ns")
        row3.addWidget(self.spbx_highPhase)
        main_layout.addLayout(row3)
        
        # Row 4: Phase shift label and spinbox
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Phase shift:"))
        self.spbx_phaseShift = QSpinBox()
        self.spbx_phaseShift.setSuffix(" [ns]")
        self.spbx_phaseShift.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spbx_phaseShift.setRange(0, 1000000) # allow up to 1 second phase shift
        self.spbx_phaseShift.setValue(0)
        self.spbx_phaseShift.setToolTip("Set the phase shift of the pulser in ns")
        row4.addWidget(self.spbx_phaseShift)
        main_layout.addLayout(row4)

        self.set_button = QPushButton("Set")
        self.set_button.setFixedHeight(40)
        self.set_button.setStyleSheet("font-size: 16px;")
        self.set_button.setToolTip("Apply the settings to the pulser")
        self.set_button.setShortcut("Return")  # Pressing Enter will trigger the button
        
        self.set_button.clicked.connect(self.on_set_clicked)
        main_layout.addWidget(self.set_button)

        main_layout.addStretch()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        ## -------------------------------------------------------------------------------------------
        ## read window position
        if self.read_window_data():
            logger.debug(f"Window position: x={self.xx}, y={self.yy}, "
                         f"width={self.ww}, height={self.hh}")
            self.move(self.xx, self.yy)
            self.resize(self.ww, self.hh)
            # self.setFixedWidth(600)

        else:
            try:
                screen = Display(os.environ['DISPLAY']).screen() 
            except Exception as e:
                print(f"Cannot connect to X server. Exception: {e}")
                screen = type('obj', (object,), {})()  # create empty object
                screen.width_in_pixels = 100
                screen.height_in_pixels = 100
            self.move(  int(screen.width_in_pixels/2)+10,
                        int(0.01*screen.height_in_pixels))

        self.setWindowTitle("10Hz Pulser Control")
        self.show()
        self.raise_()

    #==========================================================================
    def populate_usb_devices(self) -> None:

        self.device_combo.addItem(f"/dev/ttyUSB0")
    
    #==========================================================================
    def on_set_clicked(self) -> None:
        val1 = self.spbx_freq.value()
        val2 = self.spbx_highPhase.value()
        val3 = self.spbx_phaseShift.value()
        device = self.device_combo.currentText()[1:]  # remove leading '/' from device path
        
        # ikeshel@X86L-132: ~/Pulser10Hz > ./clk-gen-standalone                                                                                                                            
        # usage: ./clk-gen-standalone eb-path [ <io-name> <freq[Hz]> <high-phase[us]> <phase-shift[us]> ]
        # ./clk-gen-standalone dev/ttyUSB0 IO3 10 0.1 0
        logger.debug(f"Set: Input1={val1}, Input2={val2}, Input3={val3}, Device={device}")
        
        command = PULSER_COMMAND_TEMPLATE.format(
            device=device,
            freq=val1,
            high_phase=val2/1000, # convert ns to µs
            phase_shift=val3/1000 # convert µs to µs (no change, but keeping the template consistent)
        )
        self.run_screen_command("com", command)

    #==========================================================================
    def closeEvent(self, event) -> None:
        self.save_window_data() # save window position and size on close


#==============================================================================
##
#==============================================================================
if __name__ == "__main__":
 
    list_of_nodes = ["x86l-132", "x86l-253"]  # Example list of nodes

    parser = argparse.ArgumentParser()
    parser.add_argument('--node', '-n', help='Comma-separated list of nodes')

    args = parser.parse_args()

    # Determine which node to use
    if args.node:
        selected_node = args.node
        if selected_node not in list_of_nodes:
            logger.error(f"Error: Node '{selected_node}' not in available nodes: {', '.join(list_of_nodes)}")
            sys.exit(1)
    else:
        selected_node = list_of_nodes[0]  # Use first node as default
    
    # Override PULSER_NODE with selected node
    global PULSER_NODE
    PULSER_NODE = selected_node

    app = QApplication([])

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # restore default Ctrl+C behavior

    window = PulserWindow()
    
    sys.exit(app.exec())