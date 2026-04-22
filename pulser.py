#!/usr/bin/env python3

import sys, os
import signal
from loguru import logger
from Xlib.display import Display

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox)
from PyQt6.QtWidgets import QHBoxLayout

sys.path.append('package')
from win_pos_manager  import WindowPositionManager

class PulserWindow(QMainWindow, WindowPositionManager):
    def __init__(self):
        super().__init__()
        WindowPositionManager.__init__(self)
        self.init_ui()
    
    def init_ui(self):
        widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Row 1: USB Device, Set Button, and empty space
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("USB Device:"))
        self.device_combo = QComboBox()
        self.populate_usb_devices()
        row1.addWidget(self.device_combo)
        main_layout.addLayout(row1)
        
        # Row 2: Frequency label and spinbox
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Frequency:"))
        self.spinbox1 = QSpinBox()
        self.spinbox1.setSuffix(" [Hz]")
        self.spinbox1.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spinbox1.setRange(0, 1000)
        self.spinbox1.setValue(10)
        # row2.addStretch()
        row2.addWidget(self.spinbox1)
        main_layout.addLayout(row2)
        
        # Row 3: High-phase label and spinbox
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("High-phase:"))
        self.spinbox2 = QSpinBox()
        self.spinbox2.setSuffix(" [ns]")
        self.spinbox2.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spinbox2.setRange(0, 1000)
        self.spinbox2.setValue(100)
        row3.addWidget(self.spinbox2)
        main_layout.addLayout(row3)
        
        # Row 4: Phase shift label and spinbox
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Phase shift:"))
        self.spinbox3 = QSpinBox()
        self.spinbox3.setSuffix(" [µs]")
        self.spinbox3.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spinbox3.setRange(0, 1000)
        self.spinbox3.setValue(0)
        row4.addWidget(self.spinbox3)
        main_layout.addLayout(row4)

        self.set_button = QPushButton("Set")
        self.set_button.clicked.connect(self.on_set_clicked)
        main_layout.addWidget(self.set_button)

        main_layout.addStretch()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
                        
        layout.addStretch()
        widget.setLayout(layout)
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
            # screen = Display(os.environ['DISPLAY']).screen() 
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

    
    def populate_usb_devices(self):
        self.device_combo.addItem(f"/dev/ttyUSB0")
    
    def on_set_clicked(self):
        val1 = self.spinbox1.value()
        val2 = self.spinbox2.value()
        val3 = self.spinbox3.value()
        device = self.device_combo.currentText()
        
        # ikeshel@X86L-132: ~/Pulser10Hz > ./clk-gen-standalone                                                                                                                            
        # usage: ./clk-gen-standalone eb-path [ <io-name> <freq[Hz]> <high-phase[us]> <phase-shift[us]> ]
        # ./clk-gen-standalone dev/ttyUSB0 IO3 10 0.1 0
        print(f"Set: Input1={val1}, Input2={val2}, Input3={val3}, Device={device}")

        command = f"./clk-gen-standalone {device} IO3 {val1} {val2/1000:.3f} {val3/1000:.3f}"
        print(f"Executing command: {command}")
        # os.system(command)

    #==========================================================================
    def closeEvent(self, event):
        '''Must stay with Main widget'''
        logger.debug("closeEvent")
        self.save_window_data() # save window position and size on close

if __name__ == "__main__":
    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # restore default Ctrl+C behavior

    window = PulserWindow()
    window.show()
    sys.exit(app.exec())