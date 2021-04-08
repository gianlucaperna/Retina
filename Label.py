import pandas as pd

#ETICHETTATURA NOSTRA


def label_by_length(dict_flow_data, threshold):
    #serve per etichettare mettendo il nome del software
    to_drop = []
    for flow_id in dict_flow_data.keys():
        if dict_flow_data[flow_id]["len_udp"].mean() < threshold:
            if max(dict_flow_data[flow_id]["len_udp"]) < threshold:
                dict_flow_data[flow_id]["label"] = 0
            else:
               #print(f"Controllo flusso {flow_id}, sospetto ScreenSharing, name: {name}, max: {max(dict_flow_data[flow_id]['len_udp'])}, int: {max(dict_flow_data[flow_id]['rtp_interarrival'])}")
                value_counts = dict_flow_data[flow_id]['rtp_interarrival'].value_counts()
                if value_counts.index[0]%192==0:#192 è 5ms, 960 è 20ms
                   #print(f"Il flusso {flow_id}, è audio, controllato inter-RTP")
                    dict_flow_data[flow_id]["label"] = 0
                to_drop.append(flow_id)
        else:
            dict_flow_data[flow_id]["label"] = 1
        # dict_flow_data[flow_id]["label2"] = label
    for k in to_drop:
        dict_flow_data.pop(k, None)
    return dict_flow_data


# def etichetto_basic(dict_flow_data, screen, quality, software):
#     if (screen is None) and (quality is None) and (software == "webex"):
#         dict_flow_data = labelling2(dict_flow_data, screen, quality) #etichetto audio video fec audio fec video
#         for flow_id in dict_flow_data:
#             dict_flow_data[flow_id]["label"] = -1
#         return dict_flow_data
#     elif screen is None and quality is None:
#         for flow_id in dict_flow_data:
#             dict_flow_data[flow_id]["label"] = -1
#             dict_flow_data[flow_id]["label2"] = -1
#         return dict_flow_data
#     dict_flow_data = labelling (dict_flow_data, screen, quality)
#     dict_flow_data = labelling2(dict_flow_data, screen, quality)
#     return dict_flow_data

# def audio_vs_fec_vs_ss(dict_flow_data, flow_id):
#     if (dict_flow_data[flow_id]["rtp_timestamp"] == 0).all():
#         dict_flow_data[flow_id]["label"] =  4#FEC audio
#         #print("FEC_0: {}".format(flow_id))
#     elif check_fec_equal(dict_flow_data,flow_id):
#         #print("FEC_same: {}".format(flow_id))
#         dict_flow_data[flow_id]["label"] =  4#FEC audio ricevuto
#     else:
#         dict_flow_data[flow_id]["label"] = [ 3 if x[-1] == str(1) else 0 for x in dict_flow_data[flow_id]["rtp_csrc"]]
#         #print("Aia {}".format(flow_id))
#         #print("CSRC\n {}".format(dict_flow_data[flow_id]["rtp_csrc"]))
#     return dict_flow_data[flow_id]

# def video_vs_fec(dict_flow_data, flow_id, screen = None, quality = None):
#     if (dict_flow_data[flow_id]["rtp_timestamp"] == 0).all():
#         dict_flow_data[flow_id]["label"] = 2 #FEC VIDEO
#         #print("FEC_0_vid: {}".format(flow_id))
#     elif check_fec_equal(dict_flow_data,flow_id):
#         dict_flow_data[flow_id]["label"] = 2 #FEC VIDEO RICEVUTO
#         #print("FEC_same_video: {}".format(flow_id))
#     elif check_fec_equal_90(dict_flow_data,flow_id):
#         dict_flow_data[flow_id]["label"] = 2
#     elif (quality == "HQ"):
#         dict_flow_data[flow_id]["label"] =  5#Video HQ 720p
#     elif (quality == "LQ"): #standard quality
#         dict_flow_data[flow_id]["label"] =  6#Video LQ 180p
#     elif (quality == "MQ"): #standard quality
#         dict_flow_data[flow_id]["label"] =  7#Video MQ 360p
#     elif (screen is not None): #screen
#         #print ("here")
#         dict_flow_data[flow_id]["label"] =  3# screen
#     else:
#         dict_flow_data[flow_id]["label"] =  1 #Video Root-Class
#         #print("labelling_video: {}".format(flow_id))
#     return dict_flow_data[flow_id]

# def automate_classify (dict_flow_data, flow_id, screen = None, quality = None):
#     if dict_flow_data[flow_id]["len_udp"].mean() < 400:
#         dict_flow_data[flow_id] = audio_vs_fec_vs_ss(dict_flow_data, flow_id)
#     else:
#         dict_flow_data[flow_id] = video_vs_fec(dict_flow_data, flow_id,\
#                                                screen, quality)
#     return dict_flow_data[flow_id]
#
#
# def labelling (dict_flow_data,screen = None, quality = None):
#     for flow_id in dict_flow_data:
#         dict_flow_data[flow_id] = automate_classify(dict_flow_data, flow_id,\
#                                                     screen, quality)
#     return dict_flow_data

