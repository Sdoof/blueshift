# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _trade.pyx>

cimport cython
cimport _order_types
from _trade cimport Trade
import uuid
import hashlib

cdef class Position:
    '''
        Trade object definition. A trade belongs to an order that 
        generated the trade(s)
    '''
    cdef readonly object pid
    cdef readonly int hashed_pid
    cdef readonly int instrument_id
    cdef readonly int sid
    cdef readonly object symbol
    cdef readonly object exchange_name
    cdef readonly int quantity
    cdef readonly int buy_quantity
    cdef readonly float buy_price
    cdef readonly int sell_quantity
    cdef readonly float sell_price
    cdef readonly float pnl
    cdef readonly float realized_pnl
    cdef readonly float unrealized_pnl
    cdef readonly float last_price
    cdef readonly object timestamp
    cdef readonly float value
    cdef readonly int product_type
    
    def __init__(self,
                 object symbol,        
                 object exchange_name, 
                 int sid,
                 int quantity,              
                 int side,    
                 object instrument_id,
                 int product_type,
                 float average_price,
                 object timestamp,
                 object exchange_timestamp):
        '''
            The algo creates a position once a new trade is done and a 
            matching position is not found. Matching is done on the underlying
            and once a position is closed, it is never re-used. A new one will
            be created instead.
        '''
        if sid != -1:
            self.sid = sid
            #asset = asset_finder.find_by_symbol(symbol,exchange_name)
            asset = None
            self.symbol = asset.symbol
            self.exchange_name = asset.exchange_name
        else:
            self.sid = -1
            self.symbol = symbol
            self.exchange_name = exchange_name
            
        h = hashlib.md5()
        h.update((symbol + exchange_name + str(sid)).encode('utf-8'))
        self.pid = h.hexdigest()
        self.hashed_pid = hash(self.pid)
        self.instrument_id = instrument_id
    
        self.quantity = quantity
        
        if side == _order_types.BUY:
            self.buy_price = average_price
            self.buy_quantity = quantity
        else:
            self.sell_quantity = quantity
            self.sell_price = average_price
        
        self.pnl = 0
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.last_price = average_price
        self.timestamp = timestamp
        self.value = quantity*average_price
        self.product_type = product_type
        
        
    def __int__(self):
        return self.hashed_pid
    
    def __hash__(self):
        return self.hashed_pid
    
    def __eq__(x,y):
        try:
            return int(x) == int(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Position:sym:%s,qty:%d,realized:%f, unrealized:%f' %\
            (self.symbol,self.quantity, self.realized_pnl, 
             self.unrealized_pnl)
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {'pid':self.pid,
                'hashed_pid':self.hashed_pid,
                'instrument_id':self.instrument_id,
                'sid':self.sid,
                'symbol':self.symbol,
                'exchange_name':self.exchange_name,
                'quantity':self.quantity,
                'buy_quantity':self.buy_quantity,
                'buy_price':self.buy_price,
                'sell_quantity':self.sell_quantity,
                'sell_price':self.sell_price,
                'pnl':self.pnl,
                'realized_pnl':self.realized_pnl,
                'unrealized_pnl':self.unrealized_pnl,
                'last_price':self.last_price,
                'timestamp':self.timestamp,
                'value':self.value,
                'product_type':self.product_type
                }
        
    cpdef __reduce__(self):
        return(self.__class__,( self.pid,
                                self.hashed_pid,
                                self.instrument_id,
                                self.sid,
                                self.symbol,
                                self.exchange_name,
                                self.quantity,
                                self.buy_quantity,
                                self.buy_price,
                                self.sell_quantity,
                                self.sell_price,
                                self.pnl,
                                self.realized_pnl,
                                self.unrealized_pnl,
                                self.last_price,
                                self.timestamp,
                                self.value,
                                self.product_type
                                ))
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    @classmethod
    def from_trade(cls,Trade t):
        p = Position(t.symbol, t.exchange_name, t.sid, t.quantity, 
                     t.side, t.instrument_id, t.product_type, 
                     t.average_price, t.exchange_timestamp, 
                     t.timestamp)
        return p
    
    cpdef update(self, Trade trade):
        if trade.side == _order_types.BUY:
            self.buy_price = self.buy_quantity*self.buy_price + \
                                trade.average_price*trade.quantity
            self.buy_quantity = self.buy_quantity + trade.quantity
            self.buy_price = self.buy_price / self.buy_quantity
            self.quantity = self.quantity + trade.quantity
        else:
            self.sell_price = self.sell_quantity*self.sell_price + \
                                trade.average_price*trade.quantity
            self.sell_quantity = self.sell_quantity + trade.quantity
            self.sell_price = self.sell_price / self.sell_quantity
            self.quantity = self.quantity - trade.quantity
        
        self.last_price = trade.average_price
        self.value = self.quantity*self.last_price
        self.timestamp = trade.timestamp
        
        if self.buy_quantity > self.sell_quantity:
            self.realized_pnl = self.sell_quantity*\
                                    (self.sell_price - self.buy_price)
            self.unrealized_pnl = (self.buy_quantity - self.sell_quantity)*\
                                    (self.last_price - self.buy_price)
        else:
            self.realized_pnl = self.buy_quantity*\
                                    (self.sell_price - self.buy_price)
            self.unrealized_pnl = (self.sell_quantity - self.buy_quantity)*\
                                    (self.sell_price - self.last_price)
                                    
        self.pnl = self.unrealized_pnl + self.realized_pnl
        
    cpdef if_closed(self):
        if self.quantity == 0:
            return True
        return False
        
        
        
        
        
        
        
        
        
        
        