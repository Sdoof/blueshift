# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 10:33:18 2018

@author: prodipta
"""
import pandas as pd

from blueshift.algorithm.algorithm import TradingAlgorithm, MODE
from blueshift.execution.clock import RealtimeClock
from blueshift.algorithm.api import get_broker

start_date = pd.Timestamp('2010-01-04')
end_date = pd.Timestamp('2018-01-04')
tz = 'Asia/Calcutta'

brkr = get_broker("backtest",start_date=start_date, end_date=end_date, 
                    tz=tz,initial_capital=10000)

algo = TradingAlgorithm(broker=brkr, algo="user_algo.py")
algo.back_test_run()


from blueshift.utils.brokers.zerodha import (KiteAuth,
                                             KiteAssetFinder,
                                             KiteRestData,
                                             KiteBroker)

kite_auth = KiteAuth(config='kite_config.json', tz='Asia/Calcutta',
                     timeout=(8, 45))
kite_auth.login(request_token='koV1lSFax3TZnsBjO5Kr9s1b58UNrCNo')
kite_asset_finder = KiteAssetFinder(auth=kite_auth)
kite_data = KiteRestData(auth=kite_auth)
kite_broker = KiteBroker(auth = kite_auth,
                         asset_finder=kite_asset_finder)
clock = RealtimeClock(kite_data._trading_calendar,5)

live_algo = TradingAlgorithm(capital=1000.0,
                             algo="kite_strategy.py",
                             clock = clock,
                             data_portal = kite_data,
                             broker = kite_broker,
                             asset_finder = kite_asset_finder,
                             mode = MODE.LIVE)
live_algo.live_run()


