import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt

app = QApplication(sys.argv)

view = QWebEngineView()
view.setWindowFlags(Qt.WindowType.FramelessWindowHint)

view.setUrl(QUrl("https://www.google.com"))
view.show()

sys.exit(app.exec())

