import pandas as pd
from typing import Tuple


class Experiment:

    def __init__(self, data_tuple: Tuple[pd.DataFrame, pd.DataFrame]):
        self.cv = data_tuple[0]
        self.eqcm = data_tuple[1]

        self.key = ""

        self.time_diff = 0.0
        self.cycle_number = 2
        self.savgol_window = 30
        self.savgol_order = 0
        self.drift_order = 1
        self.notes = ""

    # WIP database
    # def to_dict(self):
    #     return {self.key: { 
    #                        "time_diff": self.time_diff,
    #                        "cycle_number": self.cycle_number,
    #                        "savgol_window": self.savgol_window,
    #                        "savgol_order": self.savgol_order,
    #                        "drift_order": self.drift_order,
    #                        "notes": self.notes
    #                        }
    #             }
    #
    # def from_dict(self, entry):
    #     self.time_diff = entry['time_diff']
    #     self.cycle_number = entry['cycle_number']
    #     self.savgol_window = int(entry['savgol_window'])
    #     self.savgol_order = int(entry['savgol_order'])
    #     self.drift_order = int(entry['drift_order'])
    #     self.notes = entry['notes']
