#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import warnings

# warnings.filterwarnings("ignore", "(?s).*MATPLOTLIBDATA.*", category=UserWarning)
warnings.filterwarnings("error")
from MergeCSV import merge_csv
from pcap2csv import pcap_to_csv, pcap_to_port
import argparse
import os
import multiprocessing
import multiprocessing.pool
from rich.console import Console
from rich.table import Table
from rich import box


def set_n_process(pcap_app, n_proc):
    n_process = multiprocessing.cpu_count() - 1
    if n_process > n_proc:
        n_process = 30
    if len(pcap_app) < n_proc:
        n_process = len(pcap_app)
    return n_process


def find_ports(pool_tuple):
    new_dir_name_file = pool_tuple[0]
    result_list = pool_tuple[1]
    dict_pcap_port = pcap_to_port(new_dir_name_file)
    result_list.append(dict_pcap_port)


def recursive_files(directory_p):
    pcap_app = []
    if os.path.isfile(directory_p):
        last_path = os.path.basename(os.path.normpath(directory_p))
        if last_path.split(".")[1].startswith("pcap"):
            return [directory_p]  # torno il file su cui lavorare
        else:
            return -1  # ritorno errore
    else:
        for r, d, f in os.walk(directory_p):
            for file in f:
                if ('.pcap' in file or '.pcapng' in file):
                    pcap_app.append(os.path.join(r, file))
        return pcap_app


if __name__ == "__main__":
    console = Console()
    with open("text.txt", "r") as f:
        console.print(
            f"[bold magenta]{f.read()}[/bold magenta]\n[bold magenta]Authors:[/bold magenta] Gianluca Perna[i](gianluca.perna@polito.it)[/i], Dena Markudova[i](dena.markudova@polito.it)[/i]\n\n")

    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="RTP flow analyzer")
    parser.add_argument("-d", "--directory", help="Master directory", required=True)
    parser.add_argument("-j", "--join", help="Join all .csv", action='store_true')
    parser.add_argument("-p", "--plot", help="Plot info", choices=['static', 'dynamic'], default=None, type=str.lower)
    parser.add_argument("-so", "--software", help="webex, skype, msteams, webrtc, other",
                        choices=['webex', 'webrtc', 'msteams', 'zoom', 'skype', 'other'], default="other",
                        type=str.lower)
    parser.add_argument("-log", "--log_dir", help="Directory logs file", default=None)
    parser.add_argument("-dp", "--drop", help="Minimum length in time of the flow", type=int, default=10)
    parser.add_argument("-gl", "--general_log", help="General log for flows, like Tstat", action='store_true',
                        default=False)
    parser.add_argument("-ta", "--time_aggregation", help="time window aggregation", nargs='+', type=int, default=[1])
    parser.add_argument("-po", "--port", help="Add RTP port", nargs='+', type=int, default=[])
    parser.add_argument("-lr", "--loss_rate", help="Set to drop flow with greater or equal loss_rate (default 0.2)",
                        type=float, default=0.2)
    parser.add_argument("-th", "--threshold", help="Set threshold for unsupervised labelling", type=float, default=400)
    parser.add_argument("-proc", "--process", help="Set number of processes", type=int, default=8)
    console.print("!!!!! Time Aggregation is in milliseconds !!!!! ")
    args = parser.parse_args()

    # Handle the directory of pcaps
    directory_p = args.directory
    pcap_app = recursive_files(directory_p)
    if (pcap_app == -1):
        raise NameError("Inserted file not valid")

    # Set number of processes as number of pcaps
    n_process = set_n_process(pcap_app, args.process)
    table = Table(show_header=True, header_style="bold magenta", box=box.HORIZONTALS, show_footer=True)
    table.add_column("Pcap(s) to elaborate:", justify="center",
                     footer=f"[bold magenta]N. worker:[/] [cornflower_blue bold]{n_process}[/], [bold magenta]PID main:[/bold magenta] [cornflower_blue bold]{os.getpid()}[/]")
    for i in pcap_app: table.add_row(i, style="cornflower_blue bold")
    console.print(table)

    # For each .pcap in the folders, do the process
    manager = multiprocessing.Manager()
    result_list = manager.list()
    # creation of general log
    if args.general_log:
        OUTDIR = "logs"
        if os.path.isdir(directory_p):
            path_general_log = os.path.join(directory_p, OUTDIR)
        else:
            path_general_log = os.path.join(os.path.dirname(directory_p), OUTDIR)
        if not os.path.isdir(path_general_log):
            os.makedirs(path_general_log)
    else:
        path_general_log = False

    # Find the RTP ports
    pool = multiprocessing.Pool(processes=n_process, maxtasksperchild=1, )
    pool_tuple = [(x, result_list) for x in pcap_app]
    pool.imap_unordered(find_ports, pool_tuple, chunksize=1)
    pool.close()
    pool.join()

    # Main
    # Decode RTP traffic according to ports and create the aggregation .csv files
    pool = multiprocessing.Pool(processes=n_process, maxtasksperchild=1, )

    pool_dict = [{"pcap": x["pcap"],
                  "port": x["port"] + args.port,
                  "plot": args.plot,
                  "loss_rate": args.loss_rate,
                  "software": args.software,
                  "log_dir": args.log_dir,
                  "drop_len": args.drop,
                  "path_general_log": path_general_log,
                  "time_aggregation": args.time_aggregation,
                  "threshold": args.threshold,
                  }
                 for x in result_list]

    pool.imap_unordered(pcap_to_csv, pool_dict, chunksize=1)
    pool.close()
    pool.join()

    if (args.join):
        for time_agg in args.time_aggregation:
            merge_csv(directory_p, time_agg)
