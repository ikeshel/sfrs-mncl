
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
from mbs_node      import MBSNode
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
        self.toggle_all_konsoles.triggered.connect(lambda checked: self.konsole_action(MBSNode.list_of_nodes, self.list_screens, checked))

        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Check all screens").triggered.connect(self.check_all_screens)

        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Restart all processes").triggered.connect(self.restart_all_processes)
        self.node_menu.addAction("Stop all processes").triggered.connect(self.stop_all_processes)
        self.node_menu.addAction("Start all processes").triggered.connect(self.start_all_processes)

        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Stop all WEB-MBS processes").triggered.connect(self.stop_webmbs_processes)
        self.node_menu.addAction("Start all WEB-MBS processes").triggered.connect(self.start_webmbs_processes)

        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Stop all MBS processes").triggered.connect(self.stop_mbs_processes)
        self.node_menu.addAction("Start all MBS processes").triggered.connect(self.start_mbs_processes)

        self.node_menu.addSeparator() #---------------------------------------------
        self.node_menu.addAction("Add Node").setDisabled(True)
        self.node_menu.addAction("Remove Node").setDisabled(True)
        self.node_menu.addSeparator()

        # # Settings Menu
        # self.settings_menu = self.menubar.addMenu("Settings")
        # self.settings_menu.addAction("Configure Nodes")

    #==========================================================================
    def check_all_screens(self):
        logger.debug("Checking all screens on all nodes...")

        for node in reversed(self.nodes):
            node.check_screens()
        logger.success("All screens checked on all nodes.") 

    #==========================================================================
    def start_mbs_processes(self):
        logger.debug("Starting MBS processes on all nodes...")

        self.check_all_screens()
        for node in reversed(self.nodes[1:]):
            logger.debug(f"Starting MBS processes on node: {node.name}")
            node.start_mbs("force")
        
        time.sleep(10)
        logger.debug(f"Starting MBS processes on node: {self.nodes[0].name}")
        self.nodes[0].start_mbs("force")
        logger.success("MBS processes started on all nodes.")

    #=========================================================================
    def start_webmbs_processes(self):
        logger.debug("Starting WEB-MBS processes on all nodes...")

        self.check_all_screens()
        for node in reversed(self.nodes):
            logger.debug(f"Starting WEB-MBS processes on node: {node.name}")
            node.start_webmbs("force")
        logger.success("WEB-MBS processes started on all nodes.")

    #==========================================================================
    def stop_mbs_processes(self):
        logger.debug("Stopping MBS processes on all nodes...")

        for node in self.nodes:
            logger.debug(f"Stopping MBS processes on node: {node.name}")
            node.stop_mbs("force")
        logger.success("MBS processes stopped on all nodes.")
    
    #=========================================================================
    def stop_webmbs_processes(self):
        logger.debug("Stopping WEB-MBS processes on all nodes...")

        for node in self.nodes:
            logger.debug(f"Stopping WEB-MBS processes on node: {node.name}")
            node.stop_webmbs("force")
        logger.success("WEB-MBS processes stopped on all nodes.")

    #==========================================================================
    # Restarting all processes is a two-step process: first we stop all processes on all nodes, then we start them again. 
    # This ensures that we don't have any conflicts or issues with processes that are still running while we try to start new ones.
    #==========================================================================
    def restart_all_processes(self):
        logger.debug("Restarting all processes on all nodes...")
        self.check_all_screens()
        self.stop_all_processes()
        self.start_all_processes()
        logger.success("All processes restarted on all nodes.")

    #=========================================================================
    def stop_all_processes(self):
        logger.debug("Stopping all processes on all nodes...")
        self.stop_webmbs_processes()
        self.stop_mbs_processes()
        logger.success("All processes stopped on all nodes.")

    #==========================================================================
    def start_all_processes(self):
        logger.debug("Starting all processes on all nodes...")
        self.check_all_screens()
        self.start_mbs_processes()
        self.start_webmbs_processes()
        logger.success("All processes started on all nodes.")

    #==========================================================================
    def build_node_menu(self, node):

        node.menu.addAction("Show/hide Dashboard").triggered.connect(node.show_hide_dashboard)
        node.menu.addAction("Open Dashboard in external browser").triggered.connect(node.open_external_browser)

        node.menu.addSeparator() #---------------------------------------------
        self.toggle_node_konsoles = node.menu.addAction("Open/Close node konsoles")
        self.toggle_node_konsoles.setCheckable(True)
        self.toggle_node_konsoles.triggered.connect(lambda checked: self.konsole_action([node], self.list_screens, checked))

        node.menu.addSeparator() #---------------------------------------------
        self.toggle_com_konsole = node.menu.addAction("Open/Close COM Konsole")
        self.toggle_com_konsole.setCheckable(True)
        self.toggle_com_konsole.triggered.connect(lambda checked: node.konsole_manager("com", "open") if checked else node.konsole_manager("com", "close"))


        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Restart WEB-MBS").triggered.connect(node.restart_webmbs)
        node.menu.addAction("Stop WEB-MBS").triggered.connect(node.stop_webmbs)
        node.menu.addAction("Start WEB-MBS").triggered.connect(node.start_webmbs)

        self.toggle_web_konsole = node.menu.addAction("Open/Close WEB-MBS Konsole")
        self.toggle_web_konsole.setCheckable(True)
        self.toggle_web_konsole.triggered.connect(lambda checked: node.konsole_manager("web", "open") if checked else node.konsole_manager("web", "close"))

        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Restart MBS").triggered.connect(node.restart_mbs)
        node.menu.addAction("Stop MBS").triggered.connect(node.stop_mbs)
        node.menu.addAction("Start MBS").triggered.connect(node.start_mbs)

        self.toggle_mbs_konsole = node.menu.addAction("Open/Close MBS Konsole")
        self.toggle_mbs_konsole.setCheckable(True)
        self.toggle_mbs_konsole.triggered.connect(lambda checked: node.konsole_manager("mbs", "open") if checked else node.konsole_manager("mbs", "close"))

        node.menu.addSeparator() #---------------------------------------------
        node.menu.addAction("Open screens").triggered.connect(node.check_screens)
        node.menu.addAction("Kill screens").triggered.connect(node.kill_screens)

    #==========================================================================
    def konsole_action(self, node_list, screen_list, checked):

        logger.info(f"Toggling konsoles for nodes: {node_list} and screens: {screen_list}")

        if checked:
            action = "open"
            logger.debug(f"Opening konsoles for nodes: {node_list} and screens: {screen_list}")
        else:
            action = "close"
            logger.debug(f"Closing konsoles for nodes: {node_list} and screens: {screen_list}")

        for node in node_list:
            for screen in screen_list:
                logger.debug(f"Processing: {node}-{screen}")
                node.konsole_manager(screen, action)
            self.toggle_com_konsole.setChecked(checked)
            self.toggle_web_konsole.setChecked(checked)
            self.toggle_mbs_konsole.setChecked(checked)

    #==========================================================================
    def check_for_updates(self)-> None:

        logger.info("Checking for updates...")

        command_list = ["setenv https_proxy http://proxy.gsi.de:8080",
                        "setenv http_proxy http://proxy.gsi.de:8080",
                        "cd ~/sfrs-mncl", "git fetch", "git pull", "cd"]
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