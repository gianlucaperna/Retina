import os
import sys
from MeetData import WebexDataset, webrtcDataset, OtherDataset
import glob
from functools import reduce


def find_log(extension, name, file_log):
    # file log potrebbe essere una directory padre in cui cercare

    if file_log:
        file_log = glob.glob(os.path.join(file_log, "**", f"{name}.{extension}"), recursive=True)  # lista che contiene in teoria solo la dir+name.log
        print("FILE_LOG: ", file_log)
        if len(file_log) > 1:
            print(f'Found {len(file_log)} files log with the same name, they will be ignored.')
        else:
            file_log = file_log[0]
        return file_log
    else:
        return None


def tshark_to_stat(dict_flow_data,
                   pcap_path,
                   name,
                   time_aggregation,
                   threshold,
                   software=None,
                   file_log=None,
                   loss_rate=0.2):
    try:

        if software == "webex":
            file_log = find_log("log", name, file_log)
        elif software == "webrtc":
            file_log = find_log("txt", name, file_log)
        else:
            file_log = None

        # Webex with log
        if (software == "webex") and file_log:
            dataset_dropped = WebexDataset(dict_flow_data, name, file_log, time_aggregation,
                                           loss_rate=loss_rate)
            if "quality" in dataset_dropped.columns:
                dataset_dropped["quality"].fillna("other", inplace=True)

        # webrtc with log
        elif (software == "webrtc") and file_log:
            dataset_dropped = webrtcDataset(dict_flow_data, name, file_log, time_aggregation)
            if "quality" in dataset_dropped.columns:
                dataset_dropped["quality"].fillna("other", inplace=True)

        elif (software == "other") or (file_log is None):
            dataset_dropped = OtherDataset(dict_flow_data, name, time_aggregation, threshold)

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
                                                          'index': 'timestamp',
                                                          }, errors="ignore")

        if "flow" in dataset_dropped.columns:
            dataset_dropped["flow"] = dataset_dropped["flow"].apply(eval)
            if len(dataset_dropped["flow"].iloc[0]) == 6:
                dataset_dropped["ssrc"], dataset_dropped["ip_src"], dataset_dropped["ip_dst"], dataset_dropped["prt_src"], dataset_dropped["prt_dst"], dataset_dropped["p_type"] = \
                    zip(*dataset_dropped["flow"])
            elif len(dataset_dropped["flow"].iloc[0]) == 5:
                dataset_dropped["ssrc"], dataset_dropped["ip_src"], dataset_dropped["ip_dst"], dataset_dropped["prt_src"], dataset_dropped["prt_dst"] = \
                    zip(*dataset_dropped["flow"])
            else:
                pass

        pcap_path = os.path.join(pcap_path, name)
        with open(pcap_path + f"_{time_aggregation}s.csv", "w") as file:
            dataset_dropped.to_csv(file, index=False)
        return dataset_dropped

    except Exception as e:
        print('tshark2stat: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
