import pandas as pd


def calculate_packet_loss(dict_flow_data):

    #Calculate packet loss
    dict_flow_packet_loss = {}
    for flow_id in dict_flow_data:
        seq = dict_flow_data[flow_id]['rtp_seq_num'].sort_values()
        seq_diff = (seq - seq.shift()).fillna(1)
        dict_flow_packet_loss[flow_id] = (seq_diff.where(seq_diff != 1)-1).sum()

    print("Packet losses: ", dict_flow_packet_loss)

    return dict_flow_packet_loss
