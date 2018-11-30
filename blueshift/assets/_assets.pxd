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
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
cimport cython

cpdef enum AssetClass:
    EQUITY = 0,
    FOREX = 1,
    COMMODITY = 2,
    RATES = 3,
    CASH = 4,
    CRYPTO = 5,
    VOL = 6
    
cpdef enum InstrumentType:
    SPOT = 0,
    FUTURES = 1,
    OPT = 2,
    FUNDS = 3,
    CFD = 4,
    STRATEGY = 6
    
cpdef enum MktDataType:
    OHLCV = 0,       # full OHLCV price data tied to a sym
    SERIES = 1,      # single point series data tied to a sym
    GENERAL = 2,     # general purpose multi-column data for a sym
    
cpdef enum OptionType:
    CALL = 0        # european call
    PUT = 1         # european put

cdef class MarketData:
    cdef readonly int sid
    cdef readonly hashed_id
    cdef readonly int mktdata_type
    cdef readonly object symbol
    cdef readonly object name
    cdef readonly object start_date
    cdef readonly object end_date
    cdef readonly object ccy
    cpdef to_dict(self)
    cpdef __reduce__(self)

cdef class Asset(MarketData):
    cdef readonly int asset_class
    cdef readonly int instrument_type
    cdef readonly int mult
    cdef readonly int tick_size # ticksize is multiplied by 10000
    cdef readonly object auto_close_date
    cdef readonly object exchange_name
    cdef readonly object calendar_name
    cpdef to_dict(self)
    cpdef __reduce__(self)