#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys
from loguru import logger

from gui_env import ensure_gui_environment

ensure_gui_environment()

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

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
        self.setWindowTitle("MBS Browser")
    
    #=====================================================================
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.wm[0], self.wm[1], self.wm[2], self.wm[3])
    

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == "__main__":

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # restore default Ctrl+C behavior

    app = QApplication(sys.argv)

    mypv = "SFRS:FHF1:SCIFI2:SFP0:DEV0:SIPM:TEMP" if len(sys.argv) < 2 else sys.argv[1]

    browser = MBSBrowser()

    url=f"http://dtlpc019.gsi.de:17665/retrieval/ui/viewer/archViewer.html?pv={mypv}"
    browser.view.load(QUrl(url))

    browser.move(200, 20) # move the window to a specific position on the screen
    browser.resize(900, 600) # resize the window to a specific size
    browser.show()
    browser.raise_()
    browser.activateWindow()

    sys.exit(app.exec())
