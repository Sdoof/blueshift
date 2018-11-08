# -*- coding: utf-8 -*-
"""
Created on Fri Oct 26 10:42:50 2018

@author: prodipta
"""
import pandas as pd
import random

from blueshift.utils.brokers.zerodha import (KiteAuth,
                                             KiteAssetFinder,
                                             KiteRestData,
                                             KiteBroker)

kite_auth = KiteAuth(config='kite_config.json', tz='Asia/Calcutta',
                     timeout=(8, 45))
kite_auth.login(request_token='IQI0Efq82lHHRu9Pw1Ihwtg3xgyTGiX6')
kite_asset_finder = KiteAssetFinder(auth=kite_auth)
kite_data = KiteRestData(auth=kite_auth)
kite_broker = KiteBroker(auth = kite_auth,
                         asset_finder=kite_asset_finder)

# test asset creation
tickers = kite_asset_finder._instruments_list.tradingsymbol
n = len(tickers)-1
assets = []

t1 = pd.Timestamp.now()
for i in range(1000):
    sym = tickers.iloc[random.randint(0, n)]
    asset = kite_asset_finder.symbol_to_asset(sym)
    if asset is None:
        print(f"failed to create asset for {sym}")
        continue
    assets.append(asset)

t2 = pd.Timestamp.now()
time_elapsed = (t2-t1).total_seconds()*1000
print(f"time elapsed {time_elapsed}")

# test data fetching
syms = ['ACC','NIFTY-I','NIFTY-II','USDINR-II','GBPINR18DECFUT']
assets = [kite_asset_finder.symbol_to_asset(sym) for sym in syms]
df = kite_data.current(assets, ['open','close', 'last', 'volume'])


# test history function
syms = ['ACC','INFY','NIFTY18DEC10900CE','NIFTY-I','NIFTY-II',
        'NIFTY18DEC10900PE','NIFTY18DEC11000CE','USDINR-II',
        'GBPINR18DECFUT','BANKNIFTY-I','NIFTY18DEC12000CE',
        'BANKNIFTY-II']

assets = [kite_asset_finder.symbol_to_asset(sym) for sym in syms]
t1 = pd.Timestamp.now()
df = kite_data.history(assets,['open','close','volume'],60,"1d")
t2 = pd.Timestamp.now()
time_elapsed = (t2-t1).total_seconds()*1000
print(f"time elapsed {time_elapsed}")

for asset in assets:
    try:
        print(len(df.loc[asset]))
    except KeyError:
        print(f'not found {asset.symbol}')
        
        
# test order and position fetching
positions = kite_broker.positions
orders = kite_broker.orders
open_orders = kite_broker.open_orders
