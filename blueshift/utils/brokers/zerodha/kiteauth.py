# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:27:37 2018

@author: prodipta
"""

import json
import pandas as pd

from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.authentications import TokenAuth
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling)
from blueshift.utils.decorators import singleton
from blueshift.utils.mixins import APIRateLimitMixin

# pylint: disable=invalid-name, missing-docstring
kite_calendar = TradingCalendar('NSE',tz='Asia/Calcutta',opens=(9,15,0), 
                                closes=(15,30,0))



@singleton
class KiteConnect3(APIRateLimitMixin, KiteConnect):
    '''
        kiteconnect modified to force a singleton (and to print pretty).
    '''
    def __init__(self, *args, **kwargs):
        # pylint: disable=bad-super-call
        #super(self.__class__, self).__init__(*args, **kwargs)
        api_key = kwargs.get('api_key',None)
        access_token = kwargs.get('access_token',None)
        root = kwargs.get('root',None)
        debug = kwargs.get('debug',False)
        timeout = kwargs.get('timeout',None)
        proxies = kwargs.get('proxies',None)
        pool = kwargs.get('pool',None)
        disable_ssl = kwargs.get('disable_ssl',False)
        
        KiteConnect.__init__(self, api_key, access_token, root,
                             debug, timeout, proxies, pool,
                             disable_ssl)
        APIRateLimitMixin.__init__(self, *args, **kwargs)
        
        # max instruments that can be queried at one call
        self._max_instruments = kwargs.get("max_instruments",None)
        
        if not self._rate_limit:
            # Kite has 3 per sec, we are conservative
            self._rate_limit = 2
            self._rate_limit_count = self._rate_limit
            
        if not self._rate_period:
            self._rate_period = 1
        
        if not self._max_instruments:
            # max allowed is 500 for current, and one for history
            self._max_instruments = 50
            
        # we reset this value on first call
        self._rate_limit_since = None 
        
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
            
        holidays = kwargs.get("holidays",None)
        if holidays:
            try:
                dts = pd.read_csv(holidays, parse_dates=True)
                dts = pd.to_datetime(dts.iloc[:,0].tolist())
                self._trading_calendar.add_holidays(dts)
            except FileNotFoundError:
                pass
    
    def __str__(self):
        return "Kite Connect API v3.0"
    
    def __repr__(self):
        return self.__str__()
    
    
    
    

@singleton
class KiteAuth(TokenAuth):
    '''
        The authentication class handles the user login/ logout and 
        managing of the sessions validity etc. It creates and validate
        the underlying API object which shall be passed around for any
        subsequent interaction.
    '''
    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        config = None
        config_file = kwargs.pop('config',None)
        if config_file:
            try:
                with open(config_file) as fp:
                    config = json.load(fp)
            except FileNotFoundError:
                pass
        
        if config:
            kwargs = {**config, **kwargs}
        
        if not kwargs.get('name',None):
            kwargs['name'] = 'kite'
        
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(*args, **kwargs)
        self._api_key = kwargs.get('api_key',None)
        self._api_secret = kwargs.get('api_secret',None)
        self._user_id = kwargs.get('id',None)
        self._request_token = kwargs.get('reuest_token',None)
        
        self._access_token = self.auth_token
        self._api = KiteConnect3(api_key=self._api_key,
                                 holidays=kwargs.get("holidays",None),
                                 rate_period=kwargs.get("rate_period",None),
                                 rate_limit=kwargs.get("rate_limit",None))
        self._trading_calendar = self._api._trading_calendar
        
    @property
    def api_key(self):
        return self._api_key
    
    @property
    def api_secret(self):
        return self._api_secret
    
    @property
    def user_id(self):
        return self._user_id
    
    def login(self, *args, **kwargs):
        '''
            Set access token if available. Else do an API call to obtain
            an access token. If it fails, it is catastrophic. We cannot
            continue and raise TERMINATE level error.
        '''
        auth_token = kwargs.pop("auth_token",None)
        if auth_token:
            self.set_token(auth_token, *args, **kwargs)
            self._access_token = auth_token
            self._api.set_access_token(auth_token)
            return
        
        request_token = kwargs.get("request_token",None)
        if not request_token:
            msg = "no authentication or request token supplied for login"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._request_token = request_token
        try:
            data = self._api.generate_session(self._request_token, 
                                             api_secret=self._api_secret)
            self._api.set_access_token(data["access_token"])
            self._access_token = data["access_token"]
            self.set_token(self._access_token)
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
    def logout(self):
        '''
            API call to logout. If it fails, it is not catastrophic. We
            just warn about it.
        '''
        try:
            self._api.invalidate_access_token()
            self._access_token = self._auth_token = None
            self._last_login = self._valid_till = None
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise AuthenticationError(msg=msg, handling=handling)
