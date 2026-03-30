
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.36"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_CLASSINFO
from PyQt5.QtDBus import (  QDBusAbstractAdaptor, 
                            QDBusAbstractInterface )

ST3_DBUS_ADDRESS = 'ST3.communication.chat'

###############################################################################
class DbusChatAdaptor(QDBusAbstractAdaptor):

    Q_CLASSINFO("D-Bus Interface", ST3_DBUS_ADDRESS)

    Q_CLASSINFO("D-Bus Introspection", ''
        '  <interface name="'+ST3_DBUS_ADDRESS+'">\n'
        '    <signal name="message">\n'
        '      <arg direction="out" type="s" name="module_name"/>\n'
        '      <arg direction="out" type="s" name="text"/>\n'
        '    </signal>\n'
        '    <signal name="action">\n'
        '      <arg direction="out" type="s" name="module_name"/>\n'
        '      <arg direction="out" type="s" name="text"/>\n'
        '    </signal>\n'
        '  </interface>\n'
        '')

    action   = pyqtSignal(str, str)
    message  = pyqtSignal(str, str)

    #__________________________________________________________________________
    def __init__(self, parent):
        super(DbusChatAdaptor, self).__init__(parent)

        self.setAutoRelaySignals(True)

###############################################################################
class ChatInterface(QDBusAbstractInterface):

    action   = pyqtSignal(str, str)
    message  = pyqtSignal(str, str)

    #__________________________________________________________________________
    def __init__(self, 
                 service, 
                 path, 
                 connection, 
                 parent=None):
        super(ChatInterface, self).__init__(service, 
                                            path, 
                                            ST3_DBUS_ADDRESS,
                                            connection, 
                                            parent)


