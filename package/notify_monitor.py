


import sys
import re


import dbus
import dbus.mainloop.glib
from gi.repository import GLib

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QPushButton


TEST_RE = re.compile(r"test=([^\s&]+)")

# Use the GLib main loop for dbus-python
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class NotificationWatcher(QObject):
    notificationClosed = pyqtSignal(int, int)
    actionInvoked = pyqtSignal(int, str)
    notifyWithTest = pyqtSignal(str, str, str)  # app, summary, test_value

    def __init__(self):
        super().__init__()
        self.bus = dbus.SessionBus()

        # Signals emitted by the notification daemon
        self.bus.add_signal_receiver(
            self._on_closed,
            dbus_interface="ST3.communication.chat",
            signal_name="NotificationClosed",
        )
        self.bus.add_signal_receiver(
            self._on_action,
            dbus_interface="ST3.communication.chat",
            signal_name="ActionInvoked",
        )

        # Best-effort interception of Notify calls (often blocked / unsupported)
        # Some setups may allow it, many won't.
        try:
            self.bus.add_message_filter(self._message_filter)
            # Try to enable eavesdropping by adding an eavesdrop match rule
            # (May be rejected by dbus-daemon policy)
            self.bus.add_match_string(
                "type='method_call',interface='ST3.communication.chat',member='Notify',eavesdrop='true'"
            )
        except Exception:
            pass

    def _on_closed(self, nid, reason):
        self.notificationClosed.emit(int(nid), int(reason))

    def _on_action(self, nid, action_key):
        self.actionInvoked.emit(int(nid), str(action_key))

    def _message_filter(self, bus, message):
        try:
            if message.get_interface() != "ST3.communication.chat":
                return dbus.lowlevel.HANDLER_RESULT_NOT_YET_HANDLED
            if message.get_member() != "Notify":
                return dbus.lowlevel.HANDLER_RESULT_NOT_YET_HANDLED

            args = message.get_args_list()

            # Notify(app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout)
            app_name = str(args[0])
            summary = str(args[3])
            body = str(args[4])

            hay = summary + "\n" + body
            m = TEST_RE.search(hay)
            if m:
                self.notifyWithTest.emit(app_name, summary, m.group(1))
        except Exception:
            pass

        return dbus.lowlevel.HANDLER_RESULT_NOT_YET_HANDLED


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D-Bus Notification Monitor (no asyncio)")

        self.label = QLabel("Waiting…")
        self.label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.w = NotificationWatcher()
        self.w.notificationClosed.connect(lambda nid, r: print("Closed:", nid, r))
        self.w.actionInvoked.connect(lambda nid, a: print("Action:", nid, a))
        self.w.notifyWithTest.connect(self.on_test)

        # Integrate GLib into Qt by polling it periodically
        self.glib_ctx = GLib.MainContext.default()
        self.timer_id = self.startTimer(10)  # ms

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(lambda: self.label.setText("Waiting…"))
        layout.addWidget(self.clear_btn)

    def timerEvent(self, event):
        # Let GLib process pending D-Bus events
        while self.glib_ctx.pending():
            self.glib_ctx.iteration(False)

    def on_test(self, app, summary, val):
        self.label.setText(f"Matched test=\nApp: {app}\nSummary: {summary}\nValue: {val}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.resize(520, 180)
    win.show()
    sys.exit(app.exec_())
