# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
from blueshift.assets import AssetFinder
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.data.dataportal import DataPortal
from blueshift.execution._clock import TradingClock
from blueshift.execution.authentications import AbstractAuth
from blueshift.utils.brokers import Broker
from blueshift.utils.decorators import blueprint
from blueshift.configs import blueshift_run_get_name

@blueprint
class AlgoContext(object):
    '''
        The algorithm context acts as an interface to the input program
        as well as a container for all necessary objects to run an algo.
        The algorithm class implements just the logic of operations. 
        Context encapsulates these objects. Primarily it tracks the data 
        portal, broker api, algo clock, asset finder and authentication.
        It also keeps track of portfolio (positions) and performance.
    '''
    
    def __init__(self, *args, **kwargs):
        # name of the context. Good practice is to match the algo name
        # this will be used to tag orders where supported
        self._name = kwargs.get("name",blueshift_run_get_name())
        self.__timestamp = None
        
        # get the broker object and mark initialize
        self.__broker_initialized = False
        self.__clock = None
        self.__asset_finder = None
        self.__broker_api = None
        self.__data_portal = None
        self.__auth = None
        self.__broker_tuple = None
        self._reset_broker_tuple(*args, **kwargs) # set initialize True
        
        # object to track performance
        self.__tracker_initialized = False
        self.__calendar = None
        self.__account = None
        self.__portfolio = None
        
        # if broker is initialized we can update these
        self._reset_trackers()
            
        # initialize the performance tracker
        # TODO: this perhaps need to go and replaced by _reset_performance
        self.__performance = kwargs.get("perf",None)
        
        # in case the algo is part of a Algostack add parent
        self.parent = None
        self._reset_parent(*args, **kwargs)
        
        self._perf_initialized = False
        
    def __str__(self):
        return "Blueshift Context [name:%s, broker:%s]" % (self.name,
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
    def auth(self):
        return self.__auth
    
    @property
    def account(self):
        return self.__account
    
    @property
    def orders(self):
        return self.__broker_api.orders
    
    @property
    def open_orders(self):
        return self.__broker_api.open_orders
    
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
    
    def _reset_broker_tuple(self, *args, **kwargs):
        '''
            extract broker data
        '''
        broker_tuple = kwargs.get("broker", None)
        
        if broker_tuple:
            self.__clock = broker_tuple.clock
            self.__asset_finder = broker_tuple.asset_finder
            self.__broker_api = broker_tuple.broker
            self.__data_portal = broker_tuple.data_portal
            self.__auth = broker_tuple.auth
            
        else:
            self.__clock = kwargs.get("clock", self.__clock)
            self.__asset_finder = kwargs.get("asset_finder", 
                                             self.__asset_finder)
            self.__broker_api = kwargs.get("api", self.__broker_api)
            self.__data_portal = kwargs.get("data_portal", 
                                            self.__data_portal)
            self.__auth = kwargs.get("auth", self.__auth)
                
        # check for valid object types
        if self.__clock:
            if not isinstance(self.__clock, TradingClock):
                raise ValidationError(msg="clock supplied is of "
                                      "illegal type")            
        if self.__asset_finder:
            if not isinstance(self.__asset_finder, AssetFinder):
                    raise ValidationError(msg="asset finder supplied is of "
                                          "illegal type")
        if self.__data_portal:
            if not isinstance(self.__data_portal, DataPortal):
                    raise ValidationError(msg="data portal supplied is of "
                                          "illegal type")
        if self.__broker_api:
            if not isinstance(self.__broker_api, AbstractBrokerAPI):
                    raise ValidationError(msg="data portal supplied is of "
                                          "illegal type")
        if self.__auth:
            if not isinstance(self.__auth, AbstractAuth):
                raise ValidationError(msg="authentication supplied is of "
                                      "illegal type")
        
        self.__broker_tuple = Broker(self.__auth, self.__asset_finder,
                                     self.__data_portal,
                                     self.__broker_api,
                                     self.__clock, 
                                     self.__broker_api._mode_supports)
        
        # authentication object can be null for backtester
        if self.__asset_finder and self.__data_portal and\
            self.__broker_api and self.__clock:
            self.__broker_initialized = True
            
    def _reset_trackers(self):
        if not self.__broker_initialized:
            return
        
        self.__calendar = self.__broker_api.calendar
        self.__account = self.__broker_api.account
        self.__portfolio = self.__broker_api.positions
        self.__tracker_initialized = True
        
    def _reset_parent(self, *args, **kwargs):
        new_parent = kwargs.get("parent",None)
        
        if new_parent:
            if not isinstance(self.parent, AlgoContext):
                raise ValidationError(msg="context parent is of "
                                          "invalid type",
                                    handling=ExceptionHandling.IGNORE)
        self.parent = new_parent
        
    def _reset_performance(self, *args, **kwargs):
        self.__performance = kwargs.get("perf",None)
        
        if not self.__performance:
            timestamp = kwargs.get("timestamp",None)
            if not timestamp:
                raise InitializationError(msg="timestamp required"
                                      " to initialize"
                                      " context")
            if not isinstance(timestamp, pd.Timestamp):
                raise ValidationError(msg="timestamp must be of type"
                                      " Timestamp")
            if not self.__tracker_initialized:
                raise InitializationError(msg="accounts still not "
                                          "initialized")
            
            self.__performance = Performance(self.__account,
                                             self.__timestamp.value)
            
        if not isinstance(self.__performance, Performance):
            raise InitializationError(msg="accounts still not "
                                          "initialized")
        
        self._perf_initialized = True
    
    def reset(self, *args, **kwargs):
        self._reset_broker_tuple(*args, **kwargs)
        self._reset_trackers()
        self._reset_parent(*args, **kwargs)
    
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

        self._reset_performance(*args, **kwargs)
            
    def is_initialized(self):
       return self.__broker_initialized and self.__tracker_initialized
            
    def EOD_update(self, timestamp):
        '''
            Called end of day at after trading hours BAR. No validation
        '''
        self.__account = self.__broker_api.account
        self.__portfolio = self.__broker_api.positions
        self.__performance.update_perfs(self.__account,timestamp.value)
        self.__performance.update_pnls(self.__account,timestamp.value)
        
    def BAR_update(self, timestamp):
        '''
            Called end of every trading BAR. No validation here
        '''
        self.__account = self.__broker_api.account
        self.__portfolio = self.__broker_api.positions
        self.__performance.update_pnls(self.__account,timestamp.value)
        
    def SOB_update(self, timestamp):
        '''
            Called at start of the day. No validation.
        '''
        pass