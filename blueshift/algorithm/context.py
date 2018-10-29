# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 23:25:53 2018

@author: prodipta
"""
import numpy as np
import pandas as pd


from blueshift.blotter._perf import (Performance, 
                                     BASE_METRICS, 
                                     DAILY_METRICS)
from blueshift.utils.exceptions import (InitializationError,
                                        ValidationError,
                                        ExceptionHandling)
from blueshift.assets.assets import AssetFinder
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.data.dataportal import DataPortal
from blueshift.execution._clock import SimulationClock
from blueshift.execution.clock import RealtimeClock
from blueshift.configs.defaults import (default_asset_finder,
                                        default_data_portal,
                                        default_broker,
                                        default_clock)


class AlgoContext(object):
    
    def __init__(self, *args, **kwargs):
        # name of the context. Good practice is to match the algo name
        # this will be used to tag orders where supported
        self._name = kwargs.get("name","")
        self.__timestamp = None
        
        # get the objects if supplied, else create the defaults
        self.__algo = kwargs.get("algo", "")
        self.__performance = kwargs.get("perf",None)
        
        self.__clock = kwargs.get("clock", default_clock())
        if not isinstance(self.__clock, (SimulationClock,RealtimeClock)):
            raise ValidationError(msg="data portal supplied is of "
                                  "illegal type")
            
        self.__asset_finder = kwargs.get("asset_finder", 
                                         default_asset_finder())
        if not isinstance(self.__asset_finder, AssetFinder):
            raise ValidationError(msg="asset finder supplied is of "
                                  "illegal type")
        
        capital = kwargs.get("capital", None)
        self.__broker_api = kwargs.get("broker",
                                       default_broker(capital))        
        if not isinstance(self.__broker_api, AbstractBrokerAPI):
            raise
        self.__calendar = self.__broker_api._calendar
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
            
        self.__data_portal = kwargs.get("data_portal",
                                        default_data_portal())
        if not isinstance(self.__data_portal, DataPortal):
            raise ValidationError(msg="data portal supplied is of "
                                  "illegal type")
        
        # in case the algo is part of a Algostack
        self.parent = kwargs.get("parent",None)
        if self.parent:
            if not isinstance(self.parent, AlgoContext):
                raise InitializationError(msg="context parent is of "
                                          "invalid type")
        
    def __str__(self):
        return "Context: name:%s, broker:%s" % (self.name,
                                                self.broker)
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def name(self):
        return self._name
    
    @property
    def broker(self):
        return self.__broker_api
    
    @property
    def account(self):
        return self.__account
    
    @property
    def portfolio(self):
        return self.__portfolio
    
    @property
    def performance(self):
        perf = self.__performance.get_last_perf()
        return {DAILY_METRICS[index[0]]:value for index, value in 
                np.ndenumerate(perf)}
    
    @property
    def trading_calendar(self):
        return self.__calendar
    
    @property
    def pnls(self):
        pnl = self.__performance.get_last_pnl()
        return {BASE_METRICS[index[0]]:value for index, value in 
                np.ndenumerate(pnl)}
        
    @property
    def timestamp(self):
        return self.__timestamp
    
    def set_timestamp(self, timestamp):
        # no validation check for the sake of speed!
        self.__timestamp = timestamp
    
    @property
    def algo(self):
        return self.__algo
    
    @property
    def asset_finder(self):
        return self.__asset_finder
    
    @property
    def data_portal(self):
        return self.__data_portal
    
    @property
    def clock(self):
        return self.__clock
    
    def past_performance(self, lookback):
        idx, values = self.__performance.get_past_perfs(lookback)
        perf = pd.DataFrame(values,columns=DAILY_METRICS,
                            index=idx)
        
        perf.index = pd.to_datetime(perf.index).\
                tz_localize('Etc/UTC').\
                tz_convert(self.__calendar.tz)
        return perf
    
    def past_pnls(self, lookback):
        idx, values = self.__performance.get_past_pnls(lookback)
        pnls = pd.DataFrame(values,columns=BASE_METRICS,
                            index=idx)
        
        pnls.index = pd.to_datetime(pnls.index).\
                tz_localize('Etc/UTC').\
                tz_convert(self.__calendar.tz)
        return pnls
        
    def save(self, strpath):
        # TODO: finalize serialization
        pass
    
    @classmethod
    def read(cls, strpath, timestamp):
        # TODO: finalize reading from serialized version
        pass
    
    def update(self, *args, **kwargs):
        new_clock = kwargs.get("clock", None)
        if not isinstance(new_clock, (SimulationClock,RealtimeClock)):
            raise ValidationError(msg="clock supplied is of "
                                  "illegal type", 
                                  handling=ExceptionHandling.IGNORE)
        self.__clock = new_clock
        
        new_asset_finder = kwargs.get("asset_finder", None)
        if not isinstance(new_asset_finder, AssetFinder):
            raise ValidationError(msg="asset finder supplied is of "
                                  "illegal type", 
                                  handling=ExceptionHandling.IGNORE)
        self.__asset_finder = new_asset_finder
        
        new_broker_api = kwargs.get("broker", None)
        if not isinstance(new_broker_api, AbstractBrokerAPI):
            raise ValidationError(msg="broker api supplied is of "
                                  "illegal type", 
                                  handling=ExceptionHandling.IGNORE)
        self.__broker_api = new_broker_api
        self.__calendar = self.__broker_api.calendar
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
            
        new_data_portal = kwargs.get("data_portal", None)
        if not isinstance(new_data_portal, DataPortal):
            raise ValidationError(msg="data portal supplied is of "
                                  "illegal type", 
                                  handling=ExceptionHandling.IGNORE)
        self.__data_portal = new_data_portal
        
        new_parent = kwargs.get("parent",None)
        if new_parent:
            if not isinstance(self.parent, AlgoContext):
                raise ValidationError(msg="context parent is of "
                                          "invalid type",
                                    handling=ExceptionHandling.IGNORE)
        self.parent = new_parent
    
    def set_up(self, *args, **kwargs):
        '''
            Setting up the context before the algo start, or at any 
            re-start, initializes timestamp and performance object
        '''
        timestamp = kwargs.get("timestamp",None)
        if not timestamp:
            raise InitializationError(msg="timestamp required"
                                      " to initialize"
                                      " context")
        if not isinstance(timestamp, pd.Timestamp):
            raise ValidationError(msg="timestamp must be of type"
                                  " Timestamp")
        self.__timestamp = timestamp

        if not self.__performance:
            self.__performance = Performance(self.__account, 
                                             self.__timestamp.value)
        if not isinstance(self.__performance, Performance):
            raise ValidationError(msg="performance must be of type"
                                  " Performance")
            
    def EOD_update(self, timestamp):
        '''
            Called end of day at after trading hours BAR. No validation
        '''
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
        self.__performance.update_perfs(self.__account,timestamp.value)
        
    def BAR_update(self, timestamp):
        '''
            Called end of every trading BAR. No validation here
        '''
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
        self.__performance.update_pnls(self.__account,timestamp.value)
        
    def SOB_update(self, timestamp):
        '''
            Called at start of the day. No validation.
        '''
        pass