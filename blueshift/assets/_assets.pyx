# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _assets.pyx>

cimport cython
cimport _asset_class

cdef class MarketData:
    '''
        Basic market data object. Tradeable assets are derived from 
        this class. Also data series like macro economic data or 
        corporate fundamentals or sentiment indices are all derived
        from this generic data type.
    '''
    cdef readonly int sid
    cdef readonly int hashed_sid
    cdef readonly int mktdata_type
    cdef readonly object symbol
    cdef readonly object name
    cdef readonly object start_date
    cdef readonly object end_date
    
    def __init__(self,
                 int sid,
                 object symbol="",
                 object name="",
                 object start_date=None,
                 object end_date=None):

        self.sid = sid
        self.hashed_sid = hash(self.sid)      # for dict lookups
        self.symbol = symbol
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.mktdata_type = -1
    
    def __int__(self):
        return self.sid
    
    def __hash__(self):
        return self.hashed_sid
    
    def __index__(self):
        return self.sid
    
    def __eq__(x,y):
        try:
            return int(x) == int(y)
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
                'mktdata_type':self.mktdata_type}
        
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
    cdef readonly int asset_class
    cdef readonly int instrument_types
    cdef readonly float mult
    cdef readonly float tick_size
    cdef readonly object auto_close_date
    cdef readonly object exchange_name
    cdef readonly object calendar_name
    
    def __init__(self,
                 int sid,
                 object symbol="",
                 object name="",
                 object start_date=None,
                 object end_date=None,
                 float mult=1.0,
                 float tick_size=0.01,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None):

        super(Asset,self).__init__(
                 sid=sid,
                 symbol=symbol,
                 name=name,
                 start_date=start_date,
                 end_date=end_date)
        
        self.mult = mult
        self.tick_size = tick_size
        self.auto_close_date = auto_close_date
        self.exchange_name = exchange_name
        self.calendar_name = calendar_name
        self.mktdata_type = _asset_class.OHLCV
        self.asset_class = _asset_class.EQUITY
        self.instrument_types = -1
        
    cpdef to_dict(self):
        d = super(Asset,self).to_dict()
        d['mult']=self.mult
        d['tick_size']=self.tick_size
        d['auto_close_date']=self.auto_close_date
        d['exchange_name']=self.exchange_name
        d['calendar_name']=self.calendar_name
        d['asset_class']=self.asset_class
        d['instrument_types']=self.instrument_types
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
                               self.calendar_name))
    
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
                 float mult=1.0,
                 float tick_size=0.01,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None):
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
                 calendar_name=calendar_name)
        self.asset_class = _asset_class.EQUITY
        self.instrument_types = _asset_class.SPOT

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
                 float mult=1.0,
                 float tick_size=0.01,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None):
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
                 calendar_name=calendar_name)
        self.root = root
        self.underlying_sid = underlying_sid
        self.expiry_date = expiry_date
        if notice_date is None:
            notice_date = expiry_date
        if auto_close_date is None:
            auto_close_date = expiry_date
        self.notice_date = notice_date
        self.auto_close_date = auto_close_date
        self.asset_class = _asset_class.EQUITY
        self.instrument_types = _asset_class.FUTURES
        
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
                               self.notice_date))

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
                 float mult=1.0,
                 float tick_size=0.01,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None):
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
                 calendar_name=calendar_name)
        self.ccy_pair = ccy_pair
        self.base_ccy = base_ccy,
        self.quote_ccy = quote_ccy,
        self.asset_class = _asset_class.FOREX
        self.instrument_types = _asset_class.SPOT
        
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
                               self.quote_ccy))
        
    cpdef to_dict(self):
        d = super(Forex,self).to_dict()
        d['ccy_pair']=self.ccy_pair
        d['base_ccy']=self.base_ccy
        d['quote_ccy']=self.quote_ccy
        return d
    
cdef class EquityOptions(EquityFutures):
    '''
        Equity options assets. add strike compared to futures
    '''
    cdef readonly float strike
    
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
                 float mult=1.0,
                 float tick_size=0.01,
                 object auto_close_date=None,
                 object exchange_name=None,
                 object calendar_name=None):
        super(EquityOptions, self).__init__(
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
                 calendar_name=calendar_name)
        self.strike = strike
        self.asset_class = _asset_class.EQUITY
        self.instrument_types = _asset_class.OPT
        
    cpdef __reduce__(self):
        return(self.__class__,(self.sid,
                               self.underlying_sid,
                               self.symbol,
                               self.name,
                               self.start_date,
                               self.end_date,
                               self.mult,
                               self.tick_size,
                               self.auto_close_date,
                               self.exchange_name,
                               self.calendar_name,
                               self.root,
                               self.expiry_date,
                               self.notice_date,
                               self.strike))

    cpdef to_dict(self):
        d = super(EquityOptions,self).to_dict()
        d['strike']=self.strike
        return d
    
cdef get_class_attribs(object obj):
    attrs = [f for f in dir(obj) if not callable(getattr(obj,f)) 
        and not str(f).endswith('_') and not str(f).startswith('_')]
    return attrs