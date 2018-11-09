# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 08:43:56 2018

@author: prodipta
"""
import pandas as pd

from blueshift.assets.assets import (AssetDBConfiguration,
                                     AssetDBQueryEngineCSV,
                                     DBAssetFinder)
from blueshift.data.dataportal import DBDataPortal
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution._clock import SimulationClock
from blueshift.execution.broker import BrokerType
from blueshift.execution.backtester import BackTesterAPI


# default start, end dates and capital
tz = 'Asia/Calcutta'
start_dt = pd.Timestamp('2010-01-04',tz=tz)
end_dt = pd.Timestamp('2018-01-04',tz=tz)

# default asset finders
def default_asset_finder():
    asset_db_config = AssetDBConfiguration()
    asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
    asset_finder = DBAssetFinder(asset_db_query_engine)
    return asset_finder

# default data portal
def default_data_portal():
    return DBDataPortal()

# default calendar
def default_calendar():
    return TradingCalendar('IST',tz=tz,opens=(9,15,0), 
                          closes=(15,30,0))
    
# default clock
def default_clock():
    return SimulationClock(default_calendar(),1,start_dt,end_dt)

# default broker
def default_broker(initial_capital):
    return BackTesterAPI('blueshift',BrokerType.BACKTESTER,
                         default_calendar(), initial_capital)    
