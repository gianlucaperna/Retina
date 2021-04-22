# -*- coding: utf-8 -*-

import re
import pandas as pd
from datetime import datetime as dt
from dateutil import parser
import sys

from collections import defaultdict
import numpy as np
import json


# Function to make stream_to_df
def webrtc_log_parse(log):
    try:

        RTP_streams = defaultdict(dict)
        RTP_streams_short = defaultdict(dict)
        RTP_streams_original = defaultdict(dict)
        RTP_codecs = defaultdict(lambda: defaultdict(dict))
        RTP_tracks = defaultdict(dict)
        track_to_pc = {}
        stream_to_pc = {}
        l_stats_streams = []
        l_stats_tracks = []

        def linspace(start, end, num):
            s = parser.parse(start).timestamp()
            e = parser.parse(end).timestamp()
            return np.linspace(s, e, num)

        for pc in log["PeerConnections"]:
            for stat in log["PeerConnections"][pc]["stats"]:

                obj = "-".join(stat.split("-")[:-1])
                stat_name = stat.split("-")[-1]

                if obj.startswith("RTCInboundRTPVideoStream_") or obj.startswith("RTCOutboundRTPVideoStream_") or \
                        obj.startswith("RTCInboundRTPAudioStream_") or obj.startswith("RTCOutboundRTPAudioStream_"):
                    l_stats_streams.append(stat_name)
                    if stat_name in {"codecId", "[codec]"}:
                        values = json.loads(log["PeerConnections"][pc]["stats"][stat]["values"])
                        RTP_streams_short[obj][stat_name] = values[0]
                    if stat_name in {"ssrc", "trackId", \
                                     "frameWidth", "frameHeight", \
                                     "kind", "jitterBufferDelay", \
                                     "framesReceived", "framesSent", "jitter", "packetsLost" \
                                                                               "fecPacketsReceived",
                                     "fecPacketsDiscarded", \
                                     "packetsReceived", "packetsSent", \
                                     "totalSamplesReceived"}:
                        values = json.loads(log["PeerConnections"][pc]["stats"][stat]["values"])
                        index = linspace(log["PeerConnections"][pc]["stats"][stat]["startTime"],
                                         log["PeerConnections"][pc]["stats"][stat]["endTime"],
                                         len(values))
                        index = pd.to_datetime(index, unit="s")
                        #                    index = index.map(lambda x: x.replace(second=0))

                        series = pd.Series(values, index=index)
                        series = series.rename(stat_name)
                        a = len(series)
                        RTP_streams_original[obj][stat_name] = series

                        b = len(series)
                        if a - b != 0:
                            print(obj, stat_name, a - b)
                        #                    print(a, b)
                        RTP_streams[obj][stat_name] = series
                    stream_to_pc[obj] = pc

                if obj.startswith("RTCCodec_video_Inbound_") or obj.startswith("RTCCodec_audio_Inbound_") or \
                        obj.startswith("RTCCodec_video_Outbound_") or obj.startswith("RTCCodec_audio_Outbound_"):
                    if stat_name in {"payloadType", "mimeType", "clockRate"}:
                        values = json.loads(log["PeerConnections"][pc]["stats"][stat]["values"])
                        RTP_codecs[pc][obj][stat_name] = values[0]
                #                    print(values)

                if obj.startswith("RTCMediaStreamTrack_receiver_") or obj.startswith("RTCMediaStreamTrack_sender_"):
                    if stat_name in {"jitterBufferDelay", \
                                     "totalSamplesReceived", \
                                     "concealmentEvents", \
                                     "frameWidth", \
                                     "frameHeight", \
                                     }:
                        l_stats_tracks.append(stat_name)
                        values = json.loads(log["PeerConnections"][pc]["stats"][stat]["values"])
                        index = linspace(log["PeerConnections"][pc]["stats"][stat]["startTime"],
                                         log["PeerConnections"][pc]["stats"][stat]["endTime"],
                                         len(values))

                        series = pd.Series(values, index=pd.to_datetime(index, unit="s"))
                        series = series.rename(stat_name)

                        RTP_tracks[obj][stat_name] = series
                    track_to_pc[obj] = pc

        stream_to_track = {}
        stream_to_ssrc = {}
        for stream in RTP_streams:
            stream_to_track[stream] = RTP_streams[stream]["trackId"].iloc[0]
            ssrc_int = int(stream.split("_")[1])
            stream_to_ssrc[stream] = hex(ssrc_int)

        # Enrich RTP streams with data from RTP codec, RTP tracks
        for key, value in RTP_streams.items():

            if "ssrc" in value.keys():
                value["ssrc_hex"] = pd.Series(data=stream_to_ssrc[key], index=RTP_streams[key]["ssrc"].index).rename(
                    "ssrc_hex")
            if "framesReceived" in value.keys():
                value["fps"] = value["framesReceived"].diff().fillna(-1).rename("fps")
            elif "framesSent" in value.keys():
                value["fps"] = value["framesSent"].diff().fillna(-1).rename("fps")
            if "packetsSent" in value.keys():
                value["pps"] = value["packetsSent"].diff().fillna(-1).rename("pps")
            elif "packetsReceived" in value.keys():
                value["pps"] = value["packetsReceived"].diff().fillna(-1).rename("pps")
            if "codecId" in RTP_streams_short[key].keys():
                # value["codecId"] = pd.Series(data= RTP_streams_short[key]["codecId"], index=RTP_streams[key]["ssrc"].index).rename("codecId")
                value["codec"] = pd.Series(data=RTP_streams_short[key]["[codec]"],
                                           index=RTP_streams[key]["ssrc"].index).rename("codec")
                pc = stream_to_pc[key]
                codecId = RTP_streams_short[key]["codecId"]
                value["payloadType"] = pd.Series(data=RTP_codecs[pc][codecId]["payloadType"],
                                                 index=RTP_streams[key]["ssrc"].index).rename("payloadType")
                value["mimeType"] = pd.Series(data=RTP_codecs[pc][codecId]["mimeType"],
                                              index=RTP_streams[key]["ssrc"].index).rename("mimeType")
                value["clockRate"] = pd.Series(data=RTP_codecs[pc][codecId]["clockRate"],
                                               index=RTP_streams[key]["ssrc"].index).rename("clockRate")

            if stream_to_track[key]:
                track = stream_to_track[key]
                if "concealmentEvents" in RTP_tracks[track].keys():
                    value["concealmentEvents"] = RTP_tracks[track]["concealmentEvents"]
                    value["concealment_diff"] = RTP_tracks[track]["concealmentEvents"].diff().fillna(-1).rename(
                        "concealment_diff")
                if "jitterBufferDelay" in RTP_tracks[track].keys() and "jitterBufferDelay" not in value.keys():
                    value["jitterBufferDelay"] = RTP_tracks[track]["jitterBufferDelay"]
                if "totalSamplesReceived" in RTP_tracks[track].keys() and "totalSamplesReceived" not in value.keys():
                    value["totalSamplesReceived"] = RTP_tracks[track]["totalSamplesReceived"]
                if "frameWidth" in RTP_tracks[track].keys():
                    value["frameWidth2"] = RTP_tracks[track]["frameWidth"].rename("frameWidth2")
                if "frameHeight" in RTP_tracks[track].keys():
                    value["frameHeight2"] = RTP_tracks[track]["frameHeight"].rename("frameHeight2")

            if "jitterBufferDelay" in value.keys():
                value["jitter2"] = value["jitterBufferDelay"].diff().fillna(0).rename("jitter2")

            # Aggregate per second for all series of that stream
            for inner_key, series in value.items():
                if series.dtype in ["int", "float"]:
                    value[inner_key] = series.resample("S").mean()
                else:
                    value[inner_key] = series.resample("S").first()

        # Concatenate series into dataframes
        stream_to_df = {}

        for obj in RTP_streams:
            df = pd.concat(list(RTP_streams[obj].values()), axis=1)

            #        df = df.fillna(-1)
            df["direction"] = "receiver" if "Inbound" in obj else "sender"
            df = df.dropna(subset=['ssrc'])

            if ("video" in df["kind"].unique()) and ("frameWidth" not in df.columns):
                #                 print("Removing flow, no resolution info: ", obj)
                continue

            if "frameWidth" in df.columns:
                offset = df["frameWidth"].isna().sum() / len(df)
                #                 print(obj, offset)
                if offset < 0.99:
                    df["frameWidth"] = df["frameWidth"].fillna(method="ffill").fillna(method="bfill")
                    df["frameHeight"] = df["frameHeight"].fillna(method="ffill").fillna(method="bfill")
            #                 else:
            #                     print("Noticed a high percentage of missing values for resolution for flow: ", df["ssrc_hex"].iloc[0])

            df = df.fillna(-1)
            # Filter flows that do not send packets
            df = df[~df["pps"].isin([0, -1])]
            if len(df) <= 10:
                #                 print("Removing flow, less than 10 samples: ", obj)
                continue

            # Set label
            df["label"] = df["kind"]
            if "frameHeight" in df.columns:
                resolutions = df["frameHeight"].unique()
                for res in resolutions:
                    fps_series = df.loc[(df["frameHeight"] == res) & \
                                        (df["fps"] != 0) \
                                        ]["fps"]
                    #                     if (fps_series.mean() <= 6) and (fps_series.max() <= 10):
                    if res > 721:
                        fps_mean = fps_series.mean()
                        if fps_mean >= 6:
                            print("FPS mean nonzero higher than 6, ", fps_mean, " flow: ", df["ssrc_hex"].iloc[0])
                        df.loc[(df["frameHeight"] == res), "label"] = "screenshare"

            stream_to_df[obj] = df

        return stream_to_df

    except Exception as e:
        print('webrtc_log_parse: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("webrtc_log_parse error")


# %%


def webrtc_log_df(dict_merge, pcap_name):
    try:
        dict_label = {
            "audio": 0,
            "video": 1,
            "screenshare": 1,
        }

        df_train = pd.DataFrame()
        columns_drop = ['ssrc_hex', 'frameWidth2', 'frameHeight2', 'jitterBufferDelay',
                        'direction', 'ssrc', 'kind', 'trackId', 'packetsReceived', 'fecPacketsDiscarded',
                        'jitter', 'totalSamplesReceived', 'pps', 'codec', 'payloadType',
                        'mimeType', 'clockRate', 'concealmentEvents', 'concealment_diff',
                        'jitter2', 'framesReceived', 'packetsSent', 'framesSent',
                        'fps']  # 'frameWidth', 'frameHeight', 'fps',
        for key in dict_merge.keys():
            dict_merge[key]["label2"] = dict_merge[key]["label"].map(dict_label)
            dict_merge[key].loc[:, "flow"] = str(key)  # aggiungo nome flusso al dataset
            dict_merge[key].loc[:, "pcap"] = pcap_name

            if "video" in dict_merge[key]["label"].unique():
                resolutions = dict_merge[key][dict_merge[key]["label"] == "video"]["frameHeight"].unique()

                for res in resolutions:
                    if res < 0:  # -1 unassigned
                        dict_merge[key].loc[
                            (dict_merge[key]["label"] == "video") & \
                            (dict_merge[key]["frameHeight"] == res), \
                            "label"
                        ] = -1
                    if res > 0 and res <= 180:  # LQ
                        dict_merge[key].loc[
                            (dict_merge[key]["label"] == "video") & \
                            (dict_merge[key]["frameHeight"] == res), \
                            "label"
                        ] = 6
                    elif res > 180 and res < 720:  # MQ
                        dict_merge[key].loc[
                            (dict_merge[key]["label"] == "video") & \
                            (dict_merge[key]["frameHeight"] == res), \
                            "label"
                        ] = 7
                    else:
                        dict_merge[key].loc[  # HQ
                            (dict_merge[key]["label"] == "video") & \
                            (dict_merge[key]["frameHeight"] == res), \
                            "label"
                        ] = 5
            if "screenshare" in dict_merge[key]["label"].unique():
                dict_merge[key].loc[
                    (dict_merge[key]["label"] == "screenshare"), \
                    "label"
                ] = 3
            if "audio" in dict_merge[key]["label"].unique():
                dict_merge[key].loc[
                    (dict_merge[key]["label"] == "audio"), \
                    "label"
                ] = 0
                dict_merge[key] = dict_merge[key][dict_merge[key]["label"] == 0].assign(
                    **{'frameWidth': -1, 'frameHeight': -1})  # new
                # print(dict_merge[key]["frameWidth"])
            dict_merge[key].fillna({'frameWidth': -1, 'frameHeight': -1}, inplace=True)
            train = dict_merge[key].drop(columns_drop, axis=1, errors='ignore')
            train = train.loc[train["label"] != -1]
            df_train = pd.concat([df_train, train])
        # Attenti con questo drop!
        df_train = df_train.dropna()
        # df_train.to_csv(f"~/shared/Stadia_catture/aha_{pcap_name}.csv")
        # print(df_train[df_train["label"]==0]["frameWidth"].value_counts())
        return df_train
    except Exception as e:
        print('Log jitsi: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("LogJitsi error")
