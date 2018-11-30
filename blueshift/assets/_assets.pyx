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

# compile with <cythonize -i _assets.pyx>
# TODO: add instrument id and include that in hash

cimport cython

cdef class MarketData:
    '''
        Basic market data object. Tradeable assets are derived from 
        this class. Also data series like macro economic data or 
        corporate fundamentals or sentiment indices are all derived
        from this generic data type. Note this is NOT designed to be
        run on a distributed system - the hashing may fail!!
    '''
    
    def __init__(self,
                 int sid,
                 object symbol="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 object ccy="local"):

        self.sid = sid
        self.symbol = symbol
        self.hashed_id = hash(self.symbol+str(self.sid))
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.mktdata_type = -1
        self.ccy = ccy
    
    def __int__(self):
        return self.sid
    
    def __hash__(self):
        return self.hashed_id
    
    def __index__(self):
        return self.sid
    
    def __eq__(x,y):
        try:
            return hash(x) == hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __lt__(x,y):
        try:
            return hash(x) < hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __gt__(x,y):
        try:
            return hash(x) > hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __ne__(x,y):
        try:
            return hash(x) != hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
    
    def __str__(self):
        if self.symbol:
            return '%s(%s [%d])' % (type(self).__name__, self.symbol, self.sid)
        else:
            return '%s[%d]' % (type(self).__name__, self.sid)
        
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {
                'sid':self.sid,
                'symbol':self.symbol,
                'name':self.name,
                'start_date':self.start_date,
                'end_date':self.end_date,
                'mktdata_type':self.mktdata_type,
                'ccy':self.ccy}
        
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.symbol,
                               self.name,
                               self.start_date,
                               self.end_date))
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

cdef class Asset(MarketData):
    '''
        Template for all tradeable assets. Captures exchange and 
        calendar in addition to market data. Market data type is 
        OHLCV and also have asset multiplier (defaults to 1.0) and
        minimum tick size for price move (default to cent).
    '''
    
    def __init__(self,
                 int sid,
                 object symbol="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 int mult=1,
                 int tick_size=100, # mult by 10000
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None,
                 object ccy="local"):

        super(Asset,self).__init__(
                 sid=sid,
                 symbol=symbol,
                 name=name,
                 start_date=start_date,
                 end_date=end_date,
                 ccy=ccy)
        
        self.mult = mult
        self.tick_size = tick_size
        self.auto_close_date = auto_close_date
        self.exchange_name = exchange_name
        self.calendar_name = calendar_name
        self.mktdata_type = MktDataType.OHLCV
        self.asset_class = AssetClass.EQUITY
        self.instrument_type = -1
        
    cpdef to_dict(self):
        d = super(Asset,self).to_dict()
        d['mult']=self.mult
        d['tick_size']=self.tick_size
        d['auto_close_date']=self.auto_close_date
        d['exchange_name']=self.exchange_name
        d['calendar_name']=self.calendar_name
        d['asset_class']=self.asset_class
        d['instrument_type']=self.instrument_type
        return d
    
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.symbol,
                               self.name,
                               self.start_date,
                               self.end_date,
                               self.mult,
                               self.tick_size,
                               self.auto_close_date,
                               self.exchange_name,
                               self.calendar_name,
                               self.ccy))
    
cdef class Equity(Asset):
    '''
        Equity assets. Multiplier is set to 1.0.
    '''
    def __init__(self,
                 int sid,
                 object symbol="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 int mult=1,
                 int tick_size=100,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None,
                 object ccy="local"):
        super(Equity, self).__init__(
                 sid=sid,
                 symbol=symbol,
                 name=name,
                 start_date=start_date,
                 end_date=end_date,
                 mult=1.0,
                 tick_size=tick_size,
                 auto_close_date=auto_close_date,
                 exchange_name=exchange_name,
                 calendar_name=calendar_name,
                 ccy=ccy)
        self.asset_class = AssetClass.EQUITY
        self.instrument_type = InstrumentType.SPOT

cdef class EquityFutures(Asset):
    '''
        Equity futures assets. Multiplier is set to 1.0 and asset 
        class is set to EQFUTURES enum type. Also sets expiry date.
    '''
    cdef readonly int underlying_sid
    cdef readonly object root
    cdef readonly object notice_date
    cdef readonly object expiry_date
    
    def __init__(self,
                 int sid,
                 int underlying_sid=-1,
                 object symbol="",
                 object root="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 object expiry_date=None,
                 object notice_date=None,
                 int mult=1,
                 int tick_size=100,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None,
                 object ccy="local"):
        super(EquityFutures, self).__init__(
                 sid=sid,
                 symbol=symbol,
                 name=name,
                 start_date=start_date,
                 end_date=end_date,
                 mult=mult,
                 tick_size=tick_size,
                 auto_close_date=auto_close_date,
                 exchange_name=exchange_name,
                 calendar_name=calendar_name,
                 ccy=ccy)
        self.root = root
        self.underlying_sid = underlying_sid
        self.expiry_date = expiry_date
        if notice_date is None:
            notice_date = expiry_date
        if auto_close_date is None:
            auto_close_date = expiry_date
        self.notice_date = notice_date
        self.auto_close_date = auto_close_date
        self.asset_class = AssetClass.EQUITY
        self.instrument_type = InstrumentType.FUTURES
        
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.underlying_sid,
                               self.symbol,
                               self.root,
                               self.name,
                               self.start_date,
                               self.end_date,
                               self.mult,
                               self.tick_size,
                               self.auto_close_date,
                               self.exchange_name,
                               self.calendar_name,
                               self.expiry_date,
                               self.notice_date,
                               self.ccy))

    cpdef to_dict(self):
        d = super(EquityFutures,self).to_dict()
        d['root']=self.root
        d['underlying_sid']=self.underlying_sid
        d['expiry_date']=self.expiry_date
        d['notice_date']=self.notice_date
        return d
    
