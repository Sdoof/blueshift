# -*- coding: utf-8 -*-
"""
Created on Fri Oct 26 10:42:50 2018

@author: prodipta
"""
import pandas as pd
import random

from blueshift.utils.brokers.zerodha import (KiteAuth, 
                                             KiteRestData,
                                             KiteAssetFinder)

from blueshift.utils.exceptions import APIRateLimitCoolOff

kite_auth = KiteAuth(config='kite_config.json',tz='Asia/Calcutta',
                     timeout=(8,45))

kite_auth.login(auth_token="oVwrXjnbR5sYXyY9sxXrWpeyx6q5c8ih")

kite_asset_finder = KiteAssetFinder(auth=kite_auth)

kite_data = KiteRestData(auth=kite_auth)
            
# test api rate limit
for i in range(10):
    try:
        kite_data.current(1,2)
        print(i)
    except APIRateLimitCoolOff:
        print(f"rate limit exeeded: sleeping now for {kite_data._rate_period}s")
        kite_data.cool_off()
        
# test asset creation
tickers = kite_asset_finder._instruments_list.tradingsymbol
n = len(tickers)-1
assets = []

t1 = pd.Timestamp.now()
for i in range(1000):
    sym = tickers.iloc[random.randint(0,n)]
    asset = kite_asset_finder.symbol_to_asset(sym)
    if asset is None:
        print(f"failed to create asset for {sym}")
        continue
    assets.append(asset)
    
t2 = pd.Timestamp.now()
time_elapsed = (t2-t1).total_seconds()*1000
print(f"time elapsed {time_elapsed}")

# test data fetching
syms = ['ACC','NIFTY-I','NIFTY-II','USDINR-I','GBPINR18DECFUT']
assets = [kite_asset_finder.symbol_to_asset(sym) for sym in syms]
df = kite_data.current(assets, ['open','close', 'last', 'volume'])



