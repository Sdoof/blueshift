# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:27:45 2018

@author: prodipta
"""

import pandas as pd

from kiteconnect.exceptions import KiteException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI, BrokerType
from blueshift.utils.brokers.zerodha.kiteauth import (KiteAuth,
                                                      KiteConnect3,
                                                      kite_calendar)
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling)

class BackTesterAPI(AbstractBrokerAPI):
    
    def __init__(self, 
                 name:str="kite", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=kite_calendar,
                 **kwargs):
        
        check_input(BackTesterAPI.__init__, locals())
        super(BackTesterAPI, self).__init__(name, broker_type, calendar,
                                             **kwargs)
        self._auth = kwargs("auth",None)
        self._broker = kwargs("broker",None)
        
        if not self._api:
            if not self._auth:
                msg = "authentication and API missing"
                handling = ExceptionHandling.TERMINATE
                raise AuthenticationError(msg=msg, handling=handling)
            
            if not isinstance(self._auth, KiteAuth):
                msg = "invalid authentication object"
                handling = ExceptionHandling.TERMINATE
                raise AuthenticationError(msg=msg, handling=handling)
                
            self._api = self._auth._api
            
        if not isinstance(self._api, KiteConnect3):
            msg = "invalid kite API object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
        