#def labelling (dict_flow_data, audio = None, video = None, ip = None, screen = None, quality = None):

    #if ((audio is not None or video is not None) and ip is not None):
        #for flow_id in dict_flow_data:
            #print("hand-labeling")
            #if ( audio in flow_id and ip in flow_id ):
           #     dict_flow_data[flow_id] = audio_vs_fec(dict_flow_data, flow_id)
          #  elif ( video in flow_id and ip in flow_id ):
         #       dict_flow_data[flow_id] = video_vs_fec(dict_flow_data, flow_id, quality)
        #    elif (screen):
       #         dict_flow_data[flow_id]["label"] = 3 #Screen Sharing
      #      else:
     #           print("Pay attenction: Labbelling on Meetings Capture is failed, auto-label is used")
    #            dict_flow_data[flow_id] = automate_classify(dict_flow_data, flow_id)
   # else:
      #  for flow_id in dict_flow_data:
     #       dict_flow_data[flow_id] = automate_classify(dict_flow_data, flow_id)
    #return dict_flow_data



#CISCO ETICHETTATURA
# def check_fec_equal (dict_flow_data, flow_id):
#     try:
#         cost = pow(2,16)
#         ts = dict_flow_data[flow_id]["rtp_timestamp"]
#         sn = dict_flow_data[flow_id]["rtp_seq_num"]
#         ts_final = ts%cost
#         return ts_final.equals(sn)
#     except Exception as e:
#         return False
#
# def check_fec_equal_90(dict_flow_data, flow_id):
#     try:
#         cost = pow(2,16)
#         ts = dict_flow_data[flow_id]["rtp_timestamp"]
#         sn = dict_flow_data[flow_id]["rtp_seq_num"].astype('float64')
#         ts_final = (ts/90)%cost
#         return ts_final.equals(sn)
#     except Exception as e:
#         return False

# def labelling2 (dict_flow_data, screen = None, quality = None):
#     for flow_id in dict_flow_data:
#         try:
#             if not (any(dict_flow_data[flow_id]["rtp_csrc"].isin(["fec"]))):
#                 dict_flow_data[flow_id]["rtp_csrc"] = [ str( bin(int(x, 16))[2:] ) for x in dict_flow_data[flow_id]["rtp_csrc"] ]
#                 if (dict_flow_data[flow_id]["rtp_timestamp"] == 0).all(): #FEC Inviati
#                     dict_flow_data[flow_id] = fec_audio_video_csrc(dict_flow_data, flow_id)
#                     #print("L2_FEC_rtp_0: {}".format(flow_id))
#                 elif check_fec_equal(dict_flow_data,flow_id):
#                     dict_flow_data[flow_id] = fec_audio_video_csrc(dict_flow_data, flow_id)
#                     #print("L2_FEC_same: {}".format(flow_id))
#                 elif check_fec_equal_90(dict_flow_data,flow_id):
#                     try:
#                         dict_flow_data[flow_id] = fec_audio_video_csrc(dict_flow_data, flow_id)
#                     except:
#                         dict_flow_data[flow_id] = fec_audio_video_euristic(dict_flow_data, flow_id)
#                 else:
#                     dict_flow_data[flow_id]["label2"] = [ 1 if x[-1] == str(1) else 0 for x in dict_flow_data[flow_id]["rtp_csrc"] ]
#                     #print("L2_class: {}".format(flow_id))
#             else: #se compare una voce fec etichetta euristica
#                 dict_flow_data[flow_id] = fec_audio_video_euristic(dict_flow_data, flow_id)
#                 #print("L2_FEC_EUR: {}".format(flow_id))
#         except Exception as e:
#             print(e)
#     return dict_flow_data



# def fec_audio_video_csrc(dict_flow_data, flow_id):
#
#     dict_flow_data[flow_id]["label2"] = [ 2 if x[-1] == str(1) else 4 for x in dict_flow_data[flow_id]["rtp_csrc"] ]
#     return dict_flow_data[flow_id]
#
#
# def fec_audio_video_euristic(dict_flow_data, flow_id):
#
#
#     if dict_flow_data[flow_id]["len_udp"].mean() < 400:
#         dict_flow_data[flow_id]["label2"] =  4#FEC audio
#         #print("L2_FEC_out: {}".format(flow_id))
#     else:
#         dict_flow_data[flow_id]["label2"] = 2 #FEC VIDEO
#     return dict_flow_data[flow_id]
