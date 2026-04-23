
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys, time
import subprocess
from loguru import logger

from PyQt6.QtWidgets import QApplication, QMessageBox

##
sys.path.append('package')
from ssh_commander import SSHCommander

#==============================================================================
class MenuBarManager(SSHCommander):

    #==========================================================================
    def __init__(self):
        self.menubar = self.menuBar()

        # Help Menu
        self.help_menu = self.menubar.addMenu("Help")
        
        self.update_action = self.help_menu.addAction("Check for updates")
        self.update_action.triggered.connect(self.check_for_updates)

        self.about_action = self.help_menu.addAction("About")
        self.about_action.triggered.connect(self.show_about)

    #==========================================================================
    def menuBar(self):
        pass

    #==========================================================================
    def setup_mbs_menu(self):

            # Node Menu
            self.node_menu = self.menubar.addMenu("All nodes")
            self.node_menu.addAction("Open all Dashboards").triggered.connect(self.show_all_dashboards)
            self.node_menu.addAction("Open all dashboards in external browser").triggered.connect(self.open_external_browsers)
            self.node_menu.addSeparator()
            self.node_menu.addAction("Open all the konsoles").triggered.connect(lambda: subprocess.run(["scripts/open_konsoles.py", "node", "all", "screen", "all", "open"]))
            self.node_menu.addAction("Close all the konsoles").triggered.connect(lambda: subprocess.run(["scripts/open_konsoles.py", "node", "all", "screen", "all", "close"]))
            self.node_menu.addSeparator()
            self.node_menu.addAction("Configure All Nodes").disabled = True
            self.node_menu.addSeparator()
            self.node_menu.addAction("Add Node").setDisabled(True)
            self.node_menu.addAction("Remove Node").setDisabled(True)
            self.node_menu.addSeparator()

            # Settings Menu
            self.settings_menu = self.menubar.addMenu("Settings")
            self.settings_menu.addAction("Configure Nodes")

    #==========================================================================
    def build_node_menu(self, node):

        node.menu.addAction("Show/hide Dashboard").triggered.connect(node.show_window)
        node.menu.addAction("Open Dashboard in external browser").triggered.connect(node.open_external_browser)
        node.menu.addSeparator()
        node.menu.addAction("Check screens").triggered.connect(node.check_screens)
        node.menu.addSeparator()
        node.menu.addAction("Kill screens").triggered.connect(node.kill_screens)
        node.menu.addSeparator()
        node.menu.addAction("Restart MBS").triggered.connect(node.restart_mbs)
        node.menu.addAction("Stop MBS").triggered.connect(node.stop_mbs)
        node.menu.addAction("Start MBS").triggered.connect(node.start_mbs)
        node.menu.addAction("Toggle Konsole").triggered.connect(lambda: node.toggle_konsole("mbs"))
        node.menu.addSeparator()
        node.menu.addAction("Restart WEB-MBS").triggered.connect(node.restart_webmbs)
        node.menu.addAction("Stop WEB-MBS").triggered.connect(node.stop_webmbs)
        node.menu.addAction("Start WEB-MBS").triggered.connect(node.start_webmbs)

    #==========================================================================
    def check_for_updates(self)-> None:
        logger.info("Checking for updates...")

        command_list = ["cd ~/mncl", "git fetch", "git pull", "cd"]

        if QMessageBox.question(self, "Check for Updates", "Would you like to pull from git?") == QMessageBox.StandardButton.Yes:           
            for node in self.nodes:
                for command in command_list:
                    return_code, stdout, stderr = node.run_screen_command("com", command)
                    time.sleep(1)  # Wait 1 second between commands
                    if return_code == 0:
                        logger.success(f"Update successful on {node.name}: {stdout}")
                    else:
                        logger.error(f"Update failed on {node.name}: {stderr}")
                        return
                return
        else:
            logger.info("Update cancelled by user.")
        logger.info("Update process completed.")

    #==========================================================================
    def show_about(self):
        QMessageBox.information(self, 
                                "About", 
                                f"MBS Node Manager\n"
                                f"Version {__version__}\n\n"
                                f"Author: {__author__}\n"
                                f"Email: {__email__}\n"
                                f"Copyright: {__copyright__}")

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':
    logger.info("This is a module, not a standalone application.")
    app = QApplication(sys.argv)
    menubar_manager = MenuBarManager()
    menubar_manager.show()
    sys.exit(app.exec())