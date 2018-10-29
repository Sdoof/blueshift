# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:26:59 2018

@author: prodipta
"""
import json
import pandas as pd
import numpy as np
from math import ceil

from kiteconnect.exceptions import KiteException

from blueshift.data.rest_data import RESTData
from blueshift.data.dataportal import OHLCV_FIELDS
from blueshift.utils.exceptions import (AuthenticationError, 
                                        ExceptionHandling,
                                        APIException,
                                        SymbolNotFound,
                                        UnsupportedFrequency)
from blueshift.utils.decorators import api_rate_limit, singleton

from blueshift.utils.brokers.zerodha.kiteassets import KiteAssetFinder
from blueshift.utils.brokers.zerodha.kiteauth import kite_calendar

LRU_CACHE_SIZE = 512


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
            self._rate_limit = 2
            self._rate_limit_count = self._rate_limit
            
        if not self._trading_calendar:
            self._trading_calendar = kite_calendar
            
        if not self._max_instruments:
            # max allowed is 500 for current, and one for history
            self._max_instruments = 50
        
        self._rate_limit_since = None # we reset this value on first call
        
        self._asset_finder = kwargs.get("asset_finder", None)
        if self._asset_finder is None:
            self._asset_finder = KiteAssetFinder(auth=self._auth)
            
        self._minute_per_day = int((kite_calendar._close_nano - 
                                    kite_calendar._open_nano)/(60*1E9))
        
    @api_rate_limit
    def current(self, assets, fields):
        # prune the list if we exceed max instruments
        if len(assets) > self._max_instruments:
            assets = assets[:self._max_instruments]
            
        instruments = [asset.exchange_name+":"+asset.symbol for\
                          asset in assets]
        try:
            data = self._api.ohlc(instruments)
            return self._ohlc_to_df(data, instruments, assets, 
                                    fields)
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARNING
            raise APIException(msg=msg, handling=handling)
        
    def history(self, assets, fields, nbar, frequency):
        # prune the list if we exceed max instruments
        if len(assets) > self._max_instruments:
            assets = assets[:self._max_instruments]
            
        frequency = frequency.lower()
        
        if frequency not in ['1m','1d']:
            raise UnsupportedFrequency(msg=frequency)
        
        interval = 'minute' if frequency == '1m' else 'day'
        
        if frequency == "1m":
            n_days = ceil(nbar/self._minute_per_day)
        else:
            n_days = int(nbar)
            
        if n_days == 0:
            return
            
        to_date = pd.Timestamp.now(tz=self.tz).normalize()
        from_date = to_date + pd.Timedelta(days=-(n_days+10))
        valid_sessions = self._trading_calendar.sessions(from_date,
                                                         to_date)
        to_date = valid_sessions[-1]
        from_date = valid_sessions[-n_days-1]
        
        data = {}
        for asset in assets:
            try:
                instrument = self._asset_finder.asset_to_id(asset)
                data[asset] = self._history(instrument, from_date,to_date, interval, 
                                     nbar)
            except SymbolNotFound:
                pass
            except KiteException as e:
                msg = str(e)
                handling = ExceptionHandling.WARNING
                raise APIException(msg=msg, handling=handling)
            
        return pd.concat(data)
        
    @api_rate_limit
    def _history(self, instrument_id, from_date, to_date, interval, nbar):
        try:
            data = self._api.historical_data(instrument_id,from_date.date(),
                                             to_date.date(), interval)
            return self._list_to_df(data)[-nbar:]
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise APIException(msg=msg, handling=handling)
            
    def _list_to_df(self, data):
        t, o, h, l, c, v = [], [], [], [], [], []
        for e in data:
            t.append(pd.Timestamp(e['date'],tz=self.tz))
            o.append(e.get('open',0))
            h.append(e.get('high',0))
            l.append(e.get('low',0))
            c.append(e.get('close',0))
            v.append(e.get('volume',0))
            
        return pd.DataFrame(np.array([o,h,l,c,v]).T, 
                            columns=OHLCV_FIELDS, index=t)
    
    def _ohlc_to_df(self, data, instruments, assets, fields):
        fields = [f for f in fields if f in OHLCV_FIELDS]
        out = {}
        
        def get_val(data,inst,key):
            try:
                return data[inst]['ohlc'][key]
            except KeyError:
                return 0
        
        for f in fields:
            out[f] = [get_val(data,inst,f) for inst in instruments]
        
        return pd.DataFrame(out, index = assets)
        
