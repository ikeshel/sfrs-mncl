
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.36"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_CLASSINFO
from PyQt5.QtDBus import (QDBusConnection, QDBusMessage)
from PyQt5.QtGui import QTextCursor

# parts of ST3
import dbus_chat_adaptor as chatlib

###############################################################################
class DbusSignalSlot():

    action   = pyqtSignal(str, str)
    message  = pyqtSignal(str, str)

    #__________________________________________________________________________
    def __init__(self, nikname):

        self.m_module_name = nikname
        self.m_messages = []

        # Add our D-Bus interface and connect to D-Bus.
        chatlib.DbusChatAdaptor(self)
        
        QDBusConnection.sessionBus().registerObject('/', self)

        iface = chatlib.ChatInterface('/', '', QDBusConnection.sessionBus(), self)
        
        QDBusConnection.sessionBus().connect('', '', chatlib.ST3_DBUS_ADDRESS, 'message', self.messageSlot )
        
        iface.action.connect( self.actionSlot )

        self.action.emit(self.m_module_name, "connected")


    #__________________________________________________________________________
    def rebuildHistory(self):
        history = '\n'.join(self.m_messages)
        self.chatHistory.setPlainText(history)
        self.chatHistory.moveCursor(QTextCursor.End)

    #__________________________________________________________________________
    @pyqtSlot(str, str, result=str)
    def messageSlot(self, module_name, text):
        self.m_messages.append(f"<{module_name}> {text}")

        if len(self.m_messages) > 100:
            self.m_messages.pop(0)

        self.rebuildHistory()

    #__________________________________________________________________________
    @pyqtSlot(str, str)
    def actionSlot(self, module_name, text):
        self.m_messages.append("[%s] %s" % (module_name, text))

        if len(self.m_messages) > 100:
            self.m_messages.pop(0)

        self.rebuildHistory()

    #__________________________________________________________________________
    @pyqtSlot(str)
    def textChangedSlot(self, newText):
        self.sendButton.setEnabled(newText != '')
        pass

    #__________________________________________________________________________
    @pyqtSlot()
    def sendClickedSlot(self):
        msg = QDBusMessage.createSignal('/', chatlib.ST3_DBUS_ADDRESS, 'message')
        msg << self.m_module_name << self.messageLineEdit.text()
        QDBusConnection.sessionBus().send(msg)
        self.messageLineEdit.setText('')

    #__________________________________________________________________________
    @pyqtSlot()
    def send_dbus_command(self, command):
        msg = QDBusMessage.createSignal('/', chatlib.ST3_DBUS_ADDRESS, 'message')
        msg << self.m_module_name << command
        QDBusConnection.sessionBus().send(msg)

    #==========================================================================
    @pyqtSlot()
    def read_dubs(self, mymethod="Command", command="Hi"):
        ''' '''

        ret = ''
        # try:
        #     if self.interface.isValid():
        #         response = self.interface.call(mymethod, command)
        #         if response.type() == QDBusMessage.ReplyMessage:
        #             ret = response.arguments()[0]
        #             # HMPDBusAdapterLog.debug(f'Service responded with: {ret}')
        #             print(f'Service responded with: {ret}')
        #         else:
        #             # HMPDBusAdapterLog.error(f'{response.errorMessage()}')
        #             print(f'Error: {response.errorMessage()}')
        #     else:
        #         # HMPDBusAdapterLog.warning(f'D-Bus interface {self.interface} is not valid')
        #         ret = 'Warning: D-Bus interface is not valid'
        # except:
        #     ret = ['0']
        return ret

    #__________________________________________________________________________
    @pyqtSlot()
    def send_dbus_data(self, mydata):
        msg = QDBusMessage.createSignal('/', chatlib.ST3_DBUS_ADDRESS, 'message')
        msg << self.m_module_name << str(mydata)
        QDBusConnection.sessionBus().send(msg)


    #__________________________________________________________________________
    @pyqtSlot()
    def dbus_disconnect(self):
        self.action.emit(self.m_module_name, "disconnected")

