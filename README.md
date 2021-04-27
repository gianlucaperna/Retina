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
   * [Examples](#examples)

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
  
## Arguments

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

