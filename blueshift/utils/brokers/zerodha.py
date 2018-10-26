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
from blueshift.utils.exceptions import (AuthenticationError, 
                                        ExceptionHandling,
                                        APIException,
                                        BlueShiftException)
from blueshift.utils.decorators import api_rate_limit, singleton, api_retry
from blueshift.assets.assets import BrokerAssetFinder, NoAssetFinder
from blueshift.assets._assets import (Asset, Equity, EquityFutures, Forex,
                                      EquityOption)

'''
    Create the default calendar for kiteconnect. The market is NSE.
'''
kite_calendar = TradingCalendar('NSE',tz='Asia/Calcutta',opens=(9,15,0), 
                                closes=(15,30,0))


@singleton
class KiteConnect3(KiteConnect):
    '''
        kiteconnect modified to force a singleton (and to print pretty).
    '''
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

@singleton
class KiteRestData(RESTData):
    '''
        Encalsulates the RESTful historical and current market data API
        for Zerodha kite. It contains a kite authentication object and
        access the underlying KiteConnect API via that.
    '''
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
        
        super(self.__class__, self).__init__(*args, **kwargs)
        
        if not self._api:
            if not self._auth:
                msg = "authentication and API missing"
                handling = ExceptionHandling.TERMINATE
                raise AuthenticationError(msg=msg, handling=handling)
            self._api = self._auth._api
        
        if not self._rate_limit:
            # Kite has 3 per sec, we are conservative
            self._rate_limit = 3
            self._rate_limit_count = self._rate_limit
            
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
            
        if not self._max_instruments:
            # max allowed at present is 500
            self._max_instruments = 400
        
        self._rate_limit_since = None # we reset this value on first call
        
    @api_rate_limit
    def current(self, assets, fields):
        print("current")
        
    @api_rate_limit
    def history(self, assets, fields):
        print("current")
        
@singleton
class KiteAssetFinder(BrokerAssetFinder):
    '''
        Implements the interface for Zerodha. We download the day's list 
        of tradeable instruments and map it to assets using heuristics. If
        the asset is in our database we populate SID and other fields. 
        Else we mark sid as -1. It is NOT necessary for an asset to be
        in our database for user to be able to query or trade that with
        a broker.
    '''
    EXCHANGES = ['NSE','NFO','CDS']
    AssetConstructorDispatch = {'EQNSE':Equity, 'FUTNFO': EquityFutures,
            'CENFO':EquityOption, 'PENFO':EquityOption, 'FUTCDS': Forex}
    
    def __init__(self, *args, **kwargs):
        '''
            We must have two things - an asset finder that can talk to
            asset database, and an auth object that provides us with the
            underlying API object
        '''
        super(self.__class__, self).__init__(*args, **kwargs)
        self._api = kwargs.get("api",None)
        self._auth = kwargs.get("auth",None)
        self._asset_finder = kwargs.get("asset_finder",None)
        self._trading_calendar = kwargs.get("trading_calendar",None)
        
        if not self._api:
            if not self._auth:
                msg = "authentication and API missing"
                handling = ExceptionHandling.TERMINATE
                raise AuthenticationError(msg=msg, handling=handling)
            self._api = self._auth._api
            
        if not self._asset_finder:
            self._asset_finder = NoAssetFinder()
            
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
            
        self._instruments_list = None
        self._instruments_list_valid_till = None
        
        instruments_list = kwargs.get("instruments_list",None)
        self.update_instruments_list(instruments_list)
        self.filter_instruments_list()
    
    @property
    def tz(self):
        return self._trading_calendar.tz
    
    @property
    def name(self):
        return self._auth._name
    
    def __str__(self):
        return "BrokerAssetFinder:%s" % self.name
    
    def __repr__(self):
        return self.__str__()
    
    @api_retry()
    def update_instruments_list(self, instruments_list=None):
        '''
            Download the instruments list for the day, if not already
            downloaded before.
        '''
        if instruments_list is not None:
            self._instruments_list = instruments_list
            return
        
        if self._instruments_list is not None:
            t = pd.Timestamp.now(tz=self.tz)
            if t < self._instruments_list_valid_till:
                return
        
        try:
            self._instruments_list = pd.DataFrame(self._api.\
                                            instruments())
        except Exception as e:
            msg = str(e)
            handling = ExceptionHandling.TERMINATE
            raise APIException(msg=msg, handling=handling)
        
        t = pd.Timestamp.now(tz=self.tz) + pd.Timedelta(days=1)
        self._instruments_list_valid_till = t.normalize()
        
    def filter_instruments_list(self):
        '''
            Filter instruments that we do not want - the non EQ segment
            cash instruments + single stock options + bond futures and
            indices which are not tradeable.
        '''
        # drop exchanges we do not want
        self._instruments_list = self._instruments_list.loc[
            self._instruments_list.exchange.isin(self.__class__.EXCHANGES)]
        
        # drop the indices, these are not tradeable
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "NSE-INDICES"]
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "INDICES"]
        
        # drop esoteric market segments tickers
        def flag(s):
            splits = s.split("-")
            if len(splits[-1])==2 and splits[-1] != splits[0]:
                return False
            return True
        keep = [flag(s) for s in self._instruments_list.tradingsymbol]
        self._instruments_list = self._instruments_list[keep]
        
        # drop non NIFTY/ BANK
        def single_stock_options(s,t):
            if t == 'NFO-OPT':
                if 'NIFTY' in s:
                    return True
                return False
            return True
        keep = [single_stock_options(r['tradingsymbol'],r['segment']) \
                for i, r in self._instruments_list.iterrows()]
        self._instruments_list = self._instruments_list[keep]
        
        # remove bond futures
        def bond_futures(s, t):
            if t == 'CDS' and s[0].isdigit():
                return False
            return True
        keep = [bond_futures(r['tradingsymbol'],r['exchange']) \
                for i, r in self._instruments_list.iterrows()]
        self._instruments_list = self._instruments_list[keep]
        
        # remove expiries more than 15 weeks from now
        max_expiry = self._instruments_list_valid_till \
                        + pd.Timedelta(weeks=15)
        self._instruments_list.loc[
                self._instruments_list.expiry == "","expiry"] = 0
        expiry = pd.to_datetime(self._instruments_list.expiry.values).\
                                                        tz_localize(self.tz)
        self._instruments_list.expiry = pd.to_datetime(
                self._instruments_list.expiry)
        self._instruments_list = self._instruments_list[
                self._instruments_list.expiry < max_expiry]
        
    def symbol_to_asset(self, tradingsymbol):
        asset = self._asset_finder.lookup_symbol(tradingsymbol)
        if asset is not None:
            return asset
        else:
            sym = tradingsymbol.split(":")[-1]
            base = sym.split("-I")[1]
            if base != sym:
                sym = ""
            row = self._instruments_list.loc[
                    self._instruments_list.tradingsymbol==sym,]
            constructor = self.__class__.AssetConstructorDispatch[\
                    row['instrument_type'] + row['exchange']]
            asset = constructor(-1, )
                
        
    def id_to_asset(self, instrument_id):
        pass
        
    def asset_to_symbol(self, tradingsymbol):
        pass
    
    def asset_to_id(self, tradingsymbol):
        pass
    
        
        
        
        
        