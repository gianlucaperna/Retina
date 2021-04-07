# Standard plotly imports
import plotly.graph_objs as go
import plotly.figure_factory as ff
import plotly
import plotly.express as px
import plotly.io as pio
#Python imports
import os
import pandas as pd
from Table2HTML import table
import numpy as np
import sys
from ast import literal_eval as make_tuple
import itertools
import seaborn as sns
# from rich.console import Console
# console = Console()
from rich.traceback import install
install()

def make_rtp_data(dict_flow_data, flows):

    packets_per_second = {}
    kbps_series = {}
    inter_packet_gap_s = {}
    inter_rtp_timestamp_gap = {}
    len_frame = {}
    rtp_timestamp = {}
    interarrival_min = {}
    interarrival_max = {}

    for flow_id in flows:
        #If the index is already datetime
        if isinstance(dict_flow_data[flow_id].index, pd.DatetimeIndex):
            inner_df = dict_flow_data[flow_id].sort_index().reset_index()
        else:
            inner_df = dict_flow_data[flow_id].sort_values('timestamps')
            
#         print("Index: ", inner_df.index, "Columns: ", inner_df.columns)

        # Need to define a datetime index to use resample
        datetime = pd.to_datetime(inner_df['timestamps'], unit = 's')
        inner_df = inner_df.set_index(datetime)

        packets_per_second[flow_id] = inner_df.iloc[:,0].resample('S').count()
        kbps_series[flow_id] = inner_df['len_frame'].resample('S').sum()*8/1024
        inter_packet_gap_s[flow_id] = inner_df['timestamps'].diff().dropna()
        interarrival_min[flow_id] = inter_packet_gap_s[flow_id].resample('S').min()
        interarrival_max[flow_id] = inter_packet_gap_s[flow_id].resample('S').max()
        inter_rtp_timestamp_gap[flow_id] = inner_df['rtp_timestamp'].diff().dropna()
        len_frame[flow_id] = inner_df["len_frame"].copy()
        rtp_timestamp[flow_id] = inner_df["rtp_timestamp"].copy()

    return packets_per_second, kbps_series, inter_packet_gap_s, inter_rtp_timestamp_gap, len_frame,\
            rtp_timestamp, interarrival_min, interarrival_max


#Convert tuple to string for naming purposes
def tuple_to_string(tup):
    tup_string = ''
    for i in range(len(tup)):
        if i == len(tup)-1:
            tup_string += str(tup[i])
        else:
            tup_string += str(tup[i])+'_'
    tup_string = tup_string.replace('.','-')
    tup_string = tup_string.replace(':','-')
    return tup_string


def label_for_plotting(dataset_dropped):
    
    dict_label = {
    -1 : "Unknown",
    0: "Audio",
    1: "Video all qualities",
    2: "Fec-video",
    3: "ScreenSharing",
    4: "FEC-audio",
    5: "VideoHQ",
    6: "VideoLQ",
    7: "VideoMQ",
    8: "Fec-ScreenSharing"
    }
    
    #{flow tuple: label}
    flow_label = {}
    for flow in dataset_dropped["flow"].unique():
        try:
            main_label = dataset_dropped[dataset_dropped["flow"] == flow]["label"].value_counts().index[0]
            flow_label[make_tuple(flow)] = dict_label[main_label]
        except Exception as e:
            print("Error in flow_label.")
    
    return flow_label


def make_new_unique_table (dict_flow_df, flow_label, flows):    
    unique_l = []
    for key in flows:
        value = dict_flow_df[key]
        inner_list = []
        for m in key:
            inner_list.append(m)
        inner_list.append(value["rtp_csrc"].iloc[0])
        if key in flow_label.keys():
            inner_list.append(flow_label[key])
        else:
            inner_list.append("unknown")
        unique_l.append(inner_list)

    unique_df = pd.DataFrame(data=unique_l, columns=["ssrc", "source_addr", "dest_addr", "source_port", "dest_port", "rtp_p_type", "csrc", "label"])
    return unique_df

def make_dict_csrc(dict_flow_df, unique_df, flows):
    csrcs = unique_df["csrc"].unique()
    csrc_flows = {k: [] for k in csrcs}
    for key in flows:
        value = dict_flow_df[key]
        csrc_value = value["rtp_csrc"].iloc[0]
        csrc_flows[csrc_value].append(key)
        
    csrc_colour = {}
    palette = itertools.cycle(sns.color_palette("Set1", n_colors=len(csrcs)).as_hex())
    #colors = itertools.cycle(["red", "blue", "yellow", "green", "cyan", "black", "orange"])
        
    for key in csrc_flows.keys():
        csrc_colour[key] = next(palette)

    return csrc_flows, csrc_colour
    

