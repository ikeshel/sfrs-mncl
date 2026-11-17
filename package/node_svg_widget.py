"""SVG display with an explicitly painted background for resize/letterbox areas."""

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtSvgWidgets import QSvgWidget
from node_svg import svg_for_power_led


class NodeSvgWidget(QSvgWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.power_led_color = None
        self._led_variants = {}

    def load_node_svg(self, svg_data):
        self._svg_data = svg_data
        self._led_variants.clear()
        self.power_led_color = None
        self.load(QByteArray(svg_data))
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)

    def set_power_led_color(self, color):
        if color == self.power_led_color or not self.renderer().elementExists('led_power'):
            return
        # Cache the few heartbeat variants instead of editing XML every poll.
        if color not in self._led_variants:
            self._led_variants[color] = svg_for_power_led(self._svg_data, color)
        self.load(QByteArray(self._led_variants[color]))
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.power_led_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        self.renderer().render(painter, QRectF(self.rect()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # The image is centered: even pixels outside the new image must be cleared.
        self.update()
