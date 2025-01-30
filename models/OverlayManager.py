import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import Qt, QTimer
from models.OverlayEditor import OverlayEditor
from models.OverlayWidget import OverlayWidget
from resources import *
import psutil
import win32gui
import win32process

from utils.helpers import shouldShowOverlay

class OverlayManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OverlayXpert - Oppai [0.0.4]")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon(":/icon.ico"))

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
        self.overlay_table.verticalHeader().setVisible(False)
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
        
        self.overlay_table.setItem(row, 1, QTableWidgetItem("Overlay"))
        self.overlay_table.setItem(row, 2, QTableWidgetItem(overlay.process))

        status_item = QTableWidgetItem("Active" if overlay_data.get("active", True) else "Disabled")
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setForeground(Qt.green if overlay_data.get("active", True) else Qt.red)
        self.overlay_table.setItem(row, 3, status_item)

        toggle_btn = QPushButton("Toggle")
        toggle_btn.clicked.connect(lambda _, r=row: self.toggle_overlay_status(r))
        self.overlay_table.setCellWidget(row, 4, toggle_btn)

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

                shouldShowOverlay(overlay)

                row = self.overlay_table.rowCount()
                self.overlay_table.insertRow(row)
                self.overlay_table.setItem(row, 0, QTableWidgetItem(str(index + 1)))  
                self.overlay_table.setItem(row, 1, QTableWidgetItem("Overlay"))
                self.overlay_table.setItem(row, 2, QTableWidgetItem(overlay.process))

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
        for i, overlay in enumerate(self.overlays):
            shouldShowOverlay(overlay)

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
