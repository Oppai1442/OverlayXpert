import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QSlider,
                             QLabel, QColorDialog, QSpinBox)
from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QTimer
import psutil
import win32gui
import win32process

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
        if self.active:
            self.show()
        else:
            self.hide()
        self.manager.update_overlay_data(self)

    def set_edit_mode(self, is_editing):
        self.is_editing = is_editing
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if not is_editing:
            flags |= Qt.WindowTransparentForInput  
        self.setWindowFlags(flags)
        self.show()  

    def get_contrast_text_color(self, bg_color):
        """Tính toán màu chữ dựa trên độ sáng của màu nền."""
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

class OverlayManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OverlayXpert - Oppai [0.0.1]")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("icon.ico"))

        self.overlays = []
        self.overlay_data = []
        self.editors = []

        self.initUI()
        self.load_from_json()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_processes)
        self.timer.start(1000)

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.overlay_table = QTableWidget(0, 5)
        self.overlay_table.setHorizontalHeaderLabels(["ID", "App", "Process", "Status", "Active"])
        self.overlay_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.overlay_table.cellDoubleClicked.connect(self.open_editor)
        layout.addWidget(self.overlay_table)

        controls_layout = QHBoxLayout()
        add_overlay_btn = QPushButton("Add Overlay")
        add_overlay_btn.clicked.connect(self.add_overlay)
        controls_layout.addWidget(add_overlay_btn)

        delete_overlay_btn = QPushButton("Delete Overlay")
        delete_overlay_btn.clicked.connect(self.delete_overlay)
        controls_layout.addWidget(delete_overlay_btn)

        self.edit_toggle_btn = QPushButton("Toggle Edit")
        self.edit_toggle_btn.setCheckable(True)
        self.edit_toggle_btn.clicked.connect(self.toggle_edit_mode)
        controls_layout.addWidget(self.edit_toggle_btn)

        layout.addLayout(controls_layout)
        central_widget.setLayout(layout)

    def open_editor(self, row, column):
        if row < 0 or row >= len(self.overlays):  
            return  

        overlay = self.overlays[row]
        data = self.overlay_data[row]
        editor = OverlayEditor(self, overlay, data)
        editor.show()
        self.editors.append(editor)

    def add_overlay(self):
        overlay = OverlayWidget(self)
        overlay.show()

        self.overlays.append(overlay)
        overlay_data = {
            "x": overlay.x(),
            "y": overlay.y(),
            "width": overlay.width(),
            "height": overlay.height(),
            "color": overlay.color.name(),
            "border": overlay.border,
            "opacity": overlay.opacity,
            "process": "All",
            "active": True,
        }
        self.overlay_data.append(overlay_data)

        self.save_to_json()
        row = self.overlay_table.rowCount()
        self.overlay_table.insertRow(row)
        self.overlay_table.setItem(row, 0, QTableWidgetItem(str(len(self.overlays))))

    def delete_overlay(self):
        selected_row = self.overlay_table.currentRow()
        if selected_row >= 0:
            overlay = self.overlays[selected_row]
            overlay.close()
            self.overlays.pop(selected_row)
            self.overlay_data.pop(selected_row)
            self.overlay_table.removeRow(selected_row)
            self.save_to_json()

    def toggle_edit_mode(self):
        is_editing = self.edit_toggle_btn.isChecked()
        for overlay in self.overlays:
            overlay.set_edit_mode(is_editing)

    def save_to_json(self):
        with open("overlays.json", "w") as file:
            json.dump(self.overlay_data, file, indent=4)

    def load_from_json(self):
        try:
            with open("overlays.json", "r") as file:
                self.overlay_data = json.load(file)

            hwnd = win32gui.GetForegroundWindow()
            pid = None
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

            current_process = None
            if pid:
                try:
                    current_process = psutil.Process(pid).name()
                except psutil.NoSuchProcess:
                    pass

            self.overlay_table.setRowCount(0)
            self.overlays.clear()

            for index, data in enumerate(self.overlay_data):
                overlay = OverlayWidget(
                    self,
                    x=data["x"],
                    y=data["y"],
                    width=data["width"],
                    height=data["height"],
                    color=QColor(data["color"]),
                    border=data["border"],
                    opacity=data.get("opacity", 1.0),
                    process=data.get("process", "All"),
                    active=data.get("active", True)
                )

                self.overlays.append(overlay)  

                process = data.get("process", "All")
                if (process == "All" or process == current_process) and overlay.active:
                    overlay.show()
                else:
                    overlay.hide()

                row = self.overlay_table.rowCount()
                self.overlay_table.insertRow(row)
                self.overlay_table.setItem(row, 0, QTableWidgetItem(str(index + 1)))  
                self.overlay_table.setItem(row, 1, QTableWidgetItem("Overlay"))
                self.overlay_table.setItem(row, 2, QTableWidgetItem(process))

                status_item = QTableWidgetItem("Active" if data.get("active", True) else "Disabled")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.green if data.get("active", True) else Qt.red)
                self.overlay_table.setItem(row, 3, status_item)

                toggle_btn = QPushButton("Toggle")
                toggle_btn.clicked.connect(lambda _, r=row: self.toggle_overlay_status(r))
                self.overlay_table.setCellWidget(row, 4, toggle_btn)

            print("Overlays loaded:", len(self.overlays))  

        except (FileNotFoundError, json.JSONDecodeError):
            print("JSON file not found or corrupt!")

    def toggle_overlay_status(self, row):
        overlay = self.overlays[row]
        overlay.set_active(not overlay.active)  

        status_item = self.overlay_table.item(row, 3)
        status_item.setText("Active" if overlay.active else "Disabled")
        status_item.setForeground(Qt.green if overlay.active else Qt.red)

        self.save_to_json()

    def check_processes(self):
        hwnd = win32gui.GetForegroundWindow()
        pid = None
        if hwnd:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

        current_process = None
        if pid:
            try:
                current_process = psutil.Process(pid).name()
            except psutil.NoSuchProcess:
                pass

        for i, overlay in enumerate(self.overlays):
            process = self.overlay_data[i].get("process", "All")
            should_show = overlay.active and (process == "All" or process == current_process)

            if should_show and not overlay.isVisible():  
                overlay.show()  
            elif not should_show and overlay.isVisible():  
                overlay.hide()  

    def update_overlay_data(self, overlay):
        index = self.overlays.index(overlay)
        self.overlay_data[index] = {
            "x": overlay.x(),
            "y": overlay.y(),
            "width": overlay.width(),
            "height": overlay.height(),
            "color": overlay.color.name(),
            "border": overlay.border,
            "process": overlay.process,
            "opacity": overlay.opacity,
            "active": overlay.active
        }
        self.save_to_json()

    def update_overlay_row(self, overlay, process_name):
        if overlay in self.overlays:
            index = self.overlays.index(overlay)
            self.overlay_table.setItem(index, 2, QTableWidgetItem(process_name))

