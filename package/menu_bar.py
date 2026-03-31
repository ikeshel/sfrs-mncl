
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

        # Node Menu
        self.node_menu = self.menubar.addMenu("Node")
        self.node_menu.addAction("Open all Dashboards").triggered.connect(self.show_all_dashboards) # self.show_window)
        self.node_menu.addAction("Open all dashboards in external browser").triggered.connect(self.open_external_browser) # self.open_external_browser)
        self.node_menu.addSeparator()
        self.node_menu.addAction("Configure All Nodes")
        self.node_menu.addSeparator()
        self.node_menu.addAction("Add Node").setDisabled(True)
        self.node_menu.addAction("Remove Node").setDisabled(True)
        self.node_menu.addSeparator()

        # Settings Menu
        self.settings_menu = self.menubar.addMenu("Settings")
        self.settings_menu.addAction("Configure Nodes")

        # Help Menu
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