cdef class Forex(Asset):
    cdef readonly object ccy_pair
    cdef readonly object base_ccy
    cdef readonly object quote_ccy
    
    def __init__(self,
                 int sid,
                 object symbol="",
                 object ccy_pair="",
                 object base_ccy="",
                 object quote_ccy="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 int mult=1,
                 int tick_size=100,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None,
                 object ccy="local"):
        super(Forex, self).__init__(
                 sid=sid,
                 symbol=symbol,
                 name=name,
                 start_date=start_date,
                 end_date=end_date,
                 mult=mult,
                 tick_size=tick_size,
                 auto_close_date=auto_close_date,
                 exchange_name=exchange_name,
                 calendar_name=calendar_name,
                 ccy=ccy)
        self.ccy_pair = ccy_pair
        self.base_ccy = base_ccy
        self.quote_ccy = quote_ccy
        self.asset_class = AssetClass.FOREX
        self.instrument_type = InstrumentType.SPOT
        
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.symbol,
                               self.name,
                               self.start_date,
                               self.end_date,
                               self.mult,
                               self.tick_size,
                               self.auto_close_date,
                               self.exchange_name,
                               self.calendar_name,
                               self.ccy_pair,
                               self.base_ccy,
                               self.quote_ccy,
                               self.ccy))
        
    cpdef to_dict(self):
        d = super(Forex,self).to_dict()
        d['ccy_pair']=self.ccy_pair
        d['base_ccy']=self.base_ccy
        d['quote_ccy']=self.quote_ccy
        return d
    
cdef class EquityOption(EquityFutures):
    '''
        Equity options assets. add strike compared to futures
    '''
    cdef readonly float strike
    cdef readonly int option_type
    
    def __init__(self,
                 int sid,
                 int underlying_sid=-1,
                 object symbol="",
                 object root="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 object expiry_date=None,
                 object notice_date=None,
                 float strike = 0,
                 int mult=1,
                 int tick_size=100,
                 int option_type = OptionType.CALL,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None,
                 object ccy="local"):
        super(EquityOption, self).__init__(
                 sid=sid,
                 underlying_sid=underlying_sid,
                 symbol=symbol,
                 root=root,
                 name=name,
                 start_date=start_date,
                 end_date=end_date,
                 expiry_date=expiry_date,
                 notice_date=notice_date,
                 mult=mult,
                 tick_size=tick_size,
                 auto_close_date=auto_close_date,
                 exchange_name=exchange_name,
                 calendar_name=calendar_name,
                 ccy=ccy)
        self.strike = strike
        self.asset_class = AssetClass.EQUITY
        self.instrument_type = InstrumentType.OPT
        self.option_type = option_type
        
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.underlying_sid,
                               self.symbol,
                               self.name,
                               self.start_date,
                               self.end_date,
                               self.mult,
                               self.tick_size,
                               self.option_type,
                               self.auto_close_date,
                               self.exchange_name,
                               self.calendar_name,
                               self.root,
                               self.expiry_date,
                               self.notice_date,
                               self.strike,
                               self.ccy))

    cpdef to_dict(self):
        d = super(EquityOption,self).to_dict()
        d['strike']=self.strike
        d['option_type']=self.option_type
        return d
    
cdef get_class_attribs(object obj):
    attrs = [f for f in dir(obj) if not callable(getattr(obj,f)) 
        and not str(f).endswith('_') and not str(f).startswith('_')]
    return attrs

cpdef create_asset_from_dict(object data):
    cdef int asset_type
    cdef int instrument_type
    cdef object d
    
    asset_type = data["asset_class"]
    instrument_type = data["instrument_type"]
    
    if asset_type == AssetClass.EQUITY and \
        instrument_type == InstrumentType.SPOT:
            attribs = ['sid','symbol','name','start_date','end_date',
                       'mult','tick_size','auto_close_date',
                       'exchange_name','calendar_name','ccy']
            d = {k: data[k] for k in attribs}
            return Equity.from_dict(d)
        
    elif asset_type == AssetClass.EQUITY and \
        instrument_type == InstrumentType.FUTURES:
            attribs = ['sid','underlying_sid','symbol','root','name',
                       'start_date','end_date','expiry_date',
                       'notice_date','mult','tick_size',
                       'auto_close_date','exchange_name',
                       'calendar_name','ccy']
            d = {k: data[k] for k in attribs}
            return EquityFutures.from_dict(d)
        
    elif asset_type == AssetClass.EQUITY and \
        instrument_type == InstrumentType.OPT:
            attribs = ['sid','underlying_sid','symbol','root','name',
                       'start_date','end_date','expiry_date',
                       'notice_date','strike','mult','tick_size',
                       'auto_close_date','exchange_name',
                       'calendar_name','ccy']
            d = {k: data[k] for k in attribs}
            return EquityOption.from_dict(d)
        
    elif asset_type == AssetClass.FOREX and \
        instrument_type == InstrumentType.SPOT:
            attribs = ['sid','symbol','ccy_pair','base_ccy',
                       'quote_ccy','name','start_date','end_date',
                       'mult','tick_size','auto_close_date',
                       'exchange_name','calendar_name','ccy']
            d = {k: data[k] for k in attribs}
            return Forex.from_dict(d)
    else:
        raise ValueError("Unknown asset_type or instrument")
        