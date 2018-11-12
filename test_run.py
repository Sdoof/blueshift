# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 10:33:18 2018

@author: prodipta
"""
import pandas as pd

from blueshift.algorithm.algorithm import TradingAlgorithm, MODE
from blueshift.algorithm.api import get_broker

#start_date = pd.Timestamp('2010-01-04')
#end_date = pd.Timestamp('2018-01-04')
#tz = 'Asia/Calcutta'
#
#brkr = get_broker("backtest",start_date=start_date, end_date=end_date, 
#                    tz=tz,initial_capital=10000)
#
#algo = TradingAlgorithm(broker=brkr, algo="user_algo.py")
#algo.run()


brkr = get_broker("zerodha", config='kite_config.json',
                  tz='Asia/Calcutta', timeout=(8, 45),
                  request_token='R3kbmu8RgxmTVlXNYSTFcUGYttky6wH5',
                  frequency=1)

algo = TradingAlgorithm(broker=brkr, algo="kite_strategy.py",
                        mode = MODE.LIVE)

algo.run()


