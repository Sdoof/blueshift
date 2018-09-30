# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _order.pyx>

cimport cython
cimport _order_types
from _trade cimport Trade
import uuid

status_dict = {0:'complete',1:'open',2:'rejected',3:'cancelled'}

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
    cdef readonly int sid
    cdef readonly object symbol
    cdef readonly object exchange_name
    cdef readonly object user
    cdef readonly object placed_by
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
    cdef readonly object side
    cdef readonly int status
    cdef readonly object status_message
    cdef readonly object exchange_timestamp
    cdef readonly object timestamp
    cdef readonly object tag
    
    def __init__(self,
                 int quantity,              # required
                 int side,                  # required
                 object symbol=None,        # required/ or sid
                 object exchange_name=None, # required/ or sid
                 int sid=-1,                # overrides symbol+exchange
                 int product_type=_order_types.DELIVERY,
                 int order_flag=_order_types.NORMAL,
                 int order_type=_order_types.NORMAL,
                 int order_validity = _order_types.DAY,
                 int disclosed=0,
                 float price=0,
                 float trigger_price=0,
                 object user='algo',
                 object placed_by='algo',
                 object tag='blueshift'):
        '''
            The only agent who can create (or delete) an order is 
            the user trading agent. The broker cannot create an order.
            At the time of creation, user algo can only know about
            order details known at user level. So things like filled,
            pending, status etc are set accordingly and are not part
            of the init arguments.
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
            
        self.side = side
        self.quantity = quantity
        
        self.oid = uuid.uuid4().hex
        self.hashed_oid = hash(self.oid)
        self.broker_order_id=None
        self.exchange_order_id = None
        self.parent_order_id = None
    
        self.user=user
        self.placed_by=placed_by
        self.product_type=product_type
        self.order_flag=order_flag
        self.order_type=order_type
        self.order_validity=order_validity
        
        self.filled=0
        self.pending=self.quantity
        self.disclosed=disclosed
        self.price=price
        self.average_price=0
        self.trigger_price=trigger_price
    
        self.status=_order_types.OPEN
        self.status_message=""
        self.exchange_timestamp=None
        self.timestamp=None
        self.tag=tag
    
    def __int__(self):
        return self.hashed_oid
    
    def __hash__(self):
        return self.hashed_oid
    
    def __eq__(x,y):
        try:
            return int(x) == int(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Order:sym:%s,qty:%d,status:%s' % (self.symbol,\
                    self.quantity, status_dict[self.status])
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {
                'oid':self.oid,
                'hashed_oid':self.hashed_oid,
                'broker_order_id':self.broker_order_id,
                'exchange_order_id':self.exchange_order_id,
                'parent_order_id':self.parent_order_id,
                'sid':self.sid,
                'symbol':self.symbol,
                'exchange_name':self.exchange_name,
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
                                self.sid,
                                self.symbol,
                                self.exchange_name,
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
        if update_type == _order_types.EXECUTION:
            self.partial_execution(kwargs)
        elif update_type == _order_types.MODIFICATION:
            self.user_update(kwargs)
        elif update_type == _order_types.CANCEL:
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
            self.status = _order_types.OPEN
            self.status_message = 'open'
        else:
            self.status = _order_types.COMPLETE
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
        self.status = _order_types.CANCEL
        self.status_message = 'cancel'
        
    cpdef reject(self, object reason):
        '''
            The case of reject. A reject can never be partial. the argument
            passed is a string explaining the reason to reject.
        '''
        self.status = _order_types.REJECT
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
        if 'order_type' in kwargs:
            self.order_type = kwargs['order_type']
        if 'order_validity' in kwargs:
            self.order_validity = kwargs['order_validity']
            
        if 'tag' in kwargs:
            self.tag = kwargs['tag']
        if 'disclosed' in kwargs:
            self.disclosed = kwargs['disclosed']
        

        
        
        