# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 13:50:36 2018

@author: prodipta
"""

from types import MappingProxyType as readonlydict
import pandas as pd

from blueshift.assets.assets import (AssetDBConfiguration,
                                     AssetDBQueryEngineCSV,
                                     DBAssetFinder)
from blueshift.data.dataportal import DBDataPortal
from blueshift.execution.broker import BrokerType
from blueshift.execution.backtester import BackTesterAPI
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution._clock import SimulationClock
from blueshift.utils.exceptions import InitializationError
from blueshift.utils.brokers.core import Broker

def make_broker_pack(name, *args, **kwargs):
    auth = None
    
    initial_capital = kwargs.get("initial_capital",None)
    frequency = kwargs.get("frequency",1)
    start_date = kwargs.get("start_date", None)
    end_date = kwargs.get("end_date", None)
    tz = kwargs.get("tz", None)
    holidays = kwargs.get("holidays", None)
    opens = kwargs.get("opens", (9,15,0))
    closes = kwargs.get("closes", (15,30,0))
    
    if start_date and end_date and tz:
        cal = TradingCalendar('IST',tz=tz,opens=opens, 
                          closes=closes)
    else:
        raise InitializationError(msg="no calendar supplied")
        
    if holidays:
        try:
            dts = pd.read_csv(holidays, parse_dates=True)
            dts = pd.to_datetime(dts.iloc[:,0].tolist())
            cal.add_holidays(dts)
        except FileNotFoundError:
            pass
    
    clock = SimulationClock(cal,frequency,start_date,end_date)
    
    asset_db_config = AssetDBConfiguration()
    asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
    asset_finder = DBAssetFinder(asset_db_query_engine)
    
    data_portal = DBDataPortal(*args, **kwargs)
    
    broker = BackTesterAPI('blueshift',BrokerType.BACKTESTER, 
                           cal, initial_capital)  
    
    return auth, asset_finder, data_portal, broker, clock

def BackTest(*args, **kwargs):
    name = kwargs.get("name","blueshift")
    auth, asset_finder, data_portal, broker, clock =\
            make_broker_pack(name, *args, **kwargs)
                
    backtest = Broker(auth, asset_finder, data_portal, broker, clock)
    
    return backtest

__all__ = [DBAssetFinder,
           DBDataPortal,
           BackTesterAPI,
           BackTest,
           SimulationClock]