import sys
from PyQt5.QtWidgets import (QApplication)

from models.OverlayManager import OverlayManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayManager()
    window.show()
    sys.exit(app.exec_())
