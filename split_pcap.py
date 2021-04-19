import subprocess
import os

def pcap_split(num_packets,source_pcap, pcap_path, name):
    new_dir = os.path.join(pcap_path, name+"_split")
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    print("Source pcap: ", source_pcap)
    command = ['editcap', '-c', str(num_packets), source_pcap, os.path.join(new_dir, name+".pcapng") ]
    print("NAME IN PCAP_SPLIT", name)
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding = 'utf-8', shell=False )
    except Exception as e:
        print ("Errore in split pcap: " + str(e))
        process.kill()
        raise e

    return new_dir


# if __name__ == "__main__":

#     source_pcap = r'C:\Users\Gianl\Desktop\Call_Poli\webex_cisco_call.pcapng'
#     name = 'webex_cisco_call'
#     pcap_path = r'C:\Users\Gianl\Desktop\Call_Poli'
#     new_dir = pcap_split (100000,source_pcap, pcap_path, name)
#     file_split = os.listdir(new_dir)
#     result_queue = multiprocessing.Queue()
#     for fs in file_split:
#         p = multiprocessing.Process(target=pcap_to_json, args = (fs, result_queue) )
#         jobs.append(p)
#         p.start()
