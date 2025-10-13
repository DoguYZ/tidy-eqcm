from typing import Optional
from src.experiment import Experiment
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QGridLayout,
    QWidget,
)
import pandas as pd


class Plots(QWidget):
    def __init__(
        self,
        grid: QGridLayout,
        experiment: Experiment,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.experiment = experiment

        # frequency and potential vs time
        self._canvas_freq_pot = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_freq_pot = NavigationToolbar(self._canvas_freq_pot)
        self._freq_pot_ax1 = self._canvas_freq_pot.figure.subplots()
        self._freq_pot_ax2 = self._freq_pot_ax1.twinx()
        (self._freq_pot_pot_line,) = self._freq_pot_ax1.plot([], [], "g")
        (self._freq_pot_freq_line,) = self._freq_pot_ax2.plot(
            [], [], "b", alpha=0.4
        )
        (self._freq_pot_freq_savgol_line,) = self._freq_pot_ax2.plot(
            [], [], "b"
        )
        (self._freq_pot_freq_fit_line,) = self._freq_pot_ax2.plot([], [], "r")
        self._freq_pot_ax1.set_xlabel(r"Time")
        self._freq_pot_ax1.set_ylabel(r"Potential (V)")
        self._freq_pot_ax2.set_ylabel(r"Frequency (Hz)")

        self._canvas_freq_pot.mpl_connect("button_press_event", self._on_click)

        # aligning eqcm and cv
        self._canvas_align = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_align = NavigationToolbar(self._canvas_align, self)
        self._align_ax1 = self._canvas_align.figure.subplots()
        self._align_ax2 = self._align_ax1.twinx()
        (self._align_pot_line,) = self._align_ax1.plot([], [], "g")
        (self._align_freq_line,) = self._align_ax2.plot([], [], "b", alpha=0.4)
        (self._align_freq_savgol_line,) = self._align_ax2.plot([], [], "b")
        self._align_ax1.set_xlabel(r"Time")
        self._align_ax1.set_ylabel(r"Potential (V)")
        self._align_ax2.set_ylabel(r"Frequency (Hz)")

        # cv
        self._canvas_cv = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_cv = NavigationToolbar(self._canvas_cv, self)
        self._cv_ax = self._canvas_cv.figure.subplots()
        (self._cv_line,) = self._cv_ax.plot([], [], "g")
        self._cv_ax.set_xlabel(r"Potential (V)")
        self._cv_ax.set_ylabel(r"Current (mA)")

        # eqcm
        self._canvas_eqcm = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_eqcm = NavigationToolbar(self._canvas_eqcm, self)
        self._eqcm_ax = self._canvas_eqcm.figure.subplots()
        (self._eqcm_line,) = self._eqcm_ax.plot([], [], "b", alpha=0.4)
        (self._eqcm_savgol_line,) = self._eqcm_ax.plot([], [], "b")
        self._eqcm_ax.set_xlabel(r"Potential (V)")
        self._eqcm_ax.set_ylabel(r"Frequency (Hz)")

        # change data type from list to.. set?
        self.plots_index = [
            (self._canvas_freq_pot, self._toolbar_freq_pot),
            (self._canvas_align, self._toolbar_align),
            (self._canvas_cv, self._toolbar_cv),
            (self._canvas_eqcm, self._toolbar_eqcm),
        ]

        self._build_ui(grid)

    def update_freq_pot(self) -> None:
        self._freq_pot_pot_line.set_data(
            self.experiment.cv.timestamp_s, self.experiment.cv.potential_V
        )
        self._freq_pot_freq_line.set_data(
            self.experiment.eqcm.timestamp_s, self.experiment.eqcm.frequency_Hz
        )
        self._freq_pot_freq_savgol_line.set_data(
            self.experiment.eqcm.timestamp_s,
            self.experiment.eqcm.frequency_savgol_Hz,
        )
        self._freq_pot_ax1.relim()
        self._freq_pot_ax1.autoscale_view()
        self._freq_pot_ax2.relim()
        self._freq_pot_ax2.autoscale_view()
        self._canvas_freq_pot.draw_idle()

    def update_align(self) -> None:
        self._align_pot_line.set_data(
            self.experiment.cv.timestamp_s, self.experiment.cv.potential_V
        )
        self._align_freq_line.set_data(
            self.experiment.eqcm.timestamp_s, self.experiment.eqcm.frequency_Hz
        )
        self._align_freq_savgol_line.set_data(
            self.experiment.eqcm.timestamp_s,
            self.experiment.eqcm.frequency_savgol_Hz,
        )
        self._align_ax1.relim()
        self._align_ax1.autoscale_view()
        self._align_ax2.relim()
        self._align_ax2.autoscale_view()
        self._canvas_align.draw_idle()

    def update_cv(self) -> None:
        cv_df = self._choose_cv_cycle()
        self._cv_line.set_data(cv_df.potential_V, cv_df.current_mA)
        self._cv_ax.relim()
        self._cv_ax.autoscale_view()
        self._canvas_cv.draw_idle()

    def update_eqcm(self) -> None:
        self._eqcm_line.set_data(
            self.experiment.eqcm.potential_V, self.experiment.eqcm.frequency_Hz
        )
        self._eqcm_savgol_line.set_data(
            self.experiment.eqcm.potential_V,
            self.experiment.eqcm.frequency_savgol_Hz,
        )
        self._eqcm_ax.relim()
        self._eqcm_ax.autoscale_view()
        self._canvas_eqcm.draw_idle()

    def _build_ui(self, grid: QGridLayout) -> None:
        grid.addWidget(self._toolbar_freq_pot, 0, 0)
        grid.addWidget(self._canvas_freq_pot, 1, 0)
        grid.addWidget(self._canvas_align, 2, 0)
        grid.addWidget(self._toolbar_align, 3, 0)
        grid.addWidget(self._toolbar_cv, 0, 1)
        grid.addWidget(self._canvas_cv, 1, 1)
        grid.addWidget(self._canvas_eqcm, 2, 1)
        grid.addWidget(self._toolbar_eqcm, 3, 1)

    def _choose_cv_cycle(self) -> pd.DataFrame:
        current_cycle = self.experiment.cv.loc[
            self.experiment.cv.cycle_number == self.experiment.cycle_number
        ]
        next_cycle_head = self.experiment.cv.loc[
            self.experiment.cv.cycle_number == self.experiment.cycle_number
        ].head(3)
        # Sometimes the CV is cut off mid-cycle, so add some points from the
        # next cycle
        if (
            self.experiment.cycle_number
            == self.experiment.cv.cycle_number.max()
        ):
            return current_cycle
        else:
            return pd.concat([current_cycle, next_cycle_head])

    def _on_click(self, event) -> None:
        if event.button is MouseButton.LEFT:
            if event.inaxes:
                x_fig = event.xdata

                self.experiment.cycle_number = int(
                    self.experiment.cv.loc[
                        (self.experiment.cv.timestamp_s - x_fig).abs().idxmin()
                    ].cycle_number
                )

                x_min = (
                    self.experiment.cv.query(
                        "cycle_number == @self.experiment.cycle_number"
                    )
                    .iloc[0]
                    .timestamp_s
                )
                x_max = (
                    self.experiment.cv.query(
                        "cycle_number == @self.experiment.cycle_number"
                    )
                    .iloc[-1]
                    .timestamp_s
                )

                self._align_ax1.set_xlim((x_min, x_max))
                self.update_align()
                self.update_cv()
