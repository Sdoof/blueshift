# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 10:33:18 2018

@author: prodipta
"""
import pandas as pd

from blueshift.algorithm.algorithm import TradingAlgorithm, MODE
from blueshift.algorithm.api import get_broker, register_broker
from blueshift.utils.calendars import get_calendar

start_date = pd.Timestamp('2010-01-04')
end_date = pd.Timestamp('2018-01-04')
tz = 'Asia/Calcutta'

trading_calendar= get_calendar('NSE')


register_broker("backtest",trading_calendar=trading_calendar,
                start_date=start_date,end_date=end_date,
                initial_capital=10000)
brkr = get_broker("backtest")
algo = TradingAlgorithm(broker=brkr, algo="user_algo.py")
algo.run()


#register_broker("zerodha", config='kite_config.json',
#                  tz='Asia/Calcutta', timeout=(8, 45),
#                  request_token='mavqICdDraB1djlL8pMA0wvj5vcsRsKn',
#                  frequency=1)
#
#brkr = get_broker("zerodha")
#
#algo = TradingAlgorithm(broker=brkr, algo="kite_strategy.py",
#                        mode = MODE.LIVE)
#
#algo.run()


