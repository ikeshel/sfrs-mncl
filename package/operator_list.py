
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''  '''

import sys, os

from Xlib.display import Display

try:
    screen = Display(os.environ['DISPLAY']).screen() 
except Exception as e:
    print("Cannot connect to X server. Exiting...")
    screen = type('obj', (object,), {})()  # create empty object
    screen.width_in_pixels = 1920
    screen.height_in_pixels = 1080

from loguru import logger 
#as logger
#logger.remove()
#logger.add(sys.stderr, level="INFO", format="{time:mm:ss} | {level} | {message}")

from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton
from PyQt6.QtCore import (Qt, pyqtSignal)

import constants as mycolor

#==========================================================================
class OperatorList(QWidget):

    checkbox     = []
    SelectedList = []
    strOperators = "Alois Alzheimer"

    #create signal
    operator_selected_signal = pyqtSignal()

    #==========================================================================
    def __init__(self, op_list):
        super().__init__()

        self.ListOfOperators = op_list

        self.font = QtGui.QFont()
        self.font.setPointSize(16)

        layout = QVBoxLayout()
        for proj in op_list:
            self.checkbox.append( QCheckBox( str(proj), self ) )
            self.checkbox[-1].clicked.connect(self.submit)
            self.checkbox[-1].setFont(self.font)
            layout.addWidget(self.checkbox[-1])
        
        # Create a button
        self.button = QPushButton('Submit', self)
        layout.addWidget(self.button)
        self.setLayout(layout)
        self.button.clicked.connect(self.submit_and_close)

        self.win_width  = 200
        self.win_height = 300
        self.setWindowTitle('Select operator')
        self.setFixedWidth(200)

        self.move(int(screen.width_in_pixels-self.win_width), 0)
        # self.show()

    #==========================================================================
    def submit(self):
        
        self.SelectedList.clear()
        self.strOperators = ""
        for index in range(len(self.checkbox)):
            self.checkbox[index].setStyleSheet(mycolor.st3_default)
            if self.checkbox[index].isChecked():
                self.SelectedList.append(self.ListOfOperators[index])
                self.strOperators += self.ListOfOperators[index] + "; "
                self.checkbox[index].setStyleSheet(mycolor.st3_green)

        logger.debug(len(self.SelectedList))
        if len(self.SelectedList) ==0:
            self.strOperators = "Alois Alzheimer"

        logger.debug(self.strOperators)

        self.operator_selected_signal.emit()

    #==========================================================================
    def submit_and_close(self):
        
        self.submit()
        self.close()

    #==========================================================================
    def closeEvent(self, event):
        ''''''
        logger.debug('closeEvent')
        self.close()

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mylist = ['Robert', 'Kerstin', 'Irakli', 'David', 'Dachi']
    ex = OperatorList(mylist)
    ex.show()
    sys.exit(app.exec_())
