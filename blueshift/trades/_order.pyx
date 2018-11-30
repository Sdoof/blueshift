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

# compile with <cythonize -i _order.pyx>

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
from _trade cimport Trade
from blueshift.assets._assets cimport Asset
import uuid

status_dict = {0:'complete',1:'open',2:'rejected',3:'cancelled'}
side_dict = {0:'BUY',1:'SELL'}

cdef class Order:
    '''
        Order objects definition. This provisions for order group
        through parent order ID, as well as other standard fields.
        The `oid` is the field through which the platform tracks an 
        order (which can be different from broekr or exchange IDs).
    '''
    cdef readonly object oid
    cdef readonly int hashed_oid
    cdef readonly object broker_order_id
    cdef readonly object exchange_order_id
    cdef readonly object parent_order_id
    cdef readonly Asset asset
    cdef readonly object user
    cdef readonly object placed_by      # the algo ID!
    cdef readonly int product_type
    cdef readonly int order_flag
    cdef readonly int order_type
    cdef readonly int order_validity
    cdef readonly int quantity
    cdef readonly int filled
    cdef readonly int pending
    cdef readonly int disclosed
    cdef readonly float price
    cdef readonly float average_price
    cdef readonly float trigger_price
    cdef readonly float stoploss_price
    cdef readonly int side
    cdef readonly int status
    cdef readonly object status_message
    cdef readonly object exchange_timestamp
    cdef readonly object timestamp
    cdef readonly object tag
    
    def __init__(self,
                 int quantity,              # required
                 int side,                  # required
                 Asset asset,               # required
                 int product_type=ProductType.DELIVERY,
                 int order_flag=OrderFlag.NORMAL,
                 int order_type=OrderType.MARKET,
                 int order_validity = OrderValidity.DAY,
                 int disclosed=0,
                 float price=0,             # for limit prices
                 float trigger_price=0,     # for stoplosses
                 float stoploss_price=0,     # for stoplosses
                 object user='algo',
                 object placed_by='algo',   # algo ID
                 object tag='blueshift',
                 object oid=None,
                 object broker_order_id=None,
                 object exchange_order_id=None,
                 object parent_order_id=None,
                 int filled=0,
                 int pending=0,
                 float average_price=0,
                 int status=OrderStatus.OPEN,
                 object status_message=None,
                 object exchange_timestamp=None,
                 object timestamp=None):
        '''
            The only agent who can create (or delete) an order is 
            the user trading agent. The broker cannot create an order.
            At the time of creation, user algo can only know about
            order details known at user level. So things like filled,
            pending, status etc are set accordingly and are not part
            of the init arguments.
        '''
        self.asset = asset
        self.side = side
        self.quantity = quantity
        
        self.oid = uuid.uuid4().hex if oid is None else oid
        self.hashed_oid = hash(self.oid)
        self.broker_order_id=broker_order_id
        self.exchange_order_id = exchange_order_id
        self.parent_order_id = parent_order_id
    
        self.user=user
        self.placed_by=placed_by
        self.product_type=product_type
        self.order_flag=order_flag
        self.order_type=order_type
        self.order_validity=order_validity
        
        self.filled=filled
        self.pending=pending if pending != 0 else (quantity-filled)
        self.disclosed=disclosed
        self.price=price
        self.average_price=average_price
        self.trigger_price=trigger_price
        self.stoploss_price = stoploss_price
    
        self.status=status
        self.status_message=status_message
        self.exchange_timestamp=exchange_timestamp
        self.timestamp=timestamp
        self.tag=tag
    
    
    def __hash__(self):
        return self.hashed_oid
    
    def __eq__(x,y):
        try:
            return hash(x) == hash(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Order[sym:%s, qty:%d, side:%s, filled:%d, at:%f, status:%s]' % \
                (self.asset.symbol,self.quantity,side_dict[self.side], 
                 self.filled,self.average_price,
                 status_dict[self.status])
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {
                'oid':self.oid,
                'hashed_oid':self.hashed_oid,
                'broker_order_id':self.broker_order_id,
                'exchange_order_id':self.exchange_order_id,
                'parent_order_id':self.parent_order_id,
                'asset':self.asset,
                'user':self.user,
                'placed_by':self.placed_by,
                'product_type':self.product_type,
                'order_flag':self.order_flag,
                'order_type':self.order_type,
                'order_validity':self.order_validity,
                'quantity':self.quantity,
                'filled':self.filled,
                'pending':self.pending,
                'disclosed':self.disclosed,
                'price':self.price,
                'average_price':self.average_price,
                'trigger_price':self.trigger_price,
                'stoploss_price':self.stoploss_price,
                'side':self.side,
                'status':self.status,
                'status_message':self.status_message,
                'exchange_timestamp':self.exchange_timestamp,
                'timestamp':self.timestamp,
                'tag':self.tag}
        
    cpdef __reduce__(self):
        return(self.__class__,( self.oid,
                                self.hashed_oid,
                                self.broker_order_id,
                                self.exchange_order_id,
                                self.parent_order_id,
                                self.asset,
                                self.user,
                                self.placed_by,
                                self.product_type,
                                self.order_flag,
                                self.order_type,
                                self.order_validity,
                                self.quantity,
                                self.filled,
                                self.pending,
                                self.disclosed,
                                self.price,
                                self.average_price,
                                self.trigger_price,
                                self.stoploss_price,
                                self.side,
                                self.status,
                                self.status_message,
                                self.exchange_timestamp,
                                self.timestamp,
                                self.tag))
        
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

        
    cpdef update(self,int update_type, object kwargs):
        '''
            This method is called by the execution platform, based on the 
            type of updates to be done appropriate arguments must be passed.
            No validation done here.
        '''
        if update_type == OrderUpdateType.EXECUTION:
            self.partial_execution(kwargs)
        elif update_type == OrderUpdateType.MODIFICATION:
            self.user_update(kwargs)
        elif update_type == OrderUpdateType.CANCEL:
            self.partial_cancel()
        else:
            self.reject(kwargs)

        
        
    cpdef partial_execution(self, Trade trade):
        '''
            Pass on a Trade object to update a full or partial execution
        '''
        self.average_price = (self.filled*self.average_price + \
                trade.quantity*trade.average_price)
        self.filled = self.filled + trade.quantity
        self.average_price = self.average_price/self.filled
        self.pending = self.quantity - self.filled
        if self.pending > 0:
            self.status = OrderStatus.OPEN
            self.status_message = 'open'
        else:
            self.status = OrderStatus.COMPLETE
            self.status_message = 'complete'
            
        if self.broker_order_id is None:
            self.broker_order_id = trade.broker_order_id
            self.exchange_order_id = trade.exchange_order_id
            self.exchange_timestamp = trade.exchange_timestamp
            self.timestamp = trade.timestamp
            
    cpdef partial_cancel(self):
        '''
            This cancels the remaining part of the order. The order is marked
            cancelled. The exeucted part should modify the corresponding
            positions already
        '''
        self.status = OrderStatus.CANCELLED
        self.status_message = 'cancel'
        
    cpdef reject(self, object reason):
        '''
            The case of reject. A reject can never be partial. the argument
            passed is a string explaining the reason to reject.
        '''
        self.status = OrderStatus.REJECTED
        self.status_message = reason
            
        
    cpdef user_update(self, object kwargs):
        '''
            Fields to be updated on user request. All fields may 
            not be present.
        '''
        if 'price' in kwargs:
            self.price = kwargs['price']
        if 'quantity' in kwargs:
            self.quantity = kwargs['quantity']
        
        if 'trigger_price' in kwargs:
            self.trigger_price = kwargs['trigger_price']
        if 'stoploss_price' in kwargs:
            self.stoploss_price = kwargs['stoploss_price']
        if 'order_type' in kwargs:
            self.order_type = kwargs['order_type']
        if 'order_validity' in kwargs:
            self.order_validity = kwargs['order_validity']
            
        if 'tag' in kwargs:
            self.tag = kwargs['tag']
        if 'disclosed' in kwargs:
            self.disclosed = kwargs['disclosed']
        

        
        
        