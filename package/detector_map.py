"""Clickable detector regions from the SuperFRS SVG's named rectangles."""

__author__ = 'Irakli Keshelashvili'
__email__ = 'i.keshelashvili@gsi.de'

from pathlib import Path
from xml.dom import minidom

from PyQt6.QtCore import QByteArray, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF, QTransform
from PyQt6.QtSvgWidgets import QSvgWidget

from node_groups import DETECTOR_GROUPS, node_group

SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
INKSCAPE_NAMESPACE = 'http://www.inkscape.org/namespaces/inkscape'


class DetectorMapWidget(QSvgWidget):
    node_clicked = pyqtSignal(str)

    def __init__(self, filename, node_configs, parent=None):
        super().__init__(parent)
        self.node_configs = {node['directory'].upper(): node for node in node_configs}
        self.hovered_id = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        with minidom.parseString(Path(filename).read_bytes()) as document:
            targets = []
            for rectangle in document.getElementsByTagNameNS(SVG_NAMESPACE, 'rect'):
                element_id = rectangle.getAttribute('id')
                detector_id = element_id
                # Inkscape's Objects panel can name a label while leaving a generated ID.
                if node_group({'directory': detector_id}) not in DETECTOR_GROUPS:
                    detector_id = rectangle.getAttributeNS(INKSCAPE_NAMESPACE, 'label').strip()
                if not element_id or node_group({'directory': detector_id}) not in DETECTOR_GROUPS:
                    continue
                targets.append((element_id, detector_id))
                # Put local transforms on a parent so Qt exposes the exact rotated
                # hit polygon, rather than an oversized axis-aligned bounding box.
                if rectangle.hasAttribute('transform'):
                    wrapper = document.createElementNS(SVG_NAMESPACE, 'g')
                    wrapper.setAttribute('transform', rectangle.getAttribute('transform'))
                    rectangle.removeAttribute('transform')
                    rectangle.parentNode.replaceChild(wrapper, rectangle)
                    wrapper.appendChild(rectangle)
            self.load(QByteArray(document.toxml(encoding='utf-8')))

        renderer = self.renderer()
        renderer.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.hotspots = {
            detector_id: renderer.transformForElement(element_id).map(
                QPolygonF(renderer.boundsOnElement(element_id))
            ) for element_id, detector_id in targets if renderer.elementExists(element_id)
        }

    def _svg_transform(self):
        view_box = self.renderer().viewBoxF()
        area = QRectF(self.contentsRect())
        if view_box.isEmpty() or area.isEmpty():
            return QTransform()
        scale = min(area.width() / view_box.width(), area.height() / view_box.height())
        return QTransform(scale, 0, 0, scale,
                          area.center().x() - scale * view_box.center().x(),
                          area.center().y() - scale * view_box.center().y())

    def element_polygon(self, element_id):
        return self._svg_transform().map(self.hotspots[element_id])

    def element_at(self, position):
        for element_id in reversed(self.hotspots):
            if self.element_polygon(element_id).containsPoint(position, Qt.FillRule.OddEvenFill):
                return element_id
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        bounds = self._svg_transform().mapRect(self.renderer().viewBoxF())
        self.renderer().render(painter, bounds)
        if self.hovered_id is not None:
            color = QColor('#1976d2') if self.hovered_id.upper() in self.node_configs else QColor('#777777')
            painter.setPen(QPen(color, 1.5))
            color.setAlpha(45)
            painter.setBrush(color)
            painter.drawPolygon(self.element_polygon(self.hovered_id))

    def mouseMoveEvent(self, event):
        element_id = self.element_at(event.position())
        if element_id != self.hovered_id:
            self.hovered_id = element_id
            config = self.node_configs.get(element_id.upper()) if element_id else None
            if config is not None:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.setToolTip(f"Open {config['node_name']} ({config['host_name']})")
            elif element_id:
                self.setCursor(Qt.CursorShape.ForbiddenCursor)
                self.setToolTip(f'{element_id}: not configured in config/mbs_nodes.yaml')
            else:
                self.unsetCursor()
                self.setToolTip('')
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_id = None
        self.unsetCursor()
        self.setToolTip('')
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            element_id = self.element_at(event.position())
            if element_id is not None:
                self.node_clicked.emit(element_id)
                event.accept()
                return
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()
