from src.widgets import InfoWindow
from src.io import load_files, DataLoadError
from src.experiment import Experiment

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QMessageBox,
)


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.info = InfoWindow(main=self)
        # self.info.filesSelected.connect(self._on_files_selected)
        self.info.show()

        self._main = QWidget()
        self.setCentralWidget(self._main)
        vbox = QVBoxLayout(self._main)
        grid = QGridLayout()

        vbox.addLayout(grid)

    def _on_files_selected(self, cv_path, eqcm_path):
        try:
            file_dict = load_files(cv_path, eqcm_path)
        except DataLoadError as e:
            QMessageBox.warning(self, "Load error", str(e))
            self.info.hide_export_rows()
            return
        except FileNotFoundError as e:
            QMessageBox.critical(self, "File not found", str(e))
            self.info.hide_export_rows()
            return

        self.info.show_export_rows()

    # Create Experiment using your existing class
    # self.experiment = expmod.Experiment(files)
    # continue with the post-load UI updates:
    # self._post_load_setup()
