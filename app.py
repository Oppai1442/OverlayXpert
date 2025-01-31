import sys
from PyQt5.QtWidgets import (QApplication)
from PyQt5.QtGui import QIcon
from resources import *

from models.OverlayManager import OverlayManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":icon.ico"))
    window = OverlayManager()
    window.show()
    sys.exit(app.exec_())
