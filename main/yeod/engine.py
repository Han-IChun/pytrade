#!/usr/bin/env python2.7

import os, sys
from datetime import date
import time
import urllib2
import pandas as pd
import numpy as np
from pyalgotrade.tools import yahoofinance
from urllib2 import  HTTPError
import multiprocessing
import finsymbols
local_path = os.path.dirname(__file__)

def doreg(df):
    df["open"] = df["open"] * df["adjclose"]/df["close"]
    df["high"] = df["high"] * df["adjclose"]/df["close"]
    df["low"]  = df["low"]   * df["adjclose"]/df["close"]
    df["close"]= df["close"] * df["adjclose"]/df["close"]
    df["volume"] = df["volume"] * df["adjclose"]/df["close"]
    return df
def download_csv(instrument):
    url = "http://chart.finance.yahoo.com/table.csv?s=%s&ignore=.csv" % (instrument)
    print url
    f = urllib2.urlopen(url)

    buff = f.read()
    f.close()
    # Remove the BOM
    while not buff[0].isalnum():
        buff = buff[1:]
    return buff

def _single(symbol, data_dir):
    retry = 3
    eod = None
    while retry > 0:
        try:
            #eod = yahoofinance.download_csv(symbol, date(1970,01,01),date(2099,01,01), 'd')
            eod = download_csv(symbol)
            fname = os.path.join(data_dir,symbol+".csv")
            with open(fname + ".org", 'w') as fout:
                print >> fout, eod
        except Exception,ex:
            if isinstance(ex, HTTPError) and int(ex.getcode()) == 404:
                print symbol, "404, just break"
                break
            print symbol, Exception, ":", ex, " ", ex
            time.sleep(6)
            retry -=1
            continue
        break

    if not eod is None:
        names = ["date", 'open', 'high', 'low', 'close', 'volume', 'adjclose']
        df = pd.read_csv(fname+".org", header=None, names=names, dtype={"volume":np.float64}, skiprows =1, parse_dates=True)
        df= df.dropna()
        df = df.sort(["date"], ascending=True)
        df = doreg(df)
        df.to_csv(fname)
        print df.head()
        return len(eod)
    return -1

def work(syms,data_dir, processes):
    syms.sort()
    pool = multiprocessing.Pool(processes = int(processes) )
    result = {}
    for sym in syms:
        if sym.find('^') > 0:
            continue
        if sym.find('.') > 0:
            continue
        if os.path.isfile(os.path.join(data_dir, sym + ".csv")):
            continue
        if processes <= 1:
            _single(sym, data_dir)
        else:
            pool.apply_async(_single, (sym, data_dir))
    pool.close()
    pool.join()
    succ = 0; fail = 0
    for each in result:
        if result[each] > 0: succ += 1
        else: fail += 1
    return fail
