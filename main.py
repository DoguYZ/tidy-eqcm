from src.gui import ApplicationWindow
import sys
from PyQt6.QtWidgets import QApplication


qapp = QApplication.instance()
if not qapp:
    qapp = QApplication(sys.argv)
app = ApplicationWindow()
app.show()
app.activateWindow()
app.raise_()
qapp.exec()
