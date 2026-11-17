"""Offline subprocess fixture: real Qt windows and IPC, with no hardware traffic."""

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'package'))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtCore import QProcess, QTimer
from PyQt6.QtWidgets import QApplication, QWidget
from loguru import logger
import mbs_node_manager as manager
import mbs_node
from mncl_logger import MnclLogger
from konsole_status import KonsoleWindowMonitor

logger.remove()
MnclLogger.setup_logger = lambda self: None
KonsoleWindowMonitor.start = lambda self: None
mbs_node.MBSNode.check_ssh = lambda self: True
mbs_node.MBSNode.read_node_murx_config = lambda self: None


class OfflineBrowser(QWidget):
    def __init__(self, url):
        super().__init__()


mbs_node.MBSBrowser = OfflineBrowser
state_dir = Path.cwd() / 'state'
state_dir.mkdir(exist_ok=True)

if sys.argv[1] == '--overview':
    import node_process
    import super_frs_manager as overview

    class OfflineProcess(QProcess):
        def setArguments(self, arguments):
            # Exercise the production detached launcher with offline node startup.
            super().setArguments([str(Path(__file__).resolve()), *arguments[1:]])

    node_process.QProcess = OfflineProcess
    app = QApplication([])
    window = overview.SuperFrsManager()
    for config in window.node_configs.values():
        window.open_node(config['directory'])
    timer = QTimer(app)
    timer.timeout.connect(lambda: window.close() if (state_dir / 'close-overview').exists() else None)
    timer.start(40)
    QTimer.singleShot(20000, app.quit)
    sys.exit(app.exec())

directory = sys.argv[sys.argv.index('--node') + 1].upper()
activations = 0
show_window = manager.NodeWindowController._show_window


def record_window(window):
    global activations
    result = show_window(window)
    activations += 1
    state = dict(pid=os.getpid(), session=os.getsid(0), activations=activations,
                 directory=window.nodes[0].directory, hosts=[node.node_host for node in window.nodes],
                 log_file=window.test_log_file)
    temporary = state_dir / f'{directory}.tmp'
    temporary.write_text(json.dumps(state))
    temporary.replace(state_dir / f'{directory}.json')
    return result


class OfflineApplication(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.quit() if (state_dir / f'stop-{directory}').exists() else None)
        self.timer.start(40)
        QTimer.singleShot(20000, self.quit)


manager.NodeWindowController._show_window = staticmethod(record_window)
manager.QApplication = OfflineApplication
sys.exit(manager.main(sys.argv[1:]))
