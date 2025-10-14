import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
from janitor import clean_names, remove_empty
from src.experiment import ToyExperiment


class DataLoadError(Exception):
    pass


def load_files(
    cv_path: Path, eqcm_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads and cleans the CV (EC-Lab .txt) and EQCM (EQCM-Leiden script .csv)
    data files and returns them as a dict {'cv': df, 'eqcm': df}.
    """
    cv_untrimmed = _clean_cv_data(cv_path)
    eqcm_untrimmed = _clean_eqcm_data(eqcm_path)

    cv, eqcm = _trim_data(cv_untrimmed, eqcm_untrimmed)

    return (cv, eqcm)


def export_files(
    experiment: ToyExperiment, cv_save_path: Path, eqcm_save_path: Path
) -> None:
    current_cycle_cv = experiment.cv.loc[
        experiment.cv.cycle_number == experiment.cycle_number
    ]
    next_cycle_head = experiment.cv.loc[
        experiment.cv.cycle_number == experiment.cycle_number
    ].head(3)
    cv = pd.concat([current_cycle_cv, next_cycle_head])

    eqcm = experiment.eqcm.loc[
        experiment.eqcm["cycle_number"] == experiment.cycle_number
    ]

    cv.to_csv(cv_save_path, index=False)
    eqcm.to_csv(eqcm_save_path, index=False)


def _clean_cv_data(file_name: Path) -> pd.DataFrame:
    required_cols = {
        "time/s",  # absolute time
        "Ewe/V",
        "<I>/mA",
        "cycle number",
    }

    try:
        cv_df = pd.read_csv(file_name, sep="\t")
    except Exception as e:
        raise DataLoadError(f"Unable to load CV file.\n\n{e}")

    if not required_cols.issubset(cv_df.columns):
        missing_cols = required_cols.difference(cv_df.columns)
        raise DataLoadError(f"Missing columns in CV file:\n\n{missing_cols}")

    try:
        cv_df_clean: pd.DataFrame = (
            cv_df.pipe(clean_names)
            .pipe(remove_empty)
            .rename(
                columns={
                    "time_s": "timestamp_s",
                    "ewe_v": "potential_V",
                    "<i>_ma": "current_mA",
                }
            )
            .assign(timestamp_s=lambda x: pd.to_datetime(x.timestamp_s))
            .astype({"timestamp_s": "int64"})
            .assign(timestamp_s=lambda x: x.timestamp_s / 1e9)
            .astype({"cycle_number": "int"})
        )
    except Exception as e:
        raise DataLoadError(f"Unable to parse CV data.\n\n{e}")

    return cv_df_clean


def _clean_eqcm_data(file_name: Path) -> pd.DataFrame:
    required_cols = {"Timestamp", "Frequency"}

    try:
        eqcm_df = pd.read_csv(file_name, sep=",")
    except Exception as e:
        raise DataLoadError(f"Unable to load EQCM file.\n\n{e}")

    if not required_cols.issubset(eqcm_df.columns):
        missing_cols = required_cols.difference(eqcm_df.columns)
        raise DataLoadError(f"Missing columns in EQCM file:\n\n{missing_cols}")

    try:
        eqcm_df_clean: pd.DataFrame = (
            eqcm_df.pipe(clean_names)
            .drop("time_elapsed_s_", axis=1)
            .assign(timestamp=lambda x: x.timestamp + 7200)  # Timezone offset
            .assign(frequency_savgol_Hz=lambda x: x.frequency)
            .rename(
                columns={
                    "timestamp": "timestamp_s",
                    "frequency": "frequency_Hz",
                }
            )
        )
    except Exception as e:
        raise DataLoadError(f"Unable to parse EQCM data.\n\n{e}")

    return eqcm_df_clean


def _trim_data(
    cv_df: pd.DataFrame, eqcm_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    trimmed_cv_df = cv_df.loc[
        cv_df["timestamp_s"] <= eqcm_df["timestamp_s"].iloc[-1]
    ]
    trimmed_eqcm_df = eqcm_df[
        eqcm_df["timestamp_s"] >= cv_df["timestamp_s"].iloc[0]
    ]
    trimmed_eqcm_df = trimmed_eqcm_df[
        trimmed_eqcm_df["timestamp_s"] <= cv_df["timestamp_s"].iloc[-1]
    ]

    trimmed_eqcm_df.index = np.arange(len(trimmed_eqcm_df))

    if len(trimmed_cv_df) == 0 or len(trimmed_eqcm_df) == 0:
        raise DataLoadError(
            "No concurrent measurement data.\n\n"
            "Are the CV and EQCM files of the same experiment, "
            "and is the exported CV timestamp in absolute time?"
        )

    return (trimmed_cv_df, trimmed_eqcm_df)
