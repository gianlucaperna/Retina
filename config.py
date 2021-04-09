
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