"""Detached node managers with local activation and overview menu commands."""

__author__ = 'Irakli Keshelashvili'
__email__ = 'i.keshelashvili@gsi.de'

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from dataclasses import dataclass

from loguru import logger
from PyQt6.QtCore import QIODevice, QLockFile, QObject, QProcess, QTimer, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from ssh_commander import SSHCommander

NODE_COMMANDS = frozenset({
    'show_hide_dashboard', 'open_external_browser', 'check_screens',
    'start_mbs', 'stop_mbs', 'start_webmbs', 'stop_webmbs', 'konsole_manager',
})


def node_server_name(directory, working_directory=None):
    # Keep repositories, desktop sessions, and users independent.
    identity = [os.getuid(), str(Path(working_directory or Path.cwd()).resolve()),
                os.environ.get('DISPLAY', ''), os.environ.get('WAYLAND_DISPLAY', ''), directory.upper()]
    digest = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:32]
    return f'sfrs-node-{digest}'


def send_node_command(server_name, command, args=()):
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(150):
        return False
    socket.write(json.dumps({'command': command, 'args': list(args)}).encode() + b'\n')
    if socket.bytesToWrite() and not socket.waitForBytesWritten(150):
        socket.abort()
        return False
    socket.disconnectFromServer()
    return True


class NodeInstanceServer(QObject):
    command_received = pyqtSignal(str, list)

    def __init__(self, directory, working_directory=None, parent=None):
        super().__init__(parent)
        self.name = node_server_name(directory, working_directory)
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self._accept_connections)
        self.lock = QLockFile(str(Path(tempfile.gettempdir()) / f'{self.name}.lock'))
        self.lock.setStaleLockTime(0)
        self.buffers = {}

    def start(self):
        if send_node_command(self.name, 'activate'):
            return False
        if not self.lock.tryLock(0):
            # Another launch is already acquiring the socket and opening the window.
            send_node_command(self.name, 'activate')
            return False
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError(f'Cannot create node activation socket: {self.server.errorString()}')
        return True

    def _accept_connections(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.buffers[socket] = b''
            socket.readyRead.connect(lambda socket=socket: self._read_command(socket))
            socket.disconnected.connect(lambda socket=socket: self._release(socket))
            self._read_command(socket)

    def _release(self, socket):
        self.buffers.pop(socket, None)
        socket.deleteLater()

    def _read_command(self, socket):
        data = self.buffers.get(socket, b'') + bytes(socket.readAll())
        self.buffers[socket] = data
        if len(data) > 4096:
            socket.abort()
            return
        if b'\n' not in data:
            return
        try:
            request = json.loads(data.split(b'\n', 1)[0])
            command, args = request['command'], request.get('args', [])
            if (command in NODE_COMMANDS | {'activate', 'close', 'ping'}
                    and isinstance(args, list) and len(args) <= 2
                    and all(isinstance(arg, str) for arg in args)):
                if command != 'ping':
                    self.command_received.emit(command, args)
        except (ValueError, KeyError, TypeError):
            logger.warning('Ignoring invalid node-manager message')
        socket.disconnectFromServer()

    def close(self):
        if self.server.isListening():
            self.server.close()
            self.lock.unlock()


class NodeProcessProxy(SSHCommander):
    """Forward existing overview actions to the node's own GUI process."""

    def __init__(self, config, working_directory):
        super().__init__(hostname=config['host_name'])
        self.name = config['node_name']
        self.directory = config['directory']
        self.node_host = config['host_name']
        self.server_name = node_server_name(self.directory, working_directory)

    def is_running(self):
        return send_node_command(self.server_name, 'ping')

    def __getattr__(self, name):
        if name not in NODE_COMMANDS:
            raise AttributeError(name)

        def forward(*args):
            if not send_node_command(self.server_name, name, args):
                logger.warning(f'{self.directory} manager is no longer running')
        return forward


@dataclass
class PendingNodeWindow:
    opening: bool
    deadline: float
    close_sent: bool = False


class NodeProcessController(QObject):
    def __init__(self, node_configs, working_directory=None):
        super().__init__()
        self.working_directory = Path(working_directory or Path.cwd()).resolve()
        self.node_configs = {node['directory'].upper(): node for node in node_configs}
        self.proxies = {directory: NodeProcessProxy(node, self.working_directory)
                        for directory, node in self.node_configs.items()}
        self._pending = {}
        self._pending_timer = QTimer(self)
        self._pending_timer.setInterval(200)
        self._pending_timer.timeout.connect(self._refresh_pending)

    @property
    def nodes(self):
        return [node for node in self.proxies.values() if node.is_running()]

    @property
    def open_directories(self):
        opened = {node.directory.upper() for node in self.nodes}
        for directory, request in self._pending.items():
            if request.opening:
                opened.add(directory)
            else:
                opened.discard(directory)
        return opened

    def _refresh_pending(self):
        for directory, request in list(self._pending.items()):
            node = self.proxies[directory]
            running = node.is_running()
            if request.opening and request.close_sent and not running:
                self._pending.pop(directory, None)
                try:
                    self.open_node(self.node_configs[directory])
                except RuntimeError as error:
                    logger.error(str(error))
                continue
            if request.opening and request.close_sent:
                running = False  # Wait for the previous window to finish closing.
            finished = running if request.opening else request.close_sent and not running
            if finished or time.monotonic() >= request.deadline:
                self._pending.pop(directory, None)
            elif not request.opening and not request.close_sent:
                request.close_sent = send_node_command(node.server_name, 'close')
        if not self._pending:
            self._pending_timer.stop()

    def close_node(self, config):
        directory = config['directory'].upper()
        node = self.proxies[directory]
        sent = send_node_command(node.server_name, 'close')
        previous = self._pending.get(directory)
        # A close requested during Python/Qt startup must wait for the node's socket.
        if sent or previous is not None:
            close_sent = sent or (previous is not None and previous.close_sent)
            self._pending[directory] = PendingNodeWindow(False, time.monotonic() + 15, close_sent)
            self._pending_timer.start()
        return sent

    def open_node(self, config):
        directory = config['directory'].upper()
        node = self.proxies[directory]
        request = self._pending.get(directory)
        if request is not None and request.close_sent:
            # A queued close cannot be cancelled; reopen after the old socket closes.
            request.opening = True
            request.deadline = time.monotonic() + 15
            return node
        if send_node_command(node.server_name, 'activate'):
            self._pending.pop(directory, None)
            return node
        request = self._pending.get(directory)
        if request is not None and time.monotonic() < request.deadline:
            request.opening = True
            return node

        process = QProcess()
        process.setProgram(sys.executable)
        script = Path(__file__).resolve().parents[1] / 'mbs_node_manager.py'
        process.setArguments([str(script), '--node', config['directory']])
        process.setWorkingDirectory(str(self.working_directory))
        process.setStandardInputFile(QProcess.nullDevice())
        process.setStandardOutputFile(QProcess.nullDevice())
        log_dir = self.working_directory / 'logs'
        log_dir.mkdir(exist_ok=True)
        process.setStandardErrorFile(str(log_dir / f'launcher_{node.server_name}.log'), QIODevice.OpenModeFlag.Append)
        started, pid = process.startDetached()
        if not started:
            raise RuntimeError(f'Cannot start {node.name}: {process.errorString()}')
        self._pending[directory] = PendingNodeWindow(True, time.monotonic() + 15)
        self._pending_timer.start()
        logger.info(f'Started independent manager for {node.name} (PID {pid})')
        return node
