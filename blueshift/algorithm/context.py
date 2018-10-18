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
from blueshift.utils.exceptions import InitializationError
from blueshift.assets.assets import (AssetDBConfiguration,
                                     AssetDBQueryEngineCSV,
                                     AssetFinder)


class AlgoContext(object):
    
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name",None)
        self.__account = None
        self.__performance = None
        self.__portfolio = None
        self.__broker_api = None
        self.__calendar = None
        
        self.__broker_initialized = False
        self.__data_initialized = False
        
        self.__algo = None
        self.__timestamp = None
        self.__asset_finder = None
        self.__data = None
        
    @property
    def name(self):
        return self._name
    
    @property
    def broker(self):
        return str(self.__broker_api)
    
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
    
    @property
    def algo(self):
        return self.__algo
    
    @property
    def asset_finder(self):
        return self.__asset_finder
    
    @property
    def data(self):
        return self.__data
    
    def past_performance(self, lookback):
        idx, values = self.__performance.get_past_perfs(lookback)
        perf = pd.DataFrame(values,columns=DAILY_METRICS,
                            index=idx)
        
        perf.index = pd.to_datetime(perf.index).tz_localize('Etc/UTC').tz_convert(self.__calendar.tz)
        return perf
    
    def past_pnls(self, lookback):
        idx, values = self.__performance.get_past_pnls(lookback)
        pnls = pd.DataFrame(values,columns=BASE_METRICS,
                            index=idx)
        
        pnls.index = pd.to_datetime(pnls.index).tz_localize('Etc/UTC').tz_convert(self.__calendar.tz)
        return pnls
    
    def broker_context(self, broker_api):
        self.__broker_api = broker_api
        self.__broker_initialized = True
    
    def set_up(self, *args, **kwargs):
        '''
            Setting up the context before the algo start, or at any 
            re-start
        '''
        timestamp = kwargs.get("timestamp",None)
        if not timestamp:
            raise InitializationError(msg="timestamp required to initialize"
                                      "context")
        self.timestamp = timestamp
        
        # check for saved context, if found laod and return
        saved_context = kwargs.get("context_path",None)
        if saved_context:
            self.read_context(saved_context, timestamp)
            return
        
        # asset finder
        asset_db_config = AssetDBConfiguration()
        asset_db_query_engine = AssetDBQueryEngineCSV(asset_db_config)
        self.__asset_finder = AssetFinder(asset_db_query_engine)
        
        # set up the API object
        broker_api = kwargs.get("broker",None)
        if not broker_api:
            raise InitializationError(msg="broker details required to "
                                      "initialize context")
        self.broker_context(broker_api)
        self.__calendar = self.__broker_api.broker.calendar
            
        
        self.parent = kwargs.get("parent",None)
        if self.parent:
            if type(self.parent) != type(self):
                raise InitializationError(msg="context parent is of "
                                          "invalid type")
        
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
        
        self.__performance = kwargs.get("performance",None)
        if not self.__performance:
            self.__performance = Performance(self.__account, self.timestamp.value)
            
        self.__data_initialized = True
            
    def EOD_update(self, timestamp):
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
        self.__performance.update_perfs(self.__account,timestamp.value)
        
    def BAR_update(self, timestamp):
        self.__account = self.__broker_api.account()
        self.__portfolio = self.__broker_api.positions()
        self.__performance.update_pnls(self.__account,timestamp.value)
        
    def SOB_update(self, timestamp):
        pass