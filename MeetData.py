# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 14:11:23 2020

@author: Gianl
"""
import pandas as pd
import numpy as np
from Label import labelling
from Label import labelling2
from Label import etichetto_name
from InterStatistics import inter_statistic
from SeriesStats import *
from LogWebexManager import *
from LogJitsiManager import webrtc_log_parse, JitsiLogdf
from scipy.stats import kurtosis, skew, moment
import pickle
import time
import json


#OLD LABELLING PER RIMANERE COMPATIBILE CON VECCHIO SOFTWARE

def etichetto_basic(dict_flow_data, screen, quality, software):
    if (screen is None) and (quality is None) and (software == "webex"):
        dict_flow_data = labelling2(dict_flow_data, screen, quality) #etichetto audio video fec audio fec video
        for flow_id in dict_flow_data:
            dict_flow_data[flow_id]["label"] = -1
        return dict_flow_data
    elif screen is None and quality is None:
        for flow_id in dict_flow_data:
            dict_flow_data[flow_id]["label"] = -1
            dict_flow_data[flow_id]["label2"] = -1
        return dict_flow_data
    dict_flow_data = labelling (dict_flow_data, screen, quality)
    dict_flow_data = labelling2(dict_flow_data, screen, quality)
    return dict_flow_data

def moment3(series):
    return moment(series, moment=3)
def moment4(series):
    return moment(series, moment=4)

def common(dict_flow_data, time_aggregation, dict_params_stats, pcap, etichetto=None, label=None, name=None, screen=None, quality=None, software=None):
    try:
        start=time.time()
        LEN_DROP = 0
       # start = len(dict_flow_data.keys())
        dict_flow_data, LEN_DROP = inter_statistic (dict_flow_data, LEN_DROP)
        percentili = [p10, p20, p25, p30, p40, p50, p60, p70, p75, p80, p90, p95, max_min_R, kurtosis, skew,\
            moment3, moment4, len_unique_percent, max_value_count_percent, min_max_R]
        dict_flow_data_2 = {}
        if etichetto=="etichetto":
            dict_flow_data = etichetto_basic(dict_flow_data, screen, quality, software)
        elif etichetto=="etichetto_name":
            dict_flow_data = etichetto_name(dict_flow_data,label,name)
        params = {
            'interarrival' : ['std', 'mean', 'min', 'max', max_min_diff]+percentili,\
            'len_udp' : ['std', 'mean', 'count', kbps, max_min_diff]+percentili, \
            'interlength_udp' : ['std', 'mean', max_min_diff]+percentili,\
            'rtp_interarrival' : ['std', 'mean', zeroes_count, max_min_diff]+percentili ,\
            "rtp_marker" : [sum_check], \
            "rtp_seq_num" : [packet_loss], \
                                                                 } #            "inter_time_sequence": ['std', 'mean', max_min_diff]+percentili, \
        params.update(dict_params_stats)
        for flow_id in dict_flow_data.keys():
            dict_flow_data[flow_id]["timestamps"] = pd.to_datetime(dict_flow_data[flow_id]["timestamps"], unit = 's')
            dict_flow_data[flow_id].set_index('timestamps', inplace = True)
            dict_flow_data[flow_id] = dict_flow_data[flow_id].dropna() 
            dict_flow_data_2[flow_id] = dict_flow_data[flow_id].resample(f"{time_aggregation}L").agg(params)
            dict_flow_data_2[flow_id]["flow"]=str(flow_id)
            dict_flow_data_2[flow_id]["pcap"]=str(pcap)

        for flow_id in dict_flow_data_2.keys():
            dict_flow_data_2[flow_id].reset_index(inplace = True, drop = False)
            new_header = [h[0] + "_" + h[1] if h[1] else h[0] for h in dict_flow_data_2[flow_id]]
            dict_flow_data_2[flow_id].columns = new_header
        print(f"common time:{time.time()-start} pcap:{pcap}")
    except Exception as e:
        print(f"Errore in common {e}" )
    return dict_flow_data, dict_flow_data_2

def OtherDataset(dict_flow_data, pcap_path, name, label, time_aggregation):
    try:
        params={"label": [value_label],  "label2": [value_label]}
        dict_flow_data, dict_flow_data_2=common(dict_flow_data, time_aggregation, params, name,etichetto="etichetto_name", label=label, name=name)
        dataset_dropped=pd.concat([dict_flow_data_2[key] for key in dict_flow_data_2.keys()])
        dataset_dropped.dropna(inplace=True)
        dataset_dropped.reset_index(inplace = True, drop = True)
        return dataset_dropped
    except Exception as e:
        print('MeetData: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("Pcap2Json error")


def WebexDataset(dict_flow_data, pcap_path, name, screen , quality, software, file_log, time_aggregation, loss_rate=0.2):
    try:
        start=time.time()
        df_train = pd.DataFrame()
        if file_log:
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
                        print(f"d_log errore, salvo {e}")
                        import pickle
                        with open(f"d_log_errore_{name}_{key}.pickle", "wb") as f:
                            pickle.dump(d_log,f)
            #Merge dei dati del log e dict_flow_data_2
            dict_merge, flows_not_in_log = DictMerge(dict_flow_data_2, d_log, fec_dict)
            #Per rendere il codice operabile con json2stat
            df_train = WebLogdf(dict_merge, name)
            print(f"WebexDataset time:{time.time()-start} name: {name}")
            return df_train
        else:
            #Se non abbiamo il log
            dict_flow_data,dict_flow_data_2=common(dict_flow_data, time_aggregation, {}, name, etichetto="etichetto",screen=screen, quality=quality, software=software)
            print("1", dict_flow_data_2)
            dataset_dropped = pd.concat([dict_flow_data_2[key] for key in dict_flow_data_2])
            print("2", dataset_dropped)
            dataset_dropped.dropna()
            dataset_dropped.reset_index(inplace = True, drop = True)
            return dataset_dropped
    except Exception as e:
        print('MeetData - WebexDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("WebexDataset error")



def JitsiDataset(dict_flow_data, pcap_path, name, screen , quality, software, file_log, time_aggregation):

    try:
        #Notes per Gianluca: vedi se e' tutto a posto con timestamps - a volte serve come indice, a volte no
        dict_flow_data, dict_flow_data_2 = common(dict_flow_data, time_aggregation, {}, name)
        #dict_flow_data_2[flow_id] = dict_flow_data_2[flow_id].set_index("timestamps") dopo new header credo inutile
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
        df_train = JitsiLogdf(dict_merge, name)
        df_train.reset_index(drop=False, inplace=True)

        return df_train

    except Exception as e:
        print('JitsiDataset: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("JitsiDataset error")



def ZoomDataset(dict_flow_data, pcap_path, name, screen , quality, software, file_log):
    pass



