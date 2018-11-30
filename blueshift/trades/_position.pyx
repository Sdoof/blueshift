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

# compile with <cythonize -i _trade.pyx>

cimport cython
cimport _order_types
from blueshift.trades._order_types import (
        ProductType,
        OrderFlag,
        OrderType,
        OrderValidity,
        OrderSide,
        OrderStatus,
        OrderUpdateType)
from blueshift.trades._trade cimport Trade
from blueshift.assets._assets cimport Asset
import uuid
import hashlib

cdef class Position:
    '''
        Trade object definition. A trade belongs to an order that 
        generated the trade(s)
    '''
    
    def __init__(self,
                 Asset asset,
                 int quantity,              
                 int side,    
                 object instrument_id,
                 int product_type,
                 float average_price,
                 float margin,
                 object timestamp,
                 object exchange_timestamp,
                 int buy_quantity=0,
                 float buy_price=0,
                 int sell_quantity=0,
                 float sell_price=0,
                 float pnl=0,
                 float realized_pnl=0,
                 float unrealized_pnl=0,
                 float last_price=0):
        '''
            The algo creates a position once a new trade is done and a 
            matching position is not found. Matching is done on the underlying
            and once a position is closed, it is never re-used. A new one will
            be created instead.
        '''
        self.asset = asset
        self.pid = hash(asset)
        self.instrument_id = instrument_id
        
        if side != -1:
            if side == OrderSide.BUY:
                self.quantity = quantity
                self.buy_price = average_price
                self.buy_quantity = quantity
                self.sell_quantity = 0
                self.sell_price = 0
            else:
                self.quantity = -quantity
                self.sell_quantity = quantity
                self.sell_price = average_price
                self.buy_price = 0
                self.buy_quantity = 0
            self.pnl = 0
            self.realized_pnl = 0
            self.unrealized_pnl = 0
            self.last_price = average_price
            self.margin = margin
            self.timestamp = timestamp
            self.value = quantity*average_price
            self.product_type = product_type
        else:
            self.quantity = quantity
            self.buy_price = buy_price
            self.buy_quantity = buy_quantity
            self.sell_quantity = sell_quantity
            self.sell_price = sell_price
            self.pnl = pnl
            self.realized_pnl = realized_pnl
            self.unrealized_pnl = unrealized_pnl
            self.last_price = last_price
            self.margin = margin
            self.timestamp = timestamp
            self.value = quantity*last_price
            self.product_type = product_type
        
    
    def __hash__(self):
        return self.pid
    
    def __eq__(x,y):
        try:
            return hash(x) == hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Position[sym:%s,qty:%d,realized:%f, unrealized:%f]' %\
            (self.asset.symbol,self.quantity, self.realized_pnl, 
             self.unrealized_pnl)
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {'pid':self.pid,                
                'instrument_id':self.instrument_id,
                'asset':self.asset,
                'quantity':self.quantity,
                'buy_quantity':self.buy_quantity,
                'buy_price':self.buy_price,
                'sell_quantity':self.sell_quantity,
                'sell_price':self.sell_price,
                'pnl':self.pnl,
                'realized_pnl':self.realized_pnl,
                'unrealized_pnl':self.unrealized_pnl,
                'last_price':self.last_price,
                'margin':self.margin,
                'timestamp':self.timestamp,
                'value':self.value,
                'product_type':self.product_type
                }
        
    cpdef __reduce__(self):
        return(self.__class__,( self.pid,
                                self.instrument_id,
                                self.asset,
                                self.quantity,
                                self.buy_quantity,
                                self.buy_price,
                                self.sell_quantity,
                                self.sell_price,
                                self.pnl,
                                self.realized_pnl,
                                self.unrealized_pnl,
                                self.last_price,
                                self.margin,
                                self.timestamp,
                                self.value,
                                self.product_type
                                ))
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    @classmethod
    def from_trade(cls,Trade t, float margin=0):
        p = Position(t.asset, t.quantity, 
                     t.side, t.instrument_id, t.product_type, 
                     t.average_price, margin, t.exchange_timestamp, 
                     t.timestamp)
        return p
    
    cpdef update(self, Trade trade, float margin):
        if trade.side == OrderSide.BUY:
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
        self.margin = self.margin + margin
        
    cpdef if_closed(self):
        if self.quantity == 0:
            return True
        return False
        
        
        
        
        
        
        
        
        
        
        