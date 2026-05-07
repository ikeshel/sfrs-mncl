
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
from package.mbs_node import MBSNode
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

        self.node_menu.addSeparator() #---------------------------------------------
        self.toggle_all_konsoles = self.node_menu.addAction("Open/Close all konsoles")
        self.toggle_all_konsoles.setCheckable(True)
        self.toggle_all_konsoles.triggered.connect(self.konsole_action)
        # open_command = ['./scripts/konsole_manager.py', '--nodes', 'x86l-132,x86l-157,x86l-170,x86l-253', '--screens', 'com,web,mbs', '--open']
        # # self.node_menu.addAction("Open all the konsoles").triggered.connect(lambda: subprocess.run(open_command))

        # konsole_manager_command = ['./scripts/konsole_manager.py', '--nodes', 'x86l-132,x86l-157,x86l-170,x86l-253', '--screens', 'com,web,mbs', '--close']
        # # self.node_menu.addAction("Close all the konsoles").triggered.connect(lambda: subprocess.run(konsole_manager_command))

        # open_command = ['./scripts/konsole_manager.py', '--nodes', f'{node.node_host}', '--screens', 'mbs,web,com', '--open']
        # close_command = ['./scripts/konsole_manager.py', '--nodes', f'{node.node_host}', '--screens', 'mbs,web,com', '--close']
        # self.toggle_all_konsoles = node.menu.addAction("Open/Close all konsoles")
        # self.toggle_all_konsoles.setCheckable(True)
        # # self.toggle_all_konsoles.triggered.connect(lambda: subprocess.run(open_command))
        # self.toggle_all_konsoles.triggered.connect(lambda:   self.toggle_com_konsole.setChecked(True) or self.toggle_web_konsole.setChecked(True) or self.toggle_mbs_konsole.setChecked(True) or subprocess.run(open_command)
        #                                                 if self.toggle_all_konsoles.isChecked() 
        #                                                 else self.toggle_com_konsole.setChecked(False) or self.toggle_web_konsole.setChecked(False) or self.toggle_mbs_konsole.setChecked(False) or subprocess.run(close_command)
        #                                       )


        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Configure All Nodes").disabled = True
        self.node_menu.addSeparator()
        self.node_menu.addAction("Add Node").setDisabled(True)
        self.node_menu.addAction("Remove Node").setDisabled(True)
        self.node_menu.addSeparator()

        # # Settings Menu
        # self.settings_menu = self.menubar.addMenu("Settings")
        # self.settings_menu.addAction("Configure Nodes")

    #==========================================================================
    def build_node_menu(self, node):

        node.menu.addAction("Show/hide Dashboard").triggered.connect(node.show_hide_dashboard)
        node.menu.addAction("Open Dashboard in external browser").triggered.connect(node.open_external_browser)

        node.menu.addSeparator() #---------------------------------------------
        open_command = ['./scripts/konsole_manager.py', '--nodes', f'{node.node_host}', '--screens', 'mbs,web,com', '--open']
        close_command = ['./scripts/konsole_manager.py', '--nodes', f'{node.node_host}', '--screens', 'mbs,web,com', '--close']
        self.toggle_node_konsoles = node.menu.addAction("Open/Close node konsoles")
        self.toggle_node_konsoles.setCheckable(True)
        self.toggle_node_konsoles.triggered.connect(lambda: self.toggle_com_konsole.setChecked(True) or \
                                                            self.toggle_web_konsole.setChecked(True) or \
                                                            self.toggle_mbs_konsole.setChecked(True) or \
                                                            subprocess.run(open_command)
                                                        if self.toggle_node_konsoles.isChecked() 
                                                        else    self.toggle_com_konsole.setChecked(False) or \
                                                                self.toggle_web_konsole.setChecked(False) or \
                                                                self.toggle_mbs_konsole.setChecked(False) or \
                                                                subprocess.run(close_command))

        node.menu.addSeparator() #---------------------------------------------
        self.toggle_com_konsole = node.menu.addAction("Open/Close COM Konsole")
        self.toggle_com_konsole.setCheckable(True)
        self.toggle_com_konsole.triggered.connect(lambda: node.konsole_manager("com", "open") if self.toggle_com_konsole.isChecked() else node.konsole_manager("com", "close"))


        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Restart WEB-MBS").triggered.connect(node.restart_webmbs)
        node.menu.addAction("Stop WEB-MBS").triggered.connect(node.stop_webmbs)
        node.menu.addAction("Start WEB-MBS").triggered.connect(node.start_webmbs)

        self.toggle_web_konsole = node.menu.addAction("Open/Close WEB-MBS Konsole")
        self.toggle_web_konsole.setCheckable(True)
        self.toggle_web_konsole.triggered.connect(lambda: node.konsole_manager("web", "open") if self.toggle_web_konsole.isChecked() else node.konsole_manager("web", "close"))

        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Restart MBS").triggered.connect(node.restart_mbs)
        node.menu.addAction("Stop MBS").triggered.connect(node.stop_mbs)
        node.menu.addAction("Start MBS").triggered.connect(node.start_mbs)

        self.toggle_mbs_konsole = node.menu.addAction("Open/Close MBS Konsole")
        self.toggle_mbs_konsole.setCheckable(True)
        self.toggle_mbs_konsole.triggered.connect(lambda: node.konsole_manager("mbs", "open") if self.toggle_mbs_konsole.isChecked() else node.konsole_manager("mbs", "close"))

        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Open screens").triggered.connect(node.check_screens)
        node.menu.addAction("Kill screens").triggered.connect(node.kill_screens)

    #==========================================================================
    def konsole_action(self):

        logger.info(MBSNode.list_of_nodes)
        if self.toggle_all_konsoles.isChecked():
            logger.info("Opening all konsoles...")
            for node in MBSNode.list_of_nodes:
                node.konsole_manager("com", "open")
                node.konsole_manager("web", "open")
                node.konsole_manager("mbs", "open")
        else:
            logger.info("Closing all konsoles...")
            for node in MBSNode.list_of_nodes:
                node.konsole_manager("com", "close")
                node.konsole_manager("web", "close")
                node.konsole_manager("mbs", "close")

    #==========================================================================
    def check_for_updates(self)-> None:

        logger.info("Checking for updates...")

        command_list = ["cd ~/mncl", "git fetch", "git pull", "cd"]
        success_flag = True

        if QMessageBox.question(self, "Check for Updates", "Would you like to pull from git?") == QMessageBox.StandardButton.Yes:           
            for node in self.nodes:
                for command in command_list:
                    return_code, _, stderr = node.run_screen_command("com", command)
                    time.sleep(1)  # Wait 1 second between commands
                    if return_code:
                        logger.error(f"Command failed on {node.name}: {stderr}")
                        success_flag = False
                        break
                if success_flag:
                    logger.info("Update process completed.")
                    return
                else:
                    logger.error(f"Update process failed for {node.name}.")
        else:
            logger.info("Update cancelled by user.")

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