class OverlayEditor(QWidget):
    def __init__(self, manager, overlay, data):
        super().__init__()
        self.manager = manager
        self.overlay = overlay
        self.data = data

        self.setWindowTitle("Edit Overlay")
        self.setGeometry(200, 200, 300, 300)

        layout = QVBoxLayout()

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 1920)
        self.x_spin.setValue(data["x"])
        self.x_spin.valueChanged.connect(self.update_overlay)
        layout.addWidget(QLabel("X Position:"))
        layout.addWidget(self.x_spin)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 1080)
        self.y_spin.setValue(data["y"])
        self.y_spin.valueChanged.connect(self.update_overlay)
        layout.addWidget(QLabel("Y Position:"))
        layout.addWidget(self.y_spin)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 1920)
        self.width_spin.setValue(data["width"])
        self.width_spin.valueChanged.connect(self.update_overlay)
        layout.addWidget(QLabel("Width:"))
        layout.addWidget(self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 1080)
        self.height_spin.setValue(data["height"])
        self.height_spin.valueChanged.connect(self.update_overlay)
        layout.addWidget(QLabel("Height:"))
        layout.addWidget(self.height_spin)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(overlay.opacity * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        layout.addWidget(QLabel("Opacity:"))
        layout.addWidget(self.opacity_slider)

        self.process_combo = QComboBox()
        self.process_combo.addItem("All")
        self.process_combo.addItems(self.get_process_list())
        self.process_combo.setCurrentText(data.get("process", "All"))
        self.process_combo.currentTextChanged.connect(self.update_process)
        layout.addWidget(QLabel("Process:"))
        layout.addWidget(self.process_combo)

        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)

        self.setLayout(layout)

    def update_overlay(self):
        self.data["x"] = self.x_spin.value()
        self.data["y"] = self.y_spin.value()
        self.data["width"] = self.width_spin.value()
        self.data["height"] = self.height_spin.value()
        self.overlay.setGeometry(
            self.data["x"], self.data["y"], self.data["width"], self.data["height"]
        )
        self.manager.save_to_json()

    def update_opacity(self, value):
        opacity = value / 100.0
        self.data["opacity"] = opacity
        self.overlay.set_opacity(opacity)
        self.manager.save_to_json()

    def update_process(self, process_name):
        self.data["process"] = process_name
        self.manager.update_overlay_row(self.overlay, process_name)  
        self.overlay.process = process_name
        self.manager.save_to_json()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.data["color"] = color.name()
            self.overlay.color = color
            self.overlay.update()
            self.manager.save_to_json()

    def get_process_list(self):
        def is_window_visible(hwnd):
            return win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd)

        visible_windows = []
        win32gui.EnumWindows(
            lambda hwnd, _: visible_windows.append(hwnd)
            if is_window_visible(hwnd)
            else None,
            None,
        )

        visible_pids = set()
        for hwnd in visible_windows:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            visible_pids.add(pid)

        processes = []
        for p in psutil.process_iter(["pid", "name"]):
            if p.info["pid"] in visible_pids:
                processes.append(p.info["name"])

        return list(set(processes))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayManager()
    window.show()
    sys.exit(app.exec_())
