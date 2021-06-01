# Zoom and Microsoft Teams PCAP Cleaner

Clean a capture file to make Zoom or Microsoft Teams RTP flows look like standard ones.
To do this, the tool decapsulates the RTP packets from the custom Zoom or Microsoft Teams transport protocol.

The information to create this tool is largely based from [this](https://citizenlab.ca/2020/04/move-fast-roll-your-own-crypto-a-quick-look-at-the-confidentiality-of-zoom-meetings/).

The input can be PCAP or PCAPNG. The output is in PCAP format. The tool can read/write also from the standard input/output.

Prerequisites: you need Python3 with the `dpkt` package installed.

Usage: 
```
zoom_pcap_cleaner [infile] [outfile]
    If outfile is omitted, print on the standard output.
    If infile is omitted, read from the standard input.
```
