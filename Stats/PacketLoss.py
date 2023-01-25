import pandas as pd
import copy
import numpy as np
import sys

# the function used to derive all sequence numbers and potential dropped packets(in last 1/3 samples) aggregated in the target time bin
def func(df):
    if not df.empty:
        check_packets_num = int(len(df.index) / 3)
        ser = df[df.columns[0]]
        ser = ser.drop_duplicates()
        lost_packet = []
        if len(ser) != 1:
            for i in range(len(ser)-check_packets_num, len(ser)):

                # in case there are any dropped packet 
                if ser.iloc[i] > ser.iloc[i-1] and ser.iloc[i] - ser.iloc[i-1] != 1:
                    for num in range(ser.iloc[i-1]+1, ser.iloc[i]):
                        lost_packet.append(num)

                # in case the seq num reaching max and packet with seq num 0 is dropped
                elif ser.iloc[i] < ser.iloc[i-1] and ser.iloc[i] != 0:
                    for num in range(0, ser.iloc[i]):
                        lost_packet.append(num)

            return pd.Series([ser.values, lost_packet], index=['seq_list', 'end_lost_packets'])
        else:
            return pd.Series([ser.values, lost_packet], index=['seq_list', 'end_lost_packets'])
    else:
        return pd.Series([[-1], [-1]], index=['seq_list', 'end_lost_packets']) # no info is available

def calculate_packet_loss(flow_data, time_aggregation):
    try:
        df_temp = copy.deepcopy(flow_data)
        df_temp.drop_duplicates()
        df_temp = df_temp[['rtp_seq_num']]
        df_temp = df_temp.sort_index()
        df_temp = df_temp.groupby(pd.Grouper(freq=f"{time_aggregation}L")).apply(func)
        df_temp['num_packet_loss'] = 0
        df_temp=df_temp.astype(object)

        # deal with the potential miss-sent packets
        length = len(df_temp.index)
        for i in range(1, length):
            if df_temp.iloc[i, 0][0] != -1:
                seq_list = df_temp.iloc[i, 0].copy()
                end_lost = df_temp.iloc[i-1, 1].copy()
                seq_start = int(len(seq_list) / 3)
                actual_seq_list = []
                count = 1
                for elem in seq_list:

                    # only considering the first 1/3 samples
                    if count < seq_start:
                        if elem not in end_lost:
                            actual_seq_list.append(elem)
                        else:
                            df_temp.iloc[i-1, 0] = np.append(df_temp.iloc[i-1, 0], elem)
                    else:
                        actual_seq_list.append(elem)
                    count += 1

                df_temp.iloc[i, 0] = np.array(actual_seq_list)

        # derive loss num by comparing consecutive seq num and also deal with exchange
        for i in range(1, len(df_temp.index)):
            if df_temp.iloc[i, 0][0] != -1:
                seq_list = df_temp.iloc[i, 0].copy()

                # record the last seq num which may be the 'exchange' sequence number after sort
                end_seq_num = seq_list[-1]
                for idx_transition in range(0, len(seq_list)):
                    if seq_list[idx_transition] == 65535:
                        if idx_transition != len(seq_list)-1:
                            seq_list_after_transition = seq_list[idx_transition+1:].copy()
                            seq_list_after_transition.sort()
                            end_seq_num = seq_list_after_transition[-1]
                        break

                seq_list.sort()
                num_lost = 0
                for idx in range(1, len(seq_list)):
                    if seq_list[idx-1] != end_seq_num:
                        num_lost += seq_list[idx] - seq_list[idx-1] - 1
                df_temp.iloc[i, 2] = num_lost
            else:
                df_temp.iloc[i, 2] = -1

        return df_temp['num_packet_loss'].values
    except Exception as e:
        print('Calculating the Number of packet loss: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("WebexDataset error")


# the orignial simple method
# def calculate_packet_loss(dict_flow_data):

#     #Calculate packet loss
#     dict_flow_packet_loss = {}
#     for flow_id in dict_flow_data:
#         seq = dict_flow_data[flow_id]['rtp_seq_num'].sort_values()
#         seq_diff = (seq - seq.shift()).fillna(1)
#         dict_flow_packet_loss[flow_id] = (seq_diff.where(seq_diff != 1)-1).sum()

#     print("Packet losses: ", dict_flow_packet_loss)

#     return dict_flow_packet_loss
