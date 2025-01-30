from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QComboBox, QSlider, QLabel, QColorDialog, QSpinBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from resources import *
import psutil
import win32gui
import win32process

class OverlayEditor(QWidget):
    def __init__(self, manager, overlay, data):
        super().__init__()
        self.manager = manager
        self.overlay = overlay
        self.data = data

        self.setWindowTitle("Edit Overlay")
        self.setGeometry(200, 200, 300, 300)
        self.setWindowIcon(QIcon(":/icon.ico"))

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
        layout.addWidget(QLabel("Restricted Process:"))
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
