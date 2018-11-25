# -*- coding: utf-8 -*-
"""
Created on Sun Nov 25 13:09:36 2018

@author: prodi
"""
import pandas as pd
from os.path import expanduser

from blueshift.configs import BlueShiftConfig
from blueshift.alerts import BlueShiftAlertManager
from blueshift.utils.calendars import TradingCalendar
from blueshift.utils.brokers.backtest import BackTest
from blueshift.algorithm.algorithm import TradingAlgorithm
from blueshift.algorithm.context import AlgoContext

config = BlueShiftConfig(expanduser('~/.blueshift/.blueshift_config.json'))
alert_manager = BlueShiftAlertManager(config=config)

trading_calendar = TradingCalendar(name='NSE-Calendar', 
                                   tz='Asia/Calcutta',
                                   opens=(9,15,0),
                                   closes=(15,30,0),
                                   weekends=(5,6))


backtester = BackTest(name='Blueshift', 
                      start_date=pd.Timestamp("2010-01-04"),
                      end_date=pd.Timestamp("2018-01-04"),
                      frequency=1, trading_calendar=trading_calendar,
                      initial_capital=10000)

context = AlgoContext(name='Blueshift', broker=backtester)

algo = TradingAlgorithm(name="Blueshift", context=context, algo="user_algo.py")

