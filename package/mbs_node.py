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

# 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtSvg import QSvgWidget

#
sys.path.append('package')
from mbs_browser import MBSBrowser

#==============================================================================
#==============================================================================
# MBS Node Widget
class MBSNode(QtWidgets.QWidget):

    list_of_nodes = [] # class variable to keep track of all node instances

    #=========================================================================
    def __init__(self, name="Node", node_host="localhost"):
        super().__init__()
        self.name = name
        self.node_host = node_host
        self.menu = None
        self.setObjectName(f"node_{name}")
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        self.init_ui()
        MBSNode.list_of_nodes.append(self) # add instance to the class variable list

    #=========================================================================
    def init_ui(self):
        node_svg = QSvgWidget("images/node.svg")
        
        svg_layout = QtWidgets.QVBoxLayout()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addWidget(node_svg)
        self.setLayout(svg_layout)
        
        self.lbl_node_name = QtWidgets.QLabel(self)
        self.lbl_node_name.setObjectName(f"lbl_{self.name}")
        self.lbl_node_name.setText(f"{self.name}\n{self.node_host}")
        self.lbl_node_name.setCursor(Qt.PointingHandCursor)
        self.lbl_node_name.setToolTip(f"Click to open {self.name} Dashboard")
        self.lbl_node_name.setGeometry(QtCore.QRect(10, 5, 90, 40))
        self.lbl_node_name.setAlignment(Qt.AlignCenter)
        self.lbl_node_name.setFont(QFont("Arial", 10, QFont.Bold))
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

    #===========================================================================
    def check_ping(self):

        self.ping_toggling = not getattr(self, 'ping_toggling', False) # invert the toggling value to alternate colors on each check

        try:
            result = subprocess.run(
                f'ping -c 1 {self.node_host}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                # logger.debug(f"{self.name} node is reachable: {result.stdout}")
                if self.ping_toggling:
                    self.status_ping.setStyleSheet(f"background-color: lightgreen; border-radius: {self.radius}px;")
                else:
                    self.status_ping.setStyleSheet(f"background-color: green; border-radius: {self.radius}px;")
                return True
        except subprocess.TimeoutExpired:
            logger.error(f"Ping command timed out for {self.name} node")
            self.status_ping.setStyleSheet(f"background-color: red; border-radius: {self.radius}px;")
            return False
        except Exception as e:
            logger.error(f"Ping failed for {self.name} node: {e}")
            self.status_ping.setStyleSheet(f"background-color: red; border-radius: {self.radius}px;")
            return False

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
        if QtWidgets.QMessageBox.question(self, 
                                       "Kill Screens", 
                                       f"Are you sure you want to kill the screens on {self.name} node?", 
                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
                                       QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
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
    def restart_mbs(self):
        logger.debug(f"Restarting {self.name} node...")
        # Here you would add the actual logic to restart the node, e.g. by sending a command to the server
        # For demonstration, we will just show a message box
        if QtWidgets.QMessageBox.question(self, 
                                       "Restart Node", 
                                       f"Are you sure you want to restart the {self.name} node?", 
                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
                                       QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            try:
                result = subprocess.run(
                    f'ssh ikeshel@{self.node_host} "~/mncl/bin/restart_full_mbs.csh"',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                logger.success(f"Restart node output for {self.name}: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Restart node error for {self.name}: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"Restart node command timed out for {self.name}")
            except Exception as e:
                logger.error(f"Restart node failed for {self.name}: {e}")

    #==========================================================================    
    def closeEvent(self, a0):
        logger.debug(f"Closing node {self.name} window...")
        self.browser_window.close() #if hasattr(self, 'browser_window') else None
        MBSNode.list_of_nodes.remove(self) # remove instance from the class variable list
        return super().closeEvent(a0)
