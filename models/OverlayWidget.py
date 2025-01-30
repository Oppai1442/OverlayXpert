from PyQt5.QtWidgets import (QWidget)
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QBrush, QFont
from PyQt5.QtCore import Qt

from utils import shouldShowOverlay

class OverlayWidget(QWidget):
    def __init__(self, manager, x=0, y=0, width=100, height=100, color=QColor(0, 0, 0), border=0, opacity=1.0, process="All", active=True):
        super().__init__()
        self.manager = manager
        self.setGeometry(x, y, width, height)
        self.color = color
        self.border = border
        self.opacity = opacity  
        self.process = process  
        self.active = active  
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.is_editing = False
        self.dragging = False
        self.resizing = False
        self.drag_start_pos = None
        self.resize_direction = None

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.setWindowOpacity(opacity)  

    def set_active(self, active):
        self.active = active

        shouldShowOverlay(self)

        self.manager.update_overlay_data(self)

    def set_edit_mode(self, is_editing):
        self.is_editing = is_editing
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if not is_editing:
            flags |= Qt.WindowTransparentForInput  
        self.setWindowFlags(flags)
        shouldShowOverlay(self)

    def get_contrast_text_color(self, bg_color):
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        return Qt.black if luminance > 128 else Qt.white  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.opacity)  
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(self.color, self.border))

        rect = self.rect().adjusted(self.border, self.border, -self.border, -self.border)
        painter.drawRoundedRect(rect, 10, 10)

        if self.manager:
            overlay_index = self.manager.overlays.index(self) + 1  
            text = f"ID: {overlay_index}"

            text_color = self.get_contrast_text_color(self.color)  
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 12, QFont.Bold))  
            text_rect = painter.boundingRect(rect, Qt.AlignCenter, text)  
            painter.drawText(text_rect, Qt.AlignCenter, text)  

    def update_overlay(self, x, y, width, height, color, border):
        self.setGeometry(x, y, width, height)
        self.color = color
        self.border = border
        self.update()

    def mousePressEvent(self, event):
        if self.is_editing:
            self.manager.timer.stop()  
            if event.button() == Qt.LeftButton:
                self.drag_start_pos = event.pos()
                margin = 10

                if event.x() <= margin:
                    if event.y() <= margin:
                        self.resizing = True
                        self.resize_direction = "top-left"
                    elif event.y() >= self.height() - margin:
                        self.resizing = True
                        self.resize_direction = "bottom-left"
                    else:
                        self.resizing = True
                        self.resize_direction = "left"
                elif event.x() >= self.width() - margin:
                    if event.y() <= margin:
                        self.resizing = True
                        self.resize_direction = "top-right"
                    elif event.y() >= self.height() - margin:
                        self.resizing = True
                        self.resize_direction = "bottom-right"
                    else:
                        self.resizing = True
                        self.resize_direction = "right"
                elif event.y() <= margin:
                    self.resizing = True
                    self.resize_direction = "top"
                elif event.y() >= self.height() - margin:
                    self.resizing = True
                    self.resize_direction = "bottom"
                else:
                    self.dragging = True

    def mouseMoveEvent(self, event):
        if self.is_editing:
            margin = 10
            if self.resizing:
                self.setCursor(self.get_resize_cursor(self.resize_direction))
                self.handle_resize(event)
                self.manager.update_overlay_data(self)
            elif self.dragging:
                self.setCursor(QCursor(Qt.SizeAllCursor))
                delta = event.pos() - self.drag_start_pos
                new_x = max(0, self.x() + delta.x())
                new_y = max(0, self.y() + delta.y())
                self.move(new_x, new_y)
                self.manager.update_overlay_data(self)
            else:
                self.update_cursor(event, margin)

    def mouseReleaseEvent(self, event):
        if self.is_editing:
            if self.dragging:
                self.dragging = False
            if self.resizing:
                self.resizing = False
                self.resize_direction = None
                self.setCursor(QCursor(Qt.ArrowCursor))

            self.manager.update_overlay_data(self)
            self.manager.timer.start()  

    def resizeEvent(self, event):
        if self.is_editing:
            self.manager.update_overlay_data(self)

    def update_cursor(self, event, margin):
        if event.x() <= margin:
            if event.y() <= margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            elif event.y() >= self.height() - margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            else:
                self.setCursor(QCursor(Qt.SizeHorCursor))
        elif event.x() >= self.width() - margin:
            if event.y() <= margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            elif event.y() >= self.height() - margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.SizeHorCursor))
        elif event.y() <= margin:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        elif event.y() >= self.height() - margin:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def handle_resize(self, event):
        new_x, new_y, new_width, new_height = self.x(), self.y(), self.width(), self.height()
        if "left" in self.resize_direction:
            delta_x = event.x()
            new_x = max(0, self.x() + delta_x)
            new_width = max(10, self.width() - delta_x)
        if "right" in self.resize_direction:
            new_width = max(10, event.x())
        if "top" in self.resize_direction:
            delta_y = event.y()
            new_y = max(0, self.y() + delta_y)
            new_height = max(10, self.height() - delta_y)
        if "bottom" in self.resize_direction:
            new_height = max(10, event.y())

        if (
            new_x != self.x() or new_y != self.y() or
            new_width != self.width() or new_height != self.height()
        ):
            self.setGeometry(new_x, new_y, new_width, new_height)

    def get_resize_cursor(self, direction):
        return {
            "top-left": QCursor(Qt.SizeFDiagCursor),
            "top-right": QCursor(Qt.SizeBDiagCursor),
            "bottom-left": QCursor(Qt.SizeBDiagCursor),
            "bottom-right": QCursor(Qt.SizeFDiagCursor),
            "left": QCursor(Qt.SizeHorCursor),
            "right": QCursor(Qt.SizeHorCursor),
            "top": QCursor(Qt.SizeVerCursor),
            "bottom": QCursor(Qt.SizeVerCursor)
        }.get(direction, QCursor(Qt.ArrowCursor))
