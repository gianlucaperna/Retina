# -*- coding: utf-8 -*-
"""
Created on Wed May  6 17:17:04 2020

@author: Gianl
"""
import pandas as pd
import sys
from SeriesStats import packet_loss


stats = []


def compute_stats(data, flow_id, file, out_gl, drop_packet, internal_mask, time_drop):
    OUTDIR = out_gl
    INTERNAL_MASK = internal_mask
    MIN_PKT = drop_packet
    MIN_DURAT = time_drop
    try:
        ipg = data["timestamps"].diff()
        bitrate = data["len_frame"].sum() / (data["timestamps"].max() - data["timestamps"].min()) * 8

        data["time_sec"] = data["timestamps"].astype("int")
        tempo = list(data.time_sec.unique())
        rates = (data.groupby("time_sec")["len_frame"].sum() * 8)
        packetloss = data.groupby("time_sec")["rtp_seq_num"].apply(packet_loss)
        if INTERNAL_MASK in flow_id[2]:
            direction = "S"
        elif INTERNAL_MASK in flow_id[1]:
            direction = "C"
        else:
            direction = "UNK"
        s = pd.Series({
            "pkt_nb": len(data["len_frame"]),
            "pkt_avg": data["len_frame"].mean(),
            "pkt_std": data["len_frame"].std(),
            "ipg_avg": ipg.mean(),
            "ipg_std": ipg.std(),
            "bitrate": bitrate,
            "rates_per_sec": ":".join([str(v) for v in rates.values]),
            "databyte": data["len_frame"].sum(),
            "durat": data["timestamps"].max() - data["timestamps"].min(),
            "direction": direction,
            "c_ip": flow_id[2],
            "s_ip": flow_id[1],
            "c_port": flow_id[4],
            "s_port": flow_id[3],
            "channel": f"{flow_id[0]}_{flow_id[5]}",
            "file": file,
            "timestamps": ":".join([str(v) for v in tempo]),
            "packet_loss": ":".join([str(v) for v in packetloss.values]),
        })

        if len(data["len_frame"]) >= MIN_PKT and \
                data["timestamps"].max() - data["timestamps"].min() >= MIN_DURAT:
            return s
        else:
            return None
    except Exception as e:
        print('Martino_log: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
