# Retina (Real-Time Analyzer)

Analyse Real Time Communications traffic (RTC) with this command-line tool written exclusively in Python.
Given one or more packet captures of RTC traffic, Retina produces a rich log of statistics on observed streams.
It is highly configurable and gives the possibility to choose the types of statistics to output, the desired temporal aggregation (ex. per-second statistsics) as well as many other parameters. If the packet capture comes along with application logs, it can match the data and enrich its output with application and QoE-related statistics. Retina uses multiprocessing if given more than one captures to process.


For more information about this Readme file and the tool please write to:
[gianluca.perna@polito.it](mailto:gianluca.perna@polito.it)
[dena.markudova@polito.it](mailto:dena.markudova@polito.it)

## Table of Contents
<!---
Done with https://github.com/ekalinin/github-markdown-toc )
-->
   * [Installation](#installation)
   * [Usage](#usage)
   * [Modes](#modes)
   * [Arguments](#arguments)
   * [Functionalities](#functionalities)
   * [Configuration](#configuration)
   * [Retreive Logs](#logs)
   * [Plot](#plot)

## Installation

Simply clone this repo.
Also the installation of tshark is required:
```
 sudo apt-get install -y tshark
```

The tool uses a lot of libraries like numpy, matplotlib etc.
You can easily install all the requirements running:
```
pip3 install -r requirements.txt
```

Retina is also available as a dockerized version, compiled for *arm* and *amd* systems, you can install it by running this command:

```
docker pull gianlucapolito/retina:v2
```

## Usage
This is a `command line tool` with many functionalities controlled by arguments.

An example of basic usage is:
```
python3 Retina.py -d test/webex -so webex -log test/log/webex -ta 1000 2000
```
where Retina.py is the *main* and the rest are arguments.
The outputs will be `.csv` files with the `same name` of the pcaps.
In this case we got two output files that are pcap1_1000s.csv and pcap2_2000s.csv

To run the docker, use:
```
docker run -v /Users/gianlucaperna/Desktop/Debug_webex:/Debug_webex retina -d /Debug_webex -log /Debug_webex -so webex -ta 2000
```
where after -v you specify the folder to mount, then you specify all the parameters that are explained in the section [Arguments](#arguments).

  
#### Basic arguments

The most important arguments are:
* `directory (-d)`: master directory which contains all pcaps that we want to elaborate.
* `log (-log)`: the path for the application log files (.txt for Webex and .log for webRTC). Note that the log files MUST have the same name of their corresponding pcaps.
* `software (-so)`: which software will be analysed [webex, webrtc, zoom, msteams, skype, other]. When passing the -log parameter, (for Webex and webRTC) it is important to correctly specify the -so argument.
* `plot (-p)`: which type of plots to create [dynamic, static]
* `time_aggregation (-ta)`: specify the time aggregation for the data. Values are in **ms**. ex. 1000 for time aggregation of 1s.
* `join (-j)`: Join all .csv files into one dataset, if elaborating many pcaps.
* `loss rate (-lr)`: maximum value of loss rate that a flow can have to be considered. If the value computed on a flow is over the loss rate, the flow will be discarded. Default=0.2 [0-1]
* `drop_packet (-dp)`: minimum number of packet that should be present in the flow for it to be considered. Default=100
* `drop_time (-dp_time)`: minimum duration of flow for it to be considered. Default=20
* `port (-po)`: port numbers for the specific RTC application. Retina uses a heuristic to understand on which port there is RTP traffic. If you need, you can specify the ports instead.
* `process (-proc)`: maximum number of process that the tool is allowed to use. This is to avoid consuming all CPU. If the number of pcaps is larger than the number of process, the tool will use as many processes as the number of pcaps.
* `threshold (-th)`: If you don't provide a -log file Retina can try to label your data in Audio/Video using an heuristic based on mean length of the packets in a flow. Default=400

## Per-flow log

* `general_log (-gl)`: Create a smaller per-flow log (general log)
* `output_gl (-out_gl)`: Specify the path for the per-flow log
* `internal_mask (-im)`: Specify the internal mask of the network to set the direction of the flows. Default="192.168." for outbound flows

## Functionalities

We show the basic scheme of Retina on Figure 1.
It needs one or more RTP traffic pcap files as input and outputs various statistic logs and plots:

1) .csv with statistics calculated for [time aggregation] ms for each flow
2) Per-flow log. This log is inspired by **Tstat** ([link tstat]), a tool for network traffic monitoring. 
3) Static plots (.png files) or responsive plots (.html files) on various flow characteristics like bitrate, number of packets, packet interarrival etc.

Retina is able to recognize 5 main class using the log, that are:

1) HQ class (video >= 720p)
2) MQ class (video 360 <= MQ < 720p)
3) LQ class (video LQ < 360p)
4) Audio
5) ScreenSharing

In case of Webex application we have also the FEC [RFC2733](https://www.rfc-editor.org/rfc/rfc2733) flow that are always audio/video flow but with the purpose of recover error.

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

#### How modify config.py file
If you are intersted in only some statistics, you can easly speed up the code deleting all that you don't need.
For example, imagine that we want only the percentile 60 for each stats, we can write in the config.py file this:
```
percentiles = ["p60"]
```
In this way we avoid to compute all the other percentiles.


## Retreive Logs

Windows Webext Teams log Path:
```
C:\Users\{name_user}\AppData\Local\CiscoSpark\media\calls
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

## Plot

Retina is able to produce in output different kind of plots, we can summarize them in 3 categories:
- static
- dyniamic
- interactive

In particular, when in Retina you use **-p** parameters, you then have to specify on of the three arguments written above.
With **-p static** you receive in output a folder per each flow inside the pcap, in which is stored different **.png** pictures, desbring different stats of the flow. In particular you will have chart for:
- bitrate
- packet length
- rtp timestamp
- interarrival

If you specify instead **-p dynamic** you got the same as the static, but, in different **html** files for more responsive experience.

In the last case, that is **-p interactive** you got a **.pickle** file that you will upload on a dedicate dashboard that you can found at this link: https://share.streamlit.io/gianlucapolito/retina-dashboard/main/dashboard.py .
The last case is strongly suggested if you are interested in analyze your traffic in a really cool and responsive way.
