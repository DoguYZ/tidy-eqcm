from pathlib import Path
import pandas as pd
import numpy as np
from janitor import clean_names, remove_empty


def main(file_path):
    p = Path(file_path)
    base_name = str(p.parent / p.stem)

    file_dict = {
            'file_name': base_name,
            'cv_file_name': base_name + '_04_CV_C01.txt', 
            'eqcm_file_name': file_path
            }

    file_dict['cv_data'] = clean_cv_data(file_dict['cv_file_name'])
    file_dict['eqcm_data'] = clean_eqcm_data(file_dict['eqcm_file_name'])
    file_dict['trimmed_cv_data'], file_dict['trimmed_eqcm_data'] = \
            trim_data(file_dict['cv_data'], file_dict['eqcm_data'])

    return file_dict

def clean_cv_data(file_name):
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


def clean_eqcm_data(file_name):
    eqcm_df = (
        pd.read_csv(file_name)
        .pipe(clean_names)
        .drop('time_elapsed_s_', axis = 1)
        .assign(timestamp = lambda x: x.timestamp + 7200) # Timezone offset
    )
    return eqcm_df


def trim_data(cv_df, eqcm_df):
    trimmed_cv_df = cv_df.loc[cv_df["timestamp"] \
            <= eqcm_df["timestamp"].iloc[-1]]
    trimmed_eqcm_df = eqcm_df[eqcm_df["timestamp"] \
            >= cv_df["timestamp"].iloc[0]]
    trimmed_eqcm_df = trimmed_eqcm_df[trimmed_eqcm_df["timestamp"] \
            <= cv_df["timestamp"].iloc[-1]]

    trimmed_eqcm_df.index = np.arange(len(trimmed_eqcm_df))

    return trimmed_cv_df, trimmed_eqcm_df