def plot_stuff(pcap_path, dict_flow_df, df_unique, dataset_dropped, software):
    
    #Plotting functions
    def plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour):

        
        fig = go.Figure()

        for i in range(len(data_plot)):
            name = "Flow " + str(i) + " " + flow_label[flows[i]]
            csrc = dict_flow_df[flows[i]]["rtp_csrc"].iloc[0]
            colour = csrc_colour[csrc]

            if flows[i][1].startswith('192.'):

                mode='lines'
                fig.add_trace(go.Scatter(
                                x=data_plot[flows[i]].index,
                                y=data_plot[flows[i]],
                                mode=mode,
                                name=name,
#                                 line=dict(color=colour),
                                ))
            else:
                line=dict(dash='dash',
#                           color=colour,
                         )
                fig.add_trace(go.Scatter(
                                x=data_plot[flows[i]].index,
                                y=data_plot[flows[i]],
                                line=line,
                                name=name,
                                ))

        fig.update_layout(
            template="plotly_white",
            title=dict(text=title, x=0.4),
            xaxis_title="Time",
            yaxis_title=y_label,
            font=dict(size=18, color="#7f7f7f",),
            autosize=True,
            legend=dict(
            title="<b> RTP flows </b>", \
            font=dict(size=14) \
            ),
        )

        return fig
    
    try:
        #Main of plotting
        flow_label = label_for_plotting(dataset_dropped)

        #Saving info
        save_dir = os.path.join(pcap_path, "Plots_html")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        #Take keys of dict_flow_data in a list to iterate them easily
    #     l_keys = list(dict_flow_df.keys())

        #Take flows from dataset_dropped and turn them into tuples
        flows = []
        for flow in dataset_dropped["flow"].unique():
            flows.append(eval(flow))

        #Just checking if keys in dataset dropped are equal to those of dict flow data
#         if flows != list(dict_flow_df.keys()):
#             print("Mismatch dict_flow_data and csv data")

        #Take data from dict_flow_data
        packets_per_second,\
        kbps_series,\
        inter_packet_gap_s,\
        inter_rtp_timestamp_gap,\
        len_frame,\
        rtp_timestamp,\
        interarrival_min,\
        interarrival_max = \
                make_rtp_data(dict_flow_df, flows)


        #Take data from dataset_dropped - aggregated data (1s,2s,5s)
        losses_csv = {}
        kbps_csv = {}
        packets_per_second_csv = {}
        interarrival_std_csv = {}
        interarrival_min_csv = {}
        interarrival_max_csv = {}
        rtp_marker_sum = {}


        for flow in flows:
            df_scenario = dataset_dropped[dataset_dropped["flow"] == str(flow)].copy()
    #         df_scenario = df_scenario.sort_values('timestamps')
    #         df_scenario["timestamps"] = pd.to_datetime(df_scenario["timestamps"])
    #         df_scenario = df_scenario.set_index("timestamps")

            losses_csv[flow] = df_scenario["rtp_seq_num_packet_loss"].copy()
            kbps_csv[flow] = df_scenario["kbps"].copy()
            packets_per_second_csv[flow] = df_scenario["num_packets"].copy()
            interarrival_std_csv[flow] = df_scenario["interarrival_std"].copy()
            interarrival_min_csv[flow] = df_scenario["interarrival_min"].copy()
            interarrival_max_csv[flow] = df_scenario["interarrival_max"].copy()
            if software == "webex":
                rtp_marker_sum[flow] = df_scenario["rtp_marker_sum_check"].copy()

        #Additional useful data
        #Unique df that has also csrc and label
        unique_df = make_new_unique_table(dict_flow_df, flow_label, flows)

        #csrc_flows - {csrc: list of flow tuples with that csrc}
        #csrc_colour - {csrc: colour}
        csrc_flows, csrc_colour = make_dict_csrc(dict_flow_df, unique_df, flows)

        #Plot stuff

        # --------------Speed in kbps from dict_flow_data
