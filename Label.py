import pandas as pd


# ETICHETTATURA NOSTRA


def label_by_length(dict_flow_data, threshold):
    # serve per etichettare mettendo il nome del software
    to_drop = []
    for flow_id in dict_flow_data.keys():
        if dict_flow_data[flow_id]["len_udp"].mean() < threshold:
            if max(dict_flow_data[flow_id]["len_udp"]) < threshold:
                dict_flow_data[flow_id]["label"] = 0
            else:
                # print(f"Controllo flusso {flow_id}, sospetto ScreenSharing, name: {name}, max: {max(dict_flow_data[flow_id]['len_udp'])}, int: {max(dict_flow_data[flow_id]['rtp_interarrival'])}")
                value_counts = dict_flow_data[flow_id]['rtp_interarrival'].value_counts()
                if value_counts.index[0] % 192 == 0:  # 192 è 5ms, 960 è 20ms
                    # print(f"Il flusso {flow_id}, è audio, controllato inter-RTP")
                    dict_flow_data[flow_id]["label"] = 0
                to_drop.append(flow_id)
        else:
            dict_flow_data[flow_id]["label"] = 1
        # dict_flow_data[flow_id]["label2"] = label
    for k in to_drop:
        dict_flow_data.pop(k, None)
    return dict_flow_data
