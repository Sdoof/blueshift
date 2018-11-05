# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:27:37 2018

@author: prodipta
"""

import json
import time
import pandas as pd

from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.configs.authentications import TokenAuth
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling)
from blueshift.utils.decorators import singleton

# pylint: disable=invalid-name, missing-docstring
kite_calendar = TradingCalendar('NSE',tz='Asia/Calcutta',opens=(9,15,0), 
                                closes=(15,30,0))



@singleton
class KiteConnect3(KiteConnect):
    '''
        kiteconnect modified to force a singleton (and to print pretty).
    '''
    def __init__(self, *args, **kwargs):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(*args, **kwargs)
        
        # store login_url bound method
        
        self._trading_calendar = kwargs.get("trading_calendar",None)
        # calls per period
        self._rate_limit = kwargs.get("rate_limit",None)
        # limit period in sec
        self._rate_period = kwargs.get("rate_period",1) 
        # running count
        self._rate_limit_count = self._rate_limit
        # time since last limit reset
        self._rate_limit_since = None
        # max instruments that can be queried at one call
        self._max_instruments = kwargs.get("max_instruments",None)
        
        if not self._rate_limit:
            # Kite has 3 per sec, we are conservative
            self._rate_limit = 2
            self._rate_limit_count = self._rate_limit
            
        if not self._max_instruments:
            # max allowed is 500 for current, and one for history
            self._max_instruments = 50
            
        # we reset this value on first call
        self._rate_limit_since = None 
        
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
    
    def __str__(self):
        return "Kite Connect API v3.0"
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def tz(self):
        return self._trading_calendar.tz
    
    @property
    def rate_limit(self):
        return self._rate_limit
    
    @property
    def rate_period(self):
        return self._rate_period
    
    @property
    def rate_limit_since(self):
        return self._rate_limit_since
    
    @rate_limit_since.setter
    def rate_limit_since(self, value):
        self._rate_limit_since = value
    
    @property
    def rate_limit_count(self):
        return self._rate_limit_count
    
    @rate_limit_count.setter
    def rate_limit_count(self, value):
        self._rate_limit_count = max(0, value)
        
    def reset_rate_limits(self):
        '''
            Reset limit consumption and timing
        '''
        self._rate_limit_count = self._rate_limit
        self._rate_limit_since = pd.Timestamp.now(self.tz)
        
    def update_rate_limits(self, rate_limit, rate_period=None):
        '''
            Update rate limits parameters on the fly
        '''
        self._rate_limit = rate_limit
        if rate_period:
            self._rate_period = rate_period
            
    def cool_off(self, mult=1):
        '''
            blocking sleep to cool off rate limit violation
        '''
        time.sleep(self._rate_period*mult)

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
        self._api = KiteConnect3(self._api_key)
        
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
