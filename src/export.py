import pandas as pd
import json
import copy
import os


def main(experiment, database, database_path):
    experiment_to_database(experiment, database, database_path)
    data_to_csv(experiment)


def experiment_to_database(experiment, database, database_path):
    database[experiment.key] = experiment.to_dict()[experiment.key]

    print(f'Writing {experiment.key} into database')

    database_sorted = {k: v for k, v in sorted(database.items())}
    database_trimmed = {k: {ik: iv for ik, iv in inner.items() if ik in list(experiment.to_dict()[experiment.key].keys())}
                    for k, inner in database_sorted.items()}

    with open(database_path, 'w') as f:
        df = pd.DataFrame.from_dict(database_trimmed, orient="index")
        df.to_csv(f)


def data_to_csv(experiment_live):
    eqcm_cols = ['timestamp_moved', 
                 'potential_we_V',
                 'frequency',
                 'frequency_savgol']

    experiment = copy.deepcopy(experiment_live)

    current_cycle = experiment.cv.loc[experiment.cv['cycle_number'] == experiment.cycle_number]
    next_cycle = experiment.cv.loc[experiment.cv['cycle_number'] == experiment.cycle_number].head(3)
    combined_cycles = pd.concat([current_cycle, next_cycle])

    current_cycle_eqcm = experiment.eqcm.loc[experiment.eqcm['cycle_number'] == experiment.cycle_number]

    experiment.cv = combined_cycles.assign(technique = 'cv')
    experiment.eqcm = current_cycle_eqcm.reindex(columns = eqcm_cols).assign(technique = 'eqcm')

    combined = pd.concat([experiment.cv, experiment.eqcm], 
                         ignore_index=True, 
                         sort=False)

    directory = os.path.dirname(experiment.file_name)
    save_directory = directory.replace('Data', 'Analysis-0.1')
    save_path = os.path.join(save_directory, experiment.number + '.csv')
    os.makedirs(os.path.dirname(save_path), exist_ok = True)
    combined.to_csv(save_path, index = False)
    
