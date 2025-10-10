import pandas as pd
import json

def main(csvFilePath):
    return csv_to_json(csvFilePath)

def csv_to_json(csvFilePath):
    df = json.dumps(
            pd.read_csv(
                csvFilePath, 
                index_col = 0,
                dtype = {
                    "number": str,
                    "date": str,
                    "window": int,
                    "order": int,
                    "drift_degree": int
                    }
                )
            .fillna({"notes": ""})
            .transpose()
            .to_dict()
            )
    return json.loads(df)
