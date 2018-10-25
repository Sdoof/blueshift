# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 10:04:34 2018

@author: prodipta
"""
import json
import pandas as pd

from kiteconnect import KiteConnect

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.configs.authentications import TokenAuth
from blueshift.data.rest_data import RESTData
from blueshift.utils.exceptions import AuthenticationError, ExceptionHandling
from blueshift.utils.decorators import api_rate_limit

class KiteConnect3(KiteConnect):
    def __str__(self):
        return "Kite Connect API v3.0"
    
    def __repr__(self):
        return self.__str__()
    
kite_calendar = TradingCalendar('NSE',tz='Asia/Calcutta',opens=(9,15,0), 
                                closes=(15,30,0))

class KiteAuth(TokenAuth):
    
    def __init__(self, *args, **kwargs):
        config = None
        config_file = kwargs.pop('config',None)
        if config_file:
            try:
                with open(config_file) as fp:
                    config = json.load(fp)
            except:
                pass
        
        if config:
            kwargs = {**config, **kwargs}
        
        if not kwargs.get('name',None):
            kwargs['name'] = 'kite'
        super(KiteAuth, self).__init__(*args, **kwargs)
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
        auth_token = kwargs.get("auth_token",None)
        if auth_token:
            self.set_token(auth_token)
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
            self._auth_token = self._access_token
        except Exception as e:
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
        except Exception as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise AuthenticationError(msg=msg, handling=handling)


class KiteRestData(RESTData):
    
    def __init__(self, *args, **kwargs):
        config = None
        config_file = kwargs.pop('config',None)
        if config_file:
            try:
                with open(config_file) as fp:
                    config = json.load(fp)
            except:
                pass
        
        if config:
            kwargs = {**config, **kwargs}
        
        super(KiteRestData, self).__init__(*args, **kwargs)
        
        if not self._api:
            if not self._auth:
                msg = "authentican missing"
                handling = ExceptionHandling.WARN
                raise AuthenticationError(msg=msg, handling=handling)
            self._api = self._auth._api
            
        if not self._max_instruments:
            self._max_instruments = 400
        
        if not self._rate_limit:
            self._rate_limit = 40 # Kite has 60, we are conservative 
            self._rate_limit_count = self._rate_limit
            
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
            
        if not self._max_instruments:
            self._max_instruments = 400
            
        self._instruments_list = kwargs.get("instruments_list",None)
        self._instrument_list_valid_till = None
        self.update_instrument_list(self._instruments_list)
        
        self._rate_limit_since = None # we reset this value on first call
        self.max_instruments = 400 # max allowed at present is 500
        
    def update_instrument_list(self, instruments_list=None):
        if instruments_list is not None:
            self._instruments_list = instruments_list
        else:
            try:
                self._instruments_list = pd.DataFrame(self._api.\
                                                      instruments())
            except Exception as e:
                print(e)
                raise e
        
        t = pd.Timestamp.now(tz=self.tz) + pd.Timedelta(days=1)
        self._instrument_list_valid_till = t.normalize()
        
    @api_rate_limit
    def current(assets, fields):
        print("current")
        
    @api_rate_limit
    def history(assets, fields):
        print("current")
            
kite_auth = KiteAuth(config='kite_config.json',tz='Asia/Calcutta',
                     timeout=(8,45))
try:
    kite_auth.login(auth_token="UswRpHI6p7u9ggecPLi7VdoR6jbqgkau")
except Exception as e:
    print(e)
    print(e.handling)
            
kite_data = KiteRestData(auth=kite_auth, 
                         instruments_list=instruments_list)
            

for i in range(200):
    kite_data.current(1,2)
            