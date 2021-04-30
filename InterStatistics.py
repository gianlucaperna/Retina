import pandas as pd
import numpy as np


def inter_statistic(dict_flow_data, LEN_DROP):
    try:
        for flow_id in dict_flow_data:
            dict_flow_data[flow_id]["interarrival"] = dict_flow_data[flow_id]["timestamps"].diff()
            dict_flow_data[flow_id]["rtp_interarrival"] = dict_flow_data[flow_id]["rtp_timestamp"].diff()
            dict_flow_data[flow_id]["interlength_udp"] = dict_flow_data[flow_id]["len_udp"].diff()
            dict_flow_data[flow_id]["inter_time_sequence"] = (dict_flow_data[flow_id]["rtp_timestamp"] % pow(2, 16)) - \
                                                             dict_flow_data[flow_id]["rtp_seq_num"]
            indexNames = dict_flow_data[flow_id][dict_flow_data[flow_id]['interarrival'] > 1].index
            # Delete these row indexes from dataFrame
            LEN_DROP = LEN_DROP + len(indexNames)
            dict_flow_data[flow_id].drop(indexNames,
                                         inplace=True)  # drop tutti i pacchetti che hanno interarrivo maggiore di un secondo
            # così anche se un flusso riprende dopo tanto tempo non falsiamo le statistiche

            dict_flow_data[flow_id].dropna(inplace=True)

        return dict_flow_data, LEN_DROP
    except Exception as e:
        raise e
