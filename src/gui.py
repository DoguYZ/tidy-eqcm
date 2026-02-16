from src.widgets import InfoWindow
from src.io import DataLoadError, load_files, export_files
from src.plots import Plots
from src.experiment import Experiment, ToyExperiment
from src.transform import (
    add_potential_and_cycle_number,
    add_savgol,
    fit_drift,
    remove_drift,
)

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from copy import deepcopy

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QMessageBox,
)


class ApplicationWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.info = InfoWindow(main=self)
        self.info.loadFiles.connect(self._on_load)
        self.info.exportFiles.connect(self._on_save)
        self.info.show()

        self._main = QWidget()
        self.setCentralWidget(self._main)
        self.vbox = QVBoxLayout(self._main)
        self.grid = QGridLayout()
        self.vbox.addLayout(self.grid)

        self.experiment = Experiment()
        self.experiment_copy = deepcopy(ToyExperiment(self.experiment))

    def _on_load(self, cv_path: Path, eqcm_path: Path) -> None:
        try:
            cv_eqcm_tuple = load_files(cv_path, eqcm_path)
        except DataLoadError as e:
            QMessageBox.warning(self, "Load error", str(e))
            return

        self._clear_layout(self.grid)
        self._load_new_experiment(cv_eqcm_tuple)
        self.plots = Plots(self.grid, main=self)

    def _on_save(self, export_cv_path: Path, export_eqcm_path: Path) -> None:
        export_files_full_cycles(self.experiment_copy, export_cv_path, export_eqcm_path)

    def keyPressEvent(self, a0: Optional[QKeyEvent] = None) -> None:
        # check if an experiment is loaded
        if not hasattr(self.experiment, "cv"):
            super().keyPressEvent(a0)
            return

        shift_amount = 0.03

        if a0 is None:  # stub marks a0 as Optional; make type-checker happy
            super().keyPressEvent(a0)
            return

        if a0.key() == Qt.Key.Key_Q:
            self.close()
            self.info.close()
        elif a0.key() == Qt.Key.Key_H and (a0.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            add_potential_and_cycle_number(self.experiment_copy, 10*-shift_amount)
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_L and (a0.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            add_potential_and_cycle_number(self.experiment_copy, 10*+shift_amount)
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_H:
            add_potential_and_cycle_number(self.experiment_copy, -shift_amount)
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_L:
            add_potential_and_cycle_number(self.experiment_copy, +shift_amount)
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_U:
            self._reset_experiment()
            self.plots.update_savgol_legend()
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_N:
            self.plots.toggle_savgol_visibility()
        elif a0.key() == Qt.Key.Key_D:
            if (
                len(self.experiment_copy.eqcm)
                > self.experiment_copy.savgol_window
            ):
                self.experiment_copy.savgol_window += 1
                add_savgol(self.experiment_copy)
                self.plots.update_savgol_legend()
                self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_A:
            if (
                self.experiment_copy.savgol_window
                > self.experiment_copy.savgol_order + 1
            ):
                self.experiment_copy.savgol_window -= 1
                add_savgol(self.experiment_copy)
                self.plots.update_savgol_legend()
                self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_W:
            if (
                self.experiment_copy.savgol_window
                > self.experiment_copy.savgol_order + 2
            ):
                self.experiment_copy.savgol_order += 2
                add_savgol(self.experiment_copy)
                self.plots.update_savgol_legend()
                self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_S:
            if self.experiment_copy.savgol_order > 0:
                self.experiment_copy.savgol_order -= 2
                add_savgol(self.experiment_copy)
                self.plots.update_savgol_legend()
                self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_B and not self.plots.fit_applied:
            self.plots.toggle_fit_visibility()
            self._update_all_plus_drift()
        elif (
            a0.key() == Qt.Key.Key_C
            and not self.plots.fit_applied
            and self.plots.fit_visibility
        ):
            if self.experiment_copy.drift_order > 0:
                self.experiment_copy.drift_order -= 1
                self._update_all_plus_drift()
        elif (
            a0.key() == Qt.Key.Key_V
            and not self.plots.fit_applied
            and self.plots.fit_visibility
        ):
            self.experiment_copy.drift_order += 1
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_X:
            if self.plots.fit_visibility and not self.plots.fit_applied:
                remove_drift(self.experiment_copy, self.plots.drift)
                self.plots.toggle_fit_visibility()
                self.plots.apply_fit()
            elif not self.plots.fit_visibility and self.plots.fit_applied:
                self.experiment_copy.eqcm.frequency_Hz = deepcopy(
                    self.experiment.eqcm.frequency_Hz
                )
                add_savgol(self.experiment_copy)
                self.plots.undo_fit()
                self.plots.toggle_fit_visibility()
            else:
                return
            self._update_all_plus_drift()
        elif a0.key() == Qt.Key.Key_1:
            self.plots.toggle_fullscreen(0)
        elif a0.key() == Qt.Key.Key_2:
            self.plots.toggle_fullscreen(1)
        elif a0.key() == Qt.Key.Key_3:
            self.plots.toggle_fullscreen(2)
        elif a0.key() == Qt.Key.Key_4:
            self.plots.toggle_fullscreen(3)
        elif a0.key() == Qt.Key.Key_5:
            self.plots.toggle_fullscreen(4)
        else:
            super().keyPressEvent(a0)

    def _update_all_plus_drift(self):
        if self.plots.fit_visibility and not self.plots.fit_applied:
            self.plots.drift = fit_drift(self.experiment_copy)
            self.plots.update_freq_pot_fit()
        self.plots.update_all_plots()

    def _load_new_experiment(
        self, cv_eqcm_tuple: Tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        self.experiment = Experiment(cv_eqcm_tuple)
        self._reset_experiment()

    def _reset_experiment(self) -> None:
        self.experiment_copy = deepcopy(ToyExperiment(self.experiment))
        add_potential_and_cycle_number(self.experiment_copy)
        add_savgol(self.experiment_copy)

    def _clear_layout(self, layout) -> None:
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
