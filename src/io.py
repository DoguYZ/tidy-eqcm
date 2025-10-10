from pathlib import Path
from typing import Dict
import pandas as pd
import numpy as np
from janitor import clean_names, remove_empty


class DataLoadError(Exception):
    """Raised when input files can't be parsed or schema invalid."""

def load_files(cv_path: str, eqcm_path: str) -> Dict[str, pd.DataFrame]:
    """
    Load a CV and an EQCM CSV and return them as a dict {'cv': df, 'eqcm': df}.
    Performs minimal validation and normalizes column names.
    """
    cv_p = Path(cv_path)
    eqcm_p = Path(eqcm_path)

    if not cv_p.exists():
        raise FileNotFoundError(f"CV file not found: {cv_path}")
    if not eqcm_p.exists():
        raise FileNotFoundError(f"EQCM file not found: {eqcm_path}")

    try:
        cv = _clean_cv_data(cv_p)
    except Exception as e:
        raise DataLoadError(f"CV couldn't load, did you export the right columns?\n\n{e}")
    try:
        eqcm = _clean_eqcm_data(eqcm_p)
    except Exception as e:
        raise DataLoadError(f"EQCM couldn't load, did you load the right file?\n\n{e}")

    cv, eqcm = _trim_data(cv, eqcm)

    # FIXME Handle missing columns

    # if not required_cv.issubset(set(cv.columns)):
    #     missing = required_cv - set(cv.columns)
    #     raise DataLoadError(f"CV missing columns: {missing}")
    # if not required_eqcm.issubset(set(eqcm.columns)):
    #     missing = required_eqcm - set(eqcm.columns)
    #     raise DataLoadError(f"EQCM missing columns: {missing}")

    return {"cv": cv, "eqcm": eqcm}

def _clean_cv_data(file_name):
    """
    Cleans EC-Lab's cv .mpr data, exported to .txt. Make sure you have
    the !absolute! time_s, ewe_v, <i>_ma and cycle_number included.
    """
    cols = ['timestamp', 
            'potential_we_V',
            'current_mA',
            'cycle_number']
    cv_df = (
        pd.read_csv(file_name, sep = '\t')
        .pipe(clean_names)
        .pipe(remove_empty)
        .rename(columns={'time_s': 'timestamp', 'ewe_v': 'potential_we_V', \
                '<i>_ma': 'current_mA'})
        .assign(timestamp = lambda x: pd.to_datetime(x.timestamp))
        .astype({'timestamp': 'int64'})
        .assign(timestamp = lambda x: x.timestamp / 1e9)
        .astype({'cycle_number': 'int'})
        .reindex(columns = cols)
    )
    return cv_df


def _clean_eqcm_data(file_name):
    """
    Cleans the eqcm-leiden-v7 script EQCM data.
    """
    eqcm_df = (
        pd.read_csv(file_name)
        .pipe(clean_names)
        .drop('time_elapsed_s_', axis = 1)
        .assign(timestamp = lambda x: x.timestamp + 7200) # Timezone offset
    )
    return eqcm_df


def _trim_data(cv_df, eqcm_df):
    """
    Trims the data to when both the CV and EQCM are active.
    """
    trimmed_cv_df = cv_df.loc[cv_df["timestamp"] \
            <= eqcm_df["timestamp"].iloc[-1]]
    trimmed_eqcm_df = eqcm_df[eqcm_df["timestamp"] \
            >= cv_df["timestamp"].iloc[0]]
    trimmed_eqcm_df = trimmed_eqcm_df[trimmed_eqcm_df["timestamp"] \
            <= cv_df["timestamp"].iloc[-1]]

    trimmed_eqcm_df.index = np.arange(len(trimmed_eqcm_df))

    return trimmed_cv_df, trimmed_eqcm_df

