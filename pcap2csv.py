#Open Tshark and run command to turn pcap to json
import subprocess
import pandas as pd
import os
from tshark2stat import tshark_to_stat
from plotting_static import plot_stuff_static
from plotting import plot_stuff
from Martino_log import compute_stats
import copy
import sys
import numpy as np
import time

def pcap_to_port(source_pcap):
    try:
    # Retrive all STUN packets
        #command = ['tshark', '-r', source_pcap, '-l', '-n', '-T', 'ek', '-Y (stun)']
        command = f"tshark -r {source_pcap} -T fields  -E separator=? -E header=n -e udp.srcport -e udp.dstport"
        output, e = subprocess.Popen(command, stdout=subprocess.PIPE, encoding = 'utf-8', errors="ignore", shell=True).communicate()
    except Exception as e:
        print ("Errore in pcap_to_json: {}".format(e))
        raise e
    # I've got all STUN packets: need to find which ports are used by RTP
    used_port=set([int(x) for x in output.replace('\n','?').split('?') if x != ''])

    return {"pcap" : source_pcap, "port" : list(used_port)}

def pcap_to_csv(dict_param): #source_pcap, used_port

    try:
        source_pcap = dict_param["pcap"] #path of the pcap
        used_port = dict_param["port"]
        plot = dict_param["plot"]
        loss_rate = dict_param["loss_rate"]
        software = dict_param["software"]
        file_log = dict_param["log_dir"]
        time_drop = dict_param["drop_len"]
        general_log = dict_param["path_general_log"]
        time_aggregation = dict_param["time_aggregation"]

        # source_pcap = tuple_param[0] # path del pcap
        # used_port = tuple_param[1] #porte stun recuperate dal pcap
        # screen = tuple_param[2] # old per webex, tutti i flussi video sono etichettati come SS
        # quality = tuple_param[3] #old per webex, specifica qualità flussi video, (devono essere tutti uguali)
        # plot = tuple_param[4] # se True crea Plot
        # loss_rate = tuple_param[5] #
        # software = tuple_param[6] # webex jitsi ..
        # file_log = tuple_param[7] #directory padre dei file .log
        # time_drop = tuple_param[8] # durata in secondi minima che deve avere un flusso
        # general_log = tuple_param[9] #se c'è contiene il path dove salvare il file, altrimenti False
        # time_aggregation = tuple_param[10]
        # label = tuple_param[11]

        name = os.path.basename(source_pcap).split(".")[0] # name of the pcap without extension
        pcap_path = os.path.dirname(source_pcap) #folder where pcap is
        filtro = "rtp.version==2"
        port_add = []
        print(source_pcap)
        for port in used_port:
            port_add.append("-d udp.port==" + str(port) + ",rtp")

        command = f"""tshark -r {source_pcap} -Y {filtro} \
                     -T fields {" ".join(port_add)} -E separator=? -E header=y -e frame.time_epoch -e frame.number \
                     -e frame.len -e udp.srcport \
                     -e udp.dstport  -e udp.length  -e rtp.p_type -e rtp.ssrc -e rtp.timestamp \
                     -e rtp.seq  -e rtp.marker -e rtp.csrc.item -e ip.src -e ipv6.src -e ip.dst -e ipv6.dst  --enable-heuristic rtp_stun"""

        start = time.time()        
        o, e = subprocess.Popen(command, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        end = time.time()
        print(f"Tshark time per {name}: {end - start}")
        r = o.split("\n")
        name_col = r.pop(0)
        name_col = [e for e in name_col.split("?") if e not in ('ipv6.dst','ipv6.src')]
        del(o)
        rr = [x.split("?")[0:12]+ list(filter(None,x.split("?")[12:16])) for x in r if '' not in x.split("?")[0:9]] #for each packet keep either IPv4 or IPv6
        del(r)
        df = pd.DataFrame(rr, columns=name_col)
        #Take just the first Payload type of a stream CHANGE!!!!
        df['rtp.p_type']=df['rtp.p_type'].apply(lambda x: x.split(",")[0])
        df = df.astype({'frame.time_epoch': 'float64',
                        'frame.number': "int32",
                        'frame.len': "int32",
                        'udp.length': "int32",
                        'rtp.p_type': "int",
                        'rtp.timestamp': np.int64,
                        "udp.srcport": "int32",
                         "udp.dstport": "int32",
                        'rtp.marker': "int32",
                        'rtp.seq': "int32",
                   })
        df = df.rename(columns ={
            'frame.time_epoch' : 'timestamps',
            'frame.number' : 'frame_num',
            'frame.len' : "len_frame",
            'ip.src' : 'ip_src',
            'ip.dst' : 'ip_dst',
            'udp.srcport' : 'prt_src',
            'udp.dstport' : 'prt_dst',
            'udp.length' :  'len_udp',
            'rtp.p_type' : 'p_type',
            'rtp.ssrc' : 'ssrc',
            'rtp.timestamp' : 'rtp_timestamp',
            'rtp.seq' : 'rtp_seq_num',
            'rtp.marker' : 'rtp_marker',
             'rtp.csrc.item' : 'rtp_csrc'
                })
        df["rtp_csrc"].replace('',"fec", inplace=True)

        if software=="webex":
            columns=["ssrc", "ip_src", "ip_dst", "prt_src", "prt_dst" , "p_type"]
        elif software=="skype":
            columns=["ssrc", "ip_src", "ip_dst", "prt_src", "prt_dst"]
        elif software=="mteams":
            columns=["ssrc", "ip_src", "ip_dst", "prt_src", "prt_dst"]
        else:
            columns=["ssrc", "ip_src", "ip_dst", "prt_src", "prt_dst" , "p_type"]
        gb = df.groupby(columns)
        dict_flow_data = {x : gb.get_group(x) for x in gb.groups if x is not None and np.max(gb.get_group(x)["timestamps"]) - np.min(gb.get_group(x)["timestamps"])>time_drop}
        df_unique_flow = pd.DataFrame(columns = columns)
        for key in dict_flow_data.keys():
            df_unique_flow=df_unique_flow.append(pd.Series(key, index=columns), ignore_index=True)

        if general_log:
            general_dict_info = {}
            for flow_id in dict_flow_data:
                s = compute_stats(copy.deepcopy(dict_flow_data[flow_id]),flow_id, name+".pcapng")
                if s is not None:
                    general_dict_info[flow_id] = s
                    general_df=pd.DataFrame.from_dict(general_dict_info, orient='index').reset_index(drop = True)
                    general_df.to_csv(os.path.join(general_log,name+"_gl.csv"))

        for time_agg in time_aggregation:
            dataset_dropped = tshark_to_stat(copy.deepcopy(dict_flow_data),
                                        pcap_path,
                                        name,
                                        time_agg,
                                        software=software,
                                        file_log=file_log,
                                        loss_rate=loss_rate)
        if plot == "static":
            plot_path = os.path.join(pcap_path,name)
            plot_stuff_static(plot_path, dict_flow_data, df_unique_flow)
        elif plot == "dynamic":
            plot_path = os.path.join(pcap_path,name)
            plot_stuff(plot_path, dict_flow_data, df_unique_flow, dataset_dropped, software)
        else:
            pass
        #end2=time.time()
        #print(f"General Time per name: {end2 - end} - {end2-start}")
    except Exception as e:
        print('Pcap2Json: Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        raise NameError("Pcap2Json error")
    return