#         data_plot = kbps_series.copy()
#         title = 'Bitrate in kbps'
#         y_label = "kbps"
#         fig_kbps = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

    #     # --------------Packets per second from dict_flow_data
    #     data_plot = packets_per_second.copy()
    #     title = 'Packets per second'
    #     y_label = "Number of packets"
    #     fig_pps = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)


        # --------------Speed in kbps from dataset_dropped
        data_plot = kbps_csv.copy()
        title = 'Bitrate in kbps from csv'
        y_label = "kbps from csv"
        fig_kbps_csv = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

        # --------------Packets per second dataset_dropped
        data_plot = packets_per_second_csv.copy()
        title = 'Packets per second from csv'
        y_label = "packets per second from csv"
        fig_pps_csv = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)


        # --------------Losses dataset_dropped
        data_plot = losses_csv.copy()
        title = 'Losses from csv'
        y_label = "percentage of lost packets"
        fig_losses = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)


        # --------------Interarrival dataset_dropped
        data_plot = interarrival_std_csv.copy()
        title = 'Interarrival standard deviation from csv'
        y_label = "interarrival standard deviation"
        fig_interarrival_std = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

    #     # --------------Interarrival min from dict_flow_data
    #     data_plot = interarrival_min.copy()
    #     title = 'Interarrival min per second'
    #     y_label = "interarrival min"
    #     fig_interarrival_min = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

    #     # --------------Interarrival max from dict_flow_data
    #     data_plot = interarrival_max.copy()
    #     title = 'Interarrival max per second'
    #     y_label = "interarrival max"
    #     fig_interarrival_max = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

        # --------------Interarrival min from csv
        data_plot = interarrival_min_csv.copy()
        title = 'Interarrival min per second from csv'
        y_label = "interarrival min"
        fig_interarrival_min_csv = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

        # --------------Interarrival max from csv
        data_plot = interarrival_max_csv.copy()
        title = 'Interarrival max per second from csv'
        y_label = "interarrival max"
        fig_interarrival_max_csv = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)

        # --------------RTP marker sum check
        if software == "webex":
            data_plot = rtp_marker_sum.copy()
            title = 'RTP marker sum'
            y_label = "RTP marker sum"
            fig_rtp_marker_sum = plot_line(data_plot, title, y_label, flows, flow_label, dict_flow_df, csrc_colour)



        #Make table and save table and graphs in main html
        html_table = table(unique_df, "Main Graph", True)
        main_html_save = os.path.join(save_dir, "main_graphs.html")
        with open(main_html_save, 'w') as f:
            f.write("<h3 style='color:black;font-family:Open sans;'> Pcap folder: " +pcap_path.split("/")[-1]+ " </h3>")
            f.write(html_table)
        with open(main_html_save, 'a') as f:
