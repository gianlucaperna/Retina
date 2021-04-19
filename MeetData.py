# -*- coding: utf-8 -*-


from Label import label_by_length
from InterStatistics import inter_statistic
from SeriesStats import *
from LogWebexManager import *
from LogWebrtcManager import webrtc_log_parse, webrtc_log_df
from scipy.stats import kurtosis, skew
import time
import json
from collections import defaultdict

from config import config_dict


def common(dict_flow_data, time_aggregation, dict_params_stats, pcap, threshold=400, etichetto=None):
    try:

        config_dict_new = defaultdict(list)
        for key, value in config_dict.items():
            for element in value:
                if element not in ['std', 'mean', 'min', 'max', "count"]:
                    config_dict_new[key].append(eval(element))
                else:
                    config_dict_new[key].append(element)

        start=time.time()
        LEN_DROP = 0

        dict_flow_data, LEN_DROP = inter_statistic (dict_flow_data, LEN_DROP)
        dict_flow_data_2 = {}

        if etichetto == "label_by_length":
            print(f"I am labelling audio and video by length of packet: {threshold}")
            dict_flow_data = label_by_length(dict_flow_data, threshold)


        for flow_id in dict_flow_data.keys():

            dict_flow_data[flow_id]["timestamps"] = pd.to_datetime(dict_flow_data[flow_id]["timestamps"], unit = 's')
            dict_flow_data[flow_id].set_index('timestamps', inplace = True)
            dict_flow_data[flow_id] = dict_flow_data[flow_id].dropna()
            dict_flow_data_2[flow_id] = dict_flow_data[flow_id].resample(f"{time_aggregation}L").agg(config_dict_new)
            dict_flow_data_2[flow_id]["flow"]=str(flow_id)
            dict_flow_data_2[flow_id]["pcap"]=str(pcap)

        for flow_id in dict_flow_data_2.keys():
            dict_flow_data_2[flow_id].reset_index(inplace = True, drop = False)
            new_header = [h[0] + "_" + h[1] if h[1] else h[0] for h in dict_flow_data_2[flow_id]]
            dict_flow_data_2[flow_id].columns = new_header
        print(f"common time:{time.time()-start} pcap:{pcap}")


    except Exception as e:
        print('MeetData - common: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("Common error")
    return dict_flow_data, dict_flow_data_2

def OtherDataset(dict_flow_data, name, time_aggregation, threshold):
    try:
        params={"label": [value_label]}
        dict_flow_data, dict_flow_data_2 = common(dict_flow_data=dict_flow_data,
                                                  time_aggregation=time_aggregation,
                                                  dict_params_stats=params,
                                                  pcap=name,
                                                  etichetto="label_by_length",
                                                  threshold=threshold)
        dataset_dropped = pd.concat([dict_flow_data_2[key] for key in dict_flow_data_2.keys()])
        dataset_dropped.dropna(inplace=True)
        dataset_dropped.reset_index(inplace=True, drop=True)
        return dataset_dropped
    except Exception as e:
        print('MeetData - OtherDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("Pcap2Json error")


def WebexDataset(dict_flow_data, name, file_log, time_aggregation, loss_rate=0.2):
    try:
        start = time.time()
        df_train = pd.DataFrame()
        dict_flow_data, dict_flow_data_2 = common(dict_flow_data, time_aggregation, {}, name)
        #Gestione del LOG
        #Make fec_dict: fec_key: list of keys of all streams with the same csi
        with open(file_log, "r", encoding="ISO-8859-1") as f:
        #vado linea per line cosi
            log = f.readlines()
        fec_dict = make_fec_dict(log, dict_flow_data)
        #Crea d_log - {key come in dict_flow_data : Dataframe con dati dal log}
        #ha i dati di dal log per ogni flusso non-FEC
        #per i flussi FEC ha empty DataFrame
        d_log = make_d_log(log, dict_flow_data, loss_rate=loss_rate)

        for key, df in d_log.items():
            if "timestamps" in df.columns:
                #d_log[key] = df.set_index("timestamps").resample(f"{time_aggregation}L").ffill().bfill()
                #d_log[key].reset_index(inplace=True)
                try:
                    d_log[key] = df.set_index("timestamps").resample(f"{time_aggregation}L").ffill().bfill()
                except Exception as e:
                    print('MeetData - WebexDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
                    raise NameError("MeetData error")

        #Merge dei dati del log e dict_flow_data_2
        dict_merge, flows_not_in_log = DictMerge(dict_flow_data_2, d_log, fec_dict)
        #Per rendere il codice operabile con json2stat
        df_train = WebLogdf(dict_merge, name)
        print(f"WebexDataset time:{time.time()-start} name: {name}")
        return df_train

    except Exception as e:
        print('MeetData - WebexDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("WebexDataset error")



def webrtcDataset(dict_flow_data, name, file_log, time_aggregation):

    try:
        dict_flow_data, dict_flow_data_2 = common(dict_flow_data, time_aggregation, {}, name)
        #Gestione del LOG
        with open(file_log, "r") as f:
            log = json.load(f)
        #Funzione che fa parsing del log
        stream_to_df = webrtc_log_parse(log)
        #Allineare i keys di dict_flow_data e d_log
        d_log = {}
        for key, value in stream_to_df.items():
            ssrc = str(hex(int(key.split("_")[-1])))
            for key1 in dict_flow_data_2.keys():
                if key1[0] == ssrc:
                    d_log[key1] = value
        #Merge dei dati del log e dict_flow_data_2 nel dict_merge
        dict_merge = {}
        for key in d_log:
            a = d_log[key]
            a_new = a.resample(f"{time_aggregation}L").ffill()
            b = dict_flow_data_2[key].set_index("timestamps")
            dict_merge[key] = a_new.join(b, how="inner")
        #this returns to json2stat, it's dataset_dropped
        df_train = webrtc_log_df(dict_merge, name)
        df_train.reset_index(drop=False, inplace=True)

        return df_train

    except Exception as e:
        print('webrtcDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("webrtcDataset error")




