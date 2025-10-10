from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)


class InfoWindow(QWidget):
    filesSelected = pyqtSignal(str, str)
    exportPathsChanged = pyqtSignal(str, str)

    def __init__(self, parent=None, main=None):
        super().__init__(parent)
        self.main = main

        self.cv_path = ""
        self.eqcm_path = ""
        self.export_cv_path = ""
        self.export_eqcm_path = ""

        self.cv_edit = None
        self.eqcm_edit = None
        self.export_cv_edit = None
        self.export_eqcm_edit = None

        self._export_rows_visible = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Input rows for source files
        self._add_file_row("CV file:", self._on_browse_cv, "cv")
        self._add_file_row("EQCM file:", self._on_browse_eqcm, "eqcm")

        # Load button (disabled until both source files are selected)
        self.load_button = QPushButton("Load files")
        self.load_button.setEnabled(False)
        self.load_button.clicked.connect(self._on_load)
        self.layout.addWidget(self.load_button)

        # Export rows (hidden until Load)
        self._export_cv_row = self._create_export_row("Export new CV file:", self._on_browse_export_cv, "cv")
        self._export_eqcm_row = self._create_export_row("Export new EQCM file:", self._on_browse_export_eqcm, "eqcm")

        # Save button (disabled until export paths set)
        self.save_button = QPushButton("Save exported files")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save)
        self.layout.addWidget(self.save_button)

    def _add_file_row(self, label_text, browse_callback, technique):
        row = QHBoxLayout()
        label = QLabel(label_text)
        edit = QLineEdit()
        edit.setReadOnly(True)
        browse = QPushButton("Browse…")
        browse.clicked.connect(browse_callback)
        row.addWidget(label)
        row.addWidget(edit)
        row.addWidget(browse)
        match technique:
            case "cv":
                self.cv_edit = edit
            case "eqcm":
                self.eqcm_edit = edit
            case _:
                raise Exception("Unknown technique specified")
        self.layout.addLayout(row)

    def _create_export_row(self, label_text, browse_callback, technique):
        container = QWidget()
        row = QHBoxLayout(container)
        label = QLabel(label_text)
        edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(browse_callback)

        row.addWidget(label)
        row.addWidget(edit)
        row.addWidget(browse)

        match technique:
            case "cv":
                self.export_cv_edit = edit
            case "eqcm":
                self.export_eqcm_edit = edit
            case _:
                raise Exception("Unknown technique specified")

        return container

    def _on_browse_cv(self):
        #path, _ = QFileDialog.getOpenFileName(self, "Select CV file", str(Path.home()), "TXT files (*.txt);;All files (*)")
        path, _ = QFileDialog.getOpenFileName(self, "Select CV file", "/home/batu/University/MEP/Data", "TXT files (*.txt);;All files (*)")
        if path:
            self.cv_path = path
            self.cv_edit.setText(path)
            self._update_load_enabled()

    def _on_browse_eqcm(self):
        #path, _ = QFileDialog.getOpenFileName(self, "Select EQCM file", str(Path.home()), "CSV files (*.csv);;All files (*)")
        path, _ = QFileDialog.getOpenFileName(self, "Select EQCM file", "/home/batu/University/MEP/Data", "CSV files (*.csv);;All files (*)")
        if path:
            self.eqcm_path = path
            self.eqcm_edit.setText(path)
            self._update_load_enabled()

    def _update_load_enabled(self):
        enabled = bool(self.cv_path and self.eqcm_path)
        self.load_button.setEnabled(enabled)

    def _on_load(self):
        self.filesSelected.emit(self.cv_path, self.eqcm_path)

    def show_export_rows(self):
        if not self._export_rows_visible:
            cv_default = self._default_export_path(self.cv_path, suffix="_clean_cv.csv")
            eqcm_default = self._default_export_path(self.eqcm_path, suffix="_clean_eqcm.csv")
            self.export_cv_edit.setText(cv_default)
            self.export_eqcm_edit.setText(eqcm_default)

            self.layout.insertWidget(self.layout.count() - 1, self._export_cv_row)
            self.layout.insertWidget(self.layout.count() - 1, self._export_eqcm_row)
            self._export_rows_visible = True

        self.export_cv_path = self.export_cv_edit.text()
        self.export_eqcm_path = self.export_eqcm_edit.text()
        self._update_save_enabled()

    def hide_export_rows(self):
        if not self._export_rows_visible:
            return

        self.layout.removeWidget(self._export_cv_row)
        self.layout.removeWidget(self._export_eqcm_row)
        self._export_cv_row.setParent(None)
        self._export_eqcm_row.setParent(None)

        if self.export_cv_edit:
            self.export_cv_edit.clear()
        if self.export_eqcm_edit:
            self.export_eqcm_edit.clear()

        self._export_rows_visible = False
        self._update_save_enabled()

    def _default_export_path(self, src_path, suffix="_clean.csv"):
        try:
            p = Path(src_path)
            return str(p.with_name(p.stem + suffix))
        except Exception:
            return ""

    def _on_browse_export_cv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export clean CV as", self.export_cv_edit.text() or str(Path.home()), "CSV files (*.csv);;All files (*)")
        if path:
            self.export_cv_path = path
            self.export_cv_edit.setText(path)
            self._emit_export_changed()
            self._update_save_enabled()

    def _on_browse_export_eqcm(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export clean EQCM as", self.export_eqcm_edit.text() or str(Path.home()), "CSV files (*.csv);;All files (*)")
        if path:
            self.export_eqcm_path = path
            self.export_eqcm_edit.setText(path)
            self._emit_export_changed()
            self._update_save_enabled()

    def _emit_export_changed(self):
        self.exportPathsChanged.emit(self.export_cv_path, self.export_eqcm_path)

    def _update_save_enabled(self):
        enabled = bool(self.export_cv_edit.text() and self.export_eqcm_edit.text())
        self.save_button.setEnabled(enabled)

    def _on_save(self):
        if self.main is not None and hasattr(self.main, "save_exported_files"):
            try:
                self.main.save_exported_files(self.export_cv_edit.text(), self.export_eqcm_edit.text())
                return
            except Exception:
                pass

        self.exportPathsChanged.emit(self.export_cv_edit.text(), self.export_eqcm_edit.text())

