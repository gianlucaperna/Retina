import pandas as pd
import os


def merge_csv(directory, time_aggregation):
    dataset_final = pd.DataFrame()
    for r, d, f in os.walk(directory):
        for file in f:
            if f"_{time_aggregation}s.csv" in file:
                df_app = pd.read_csv(os.path.join(r, file))
                dataset_final = pd.concat([dataset_final, df_app], sort=False)

    dataset_final.reset_index(inplace=True, drop=True)
    dataset_final.to_csv(os.path.join(directory, f"dataset_{time_aggregation}ms.csv"))
    return dataset_final
