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
from blueshift.assets._assets cimport Asset

cdef class Trade:
    '''
        Trade object definition. A trade belongs to an order that 
        generated the trade(s)
    '''
    
    def __init__(self,
                 int tid,
                 int quantity,              
                 int side,    
                 object oid,
                 object broker_order_id,
                 object exchange_order_id,
                 object instrument_id,
                 Asset asset,                
                 int product_type,
                 float average_price,
                 float cash_flow,
                 float margin,
                 float commission,
                 object exchange_timestamp,
                 object timestamp):
        '''
            The only agent who can create a trade is the execution 
            platform. All fields are required.
        '''
        self.asset = asset
        self.tid = tid
        self.hashed_tid = hash(tid)
        self.quantity = quantity
        self.side = side
        self.oid = oid
        self.broker_order_id = broker_order_id
        self.exchange_order_id = exchange_order_id
        self.instrument_id = instrument_id
        self.product_type = product_type
        self.average_price = average_price
        self.cash_flow = cash_flow
        self.margin = margin
        self.commission = commission
        self.exchange_timestamp = exchange_timestamp
        self.timestamp = timestamp
        
    
    def __hash__(self):
        return self.hashed_tid
    
    def __eq__(x,y):
        try:
            return hash(x) == hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Trade[sym:%s,qty:%d,average price:%f]' % \
                    (self.asset.symbol,self.quantity, 
                     self.average_price)
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {'tid':self.tid,
                'hashed_tid':self.hashed_tid,
                'oid':self.oid,
                'broker_order_id':self.broker_order_id,
                'exchange_order_id':self.exchange_order_id,
                'instrument_id':self.instrument_id,
                'asset':self.asset,
                'side':self.side,
                'product_type':self.product_type,
                'average_price':self.average_price,
                'cash_flow':self.cash_flow,
                'margin':self.margin,
                'commission':self.commission,
                'exchange_timestamp':self.exchange_timestamp,
                'timestamp':self.timestamp,
                'quantity':self.quantity}
        
    cpdef __reduce__(self):
        return(self.__class__,( self.tid,
                                self.hashed_tid,
                                self.oid,
                                self.broker_order_id,
                                self.exchange_order_id,
                                self.instrument_id,
                                self.asset,
                                self.side,
                                self.product_type,
                                self.average_price,
                                self.cash_flow,
                                self.margin,
                                self.commission,
                                self.quantity,
                                self.exchange_timestamp,
                                self.timestamp))
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
        