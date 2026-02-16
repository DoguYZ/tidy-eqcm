from enum import Enum
from typing import Optional
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)


class Technique(Enum):
    CV = "cv"
    EQCM = "eqcm"


class IOType(Enum):
    INPUT = "input"
    OUTPUT = "output"


class Overwrite(Enum):
    TRUE = int("0x00000800", 16) # save
    FALSE = int("0x00400000", 16) # cancel


class InfoWindow(QWidget):
    """
    Window used to select CV and EQCM data files, and select the paths to write
    the cleaned data into.
    :signal loadFiles: signal when the load button is pressed
    :signal exportFiles: signal when save button is pressed
    """

    loadFiles = pyqtSignal(Path, Path)
    exportFiles = pyqtSignal(Path, Path)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        main: Optional[QMainWindow] = None,
    ) -> None:
        super().__init__(parent)
        self.main = main

        self._vert_layout = QVBoxLayout()
        self.setLayout(self._vert_layout)

        self.cv_path = Path()
        self.eqcm_path = Path()
        self.export_cv_path = Path()
        self.export_eqcm_path = Path()

        self._cv_edit = QLineEdit()
        self._eqcm_edit = QLineEdit()
        self._export_cv_edit = QLineEdit()
        self._export_eqcm_edit = QLineEdit()

        self._cv_edit.textChanged.connect(self._update_load_enabled)
        self._eqcm_edit.textChanged.connect(self._update_load_enabled)
        self._export_cv_edit.textChanged.connect(self._update_save_enabled)
        self._export_eqcm_edit.textChanged.connect(self._update_save_enabled)

        self._add_file_row("CV file:", Technique.CV, IOType.INPUT)
        self._add_file_row("EQCM file:", Technique.EQCM, IOType.INPUT)
        self._add_file_row("CV save file:", Technique.CV, IOType.OUTPUT)
        self._add_file_row("EQCM save file:", Technique.EQCM, IOType.OUTPUT)

        self._load_button = QPushButton("Load files")
        self._load_button.setEnabled(False)
        self._load_button.clicked.connect(self._on_load)
        self._vert_layout.addWidget(self._load_button)

        self._save_button = QPushButton("Save exported files")
        self._save_button.setEnabled(False)
        self._save_button.clicked.connect(self._on_save)
        self._vert_layout.addWidget(self._save_button)

        self._store_cv_file_name = Path()
        self._store_eqcm_file_name = Path()

    def _add_file_row(
        self,
        label_text: str,
        technique: Technique,
        io_type: IOType,
    ) -> None:
        row = QHBoxLayout()

        label = QLabel(label_text)
        browse = QPushButton("Browse…")

        if io_type == IOType.INPUT:
            if technique == Technique.CV:
                edit = self._cv_edit
            elif technique == Technique.EQCM:
                edit = self._eqcm_edit
            edit.setReadOnly(True)
        elif io_type == IOType.OUTPUT:
            if technique == Technique.CV:
                edit = self._export_cv_edit
            elif technique == Technique.EQCM:
                edit = self._export_eqcm_edit

        row.addWidget(label)
        row.addWidget(edit)
        row.addWidget(browse)

        browse.clicked.connect(
            lambda *_,
            edit=edit,
            technique=technique,
            io_type=io_type,
            func=self._on_browse: func(edit, technique, io_type)
        )

        self._vert_layout.addLayout(row)

    def _on_browse(
        self,
        edit: QLineEdit,
        technique: Technique,
        io_type: IOType,
    ) -> None:
        if io_type == IOType.INPUT:
            if technique == Technique.CV:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select file",
                    #"/var/home/dogukan/MEP/Data/",
                    "",
                    "TXT files (*.txt)",
                )
                self.cv_path = Path(path)
                ### wip
                # self._store_cv_file_name = self._default_export_path(
                #     self.cv_path
                # )
            elif technique == Technique.EQCM:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select file",
                    "",
                    "CSV files (*.csv)",
                )
                self.eqcm_path = Path(path)
                ### wip
                # self._store_eqcm_file_name = self._default_export_path(
                #     self.eqcm_path
                # )

        elif io_type == IOType.OUTPUT:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select directory",
                "",
                QFileDialog.Option.ShowDirsOnly,
            )

            if technique == Technique.CV:
                path = str(Path(path) / "clean_cv.csv")
            elif technique == Technique.EQCM:
                path = str(Path(path) / "clean_eqcm.csv")

        edit.setText(path)

    def _update_load_enabled(self) -> None:
        enabled = bool(self._cv_edit.text() and self._eqcm_edit.text())
        self._load_button.setEnabled(enabled)
        self._update_save_enabled()

    # FIXME: only if files have been loaded
    def _update_save_enabled(self) -> None:
        enabled = bool(
            self._export_cv_edit.text()
            and self._export_eqcm_edit.text()
            and self._load_button.isEnabled()
        )
        self._save_button.setEnabled(enabled)

    def _on_load(self) -> None:
        if self.cv_path.exists() and self.eqcm_path.exists():
            self.loadFiles.emit(self.cv_path, self.eqcm_path)
        elif not self.cv_path.exists():
            QMessageBox.warning(self, "tidy-eqcm", "CV file not found")
        elif not self.eqcm_path.exists():
            QMessageBox.warning(self, "tidy-eqcm", "EQCM file not found")
        else:
            QMessageBox.warning(self, "tidy-eqcm", "Files not found")

    def _on_save(self) -> None:
        self.export_cv_path = Path(self._export_cv_edit.text())
        self.export_eqcm_path = Path(self._export_eqcm_edit.text())
        if self.export_cv_path.is_dir() or self.export_eqcm_path.is_dir():
            QMessageBox.warning(
                self,
                "tidy-eqcm",
                "Please enter a file name after the directory",
            )
            return
        # make sure its a csv file
        if (
            self.export_cv_path.exists()
            and self._ask_overwrite("CV") == Overwrite.FALSE
        ):
            return
        if (
            self.export_eqcm_path.exists()
            and self._ask_overwrite("EQCM") == Overwrite.FALSE
        ):
            return

        self.exportFiles.emit(self.export_cv_path, self.export_eqcm_path)

    def _ask_overwrite(self, technique: str) -> Overwrite:
        msgBox = QMessageBox()
        msgBox.setText(f"{technique} file exists. Overwrite?")
        msgBox.setStandardButtons(
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel
        )
        msgBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
        ret = msgBox.exec()

        return Overwrite(ret)

    ### wip
    # def _default_export_path(
    #     self, data_path: Path, suffix: str = "_clean.csv"
    # ) -> Path:
    #     return data_path.with_name(data_path.stem + suffix)
