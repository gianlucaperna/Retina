
#Labelling by length of packet


def label_by_length(dict_flow_data, threshold):
    to_drop = []
    for flow_id in dict_flow_data.keys():
        if dict_flow_data[flow_id]["len_udp"].mean() < threshold:
            if max(dict_flow_data[flow_id]["len_udp"]) < threshold:
                dict_flow_data[flow_id]["label"] = 0
            else:
                value_counts = dict_flow_data[flow_id]['rtp_interarrival'].value_counts()
                if value_counts.index[0] % 192 == 0:  # 192 is 5ms, 960 is 20ms
                    dict_flow_data[flow_id]["label"] = 0
                to_drop.append(flow_id)
        else:
            dict_flow_data[flow_id]["label"] = 1
    for k in to_drop:
        dict_flow_data.pop(k, None)
    return dict_flow_data
