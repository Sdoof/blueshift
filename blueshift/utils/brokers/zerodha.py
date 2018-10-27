# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 10:04:34 2018

@author: prodipta
"""
import json
import pandas as pd
from functools import lru_cache

from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

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

LRU_CACHE_SIZE = 512
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
        self.expiries = None
        self.cds_expiries = None
        
        instruments_list = kwargs.get("instruments_list",None)
        self.update_instruments_list(instruments_list)
    
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
    
    @api_retry(exception=KiteException)
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
            self._filter_instruments_list()
            self._extract_expiries_underlyings()
            t = pd.Timestamp.now(tz=self.tz) + pd.Timedelta(days=1)
            self._instruments_list_valid_till = t.normalize()
        except Exception as e:
            raise e
            msg = str(e)
            handling = ExceptionHandling.TERMINATE
            raise APIException(msg=msg, handling=handling)
        
        
        
    def _filter_instruments_list(self):
        '''
            Filter instruments that we do not want - the non EQ segment
            cash instruments + single stock options + bond futures and
            indices which are not tradeable. We also drop expiries 
            with more than 15 weeks from today.
        '''
        self._instruments_list.dropna(inplace=True)
        # drop exchanges we do not want
        self._instruments_list = self._instruments_list.loc[
            self._instruments_list.exchange.isin(self.__class__.EXCHANGES)]
        
        # drop the indices, these are not tradeable and VIX
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "NSE-INDICES"]
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "INDICES"]
        self._instruments_list = self._instruments_list[
                self._instruments_list.tradingsymbol.str.\
                    contains('INDIAVIX')==False]
        
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
        
        # keep the first three monthly expiries, remove all else
        today = pd.Timestamp.now().normalize()
        self._instruments_list.dropna(inplace=True)
        self._instruments_list['expiry'] = pd.to_datetime(
                self._instruments_list.expiry)
        self._instruments_list.loc[pd.isnull(
                self._instruments_list.expiry),"expiry"] \
                    = pd.Timestamp.now().normalize()
        self._instruments_list = self._instruments_list[
                self._instruments_list.expiry \
                    < today + pd.Timedelta(weeks=15)]
        
        self.expiries = set(self._instruments_list.expiry[
                (self._instruments_list['exchange']=="NFO") &\
                (self._instruments_list["instrument_type"]=="FUT")])
        
        self.cds_expiries = set(self._instruments_list.expiry[
                (self._instruments_list['exchange']=="CDS") &\
                (self._instruments_list["instrument_type"]=="FUT")])
        
        self.expiries = sorted(list(self.expiries)[:3])
        self.cds_expiries = sorted(list(self.cds_expiries)[:3])
        
        self._instruments_list = self._instruments_list[
                self._instruments_list.expiry.isin(set([*self.expiries,
                                                  *self.cds_expiries,
                                                  today]))]
        
    def _extract_expiries_underlyings(self):
        '''
            Separates underlyings and and expiry month number to 
            enable searching either NIFTY18DECFUT or NIFTY-II.
        '''
        def underlying(s,e):
            s = s.split(e.strftime('%y%b').upper())
            return s[0]
        underlyings = [underlying(r['tradingsymbol'],r['expiry']) \
                for i, r in self._instruments_list.iterrows()]
        self._instruments_list['underlying'] = underlyings
        
        exp1_dict = dict(zip(self.expiries,['I',"II","III"]))
        exp2_dict = dict(zip(self.cds_expiries,['I',"II","III"]))
        def expiry_month(e,i,s, d1, d2):
            if i != "FUT":
                return ""
            else:
                if s == "NFO":
                    return d1.get(e,"")
                elif s == "CDS":
                    return d2.get(e,"")
                else:
                    return ""
        
        exp = [expiry_month(r["expiry"],
                                r["instrument_type"],
                                r["exchange"],exp1_dict,exp2_dict)\
            for i, r in self._instruments_list.iterrows()]
        self._instruments_list['exp'] = exp
        
    def _asset_from_row(self, row):
        '''
            Create an asset from a matching row from the instruments
            list.
        '''
        if row['instrument_type'] == 'EQ':
            asset = Equity(-1,symbol=row['tradingsymbol'], 
                           tick_size=row['tick_size'],
                           exchange_name='NSE')
        elif row['segment']=='NFO-FUT':
            asset = EquityFutures(-1,symbol=row['tradingsymbol'],
                                  root=row['underlying'],
                                  name=row['name'],
                                  end_date=row['expiry'],
                                  expiry_date = row['expiry'],
                                  mult=row['lot_size'],
                                  tick_size=row['tick_size'],
                                  exchange_name='NSE')
        elif row['segment']=='NFO-OPT':
            asset = EquityOption(-1,symbol=row['tradingsymbol'],
                                  root=row['underlying'],
                                  name=row['name'],
                                  end_date=row['expiry'],
                                  expiry_date = row['expiry'],
                                  strike = row['strike'],
                                  mult=row['lot_size'],
                                  tick_size=row['tick_size'],
                                  exchange_name='NSE')
        elif row['segment'] == 'CDS-FUT':
            base = 'INR'
            quote = row['underlying'][:3]
            asset = Forex(-1, symbol=row['tradingsymbol'],
                                  ccy_pair=quote+'/'+base,
                                  base_ccy=base,
                                  quote_ccy = quote,
                                  name = row['name'],
                                  end_date=row['expiry'],
                                  mult=row['lot_size'],
                                  tick_size=row['tick_size'],
                                  exchange_name='NSE')
        else:
            asset = None
            
        return asset
        
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def symbol_to_asset(self, tradingsymbol):
        '''
            Asset finder that first looks at the provided asset
            finder. If no match found, it searches the current
            list of instruments and creates an asset. This asset 
            can only be used for sending orders and fetching data
            from the broker directly, not from our database. If no
            match found even in instrument list, returns None. The
            symbol stored, if not matched in our databse, is always
            the tradeable symbol.
        '''
        asset = self._asset_finder.lookup_symbol(tradingsymbol)
        if asset is not None:
            # we got a match in our databse, return early
            return asset

        sym = tradingsymbol.split(":")[-1]
        bases = sym.split("-I")
        
        if bases[0] != sym:
            exp = bases[-1]+'I'
            row = self._instruments_list.loc[
                    (self._instruments_list.underlying==bases[0]) &\
                    (self._instruments_list.exp == exp) &\
                    (self._instruments_list.instrument_type=='FUT'),]
        else:
            row = self._instruments_list.loc[
                    self._instruments_list.tradingsymbol==sym,]
        
        if row.empty:
            # no match found. Refuse to trade the symbol
            return None
        
        row = row.iloc[0].to_dict()
        return self._asset_from_row(row)
                
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def id_to_asset(self, instrument_id):
        '''
            create an asset from the instrument id. First extract
            the matching row and search for the asset in our own
            database. If no match found, create an asset and return.
        '''
        row = self._instruments_list[self._instruments_list.\
                                     instrument_token==instrument_id]
        row = row.iloc[0].to_dict()
        asset = self._asset_finder.lookup_symbol(row['tradingsymbol'])
        
        if asset:
            return asset
        
        return self._asset_from_row(row)
        
    def asset_to_symbol(self, asset):
        return asset.symbol
    
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def asset_to_id(self, asset):
        row = self._instruments_list[self._instruments_list.\
                                     tradingsymbol==asset.symbol] 
        row = row.iloc[0].to_dict()
        return row['instrument_token']
    
        
        
        
        
        