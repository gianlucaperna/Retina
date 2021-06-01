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
   * [Arguments](#arguments)
   * [Per-flow log](#perflow)
   * [Functionalities](#functionalities)
   * [Configuration](#configuration)
   * [Application log retrieval](#applog)
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

Basic usage with one pcap file:
```
python3 Retina.py -d test/webex/pcap1.pcap -so webex -log test/log/webex -ta 1000
```
where Retina.py is the *main* and the rest are arguments. We take the pcap file *test/webex/pcap1.pcap* and its corresponding log file (of the same name) from the folder *test/log/webex* and create a `.csv` file of statistics with a time aggregation of 1 second (1000ms).
The name of the `.csv` file will be *pcap1_1000s.csv*

Basic usage with multiple pcap files in the same folder and of the same application:
```
python3 Retina.py -d test/webex -so webex -log test/log/webex -ta 1000
```
Say that we have two pcap files pcap1 and pcap2 in the folder *test/webex*. We give as input the directory *test/webex* and the directory of the application log files for the two pcaps (*test/log/webex*).
The outputs will be `.csv` files with the `same name` of the pcaps. In this case Retina will output two files: pcap1_1000s.csv and pcap2_1000s.csv


To run the docker, use:
```
docker run -v /Users/gianlucaperna/Desktop/Debug_webex:/Debug_webex retina -d /Debug_webex -log /Debug_webex -so webex -ta 2000
```
where after -v you specify the folder to mount, then you specify all the parameters that are explained in the section [Arguments](#arguments).

  
#### Arguments

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

#### Per-flow log

* `general_log (-gl)`: Create a smaller per-flow log (general log)
* `output_gl (-out_gl)`: Specify the path for the per-flow log
* `internal_mask (-im)`: Specify the internal mask of the network to set the direction of the flows. Default="192.168." for outbound flows

## Functionalities

We show the basic scheme of Retina on the figure below:
![Scheme image](https://github.com/GianlucaPoliTo/Retina/blob/main/scheme_retina.png)

It takes one or more RTP traffic pcap files as input and outputs various statistic logs and plots:

1) Per time-bin log. A `.csv` file with statistics calculated per [time aggregation] ms for each flow
2) Per-flow log. This log is inspired by [tstat](http://tstat.polito.it/), a tool for network traffic monitoring. 
3) Static plots (.png files) or responsive plots (.html files) on various flow characteristics like bitrate, number of packets, packet interarrival etc.

If an application log is provided to Retina, the per time-bin log contains details on the type of media exchanged by the RTP streams - ex. audio, video, FEC, screen sharing, including the video resolution. To simplify the resolution column we also add a classification into 5 media types:

1) High Quality video (video >= 720p)
2) Medium Quality video (video 360 <= MQ < 720p)
3) Low Quality video (video LQ < 360p)
4) Audio
5) ScreenSharing
6) FEC (Forward Error Correction streams - only for Webex)

If instead, an application log is not provided, Retina uses a heuristic based on the packet size to understand the media types, but can only recognise audio vs. video.


## Configuration
The configuraiton file **config.py** lets you choose the statistics to output. If you don't need all statistics computed, this can significantly speed up the creation of the logs.

Here is the config.py file with all possibile configuration settings:

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

We divide the statistics into three types: standard ones - "common_functions" and "percentiles", where we have all classical stats like mean, standard deviation and so on, and then "special_functions" created by us.
Below we explain the special functions, using the mathematical formulas and some intuition.

Suppose that for the time aggregation (ex. 1s), we have collected this list of values:

```
series = pandas.Series([0,0,0,0,0,1,1,1,1,2,3,4,4,5,5,6])
```

```
def max_min_diff(series):
    return series.max() - series.min()

print(max_min_diff(series)) --> 6
```
This statistic expresses the peak value in a time_aggregation window time by time, in other words, what is the maximum "oscillation" in our time_aggregation.

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
max-min ratio. With max_min_R we try to capture the importance of the *min* on the total results, in a non-linear way. The closer this value is to 1, the more the minimum is close to 0. max_min_R takes values in [0.5, 1].

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
Same as max_min_R, but the opposite ratio

```
def max_value_count_percent(series):
    try:
        return (series.value_counts().iloc[0]) / len(series)
    except Exception as e:
        return 0

print( max_value_count(series) ) --> 5/16
```
max_value_count_percent tells us how "famous" the mode in the time bin. If in the time bin we always have the same value (e.g [1,1,1,1,1,...,1]) the max_value_count_percent reach the maximum that is 1. 

```
def len_unique_percent(series):
    try:
        return len(series.unique()) / len(series)
    except Exception as e:
        return 0
        
print( len_unique_percent(series) ) --> 7/16
```

len_unique_percent is the share of different values over all values in the list. It captures the differentation in a series. 

#### Modifyint the configuration file
If you are intersted in only some statistics, you can easly modify the **config.py** file and speed up Retina.
For example, imagine that we want only the percentile 60 for each stat, we can write:
```
percentiles = ["p60"]
```
In this way we avoid to compute all the other percentiles.


## Application log retrieval

Webex application log path (Windows):
```
C:\Users\{username}\AppData\Local\CiscoSpark\media\calls
```
WebRTC application logs can be found in the browser (Chrome) at the following link:

```
chrome://webrtc-internals/
```
Open the tab when you want to start capturing. Then before closing the call press on:
```
create dump
Download the PeerConnection updates and stats data
```

## Plots

Retina is able to produce in output different kind of plots, we can summarize them in 3 categories:
- static
- dyniamic
- interactive

When using the **-p** plotting parameter, you have to specify on of the three arguments written above.

##### Static plots
With **-p static**  Retina creates a folder Plots and inside a folder per each flow inside the pcap, where it sores different figures in **.png** format, desbring different stats of the flow. If offers charts on bitrate, packet length, rtp timestamp, interarrival times.

##### Dynamic plots
With **-p dynamic** you get the same kind of plots as with the static plotting, but in different **html** files which are responsive (can be zoomed in, flows can be selected/disselected etc.).

##### Interactive plots
With **-p interactive** you get a **.pickle** file that you can upload on a dedicated dashboard that can be found at this link: https://share.streamlit.io/gianlucapolito/retina-dashboard/main/dashboard.py .
This is the recommended way to analyze the traffic.
