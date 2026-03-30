
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

from loguru import logger

from PyQt5.QtWidgets import QMenuBar, QMenu
from PyQt5.QtWidgets import QMessageBox

#==============================================================================
class MenuBarManager:

    #==========================================================================
    def __init__(self):
        self.menubar = self.menuBar()
    
        self.edit_menu = self.menubar.addMenu("Edit")
        self.help_menu = self.menubar.addMenu("Help")

        self.about_action = self.help_menu.addAction("About")
        self.about_action.triggered.connect(self.show_about)
        
    #==========================================================================
    def show_about(self):
        QMessageBox.information(self, 
                                "About", 
                                f"MBS Node Manager\n"
                                f"Version {__version__}\n\n"
                                f"Author: {__author__}\n"
                                f"Email: {__email__}\n"
                                f"Copyright: {__copyright__}")

#==============================================================================
#==============================================================================
#==============================================================================
if __name__ == '__main__':

    win = MenuBarManager()
    logger.debug(f"MenuBarManager")
