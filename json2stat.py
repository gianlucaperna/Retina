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

def json2stat (dict_flow_data, pcap_path, name, time_aggregation, screen = None, quality = None, software = None, file_log = None, label=None, loss_rate=0.2):
    try:
        if (software == "webex"):
            file_log=find_log("log", name, file_log)
            dataset_dropped = WebexDataset(dict_flow_data, pcap_path, name, screen , quality, software, file_log, time_aggregation, loss_rate=loss_rate)
            if "quality" in dataset_dropped.columns:
                dataset_dropped["quality"].fillna("other", inplace=True)
            else:
                dataset_dropped["quality"] = "other"
        elif (software == "jitsi"):
            file_log=find_log("txt", name, file_log)
            dataset_dropped = JitsiDataset(dict_flow_data, pcap_path, name, screen, quality, software, file_log, time_aggregation)
        elif (software == "zoom"):
            dataset_dropped = ZoomDataset(dict_flow_data, pcap_path, name, screen, quality, software, file_log, time_aggregation)
        elif (software == "other"):
            dataset_dropped = OtherDataset(dict_flow_data, pcap_path, name, label, time_aggregation)
            if dataset_dropped is None:
                print((f"Dataset Nan {name}"))
                return None
        else:
            pass
        if software:
            dataset_dropped = dataset_dropped.dropna()
            dataset_dropped = dataset_dropped.rename(columns={'label2_value_label': 'label2', \
                                    'label_value_label': 'label', \
                                    'len_udp_kbps': 'kbps', \
                                    'len_udp_count': 'num_packets', \
                                    'rtp_interarrival_std': 'rtp_inter_timestamp_std', \
                                    'rtp_interarrival_mean': 'rtp_inter_timestamp_mean', \
                                    'rtp_interarrival_zeroes_count': 'rtp_inter_timestamp_num_zeros', \
                                    'flow_': 'flow', \
                                    'pcap_': 'pcap', \
                                    'timestamps_': 'timestamps'}, errors="ignore")
            pcap_path = os.path.join(pcap_path, name)
            with open(pcap_path + f"_{time_aggregation}s.csv", "w") as file:
                dataset_dropped.to_csv( file, index = False)
            return dataset_dropped
    except Exception as e:
        print('Json2Stat: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
