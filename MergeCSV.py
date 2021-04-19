import pandas as pd
import os

def merge_csv (directory, time_aggregation):

    dataset_final = pd.DataFrame()
    for r, d, f in os.walk(directory):
        for file in f:
            if f"_{time_aggregation}s.csv" in file:
                df_app = pd.read_csv(os.path.join(r, file))
                dataset_final = pd.concat([dataset_final, df_app], sort = False)

    dataset_final.reset_index(inplace = True, drop = True)
    dataset_final.to_csv( os.path.join(directory, f"dataset_{time_aggregation}s.csv") )
    return dataset_final


def merge_csv_split(directory, split_directory, time_aggregation):

    print("DIRECTORY", directory)
    pcap_original_name = os.path.basename(split_directory).split("_split")[0]
    print("original name", pcap_original_name)
    dataset_final = pd.DataFrame()
    for r, d, f in os.walk(split_directory):
        for file in f:
            if f"_{time_aggregation}s.csv" in file:
                df_app = pd.read_csv(os.path.join(r, file))
                dataset_final = pd.concat([dataset_final, df_app], sort = False)

    dataset_final.reset_index(inplace = True, drop = True)
    dataset_final["pcap"] = pcap_original_name
    dataset_final.to_csv(os.path.join(directory, f"{pcap_original_name}_{time_aggregation}s.csv"))
    return dataset_final
