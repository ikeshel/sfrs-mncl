"""Read named local console windows without blocking the Qt event loop."""

__author__ = 'Irakli Keshelashvili'
__email__ = 'i.keshelashvili@gsi.de'

import re

from loguru import logger
from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

CONSOLE_TITLE = re.compile(r'(?<![\w@.-])([\w.-]+@[\w.-]+_[\w.-]+)(?=$|[\s–—])')


def parse_console_windows(output):
    """Extract complete login_screen names, allowing Konsole's title decorations."""
    names = set()
    for line in output.splitlines():
        fields = line.split(None, 3)  # Window ID, desktop, machine, title.
        if len(fields) == 4:
            names.update(CONSOLE_TITLE.findall(fields[3]))
    return names


def console_title(node, screen):
    return f"{node.username}@{node.node_host}_{screen}"


class KonsoleWindowMonitor(QObject):
    windows_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_titles = None
        self._active = False
        self._timed_out = False
        self._last_error = None
        self.process = QProcess(self)
        self.process.setProgram('wmctrl')
        self.process.setArguments(['-l'])
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._failed)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.poll)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.setInterval(750)
        self.timeout.timeout.connect(self._timeout)

    def start(self):
        self._active = True
        self.timer.start()
        self.poll()

    def poll(self):
        if not self._active or self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self._timed_out = False
        self.timeout.start()
        self.process.start()

    def stop(self):
        self._active = False
        self.timer.stop()
        self.timeout.stop()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)

    def _warn(self, message):
        if message != self._last_error:
            logger.warning(f'Cannot update console checkboxes: {message}')
            self._last_error = message

    def _timeout(self):
        self._timed_out = True
        self.process.kill()

    def _failed(self, error):
        self.timeout.stop()
        if self._active:
            self._warn('wmctrl timed out' if self._timed_out else self.process.errorString())

    def _finished(self, exit_code, exit_status):
        self.timeout.stop()
        if not self._active:
            return
        if self._timed_out:
            self._warn('wmctrl timed out')
        elif exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            error = bytes(self.process.readAllStandardError()).decode(errors='replace').strip()
            self._warn(error or 'wmctrl failed to list windows')
        else:
            output = bytes(self.process.readAllStandardOutput()).decode(errors='replace')
            self.last_titles = parse_console_windows(output)
            self._last_error = None
            self.windows_changed.emit(self.last_titles)
