import pandas as pd
import numpy as np
import json
import datetime
import os
import traceback
import sys
from MeetData import WebexDataset, JitsiDataset, ZoomDataset, OtherDataset
import glob
from functools import reduce

def find_log(extension, name, file_log):
   #file log potrebbe essere una directory padre in cui cercare
    if file_log:
        file_log = glob.glob(reduce(os.path.join, [file_log, "**", f"{name}.{extension}"]), recursive=True) #lista che contiene in teoria solo la dir+name.log
        if len(file_log) > 1:
            print(f"Trovati {len(file_log)} files log con lo stesso nome, i files saranno ignorati.")
        else:
            file_log = file_log[0]  
        return file_log
    else: return None


def tshark_to_stat(dict_flow_data,
              pcap_path,
              name,
              time_aggregation,
              software = None,
              file_log = None,
              loss_rate=0.2):
    try:

        if software == "webex":
            file_log = find_log("log", name, file_log)
        elif software == "jitsi":
            file_log = find_log("txt", name, file_log)
        else:
            file_log = None

        #Webex with log
        if (software == "webex") and file_log:
            dataset_dropped = WebexDataset(dict_flow_data, pcap_path, name, software, file_log, time_aggregation,
                                           loss_rate=loss_rate)
            if "quality" in dataset_dropped.columns:
                dataset_dropped["quality"].fillna("other", inplace=True)

        #Jitsi with log
        elif (software == "jitsi") and file_log:
            dataset_dropped = JitsiDataset(dict_flow_data, pcap_path, name, software, file_log, time_aggregation)
            if "quality" in dataset_dropped.columns:
                dataset_dropped["quality"].fillna("other", inplace=True)

        elif (software == "other"):
            dataset_dropped = OtherDataset(dict_flow_data, pcap_path, name, software, time_aggregation)

        else:
            dataset_dropped = None
            print("Software invalid")

        if dataset_dropped is None:
            print((f"Dataset Nan {name}"))
            return None

        dataset_dropped["software"] = software

        dataset_dropped = dataset_dropped.dropna()
        dataset_dropped = dataset_dropped.rename(columns={'label2_value_label': 'label2',
                                'label_value_label': 'label',
                                'len_udp_kbps': 'kbps',
                                'len_udp_count': 'num_packets',
                                'rtp_interarrival_std': 'rtp_inter_timestamp_std',
                                'rtp_interarrival_mean': 'rtp_inter_timestamp_mean',
                                'rtp_interarrival_zeroes_count': 'rtp_inter_timestamp_num_zeros',
                                'flow_': 'flow',
                                'pcap_': 'pcap',
                                'timestamps_': 'timestamp',
                                'timestamps': 'timestamp',
                                }, errors="ignore")
        pcap_path = os.path.join(pcap_path, name)
        with open(pcap_path + f"_{time_aggregation}s.csv", "w") as file:
            dataset_dropped.to_csv( file, index = False)
        return dataset_dropped

    except Exception as e:
        print('Json2Stat: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
