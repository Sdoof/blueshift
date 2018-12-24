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
Created on Fri Dec 21 16:38:06 2018

@author: prodipta
"""

import json
import pandas as pd
from requests.exceptions import RequestException

from fxcmpy.fxcmpy import ServerError

from blueshift.data.rest_data import RESTDataPortal
from blueshift.utils.types import OHLCV_FIELDS
from blueshift.utils.exceptions import (AuthenticationError, 
                                        ExceptionHandling,
                                        MissingDataError,
                                        BrokerAPIError,
                                        SymbolNotFound,
                                        UnsupportedFrequency)
from blueshift.utils.decorators import api_rate_limit, singleton, blueprint

from blueshift.utils.brokers.fxcm.fxcmassets import FXCMAssetFinder

LRU_CACHE_SIZE = 512


@singleton
@blueprint
class FXCMRestData(RESTDataPortal):
    '''
        Encalsulates the RESTful historical and current market data API
        for FXCM. It contains a kite authentication object and access 
        the underlying fxcmpy API via that.
    '''
    def __init__(self, *args, **kwargs):
        self._create(*args, **kwargs)
    
    def _create(self, *args, **kwargs):
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
            
        if not self._trading_calendar:
            self._trading_calendar = self._auth._trading_calendar
            
        self._asset_finder = kwargs.pop("asset_finder", None)
        if self._asset_finder is None:
            self._asset_finder = FXCMAssetFinder(auth=self._auth)
            
        self._minute_per_day = int((self._trading_calendar._close_nano - 
                                    self._trading_calendar._open_nano)/(60*1E9))
        
    def current(self, assets, fields):
        '''
            Fetch the current bar for the given assets and fields.
        '''
        if not isinstance(assets, list):
            assets = [assets]
        if not isinstance(fields, list):
            fields = [fields]
        
        # prune the list if we exceed max instruments
        if len(assets) > self._api._max_instruments:
            assets = assets[:self._api._max_instruments]
        
        data = []
        try:
            for asset in assets:
                df = self._get_candles(asset, fields)
                if len(assets) == 1 and len(fields) == 1:
                    return df.iloc[0,0]
                elif len(assets) == 1:
                    return df.iloc[0]                
                data.append(df)
                    
            data = pd.concat(data)
            data.index = assets
            return data
        except (ValueError, TypeError, ServerError) as e:
            msg = "in data.current: " + str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = "in data.current: " + str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
            
    def history(self, assets, fields, nbar, frequency):
        '''
            Fetch the historical bar for the given assets and fields.
            Minute data max length is 10K, we use the same cap for 
            daily data as well.
        '''
        print("inside history")
        if not isinstance(assets, list):
            assets = [assets]
        if not isinstance(fields, list):
            fields = [fields]
        
        # prune the list if we exceed max instruments
        if len(assets) > self._api._max_instruments:
            assets = assets[:self._api._max_instruments]
            
        # check and map the data frequency
        frequency = frequency.lower()
        if frequency not in ['1m','1d']:
            raise UnsupportedFrequency(msg=frequency)
        period = 'm1' if frequency == '1m' else 'D1'
            
        # cap the max period length
        nbar = int(nbar)
        if nbar > 10000:
            nbar = 10000
        
        data = {}
        print(f"got {nbar}, {period}")
        try:
            for asset in assets:
                df = self._get_candles(asset, fields, nbar=nbar, 
                                       period=period)
                print(df)
                if len(assets) == 1: 
                    return df             
                data[asset] = df
                    
            return pd.concat(data)
        except (ValueError, TypeError, ServerError) as e:
            msg = "in data.history: " + str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = "in data.history: " + str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @api_rate_limit
    def _get_candles(self, asset, fields, nbar=1, period='m1'):
        df = self._api.get_candles(asset.symbol, period=period, number=nbar)
        return self._compute_ohlc(df, fields)
    
    @classmethod        
    def _compute_ohlc(cls, px, fields):
        ohlc = {}
        valid_fields = [f for f in fields if f in OHLCV_FIELDS]
        
        for field in valid_fields:
            try:
                if field != 'volume':
                    df = px[px.columns[
                            px.columns.str.contains(field)]]
                    n = len(df.columns)
                    if n > 0:
                        ohlc[field] = df.sum(axis=1)/n
                else:
                    ohlc['volume'] = px['tickqty']
            except KeyError:
                continue
        return pd.DataFrame(ohlc, index=px.index)
        
        