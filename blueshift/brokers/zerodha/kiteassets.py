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
Created on Mon Oct 29 16:27:26 2018

@author: prodipta
"""

import pandas as pd
from functools import lru_cache
from requests.exceptions import RequestException

from kiteconnect.exceptions import KiteException



from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        APIException,
                                        SymbolNotFound,
                                        ValidationError)

from blueshift.utils.decorators import singleton, api_retry, blueprint
from blueshift.assets import BrokerAssetFinder

# pylint: disable=no-name-in-module
from blueshift.assets._assets import (Equity, EquityFutures, Forex,
                                      EquityOption, OptionType)

LRU_CACHE_SIZE = 512

@singleton
@blueprint
class KiteAssetFinder(BrokerAssetFinder):
    '''
        Implements the interface for Zerodha. We download the day's list 
        of tradeable instruments and map it to assets using heuristics. If
        the asset is in our database we populate SID and other fields. 
        Else we mark sid as -1. It is NOT necessary for an asset to be
        in our database for user to be able to query or trade that with
        a broker.
    '''
    # pylint: disable=too-many-instance-attributes
    EXCHANGES = ['NSE','NFO','CDS']
    AssetConstructorDispatch = {'EQNSE':Equity, 'FUTNFO': EquityFutures,
            'CENFO':EquityOption, 'PENFO':EquityOption, 'FUTCDS': Forex}
    
    def __init__(self, *args, **kwargs):
        self._create(*args, **kwargs)
    
    def _create(self, *args, **kwargs):
        '''
            We must have two things - an asset finder that can talk to
            asset database, and an auth object that provides us with the
            underlying API object
        '''
        # pylint: disable=bad-super-call, protected-access
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
            
        if not self._trading_calendar:
            self._trading_calendar = self._auth._trading_calendar
            
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
        # pylint: disable=protected-access
        return self._auth._name
    
    def __str__(self):
        return "Blueshift BrokerAssetFinder [name:%s]" % self.name
    
    def __repr__(self):
        return self.__str__()
    
    @api_retry(exception=KiteException)
    def update_instruments_list(self, instruments_list=None,
                                valid_till = None):
        '''
            Download the instruments list for the day, if not already
            downloaded before. If we fail, we cannot continue and so
            raise a TERMINATE level exception.
        '''
        if instruments_list is not None:
            if not isinstance(instruments_list, pd.DataFrame):
                msg="Invalid instruments list for {self.name}"
                handling = ExceptionHandling.TERMINATE
                raise ValidationError(msg=msg, handling=handling)
            self._instruments_list = instruments_list
            # check or set the expiry
            if valid_till is not None:
                # TODO: check for consistent timezone
                self._instruments_list_valid_till = valid_till
            else:
                t = pd.Timestamp.now(tz=self.tz) + pd.Timedelta(days=1)
                self._instruments_list_valid_till = t.normalize()
        
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
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.TERMINATE
            raise APIException(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.TERMINATE
            raise APIException(msg=msg, handling=handling)
        
        
        
    def _filter_instruments_list(self):
        '''
            Filter instruments that we do not want - the non EQ segment
            cash instruments + single stock options + bond futures and
            indices which are not tradeable. We also drop expiries 
            more than next three monthly ones.
        '''
        self._instruments_list.dropna(inplace=True)
        # drop exchanges we do not want
        self._instruments_list = self._instruments_list.loc[
            self._instruments_list.exchange.isin(self.__class__.EXCHANGES)]
        
        # drop the indices, these are not tradeable. We also remove
        # VIX, NIFTYIT and NIFTYMID futures and currency options.
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "NSE-INDICES"]
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "INDICES"]
        self._instruments_list = self._instruments_list[
                self._instruments_list.tradingsymbol.str.\
                    contains('INDIAVIX')==False]
        self._instruments_list = self._instruments_list[
                self._instruments_list.tradingsymbol.str.\
                    contains('NIFTYIT')==False]
        self._instruments_list = self._instruments_list[
                self._instruments_list.tradingsymbol.str.\
                    contains('NIFTYMID50')==False]
        self._instruments_list = self._instruments_list[
                self._instruments_list.segment != "CDS-OPT"]
        
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
                    = today
        
        self.expiries = set(self._instruments_list.expiry[
                (self._instruments_list['exchange']=="NFO") &\
                (self._instruments_list["instrument_type"]=="FUT")])
        
        self.cds_expiries = set(self._instruments_list.expiry[
                (self._instruments_list['exchange']=="CDS") &\
                (self._instruments_list["instrument_type"]=="FUT")])
        
        self.expiries = sorted(list(self.expiries))[:3]
        self.cds_expiries = sorted(list(self.cds_expiries))[:3]
        
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
            
            if s == "NFO":
                return d1.get(e,"")
            
            if s == "CDS":
                return d2.get(e,"")
            
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
        # pylint: disable=no-self-use
        # TODO: replace this by create_asset_from_dict from _assets
        if row['instrument_type'] == 'EQ':
            asset = Equity(-1,symbol=row['tradingsymbol'], 
                           mult=int(row['lot_size']),
                           tick_size=int(row['tick_size']*10000),
                           exchange_name='NSE')
        elif row['segment']=='NFO-FUT':
            asset = EquityFutures(-1,symbol=row['tradingsymbol'],
                                  root=row['underlying'],
                                  name=row['name'],
                                  end_date=row['expiry'],
                                  expiry_date = row['expiry'],
                                  mult=int(row['lot_size']),
                                  tick_size=int(row['tick_size']*10000),
                                  exchange_name='NFO')
        elif row['segment']=='NFO-OPT':
            opt_type = row['instrument_type']
            opt_type = OptionType.PUT if opt_type == 'PE' else\
                        OptionType.CALL
            asset = EquityOption(-1,symbol=row['tradingsymbol'],
                                  root=row['underlying'],
                                  name=row['name'],
                                  end_date=row['expiry'],
                                  expiry_date = row['expiry'],
                                  strike = row['strike'],
                                  mult=int(row['lot_size']),
                                  tick_size=int(row['tick_size']*10000),
                                  option_type = opt_type,
                                  exchange_name='NFO')
        elif row['segment'] == 'CDS-FUT':
            base = 'INR'
            quote = row['underlying'][:3]
            asset = Forex(-1, symbol=row['tradingsymbol'],
                                  ccy_pair=quote+'/'+base,
                                  base_ccy=base,
                                  quote_ccy = quote,
                                  name = row['name'],
                                  end_date=row['expiry'],
                                  mult=int(row['lot_size']),
                                  tick_size=int(row['tick_size']*10000),
                                  exchange_name='CDS')
        else:
            asset = None
            
        return asset
        
    def refresh_data(self, *args, **kwargs):
        instruments_list = kwargs.get("instruments_list",None)
        self.update_instruments_list(instruments_list)
    
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def symbol_to_asset(self, tradingsymbol, as_of_date=None):
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
        if self._asset_finder is not None:
            try:
                asset = self._asset_finder.lookup_symbol(tradingsymbol,
                                                 as_of_date)
                # we got a match in our databse, return early
                return asset
            except SymbolNotFound:
                pass

        sym = tradingsymbol.split(":")[-1]
        bases = sym.split("-I")
        
        if bases[0] != sym:
            if len(bases)>1 and bases[-1] in ['','I','II']:
                exp = bases[-1]+'I'
                row = self._instruments_list.loc[
                        (self._instruments_list.underlying==bases[0]) &\
                        (self._instruments_list.exp == exp) &\
                        (self._instruments_list.instrument_type=='FUT'),]
            else:
                row = self._instruments_list.loc[
                        self._instruments_list.tradingsymbol==sym,]
        else:
            row = self._instruments_list.loc[
                    self._instruments_list.tradingsymbol==sym,]
        
        if row.empty:
            # no match found. Refuse to trade the symbol
            # default handling is to log
            raise SymbolNotFound(msg=tradingsymbol)
        
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
        if row.empty:
            raise SymbolNotFound(msg=f"no asset found for {instrument_id}")
            
        row = row.iloc[0].to_dict()
        
        if self._asset_finder is not None:
            try:
                asset = self._asset_finder.lookup_symbol(row['tradingsymbol'])
                return asset
            except SymbolNotFound:
                pass
        
        return self._asset_from_row(row)
        
    def asset_to_symbol(self, asset):
        return asset.symbol
    
    @lru_cache(maxsize=LRU_CACHE_SIZE,typed=False)
    def asset_to_id(self, asset):
        '''
            Given an asset retrieve the instrument id. Instrument ID
            is required for placing trades or querying hisotrical
            data.
        '''
        row = self._instruments_list[self._instruments_list.\
                                     tradingsymbol==asset.symbol] 
        if row.empty:
            raise SymbolNotFound(msg=f"no id found for {asset.symbol}")
        
        row = row.iloc[0].to_dict()
        return row['instrument_token']
    
    def lookup_symbol(self, sym, as_of_date=None):
        '''
            Implementation of the interface. The plural version will
            remains same as the parent class
        '''
        # pylint: disable=unused-argument
        return self.symbol_to_asset(sym)
    
    def fetch_asset(self, sid):
        '''
            Implementation of the interface. The plural version will
            remains same as the parent class. For an SID different 
            than -1, it implies the asset is in our database and 
            a search is done using the underlying asset finder.
        '''
        if self._asset_finder is not None:
            return self._asset_finder.fetch_asset(sid)
        else:
            raise SymbolNotFound(msg=f"could not find sid {sid}")
