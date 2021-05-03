# Retina (Real-Time Analyzer)

Analyse a posteriori Real Time Traffic (RTP-SRTP) with a simple tool written in python.
This tool provides all functionality to create a dataset aggregation and to plot data.
It uses `multiprocessing` in its internal to increase the number of pcap/pcapng that you can analyse per time.
We provide a functionalities to label the data reading pcap and log file of webex application or webRTC log.

For information about this Readme file and this tool please write to
[gianluca.perna@polito.it](mailto:gianluca.perna@polito.it)
[dena.markudova@polito.it](mailto:dena.markudova@polito.it)

## Table of Content
<!---
Done with https://github.com/ekalinin/github-markdown-toc )
-->
   * [Installation](#installation)
   * [Usage](#usage)
   * [Modes](#modes)
   * [Arguments](#arguments)
   * [Functionality](#functionality)
   * [Configuration](#configuration)
   * [Logs](#logs)
## Installation

Simply clone this repo.
Also the installation of tshark is required:
```
 sudo apt-get install -y tshark
```

Dependencies are: `matplotlib numpy pandas ... we want to put all of them here?`.
You can easily install all the requirements running:
```
pip3 install -r requirements.txt
```

## Usage
This is a `command line tool` that offers different kind of functionality
Example of basic usage is:
```
python3 Retina.py -d test/webex -so webex -log test/log/webex -ta 1000 2000
```
The outputs will be a files `.csv` with the `same name` of the pcaps.
In this case we got two output that are pcap1_1000s.csv and pcap2_2000s.csv
  
#### Basic arguments

The most important arguments are:
* `directory (-d)`: master directory in which are contained all pcaps.
* `log (-log)`: the path in which are stored the log file (.txt for Webex and .log for webRTC). Pay attention that the file log MUST have the same name of the pcap.
* `software (-so)`: which software will be analysed [webex, webrtc, zoom, msteams, Skype, other] for Webex and webRTC is important to specify correctly this arguments if you pass -log parameter.
* `plot (-p)`: which type of plot to create [dynamic, static]
* `time_aggregation (-ta)`: specify the time aggregation for the data. Pay attention that the values MUST be written in ms.
* `join (-j)`: Join automatically all .csv at the end of the analyses process, to give you a complete dataset.
* `loss rate (-lr)`: maximum value of loss rate that a flow can have to be considered. If the value computed on a flow is over the loss rate, the flow will be discarded. Default=0.2 [0-1]
* `drop_packet (-dp)`: minimum number of packet that MUST be present in the flow, otherwise it will be discarded. Default=100
* `drop_time (-dp_time)`: minimum length in terms of seconds of flow to be considered, otherwise it will be discarded. Default=20
* `port (-po)`: Retina uses an heuristic to understand on which port there is RTP traffic. If you need, you can specify others port using this parameter
* `process (-proc)`: maximum number of process that the tool could be use. With this value you specify the maximum in order to avoid that multiprocessing can consume all the CPU. If the num pcaps<process, the tool will use num pcap process
* `port (-th)`: If you don't provide a -log file Retina can try to label your data in Audio/Video using an heuristic based on mean length of the packets in a flow. Default=400

## Log compatible with Tstat
* `output_gl (-out_gl)`:  path where will be stored the output of the gl
* `general_log (-gl)`: Create a general log like Tstat for flows
* `internal_mask (-im)`: Specify the internal mask of network to set the direction of the flow. Default="192.168."

## Functionality

How is shown in figure 1, Retina is a tool that take in input a pcap/pcapng files containing RTP traffic, and optionally a log file, and, produce in output different kind of stuff:

1) .csv with statistics calculated for [time aggregation] seconds for each flow
2) general log like Tstat (see more detail here [link tstat]) 
3) static plot (.png) or responsive (.html)

Retina is able to recognize 5 main class using the log, that are:

1) HQ class (video >= 720p)
2) MQ class (video 360 <= MQ < 720p)
3) LQ class (video LQ < 360p)
4) Audio
5) ScreenSharing

In case of Webex application we have also the FEC [remainder to fec RFC] flow that are always audio/video flow but with the purpose of recover error.

