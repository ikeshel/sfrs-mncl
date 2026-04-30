#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

##
import sys
import signal
import subprocess
import re
from loguru import logger

## 
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QLabel

##
sys.path.append('package')
from mbs_browser import MBSBrowser
from ssh_commander import SSHCommander

#==============================================================================
#==============================================================================
# MBS Node Widget
class MBSNode(QtWidgets.QWidget, 
              SSHCommander):

    list_of_nodes = [] # class variable to keep track of all node instances
    
    #=========================================================================
    def __init__(self, node_dict: dict):

        super().__init__(hostname=node_dict['host_name']) # initialize SSHCommander with node_host

        self.name = node_dict['node_name']
        self.node_host = node_dict['host_name']
        self.directory = node_dict['directory']
        self.active = node_dict.get('active', True) # get active status from config, default to True if not specified
        self.pc_type = node_dict.get('pc_type', 'intel_x86') # get PC type from config, default to 'intel_x86' if not specified
        self.menu = None
        self.WR_SUBSYSTEM_ID = None # example subsystem ID for MBS node, replace with actual value if needed            

        self.setObjectName(f"node_{self.directory}")
        self.setStyleSheet("background-color: white; border: 1px solid black;")

        self.read_node_murx_config() # read the MURX config to get the subsystem ID for this node

        self.init_ui()
        if not self.active:
            self.setDisabled(True) # disable the widget if the node is not active

        MBSNode.list_of_nodes.append(self) # add instance to the class variable list
        self.node_id = len(MBSNode.list_of_nodes) # assign a unique ID based on the current number of nodes in the list


    #=========================================================================
    def init_ui(self):
        node_svg = QLabel()
        node_svg.setPixmap(QPixmap(f"images/{self.pc_type}.svg"))
        
        svg_layout = QtWidgets.QVBoxLayout()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addWidget(node_svg)
        self.setLayout(svg_layout)
        
        # Create label-link for node name and set it up
        self.lbl_node_name = QtWidgets.QLabel(self)
        self.lbl_node_name.setObjectName(f"lbl_{self.directory}")
        self.lbl_node_name.setText(f"{self.directory}\n{self.node_host}")
        self.lbl_node_name.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_node_name.setToolTip(f"Click to open {self.directory} Dashboard")
        self.lbl_node_name.setGeometry(QtCore.QRect(20, 10, 90, 40))
        self.lbl_node_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_node_name.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        self.browser_window = MBSBrowser(url=f"http://{self.node_host}:8899/MBS/localhost/ControlGUI/")
        self.lbl_node_name.mousePressEvent = lambda event: self.show_hide_dashboard()      

        # Create label for subsystem ID and set it up
        self.lbl_subsystem_id = QtWidgets.QLabel(self)
        self.lbl_subsystem_id.setObjectName(f"lbl_{self.directory}_subsystem_id")
        self.lbl_subsystem_id.setFont(QFont("Times", 10, QFont.Weight.Bold))
        self.lbl_subsystem_id.setText(f"Eve ID: {self.WR_SUBSYSTEM_ID}")
        self.lbl_subsystem_id.setToolTip(f"Subsystem event ID")
        self.lbl_subsystem_id.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subsystem_id.setGeometry(QtCore.QRect(120, 50, 90, 25))

        # Create red circle widget for status indicator
        self.status_ping = QtWidgets.QWidget(self)
        self.status_ping.setToolTip(f"Ping for {self.directory} node")
        diameter = 13
        self.radius = diameter // 2
        self.status_ping.setGeometry(90-self.radius, 145-self.radius, diameter, diameter)
        self.status_ping.setStyleSheet(f"background-color: red; border-radius: {self.radius}px;")
        self.status_ping.raise_()

    #=========================================================================
    def extract_subsystem_id(self, murx_content: str) -> str:

        # Extract value after '='
        match = re.search(r'WR_SUBSYSTEM_ID\s*=\s*(\S+?)[\s,]', murx_content)
        if match:
            wr_subsystem_id = match.group(1)
            print("WR_SUBSYSTEM_ID:", wr_subsystem_id)  # -> 0x200
            return wr_subsystem_id
        else:
            print("WR_SUBSYSTEM_ID not found")
            return "0x000"

    #==========================================================================
    def read_node_murx_config(self):
        
        results = subprocess.Popen(
            f'ssh ikeshel@{self.node_host} "cat ~/{self.directory}/murx.usf"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )   
        stdout, stderr = results.communicate()
        if results.returncode == 0:
            logger.success(f"Successfully read MURX config for {self.name} node")
            self.murx_file_content = stdout.strip() # store the content of the murx config file for later use
            self.WR_SUBSYSTEM_ID = self.extract_subsystem_id(self.murx_file_content)
            logger.debug(f"Set WR_SUBSYSTEM_ID for {self.name} node: {self.WR_SUBSYSTEM_ID}")        
        else:
            logger.error(f"Failed to read MURX config for {self.name} node: {stderr}")
            self.WR_SUBSYSTEM_ID = "0x000" # set default value if reading config fails

    #==========================================================================
    def show_hide_dashboard(self):

        if self.browser_window.isVisible():
            logger.debug(f"{self.directory} dashboard is already open. Bringing it to front...")
            self.browser_window.close() # close the existing window before opening a new one
        else:
            self.browser_window.move(200+self.node_id*20, self.node_id*20) # move the window to a specific position on the screen
            self.browser_window.resize(1800, 1300) # resize the window to a specific size
            self.browser_window.show()
            self.browser_window.raise_()
            self.browser_window.activateWindow()

    #==========================================================================
    def open_external_browser(self):

        url = f"http://{self.node_host}:8899/MBS/localhost/ControlGUI/"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        # os.system(f"xdg-open {url}") # alternative method to open URL in default browser
        logger.success(f"Opening {self.name} dashboard in external browser: {url}")

    #==========================================================================
    def check_ssh(self, timeout: int = 1) -> bool:

        try:
            result = subprocess.run(
                ["ssh", "-o", f"ConnectTimeout={timeout}", f"ikeshel@{self.node_host}", "echo", "alive"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0 # return True if SSH connection is successful, False otherwise
        except Exception:
            return False

    #==========================================================================
    def konsole_manager(self, screen_name: str, command: str)-> tuple[int, str, str]:

        logger.info(screen_name)
        command = f"./scripts/konsole_manager.py --nodes {self.node_host} --screens {screen_name} --{command}"
        return subprocess.run(command.split(), capture_output=False, text=False)

    #===========================================================================
    def check_ping(self, timeout: int = 1) -> bool:

        return subprocess.call(
            ["ping", "-c", "1", "-W", str(timeout), self.node_host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) == 0
        

    #===========================================================================
    def check_screens(self):
        logger.debug(f"Checking screens for {self.name} node...")
        # Here you would add the actual logic to check the screens, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        try:
            result = subprocess.run(
                f'ssh ikeshel@{self.node_host} "~/mncl/bin/check_screens.csh"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.success(f"Check screens output for {self.name}: {result.stdout}")
            if result.stderr:
                logger.warning(f"Check screens error for {self.name}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"Check screens command timed out for {self.name}")
        except Exception as e:
            logger.error(f"Check screens failed for {self.name}: {e}")

    #==========================================================================
    def kill_screens(self):
        logger.debug(f"Killing screens for {self.name} node...")
        # Here you would add the actual logic to kill the screens, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Kill Screens",
            f"Are you sure you want to kill the screens on {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                result = subprocess.run(
                    f'ssh ikeshel@{self.node_host} "~/mncl/bin/kill_screens.csh"',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                logger.success(f"Kill screens output for {self.name}: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Kill screens error for {self.name}: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"Kill screens command timed out for {self.name}")
            except Exception as e:
                logger.error(f"Kill screens failed for {self.name}: {e}")

    #==========================================================================
    def stop_mbs(self):
        logger.debug(f"Stopping {self.name} node...")
        # Here you would add the actual logic to stop MBS, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Stop Node",
            f"Are you sure you want to stop the {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            screen_name = "mbs"
            list_of_commands = [
                'quit',
                '\x03', # Ctrl+C to interrupt the running process
                'resl'
                ]
            for cmd in list_of_commands:
                try:
                    return_code, stdout, stderr = self.run_screen_command(screen_name, cmd)
                    logger.info(f"Command: {cmd}")
                    logger.info(f"Return code: {return_code}")
                    logger.info(f"Output: {stdout}")
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")
    
    #==========================================================================
    def start_mbs(self):
        logger.debug(f"Starting {self.name} node...")
        # Here you would add the actual logic to start MBS, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Start Node",
            f"Are you sure you want to start the {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            screen_name = "mbs"
            list_of_commands = [
                f'cd ~/{self.directory}', 
                'mbs -dabc', 
                '@startup',
                '\n'
                ]                    
            for cmd in list_of_commands:
                try:
                    return_code, stdout, stderr = self.run_screen_command(screen_name, cmd)
                    logger.info(f"Command: {cmd}")
                    logger.info(f"Return code: {return_code}")
                    logger.info(f"Output: {stdout}")
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")

    #==========================================================================
    def restart_mbs(self):
        logger.debug(f"Restarting {self.name} node...")

        if QtWidgets.QMessageBox.question(
            self,
            "Restart Node",
            f"Are you sure you want to restart the {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:

            screen_name = "mbs"
            list_of_commands = [
                '\x03', # Ctrl+C to interrupt the running process
                f'cd ~/{self.directory}', 
                'quit', 
                'resl', 
                'mbs -dabc', 
                '@startup',
                '\n'
                ]
            for cmd in list_of_commands:
                try:
                    _, _, stderr = self.run_screen_command(screen_name, cmd)
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")

    #==========================================================================
    def stop_webmbs(self):
        logger.debug(f"Stopping WebMBS on {self.name} node...")
        # Here you would add the actual logic to stop WebMBS, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Stop WebMBS",
            f"Are you sure you want to stop WebMBS on {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            screen_name = "web"
            list_of_commands = [
                '\x03', # Ctrl+C to interrupt the running process
                '\x03', # Ctrl+C to interrupt the running process
                ]
            for cmd in list_of_commands:
                try:
                    return_code, stdout, stderr = self.run_screen_command(screen_name, cmd)
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")

    #==========================================================================
    def start_webmbs(self):
        logger.debug(f"Starting WebMBS on {self.name} node...")
        # Here you would add the actual logic to start WebMBS, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Start WebMBS",
            f"Are you sure you want to start WebMBS on {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            screen_name = "web"
            list_of_commands = [
                'webmbs 8899'
                ]
            for cmd in list_of_commands:
                try:
                    return_code, stdout, stderr = self.run_screen_command(screen_name, cmd)
                    logger.info(f"Command: {cmd}")
                    logger.info(f"Return code: {return_code}")
                    logger.info(f"Output: {stdout}")
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")

    #==========================================================================
    def restart_webmbs(self):
        logger.debug(f"Restarting WebMBS on {self.name} node...")
        # Here you would add the actual logic to restart WebMBS, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(
            self,
            "Restart WebMBS",
            f"Are you sure you want to restart WebMBS on {self.name} node?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
            screen_name = "web"
            list_of_commands = [
                '\x03', # Ctrl+C to interrupt the running process
                '\x03', # Ctrl+C to interrupt the running process
                'webmbs 8899'
                ]
            for cmd in list_of_commands:
                try:
                    return_code, stdout, stderr = self.run_screen_command(screen_name, cmd)
                    logger.info(f"Command: {cmd}")
                    logger.info(f"Return code: {return_code}")
                    logger.info(f"Output: {stdout}")
                    if stderr:
                        logger.error(f"{stderr}")
                except Exception as e:
                    logger.error(f"Test failed for command '{cmd}': {e}")

    #==========================================================================    
    def closeEvent(self, a0):
        logger.debug(f"Closing node {self.name} window...")
        self.browser_window.close() #if hasattr(self, 'browser_window') else None
        MBSNode.list_of_nodes.remove(self) # remove instance from the class variable list
        return super().closeEvent(a0)


#==============================================================================
#==============================================================================
if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # restore default Ctrl+C behavior
    
    node1 = MBSNode({
        'node_name': 'Node1',
        'host_name': 'x86l-132',
        'directory': 'MBS_Node1'
    })
    node1.show()
    sys.exit(app.exec())