#             f.write(fig_kbps.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_kbps_csv.to_html(full_html=False, include_plotlyjs='cdn'))
#             f.write(fig_pps.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_pps_csv.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_losses.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_interarrival_std.to_html(full_html=False, include_plotlyjs='cdn'))
#             f.write(fig_interarrival_min.to_html(full_html=False, include_plotlyjs='cdn'))
#             f.write(fig_interarrival_max.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_interarrival_min_csv.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig_interarrival_max_csv.to_html(full_html=False, include_plotlyjs='cdn'))
            if software == "webex":
                f.write(fig_rtp_marker_sum.to_html(full_html=False, include_plotlyjs='cdn'))


        print("Did the main graphs successfully")

    
        #Plot the single graphs
        for key1 in flows:
            
            csrc1 = dict_flow_df[key1]["rtp_csrc"].iloc[0]
            label1 = flow_label[key1]

            title = "Bitrate distribution"
            fig_bit_h = px.histogram(x=kbps_series[key1] ,marginal="box", opacity = 0.6,\
                histnorm = "probability density", color_discrete_sequence=["#FFA69E"])
            fig_bit_h.update_layout(
                template="simple_white",
                title=dict(text=title, x=0.5),
                xaxis_title="Bitrate [kbps]",
                yaxis_title="Probability density function",
                font=dict(size=18, color="#7f7f7f",),
                autosize=True,

            )
            fig_bit_h.update_yaxes(showgrid=True)
            fig_bit_h.update_xaxes(showgrid=True)


            #1 Plot histogram of packet length - len_frame[key1]
            title = "Packet-length distribution"
            fig_pl_h = px.histogram(x=len_frame[key1], marginal="box", opacity = 0.6,\
                histnorm = "probability density",  color_discrete_sequence=["#FF686B"])
            fig_pl_h.update_layout(
                template="simple_white",
                #grid = {"xaxis":True,"yaxis":True},
                title=dict(text=title, x=0.5),
                xaxis_title="Packet length [Byte]",
                yaxis_title="Probability density function",
                font=dict(size=18, color="#7f7f7f",),
                autosize=True,
            )
            fig_pl_h.update_yaxes(showgrid=True)
            fig_pl_h.update_xaxes(showgrid=True)


            #2 Plot packet length in time - len_frame[key1]
            # title = "Packet length in time"
            # inside=go.Scatter(x=len_frame[key1].index, y=len_frame[key1],
            #                   mode='lines', line=dict(color='#815EA4'))
            # fig_pl_t = go.Figure(inside)
            # fig_pl_t.update_layout(
            #     title=dict(text=title, x=0.5),
            #     xaxis_title="Time",
            #     yaxis_title="Packet length [B]",
            #     font=dict(size=18, color="#7f7f7f",),
            #     autosize=True,
            # )

            #3 Plot histogram of inter-packet gap - inter_packet_gap_s
            #title = "Inter-packet gap [s] histogram"
            title="Interarrival time distribution"
            fig_ipg_h = px.histogram(x=inter_packet_gap_s[key1], marginal="box", opacity = 0.6,\
                histnorm = "probability density", color_discrete_sequence=["#A5FFD6"])
            fig_ipg_h.update_layout(
                template="simple_white",
                title=dict(text=title, x=0.5),
                xaxis_title="Interarrival [s]",
                #xaxis_type="log",
                yaxis_title="Probability density function",
                font=dict(size=18, color="#7f7f7f",),
                autosize=True,
            )
            fig_ipg_h.update_yaxes(showgrid=True)
            fig_ipg_h.update_xaxes(showgrid=True)

            #4 Plot Inter-packet gap in time - inter_packet_gap_s

            #title='Inter-packet gap in time'
            # inside=go.Scatter(x=inter_packet_gap_s[key1].index, y=inter_packet_gap_s[key1],
            #                   mode='lines', line=dict(color='red'))
            # fig_ipg_t = go.Figure(inside)
            # fig_ipg_t.update_layout(
            #     title=dict(text=title, x=0.5),
            #     xaxis_title="Time",
            #     yaxis_title="Inter-packet-gap [s]",
            #     font=dict(size=18, color="#7f7f7f",),
            #     autosize=True,
            # )

            #5 Histogram of Inter rtp timestamp gap - inter_rtp_timestamp_gap
            title="Inter-timestamp RTP distribution"
            #title = "Histogram of Inter-RTP-timestamp gap"
            fig_irtg_h = px.histogram(x= inter_rtp_timestamp_gap[key1],  marginal="box", opacity = 0.6,\
                histnorm = "probability density",  color_discrete_sequence=["#84DCC6"])
            fig_irtg_h.update_layout(
                template="simple_white",
                title=dict(text=title, x=0.5),
                xaxis_title="Inter-RTP-timestamp",
                yaxis_title="Probability density function",
                font=dict(size=18, color="#7f7f7f",),
                autosize=True,
            )
            fig_irtg_h.update_yaxes(showgrid=True)
            fig_irtg_h.update_xaxes(showgrid=True)


            #6 RTP-timestamp in time - rtp_timestamp[key1]
            # title='RTP-timestamp in time'
            # inside=go.Scatter(x=rtp_timestamp[key1].index, y=rtp_timestamp[key1],
            #                   mode='markers')
            # fig_rt_t = go.Figure(inside)
            # fig_rt_t.update_layout(
            #     title=dict(text=title, x=0.5),
            #     xaxis_title="Time",
            #     yaxis_title="RTP-timestamp",
            #     font=dict(size=18, color="#7f7f7f",),
            #     autosize=True,
            # )

            #Write to html string of flow and all associated plots
            table_list = []
            for item in key1:
                table_list.append(item)
            table_list.append(csrc1)
            table_list.append(label1)
            
            html_save = os.path.join(save_dir, tuple_to_string(key1)+'.html')
            col = ["ssrc", "source_addr", "dest_addr", "source_port", "dest_port", "rtp_p_type", "csrc", "label"]
            with open(html_save, 'w') as f:
                f.write(table( pd.DataFrame(data=[table_list], columns =col), "Flow Graph"))
            with open(html_save, 'a') as f:
                f.write(fig_bit_h.to_html(full_html=False, include_plotlyjs='cdn'))
                f.write(fig_pl_h.to_html(full_html=False, include_plotlyjs='cdn'))
                #f.write(fig_pl_t.to_html(full_html=False, include_plotlyjs='cdn'))
                f.write(fig_ipg_h.to_html(full_html=False, include_plotlyjs='cdn'))
                #f.write(fig_ipg_t.to_html(full_html=False, include_plotlyjs='cdn'))
                f.write(fig_irtg_h.to_html(full_html=False, include_plotlyjs='cdn'))
                #f.write(fig_rt_t.to_html(full_html=False, include_plotlyjs='cdn'))
                
        print("Did the flow graphs successfully as well")
            
    except Exception as e:
        print('Plotting: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
