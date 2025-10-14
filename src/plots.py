from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PyQt6.QtWidgets import QGridLayout, QWidget

from typing import Optional, TYPE_CHECKING
import pandas as pd
import numpy as np

# only imports during type checking, not runtime: fix circular import
if TYPE_CHECKING:
    from src.gui import ApplicationWindow


class Plots(QWidget):
    def __init__(
        self,
        grid: QGridLayout,
        main: "ApplicationWindow",  # forward reference as string
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.main = main

        self.savgol_visibility = False
        self.fit_visibility = False
        self.fit_applied = False
        self.drift = np.array([])

        # frequency and potential vs time
        self._canvas_freq_pot = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_freq_pot = NavigationToolbar(self._canvas_freq_pot)
        self._freq_pot_ax1 = self._canvas_freq_pot.figure.subplots()
        self._freq_pot_ax2 = self._freq_pot_ax1.twinx()
        self._freq_pot_ax3 = self._freq_pot_ax1.twinx()
        (self._freq_pot_pot_line,) = self._freq_pot_ax1.plot([], [], "black")
        (self._freq_pot_freq_line,) = self._freq_pot_ax2.plot([], [], "red")
        (self._freq_pot_freq_savgol_line,) = self._freq_pot_ax2.plot(
            [], [], "red"
        )
        (self._freq_pot_freq_fit_line,) = self._freq_pot_ax3.plot(
            [], [], "blue"
        )
        self._freq_pot_freq_savgol_line.set_visible(self.savgol_visibility)
        self._freq_pot_freq_fit_line.set_visible(self.fit_visibility)
        self._freq_pot_ax1.set_title("Click to select a cycle")
        self._freq_pot_ax1.set_xlabel(r"Time (s)")
        self._freq_pot_ax1.set_ylabel(r"Potential (V)")
        self._freq_pot_ax2.set_ylabel(r"Frequency (Hz)")

        self._canvas_freq_pot.mpl_connect("button_press_event", self._on_click)

        # aligning eqcm and cv
        self._canvas_align = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_align = NavigationToolbar(self._canvas_align, self)
        self._align_ax1 = self._canvas_align.figure.subplots()
        self._align_ax2 = self._align_ax1.twinx()
        (self._align_pot_line,) = self._align_ax1.plot([], [], "black")
        (self._align_freq_line,) = self._align_ax2.plot([], [], "red")
        (self._align_freq_savgol_line,) = self._align_ax2.plot([], [], "red")
        self._align_freq_savgol_line.set_visible(self.savgol_visibility)
        self._align_ax1.set_xlabel(r"Time (s)")
        self._align_ax1.set_ylabel(r"Potential (V)")
        self._align_ax2.set_ylabel(r"Frequency (Hz)")

        v_min = self.main.experiment_copy.cv.query(
            "cycle_number == 1"
        ).potential_V.min()
        v_max = self.main.experiment_copy.cv.query(
            "cycle_number == 1"
        ).potential_V.max()

        extremes = (
            self.main.experiment_copy.cv.loc[
                self.main.experiment_copy.cv.groupby(["cycle_number"])[
                    "potential_V"
                ].idxmax()
            ]
            .reset_index(drop=True)
            .timestamp_s.tolist()
        )
        extremes += (
            self.main.experiment_copy.cv.loc[
                self.main.experiment_copy.cv.groupby(["cycle_number"])[
                    "potential_V"
                ].idxmin()
            ]
            .reset_index(drop=True)
            .timestamp_s.tolist()
        )

        for ext in extremes:
            vert_y = np.linspace(v_min, v_max, 2)
            vert_x = np.ones(2) * ext
            self._align_ax1.plot(vert_x, vert_y, "black")

        # cv
        self._canvas_cv = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_cv = NavigationToolbar(self._canvas_cv, self)
        self._cv_ax = self._canvas_cv.figure.subplots()
        (self._cv_line,) = self._cv_ax.plot([], [], "black")
        self._cv_ax.set_xlabel(r"Potential (V)")
        self._cv_ax.set_ylabel(r"Current (mA)")

        # eqcm
        self._canvas_eqcm = FigureCanvas(Figure(figsize=(5, 3)))
        self._toolbar_eqcm = NavigationToolbar(self._canvas_eqcm, self)
        self._eqcm_ax = self._canvas_eqcm.figure.subplots()
        (self._eqcm_line,) = self._eqcm_ax.plot([], [], "red")
        (self._eqcm_savgol_line,) = self._eqcm_ax.plot([], [], "red")
        self._eqcm_savgol_line.set_visible(self.savgol_visibility)
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
        self.set_align_xlims()
        self.update_all_plots()

    def update_freq_pot(self) -> None:
        self._freq_pot_pot_line.set_data(
            self.main.experiment_copy.cv.timestamp_s,
            self.main.experiment_copy.cv.potential_V,
        )
        self._freq_pot_freq_line.set_data(
            self.main.experiment_copy.eqcm.timestamp_s,
            self.main.experiment_copy.eqcm.frequency_Hz,
        )
        self._freq_pot_freq_savgol_line.set_data(
            self.main.experiment_copy.eqcm.timestamp_s,
            self.main.experiment_copy.eqcm.frequency_savgol_Hz,
        )
        self._freq_pot_ax1.relim()
        self._freq_pot_ax1.autoscale_view()
        self._freq_pot_ax2.relim()
        self._freq_pot_ax2.autoscale_view()
        ax2_ylim = self._freq_pot_ax2.get_ylim()
        self._freq_pot_ax3.set_ylim(ax2_ylim)
        self._canvas_freq_pot.draw_idle()

    def update_freq_pot_fit(self) -> None:
        self._freq_pot_ax1.set_title(
            f"Polynomial degree: {self.main.experiment_copy.drift_order}"
        )
        self._freq_pot_freq_fit_line.set_data(
            self.main.experiment_copy.eqcm.timestamp_s,
            self.drift,
        )
        # self._canvas_freq_pot.draw_idle()

    def update_align(self) -> None:
        self._align_pot_line.set_data(
            self.main.experiment_copy.cv.timestamp_s,
            self.main.experiment_copy.cv.potential_V,
        )
        self._align_freq_line.set_data(
            self.main.experiment_copy.eqcm.timestamp_s,
            self.main.experiment_copy.eqcm.frequency_Hz,
        )
        self._align_freq_savgol_line.set_data(
            self.main.experiment_copy.eqcm.timestamp_s,
            self.main.experiment_copy.eqcm.frequency_savgol_Hz,
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
        eqcm_df = self._choose_eqcm_cycle()
        self._eqcm_line.set_data(eqcm_df.potential_V, eqcm_df.frequency_Hz)
        self._eqcm_savgol_line.set_data(
            eqcm_df.potential_V,
            eqcm_df.frequency_savgol_Hz,
        )
        self._eqcm_ax.relim()
        self._eqcm_ax.autoscale_view()
        self._canvas_eqcm.draw_idle()

    def update_all_plots(self):
        self.update_freq_pot()
        self.update_align()
        self.update_eqcm()
        self.update_cv()

    def redraw_all_plots(self):
        self._canvas_freq_pot.draw_idle()
        self._canvas_align.draw_idle()
        self._canvas_cv.draw_idle()
        self._canvas_eqcm.draw_idle()

    def set_align_xlims(self) -> None:
        x_min = (
            self.main.experiment_copy.cv.query(
                "cycle_number == @self.main.experiment_copy.cycle_number"
            )
            .iloc[0]
            .timestamp_s
        )
        x_max = (
            self.main.experiment_copy.cv.query(
                "cycle_number == @self.main.experiment_copy.cycle_number"
            )
            .iloc[-1]
            .timestamp_s
        )

        self._align_ax1.set_xlim((x_min, x_max))

    def toggle_savgol_visibility(self):
        self.savgol_visibility = not self.savgol_visibility
        self._eqcm_savgol_line.set_visible(self.savgol_visibility)
        self._freq_pot_freq_savgol_line.set_visible(self.savgol_visibility)
        self._align_freq_savgol_line.set_visible(self.savgol_visibility)

        alpha = 0.4 if self.savgol_visibility else 1.0
        self._eqcm_line.set_alpha(alpha)
        self._freq_pot_freq_line.set_alpha(alpha)
        self._align_freq_line.set_alpha(alpha)
        self.redraw_all_plots()

        legend = self._eqcm_ax.get_legend()
        if not self.savgol_visibility and legend is not None:
            legend.remove()
        else:
            self.update_savgol_legend()

    def update_savgol_legend(self):
        savgol_handles = [
            Line2D(
                [0],
                [0],
                linestyle="None",
                marker="None",
                lw=2,
                label=f"window = {self.main.experiment_copy.savgol_window}",
            ),
            Line2D(
                [0],
                [0],
                linestyle="None",
                marker="None",
                lw=2,
                label=f"order = {self.main.experiment_copy.savgol_order}",
            ),
        ]

        if self.savgol_visibility:
            self._eqcm_ax.legend(
                handles=savgol_handles,
                handlelength=0,
                loc="best",
                frameon=True,
                title="Parameters",
            )

    def toggle_fit_visibility(self):
        self.fit_visibility = not self.fit_visibility
        self._freq_pot_freq_fit_line.set_visible(self.fit_visibility)

        if not self.fit_visibility:
            self._freq_pot_ax1.set_title('')

        self._canvas_freq_pot.draw_idle()

    def apply_fit(self):
        self.fit_applied = True
        self._freq_pot_ax1.set_title('Fit applied, remove it to adjust fit parameters (press X)')
        self._freq_pot_freq_line.set_color("blue")
        self._freq_pot_freq_savgol_line.set_color("blue")
        self._align_freq_line.set_color("blue")
        self._align_freq_savgol_line.set_color("blue")
        self._eqcm_line.set_color("blue")
        self._eqcm_savgol_line.set_color("blue")
        self._canvas_freq_pot.draw_idle()

    def undo_fit(self):
        self.fit_applied = False
        self._freq_pot_ax1.set_title('')
        self._freq_pot_freq_line.set_color("red")
        self._freq_pot_freq_savgol_line.set_color("red")
        self._align_freq_line.set_color("red")
        self._align_freq_savgol_line.set_color("red")
        self._eqcm_line.set_color("red")
        self._eqcm_savgol_line.set_color("red")
        self._canvas_freq_pot.draw_idle()

    def toggle_fullscreen(self, idx):
        column_count = self.main.grid.columnCount()
        row_count = self.main.grid.rowCount()
        if idx < 4:
            for i, (canvas, nav) in enumerate(self.plots_index):
                vis = i == idx
                canvas.setVisible(vis)
                nav.setVisible(vis)

            row_col_map = {0: (1, 0), 1: (2, 0), 2: (1, 1), 3: (2, 1)}
            row, col = row_col_map[idx]

            for c in range(column_count):
                self.main.grid.setColumnStretch(c, 1 if c == col else 0)
            for r in range(row_count):
                self.main.grid.setRowStretch(r, 1 if r == row else 0)
        else:
            for canvas, nav in self.plots_index:
                canvas.setVisible(True)
                nav.setVisible(True)
            for c in range(column_count):
                    self.main.grid.setColumnStretch(c, 1)
            for r in range(row_count):
                    self.main.grid.setRowStretch(r, 1)

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
        current_cycle = self.main.experiment_copy.cv.loc[
            self.main.experiment_copy.cv.cycle_number
            == self.main.experiment_copy.cycle_number
        ]
        next_cycle_head = self.main.experiment_copy.cv.loc[
            self.main.experiment_copy.cv.cycle_number
            == self.main.experiment_copy.cycle_number
        ].head(3)
        # Sometimes the CV is cut off mid-cycle, so add some points from the
        # next cycle
        if (
            self.main.experiment_copy.cycle_number
            == self.main.experiment_copy.cv.cycle_number.max()
        ):
            return current_cycle
        else:
            return pd.concat([current_cycle, next_cycle_head])

    def _choose_eqcm_cycle(self) -> pd.DataFrame:
        current_cycle = self.main.experiment_copy.eqcm.loc[
            self.main.experiment_copy.eqcm["cycle_number"]
            == self.main.experiment_copy.cycle_number
        ]
        return current_cycle

    def _on_click(self, event) -> None:
        if event.button is MouseButton.LEFT:
            if event.inaxes:
                x_fig = event.xdata

                self.main.experiment_copy.cycle_number = int(
                    self.main.experiment_copy.cv.loc[
                        (self.main.experiment_copy.cv.timestamp_s - x_fig)
                        .abs()
                        .idxmin()
                    ].cycle_number
                )

                self.set_align_xlims()
                self.update_align()
                self.update_cv()
                self.update_eqcm()
