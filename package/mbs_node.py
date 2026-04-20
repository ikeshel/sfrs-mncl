#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

#
import sys
import subprocess
from loguru import logger

# from gui_env import ensure_gui_environment
# ensure_gui_environment()

# 
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QLabel

#
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
    def __init__(self, name="Node", node_host="localhost"):

        super().__init__(hostname=node_host) # initialize SSHCommander with node_host
        self.name = name
        self.node_host = node_host
        self.menu = None
        self.setObjectName(f"node_{name}")
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        self.init_ui()
        MBSNode.list_of_nodes.append(self) # add instance to the class variable list
        

    #=========================================================================
    def init_ui(self):
        node_svg = QLabel()
        node_svg.setPixmap(QPixmap("images/node.svg"))
        
        svg_layout = QtWidgets.QVBoxLayout()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addWidget(node_svg)
        self.setLayout(svg_layout)
        
        # Create label-link for node name and set it up
        self.lbl_node_name = QtWidgets.QLabel(self)
        self.lbl_node_name.setObjectName(f"lbl_{self.name}")
        self.lbl_node_name.setText(f"{self.name}\n{self.node_host}")
        self.lbl_node_name.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_node_name.setToolTip(f"Click to open {self.name} Dashboard")
        self.lbl_node_name.setGeometry(QtCore.QRect(20, 10, 90, 40))
        self.lbl_node_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.lbl_node_name.setFont(QFont("Times", 10, QFont.Weight.Bold))
        self.browser_window = MBSBrowser(url=f"http://{self.node_host}:8899/MBS/localhost/ControlGUI/")
        self.lbl_node_name.mousePressEvent = lambda event: self.show_window()      

        # Create red circle widget for status indicator
        self.status_ping = QtWidgets.QWidget(self)
        self.status_ping.setToolTip(f"Ping for {self.name} node")
        diameter = 13
        self.radius = diameter // 2
        self.status_ping.setGeometry(90-self.radius, 145-self.radius, diameter, diameter)
        self.status_ping.setStyleSheet(f"background-color: red; border-radius: {self.radius}px;")
        self.status_ping.raise_()


    #==========================================================================
    def show_window(self):

        if self.browser_window.isVisible():
            logger.debug(f"{self.name} dashboard is already open. Bringing it to front...")
            self.browser_window.close() # close the existing window before opening a new one
        else:
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
                ["ssh", "-o", f"ConnectTimeout={timeout}", f"ikeshel@{self.node_host}", "echo alive"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0 # return True if SSH connection is successful, False otherwise
        except Exception:
            return False

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
                f'cd ~/{self.name}', 
                'mbs -dabc', 
                'help'
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
                f'cd ~/{self.name}', 
                'quit', 
                'resl', 
                'mbs -dabc', 
                'help'
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