Without the file log Retina can use an heuristic to understand what flow are Audio or Video but isn't able to understand what type of Video is.

Retina can run in a multiprocess way in order to analyse more pcaps in parallel. Anyway the type of pcap that you analyse MUST become from the same software. This means that in a main directory Where will be run Retina you can put a lot of pcap but everyone MUST become from the sample application (e.g all webex or webRTC and so on..).
The log files can be stored also in other directory, remember only that the name of the log MUST be the same of the pcap.


## Configuration
Retina is provided of configuraiton file to regulate the statistics that you want in output in the dataset.

Here is reported the config.py file with all possibile configuration settings:

```
common_functions = ["std", "mean", "min", "max", "count", "kurtosis", "skew", "moment3", "moment4"]
percentiles = ["p10", "p20", "p25", "p30", "p40", "p50", "p60", "p70", "p75", "p80", "p90", "p95"]
special_functions = ["max_min_diff", "max_min_R", "min_max_R", "len_unique_percent", "max_value_count_percent"]

config_dict = {
    'interarrival': common_functions + special_functions,
    'len_udp': ["kbps"] + common_functions + special_functions,
    'interlength_udp': common_functions + special_functions,
    'rtp_interarrival': ["zeroes_count"] + common_functions + special_functions,
    "rtp_marker": ["sum_check"],
    "rtp_seq_num": ["packet_loss"],
    "rtp_csrc": ["csrc_agg"],
    "inter_time_sequence": common_functions + special_functions,
}
```

How you can see, there are different kind of statistics, some standard that we call "common_functions" and "percentiles", in which we put all classical stats like mean, std and so on, and others created by us.
Let's explain now the special function, reading the mathematical formula and then the intuition.
Suppose in all the following example that we start having this list of values:

```
series = pandas.Series([0,0,0,0,0,1,1,1,1,2,3,4,4,5,5,6])
```

We use the variable "list" to show an example of what the special functions produces in output.

```
def max_min_diff(series):
    return series.max() - series.min()

print(max_min_diff(series)) --> 6
```
This feature explain the peak peak value in a time_aggregation window time by time, so, explain what is the maximum "oscillation" in our time_aggregation.
```
def max_min_R(series):
    try:
        a = abs(series.max())
        b = abs(series.min())
        if a == 0 and b == 0:
            return 0
        else:
            return a / (a + b)
    except Exception as e:
        print(f"Error: min_max_R a= {a}, b= {b}")
        return 0

print( max_min_R(series) ) --> 1
```
With max_min_R we try to capture in a non linear way what is the importance of the min on the total results. Infact more this value is close to 1 more the minimum is close to 0. max_min_R takes values in [0.5, 1].

```
def min_max_R(series):
    try:
        a = abs(series.max())
        b = abs(series.min())
        if a == 0 and b == 0:
            return 0
        else:
            return b / (a + b)
    except Exception as e:
        print(f"Error: min_max_R a= {a}, b= {b}")
        return 0


print( min_min_R(series) ) --> 0
```
Same but opposite of max_min_R
```
def max_value_count_percent(series):
    try:
        return (series.value_counts().iloc[0]) / len(series)
    except Exception as e:
        return 0

print( max_value_count(series) ) --> 5/16
```
max_value_count_percent tells us how is "famous" the mode in the second. If in the time_aggregation we always have the same value (e.g [1,1,1,1,1,...,1]) the max_value_count_percent reach the maximum that is 1. 

```
def len_unique_percent(series):
    try:
        return len(series.unique()) / len(series)
    except Exception as e:
        return 0
        
print( len_unique_percent(series) ) --> 7/16
```

len_unique_percent exaplain how many differentation there is in a series, differently from max_value_count_percent, here we try to understand if our data vary continuously. Infact, here we look at how many time we see different values on the total of the values. 

## Logs

Windows Webext Teams log Path:
```
```
WebRTC Chrome open the link before starting call:

```
chrome://webrtc-internals/
```
Before close the call press on
```
create dump
Download the PeerConnection updates and stats data
```

