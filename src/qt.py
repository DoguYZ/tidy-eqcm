# database
import src.csvtojson
import src.experimentClass
import src.getData
import src.export

import sys
import time

import numpy as np
import pandas as pd
import scipy.signal
import scipy.integrate
from scipy.interpolate import interp1d


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QVBoxLayout, QGridLayout, QWidget, QFileDialog, 
                             QLabel)

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton
from matplotlib.lines import Line2D

class InfoWindow(QWidget):
    def __init__(self, parent=None, main=None):
        super().__init__(parent)
        self.main = main
        self.layout = QVBoxLayout()
        self.button_file = QPushButton("Open file…")
        self.button_file.clicked.connect(self._on_click)
        self.layout.addWidget(self.button_file)
        self.setLayout(self.layout)

        self.button_save = QPushButton("Save data")
        self.button_save.clicked.connect(self._save_file)

    def _on_click(self):
        self.main._open_file_dialog()
        try:
            self.layout.removeWidget(self.label_key)
            self.layout.removeWidget(self.label_electrolyte)
            self.layout.removeWidget(self.label_sample)
            self.layout.removeWidget(self.button_save)
        except AttributeError:
            pass
        finally:
            self._show_metadata()

    def _save_file(self):
        src.export.main(self.main.experiment, self.main.database, self.main.database_path)


    def _show_metadata(self):
        self.label_key = QLabel(f'Experiment key: {self.main.experiment.key}')
        self.label_electrolyte = QLabel(f'Electrolyte: {self.main.experiment.electrolyte}')
        self.label_sample = QLabel(f'Sample: {self.main.experiment.sample}')
        self.layout.addWidget(self.label_key)
        self.layout.addWidget(self.label_electrolyte)
        self.layout.addWidget(self.label_sample)
        self.layout.addWidget(self.button_save)

    def _show_save_button(self):
        self.layout.addWidget(self.button_save)




class ApplicationWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()
        self.info = InfoWindow(main=self)
        self.info.setStyleSheet("QLabel{font-size: 18pt;}")
        self.info.show()

        try:
            self.database = src.csvtojson.main(database)
            self.database_path = database
            print('Database found')
        except:
            print('Database not found, exiting')
            sys.exit()

        self.experiment = None
        self.savgol = False
        self.drift = False
        self.handles = None
        self.handles_drift = None
        self.toggle_pretend = False

        self._main = QWidget()
        self.setCentralWidget(self._main)
        vbox = QVBoxLayout(self._main)
        grid = QGridLayout()

        # self.button = QPushButton("Open file…")
        # self.button.clicked.connect(self._open_file_dialog)
        #vbox.addWidget(self.button)

        vbox.addLayout(grid)

        ### canvases
        
        # frequency and potential vs time
        canvas_freq_pot = FigureCanvas(Figure(figsize=(5, 3)))
        toolbar_freq_pot = NavigationToolbar(canvas_freq_pot, self)
        grid.addWidget(toolbar_freq_pot, 0, 0)
        grid.addWidget(canvas_freq_pot, 1, 0)

        self._freq_pot_ax1 = canvas_freq_pot.figure.subplots()
        self._freq_pot_ax2 = self._freq_pot_ax1.twinx()

        self._freq_pot_line1, = self._freq_pot_ax1.plot([], [], 'g')
        self._freq_pot_line2, = self._freq_pot_ax2.plot([], [], 'b', alpha=0.4)
        self._freq_pot_line3, = self._freq_pot_ax2.plot([], [], 'b')
        self._freq_pot_line4, = self._freq_pot_ax2.plot([], [], 'r')

        self._freq_pot_ax1.set_xlabel(r'Time')
        self._freq_pot_ax1.set_ylabel(r'Potential (V)')
        self._freq_pot_ax2.set_ylabel(r'Frequency (Hz)')

        canvas_freq_pot.mpl_connect('button_press_event', 
                                    self._canvas1_on_click)

        # aligning eqcm and cv
        canvas_align = FigureCanvas(Figure(figsize=(5, 3)))
        toolbar_align = NavigationToolbar(canvas_align, self)
        grid.addWidget(toolbar_align, 3, 0)
        grid.addWidget(canvas_align, 2, 0)

        self._align_ax1 = canvas_align.figure.subplots()
        self._align_ax2 = self._align_ax1.twinx()

        self._align_line1, = self._align_ax1.plot([], [], 'g')
        self._align_line2, = self._align_ax2.plot([], [], 'b', alpha=0.4)
        self._align_line3, = self._align_ax2.plot([], [], 'b')

        self._align_ax1.set_xlabel(r'Time')
        self._align_ax1.set_ylabel(r'Potential (V)')
        self._align_ax2.set_ylabel(r'Frequency (Hz)')

        # cv
        canvas_cv = FigureCanvas(Figure(figsize=(5, 3)))
        toolbar_cv = NavigationToolbar(canvas_cv, self)
        grid.addWidget(toolbar_cv, 0, 1)
        grid.addWidget(canvas_cv, 1, 1)

        self._cv_ax = canvas_cv.figure.subplots()

        self._cv_line, = self._cv_ax.plot([], [], 'g')

        self._cv_ax.set_xlabel(r'Potential (V)')
        self._cv_ax.set_ylabel(r'Current (mA)')

        # eqcm
        canvas_eqcm = FigureCanvas(Figure(figsize=(5, 3)))
        toolbar_eqcm = NavigationToolbar(canvas_eqcm, self)
        grid.addWidget(toolbar_eqcm, 3, 1)
        grid.addWidget(canvas_eqcm, 2, 1)

        self._eqcm_ax = canvas_eqcm.figure.subplots()

        self._eqcm_line, = self._eqcm_ax.plot([], [], 'b', alpha=0.4)
        self._eqcm_line2, = self._eqcm_ax.plot([], [], 'b')

        self._eqcm_ax.set_xlabel(r'Potential (V)')
        self._eqcm_ax.set_ylabel(r'Frequency (Hz)')

        self.plots = [(canvas_freq_pot, toolbar_freq_pot), (canvas_align, toolbar_align), (canvas_cv, toolbar_cv), (canvas_eqcm, toolbar_eqcm)]


        ###
    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pick a file",
            "/home/batu/University/MEP/Data/",
            "CSV files (*.csv)"
        )
        if file_path:
            self._load_experiment(file_path)
            #self.label.setText(f'Currently processing: {self.experiment.key}')


    def _load_experiment(self, file_path):
        self.savgol = False
        self.drift = False
        self.toggle_pretend = False

        file_dict = src.getData.main(file_path)
        self.experiment = src.experimentClass.Experiment(file_dict)

        self.handles = [
                Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'window = {self.experiment.window}'),
                Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'order = {self.experiment.order}'),
                ]


        try:
            self.experiment.from_dict(self.database[self.experiment.key])
            print(f'Found an entry for {self.experiment.key}')
        except KeyError:
            print(f"Didn't find an entry for {self.experiment.key}")

        self.experiment.eqcm = self.experiment.eqcm.assign(
                timestamp_moved = self.experiment.eqcm.timestamp + self.experiment.time_diff)

        self.experiment.eqcm = self.experiment.eqcm.assign(
                frequency_savgol = self.experiment.eqcm.frequency)

        self.experiment.eqcm = self.experiment.eqcm.assign(
                frequency_copy = self.experiment.eqcm.frequency)

        self.experiment.eqcm = self.experiment.eqcm.assign(
                frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)

        self.experiment.eqcm = self._add_potential_and_cycle_number(
                self.experiment.cv, 
                self.experiment.eqcm, 
                0.0)

        current_cycle = self.experiment.cv.loc[self.experiment.cv['cycle_number'] == self.experiment.cycle_number]
        next_cycle = self.experiment.cv.loc[self.experiment.cv['cycle_number'] == self.experiment.cycle_number].head(3)
        combined_cycles = pd.concat([current_cycle, next_cycle])

        current_cycle_eqcm = self.experiment.eqcm.loc[self.experiment.eqcm['cycle_number'] == self.experiment.cycle_number]

        x_min = self.experiment.cv.query('cycle_number == @self.experiment.cycle_number').iloc[0].timestamp
        x_max = self.experiment.cv.query('cycle_number == @self.experiment.cycle_number').iloc[-1].timestamp

        self._align_ax1.set_xlim([x_min, x_max])

        self._update_plot(self._freq_pot_line1, 
                          self.experiment.cv.timestamp,
                          self.experiment.cv.potential_we_V)
        self._update_plot(self._freq_pot_line2, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency)
        self._update_plot(self._freq_pot_line3, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency_savgol)
        self._update_plot(self._freq_pot_line4, 
                          [],
                          [])
        self._update_plot(self._align_line1, 
                          self.experiment.cv.timestamp,
                          self.experiment.cv.potential_we_V)
        self._update_plot(self._align_line2, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency)
        self._update_plot(self._align_line3, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency_savgol)
        self._update_plot(self._cv_line, 
                          combined_cycles.potential_we_V,
                          combined_cycles.current_mA)
        self._update_plot(self._eqcm_line, 
                          current_cycle_eqcm.potential_we_V,
                          current_cycle_eqcm.frequency)
        self._update_plot(self._eqcm_line2, 
                          current_cycle_eqcm.potential_we_V,
                          current_cycle_eqcm.frequency_savgol)

        v_min = self.experiment.cv.query('cycle_number == 1').potential_we_V.min()
        v_max = self.experiment.cv.query('cycle_number == 1').potential_we_V.max()

        extremes  = self.experiment.cv.loc[self.experiment.cv.groupby(['cycle_number'])['potential_we_V']\
                .idxmax()].reset_index(drop=True).timestamp.tolist()
        extremes += self.experiment.cv.loc[self.experiment.cv.groupby(['cycle_number'])['potential_we_V']\
                .idxmin()].reset_index(drop=True).timestamp.tolist()
        
        for ext in extremes:
            vert_y = np.linspace(v_min, v_max, 2)
            vert_x = np.ones(2) * ext
            self._align_ax1.plot(
               vert_x,
               vert_y,
                   'g-')

    
    def _update_plot(self, line, x, y):
        line.set_data(x, y)
        ax = line.axes          # or store ax when you create it
        ax.relim()                             # recompute data limits
        ax.autoscale_view()
        ax.figure.canvas.draw_idle()


    def keyPressEvent(self, event):
        shift_amount = 0.05

        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.info.close()
        elif event.key() == Qt.Key.Key_Space:
            #pass
            print("space pressed")
        elif event.key() == Qt.Key.Key_H:
            self.experiment.time_diff -= shift_amount
            self.experiment.eqcm = self._add_potential_and_cycle_number(
                    self.experiment.cv, 
                    self.experiment.eqcm, 
                    -shift_amount)
            #print(f'Time shift: {self.experiment.eqcm.timestamp.iloc[0] - self.experiment.eqcm.timestamp_moved.iloc[0]}')
            self._update_all()
        elif event.key() == Qt.Key.Key_L:
            self.experiment.time_diff += shift_amount
            self.experiment.eqcm = self._add_potential_and_cycle_number(
                    self.experiment.cv, 
                    self.experiment.eqcm, 
                    +shift_amount)
            #print(f'Time shift: {self.experiment.eqcm.timestamp.iloc[0] - self.experiment.eqcm.timestamp_moved.iloc[0]}')
            self._update_all()
        elif event.key() == Qt.Key.Key_U:
            self.experiment.eqcm = self.experiment.eqcm.assign(
                    timestamp_moved = self.experiment.eqcm.timestamp)
            self.experiment.eqcm = self._add_potential_and_cycle_number(
                    self.experiment.cv, 
                    self.experiment.eqcm, 
                    0.0)
            self.experiment.time_diff = 0.0
            print(f'Time shift reset')
            self._update_all()
        elif event.key() == Qt.Key.Key_N:
            if self.savgol:
                self._eqcm_ax.get_legend().remove()
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol = self.experiment.eqcm.frequency)
                self.savgol = False
            else:
                self._eqcm_ax.legend(handles=self.handles, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._add_savgol(self.experiment, self.experiment.window, self.experiment.order)
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)
                self.savgol = True
            self._update_all()
        elif event.key() == Qt.Key.Key_M:
            if self.drift:
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency = self.experiment.eqcm.frequency_copy)
                if self.savgol:
                    self.experiment.eqcm = self.experiment.eqcm.assign(
                            frequency_savgol = self.experiment.eqcm.frequency_savgol_copy)
                else:
                    self.experiment.eqcm = self.experiment.eqcm.assign(
                            frequency_savgol = self.experiment.eqcm.frequency_copy)
                self.drift = False
            else:
                self._remove_drift(self.experiment)
                self.drift = True
            self._update_all()
        elif event.key() == Qt.Key.Key_B:
            # self.handles_drift = [
            #         Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'polynomial degree = {self.experiment.drift_degree}'),
            #         ]
            # self._freq_pot_ax1.legend(handles=self.handles_drift, handlelength=0, loc='best', frameon=True, title='Parameters')
            self._freq_pot_ax1.set_title(f'Polynomial degree: {self.experiment.drift_degree}')
            self._remove_drift(self.experiment, pretend=True)
        elif event.key() == Qt.Key.Key_C:
            if self.experiment.drift_degree > 0:
                self.experiment.drift_degree -= 1
                # self.handles_drift = [
                #         Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'polynomial degree = {self.experiment.drift_degree}'),
                #         ]
                # self._freq_pot_ax1.legend(handles=self.handles_drift, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._freq_pot_ax1.set_title(f'Polynomial degree: {self.experiment.drift_degree}')
                self._remove_drift(self.experiment, pretend=True, change=True)
        elif event.key() == Qt.Key.Key_V:
            self.experiment.drift_degree += 1
            # self.handles_drift = [
            #         Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'polynomial degree = {self.experiment.drift_degree}'),
            #         ]
            # self._freq_pot_ax1.legend(handles=self.handles_drift, handlelength=0, loc='best', frameon=True, title='Parameters')
            self._freq_pot_ax1.set_title(f'Polynomial degree: {self.experiment.drift_degree}')
            self._remove_drift(self.experiment, pretend=True, change=True)
        # elif event.key() == Qt.Key.Key_C:
        #     if self.drift and self.experiment.drift_degree > 0:
        #         self.experiment.eqcm = self.experiment.eqcm.assign(
        #                 frequency = self.experiment.eqcm.frequency_copy)
        #         if self.savgol:
        #             self.experiment.eqcm = self.experiment.eqcm.assign(
        #                     frequency_savgol = self.experiment.eqcm.frequency_savgol_copy)
        #         else:
        #             self.experiment.eqcm = self.experiment.eqcm.assign(
        #                     frequency_savgol = self.experiment.eqcm.frequency_copy)
        #         self.experiment.drift_degree -= 1
        #         self._remove_drift(self.experiment)
        #         self._update_all()
        # elif event.key() == Qt.Key.Key_V:
        #     if self.drift:
        #         self.experiment.eqcm = self.experiment.eqcm.assign(
        #                 frequency = self.experiment.eqcm.frequency_copy)
        #         if self.savgol:
        #             self.experiment.eqcm = self.experiment.eqcm.assign(
        #                     frequency_savgol = self.experiment.eqcm.frequency_savgol_copy)
        #         else:
        #             self.experiment.eqcm = self.experiment.eqcm.assign(
        #                     frequency_savgol = self.experiment.eqcm.frequency_copy)
        #         self.experiment.drift_degree += 1
        #         self._remove_drift(self.experiment)
        #         self._update_all()
        elif event.key() == Qt.Key.Key_D:
            if self.savgol:
                self.experiment.window += 1
                self.handles = [
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'window = {self.experiment.window}'),
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'order = {self.experiment.order}'),
                        ]
                self._eqcm_ax.legend(handles=self.handles, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._add_savgol(self.experiment, self.experiment.window, self.experiment.order)
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)
                self._update_all()
            else:
                pass
        elif event.key() == Qt.Key.Key_A:
            if self.savgol:
                if self.experiment.window > self.experiment.order + 1:
                    self.experiment.window -= 1
                self.handles = [
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'window = {self.experiment.window}'),
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'order = {self.experiment.order}'),
                        ]
                self._eqcm_ax.legend(handles=self.handles, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._add_savgol(self.experiment, self.experiment.window, self.experiment.order)
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)
                self._update_all()
            else:
                pass
        elif event.key() == Qt.Key.Key_W:
            if self.savgol:
                self.experiment.order += 2
                self.handles = [
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'window = {self.experiment.window}'),
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'order = {self.experiment.order}'),
                        ]
                self._eqcm_ax.legend(handles=self.handles, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._add_savgol(self.experiment, self.experiment.window, self.experiment.order)
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)
                self._update_all()
            else:
                pass
        elif event.key() == Qt.Key.Key_S:
            if self.savgol:
                if self.experiment.order > 0:
                    self.experiment.order -= 2
                self.handles = [
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'window = {self.experiment.window}'),
                        Line2D([0], [0], linestyle='None', marker='None', lw=2, label=f'order = {self.experiment.order}'),
                        ]
                self._eqcm_ax.legend(handles=self.handles, handlelength=0, loc='best', frameon=True, title='Parameters')
                self._add_savgol(self.experiment, self.experiment.window, self.experiment.order)
                self.experiment.eqcm = self.experiment.eqcm.assign(
                        frequency_savgol_copy = self.experiment.eqcm.frequency_savgol)
                self._update_all()
            else:
                pass
        elif event.key() == Qt.Key.Key_Z:
            cx, cy, zoom = 0.5, 0.5, 2.0  
            xlim = self._align_ax1.get_xlim()
            ylim = self._align_ax1.get_ylim()

            xc = xlim[0] + (xlim[1] - xlim[0]) * cx
            yc = ylim[0] + (ylim[1] - ylim[0]) * cy
            dx = (xlim[1] - xlim[0]) / (2 * zoom)
            dy = (ylim[1] - ylim[0]) / (2 * zoom)

            self._align_ax1.set_xlim(xc - dx, xc + dx)
            self._align_ax1.set_ylim(yc - dy, yc + dy)

            self._align_ax1.figure.canvas.draw_idle()
        elif event.key() == Qt.Key.Key_X:
            cx, cy, zoom = 0.5, 0.5, 0.50  
            xlim = self._align_ax1.get_xlim()
            ylim = self._align_ax1.get_ylim()

            xc = xlim[0] + (xlim[1] - xlim[0]) * cx
            yc = ylim[0] + (ylim[1] - ylim[0]) * cy
            dx = (xlim[1] - xlim[0]) / (2 * zoom)
            dy = (ylim[1] - ylim[0]) / (2 * zoom)

            self._align_ax1.set_xlim(xc - dx, xc + dx)
            self._align_ax1.set_ylim(yc - dy, yc + dy)

            self._align_ax1.figure.canvas.draw_idle()
        elif event.key() == Qt.Key.Key_1:
            self._toggle_fullscreen(0)
        elif event.key() == Qt.Key.Key_2:
            self._toggle_fullscreen(1)
        elif event.key() == Qt.Key.Key_3:
            self._toggle_fullscreen(2)
        elif event.key() == Qt.Key.Key_4:
            self._toggle_fullscreen(3)
        elif event.key() == Qt.Key.Key_5:
            self._toggle_fullscreen(4)
        else:
            super().keyPressEvent(event)

    def _canvas1_on_click(self, event):
        if event.button is MouseButton.LEFT:
            if event.inaxes:
                x_fig, y_fig = event.xdata, event.ydata

            self.experiment.cycle_number = int(
                self.experiment.cv.loc[
                    (self.experiment.cv.timestamp - x_fig).abs().idxmin()
                ].cycle_number
            )

            x_min = self.experiment.cv.query('cycle_number == @self.experiment.cycle_number').iloc[0].timestamp
            x_max = self.experiment.cv.query('cycle_number == @self.experiment.cycle_number').iloc[-1].timestamp

            self._align_ax1.set_xlim([x_min, x_max])
            self._align_ax1.figure.canvas.draw_idle()

            current_cycle = self.experiment.cv.loc[self.experiment.cv['cycle_number'] == self.experiment.cycle_number]
            next_cycle = self.experiment.cv.loc[self.experiment.cv['cycle_number'] == self.experiment.cycle_number].head(3)
            combined_cycles = pd.concat([current_cycle, next_cycle])

            print(scipy.integrate.trapezoid(
                y = current_cycle.current_mA,
                x = current_cycle.potential_we_V,
                dx = 0.01
                ))

            self._update_plot(self._cv_line, 
                              combined_cycles.potential_we_V,
                              combined_cycles.current_mA)

            current_cycle_eqcm = self.experiment.eqcm.loc[self.experiment.eqcm['cycle_number'] == self.experiment.cycle_number]
            self._update_plot(self._eqcm_line, 
                              current_cycle_eqcm.potential_we_V,
                              current_cycle_eqcm.frequency)
            self._update_plot(self._eqcm_line2, 
                              current_cycle_eqcm.potential_we_V,
                              current_cycle_eqcm.frequency_savgol)


    def _update_all(self):
        current_cycle_eqcm = self.experiment.eqcm.loc[self.experiment.eqcm['cycle_number'] == self.experiment.cycle_number]

        self._update_plot(self._freq_pot_line1, 
                          self.experiment.cv.timestamp,
                          self.experiment.cv.potential_we_V)
        self._update_plot(self._freq_pot_line2, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency)
        self._update_plot(self._freq_pot_line3, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency_savgol)
        self._update_plot(self._align_line1, 
                          self.experiment.cv.timestamp,
                          self.experiment.cv.potential_we_V)
        self._update_plot(self._align_line2, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency)
        self._update_plot(self._align_line3, 
                          self.experiment.eqcm.timestamp_moved,
                          self.experiment.eqcm.frequency_savgol)
        self._update_plot(self._eqcm_line, 
                          current_cycle_eqcm.potential_we_V,
                          current_cycle_eqcm.frequency)
        self._update_plot(self._eqcm_line2, 
                          current_cycle_eqcm.potential_we_V,
                          current_cycle_eqcm.frequency_savgol)



    def _add_potential_and_cycle_number(self, cv, eqcm, time_diff):
        # don't get decimal cycle numbers
        f = interp1d(cv.timestamp, cv.cycle_number,
                 kind='nearest', bounds_error=False,
                 fill_value=(cv.cycle_number.iloc[0], cv.cycle_number.iloc[-1]))

        eqcm.timestamp_moved += time_diff
        eqcm = eqcm.assign(potential_we_V = lambda x: np.interp( \
            x.timestamp_moved, cv.timestamp, cv.potential_we_V))
        eqcm = eqcm.assign(cycle_number=lambda d: f(d.timestamp_moved))

        return eqcm

    def _add_savgol(self, experiment, window, order):
        experiment.eqcm = experiment.eqcm.assign(
                frequency_savgol = experiment.eqcm.frequency)
        experiment.eqcm.frequency_savgol = scipy.signal.savgol_filter(experiment.eqcm.frequency, window, order)

    def _remove_drift(self, experiment, pretend=False, change=False):
        extremes = experiment.cv.loc[experiment.cv.groupby(['cycle_number'])['potential_we_V']\
                .idxmax()].reset_index(drop=True).timestamp.tolist()
        extremes_lengths = experiment.cv.groupby(['cycle_number']).count()

        if extremes_lengths.iloc[-1]['timestamp'] < 0.75*extremes_lengths.iloc[-2]['timestamp']:
            print('Not including final CV cycle')
            extremes.pop()
        else:
            print('Including final CV cycle')

        extremes_eqcm = []
        extremes_eqcm_vals = []

        for i in range(len(extremes)):
            extremes_eqcm.append(self._find_nearest(experiment.eqcm.timestamp_moved, extremes[i]))
            extremes_eqcm_vals.append(experiment.eqcm.loc[experiment.eqcm['timestamp_moved'] == extremes_eqcm[i], 'frequency_savgol'].values[0])
            
        pp2 = np.polynomial.Polynomial.fit(extremes_eqcm, extremes_eqcm_vals, deg=experiment.drift_degree)
        drift = pp2(experiment.eqcm.timestamp)
        if not pretend:
            self.toggle_pretend = False
            try:
                # self._freq_pot_ax1.get_legend().remove()
                self._freq_pot_ax1.set_title('')
            except AttributeError:
                pass
            experiment.eqcm.frequency  = experiment.eqcm.frequency - drift + drift[0]
            experiment.eqcm.frequency_savgol  = experiment.eqcm.frequency_savgol - drift + drift[0]
            self._update_plot(self._freq_pot_line4, 
                              [],
                              [])
        elif self.toggle_pretend and not change:
            self.toggle_pretend = False
            try:
                # self._freq_pot_ax1.get_legend().remove()
                self._freq_pot_ax1.set_title('')
            except AttributeError:
                pass
            self._update_plot(self._freq_pot_line4, 
                              [],
                              [])
        else:
            self.toggle_pretend = True
            self._update_plot(self._freq_pot_line4, 
                              experiment.eqcm.timestamp,
                              drift)


    def _find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]


    def _toggle_fullscreen(self, idx):
        if idx < 4:
            for i, (canvas, nav) in enumerate(self.plots):
                vis = (i == idx)
                canvas.setVisible(vis)
                nav.setVisible(vis)
        else:                              # restore normal view
            for canvas, nav in self.plots:
                canvas.setVisible(True)
                nav.setVisible(True)


def main(database):
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(sys.argv)

    app = ApplicationWindow(database)
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()

if __name__ == "__main__":
    main()
