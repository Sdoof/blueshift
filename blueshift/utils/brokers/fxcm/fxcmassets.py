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
Created on Wed Dec 12 11:28:56 2018

@author: prodipta
"""

from functools import lru_cache


from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        SymbolNotFound,
                                        ValidationError)
from blueshift.utils.decorators import singleton, blueprint
from blueshift.assets import BrokerAssetFinder

# pylint: disable=no-name-in-module
from blueshift.assets._assets import Forex

LRU_CACHE_SIZE = 64

@singleton
@blueprint
class FXCMAssetFinder(BrokerAssetFinder):
    '''
        Implements the interface for Zerodha. We download the day's list 
        of tradeable instruments and map it to assets using heuristics. If
        the asset is in our database we populate SID and other fields. 
        Else we mark sid as -1. It is NOT necessary for an asset to be
        in our database for user to be able to query or trade that with
        a broker.
    '''
    # pylint: disable=too-many-instance-attributes
    EXCHANGES = ['FXCM']
    AssetConstructorDispatch = {'FUTCDS': Forex}
    
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
        return "Blueshift BrokerAssetFinder [%s]" % self.name
    
    def __repr__(self):
        return self.__str__()
    
    def update_instruments_list(self, instruments_list=None,
                                valid_till = None):
        '''
            list of instruments are part of the api object. All these are 
            FX on margin, so no expiry dates as such and hence no validity. 
            We just return the list of instruments from the underlying api 
            object, or the passed on list after checkng they are in the 
            underlying instruments list.
        '''
        if not instruments_list:
            self._instruments_list = self._auth._api.instruments
            return
        self._instruments_list = [inst for inst in instruments_list if inst \
                                  in self._auth._api.instruments]
        
    def _asset_from_sym(self, sym):
        '''
            Create an asset from a matching entry in the instruments list.
        '''
        # pylint: disable=no-self-use
        # TODO: replace this by create_asset_from_dict from _assets
        # all instrument types are Forex.
        sym = sym.split(":")[0]
        
        if sym not in self._instruments_list:
            raise SymbolNotFound(f"no instruments with symbol {sym}")
        
        base, quote = tuple(sym.split('/'))
        
        if not base or not quote:
            raise ValidationError(f"Invalid symbol {sym} for Forex.")
        
        # TODO: hardcoded assumptions here on ticksize, generalize this.
        # NOTE: actual tick size is the inverse of this number!!
        if quote == 'JPY':
            tick_size = 100
        else:
            tick_size = 10000
        
        asset = Forex(-1, symbol=sym,
                      ccy_pair=base+'/'+quote,
                      base_ccy=base,
                      quote_ccy = quote,
                      name = sym,
                      mult=1000, # the micro-lot
                      tick_size=tick_size,
                      ccy = quote,
                      exchange_name='FXCM')
            
        return asset
    
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

        return self._asset_from_sym(tradingsymbol)
        
    def asset_to_symbol(self, asset):
        return asset.symbol
    
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
