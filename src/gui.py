from src.widgets import InfoWindow
from src.io import load_files, DataLoadError
from src.plots import Plots
from src.experiment import Experiment

from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QMessageBox,
)


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.info = InfoWindow(main = self)
        self.info.loadFiles.connect(self._on_load)
        self.info.exportFiles.connect(self._on_save)
        self.info.show()


        self._main = QWidget()
        self.setCentralWidget(self._main)
        self.vbox = QVBoxLayout(self._main)
        self.grid = QGridLayout()
        self.vbox.addLayout(self.grid)

        self.experiment = None

    def _on_load(self, cv_path, eqcm_path):
        try:
            cv_eqcm_tuple = load_files(cv_path, eqcm_path)
        except DataLoadError as e:
            QMessageBox.warning(self, "Load error", str(e))
            return

        self.experiment = Experiment(cv_eqcm_tuple)
        self.plots = Plots(self.grid, self.experiment)
        self.plots.update_freq_pot()
        self.plots.update_align()
        self.plots.update_cv()
        #self.plots.update_eqcm(self.experiment)
        

    def _on_save(self, export_cv_path, export_eqcm_path):
        pass

    # Create Experiment using your existing class
    # self.experiment = expmod.Experiment(files)
    # continue with the post-load UI updates:
    # self._post_load_setup()

