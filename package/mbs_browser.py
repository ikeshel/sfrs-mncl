#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys
from loguru import logger

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

#******************************************************************************
class MBSBrowser(QWidget):

    instance_count = 0
    wm = [10, 10, 10, 10] # window margin
    wp = [10, 10] # window position
    ws = [1800, 900] # window size

    #==========================================================================
    def __init__(self, url="http://x86l-132:8899/MBS/localhost/ControlGUI/"):
        super().__init__()
        self.initUI()
        MBSBrowser.instance_count += 1
        logger.debug(f"Opening MBS Browser instance #{MBSBrowser.instance_count} with URL: {url}")

        self.view = QWebEngineView()
        self.view.load(QUrl(url))
        self.layout.addWidget(self.view)

        self.resize(self.ws[0], self.ws[1])
        self.move(self.wp[0], self.wp[1])
        self.setWindowTitle(f"MBS Browser")
    
    #=====================================================================
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.wm[0], self.wm[1], self.wm[2], self.wm[3])
    

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == "__main__":
    app = QApplication(sys.argv)

    browser = MBSBrowser(sys.argv[1] if len(sys.argv) == 2 else "http://x86l-132:8899/MBS/localhost/ControlGUI/")
    browser.show()

    sys.exit(app.exec_())
