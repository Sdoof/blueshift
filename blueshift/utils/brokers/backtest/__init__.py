# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 13:50:36 2018

@author: prodipta
"""

import pandas as pd

from blueshift.assets.assets import (AssetDBConfiguration,
                                     AssetDBQueryEngineCSV,
                                     DBAssetFinder)
from blueshift.data.dataportal import DBDataPortal
from blueshift.execution.backtester import BackTesterAPI
from blueshift.execution._clock import SimulationClock
from blueshift.utils.exceptions import InitializationError
from blueshift.utils.types import Broker, BrokerType

def make_broker_pack(name, *args, **kwargs):
    auth = None
    trading_calendar = kwargs.get("trading_calendar",None)
    initial_capital = kwargs.get("initial_capital",None)
    frequency = kwargs.get("frequency",1)
    start_date = kwargs.get("start_date", None)
    end_date = kwargs.get("end_date", None)
    
    if not trading_calendar:
        raise InitializationError(msg="no calendar supplied")
        
    if not start_date and not end_date:
        raise InitializationError(msg="start or end dates not supplied")
        
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    
    clock = SimulationClock(trading_calendar,frequency,start_date,
                            end_date)
    
    asset_db_config = AssetDBConfiguration()
    asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
    asset_finder = DBAssetFinder(asset_db_query_engine)
    
    data_portal = DBDataPortal(*args, **kwargs)
    
    broker = BackTesterAPI('blueshift',BrokerType.BACKTESTER, 
                           trading_calendar, initial_capital)  
    
    return auth, asset_finder, data_portal, broker, clock

def BackTest(*args, **kwargs):
    name = kwargs.pop("name","blueshift")
    auth, asset_finder, data_portal, broker, clock =\
            make_broker_pack(name, *args, **kwargs)
                
    backtest = Broker(auth, asset_finder, data_portal, broker, clock)
    
    return backtest

__all__ = [DBAssetFinder,
           DBDataPortal,
           BackTesterAPI,
           BackTest,
           SimulationClock]