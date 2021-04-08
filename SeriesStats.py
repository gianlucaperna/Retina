# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 15:16:19 2020

@author: Gianl
"""
import numpy as np
import pandas as pd
from scipy.stats import moment


def moment3(series):
    return moment(series, moment=3)

def moment4(series):
    return moment(series, moment=4)

def packet_loss(series):
    try:
        if not series.empty:
            if max(series)-min(series) > 15000:
                #qui siamo nel cammbio
                series = [i if i >40000 else i+65536 for i in series]
            rx = len(series)
            tx = max(series)-min(series)+1
            return 1-(rx/tx)
        else:
            #print("qui")
            return -1
    except Exception as e:
        print(e)

def sum_check(series):
    if -1 in series:
        return -1
    else:
        return series.sum()

def kbps(series):
    return series.sum()*8/1024

def zeroes_count(series):
    a = series[series == 0].count()
    if np.isnan(a):
        return 0
    else:
        return a

def value_label(series):

    value = series.value_counts()
    try:
        return value.index[0]
    except:
        pass


def p10(x):
    return (x.quantile(0.10)* 0.01)
def p20(x):
    return (x.quantile(0.20)* 0.01)
def p30(x):
    return (x.quantile(0.30)* 0.01)
def p40(x):
    return (x.quantile(0.40)* 0.01)
def p50(x):
    return (x.quantile(0.50)* 0.01)
def p60(x):
    return (x.quantile(0.60)* 0.01)
def p70(x):
    return (x.quantile(0.70)* 0.01)
def p80(x):
    return (x.quantile(0.80)* 0.01)
def p90(x):
    return (x.quantile(0.90)* 0.01)
def p95(x):
    return (x.quantile(0.95)* 0.01)

def p25(x):
    return (x.quantile(0.25)* 0.01)
def p75(x):
    return (x.quantile(0.75)* 0.01)


def max_min_diff(series):
    return series.max() - series.min()

def max_min_R(series):
    try:
        a = abs(series.max())
        b = abs(series.min())
        if a == 0 and b == 0:
            return 0
        else:
            return a/(a+b)
    except Exception as e:
        print(f"Error: min_max_R a= {a}, b= {b}")
        return 0

def min_max_R(series):
    try:
        a = abs(series.max())
        b = abs(series.min())
        if a == 0 and b == 0:
            return 0
        else:
            return b/(a+b)
    except Exception as e:
        print(f"Error: min_max_R a= {a}, b= {b}")
        return 0

def max_value_count_percent(series):
    try:
        return (series.value_counts().iloc[0])/len(series)
    except Exception as e:
        return 0

def len_unique_percent(series):
    try:
        return len(series.unique())/len(series)
    except Exception as e:
        return 0
