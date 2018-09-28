# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

# compile with <cythonize -i _trade.pyx>

cimport cython
cimport _order_types

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
                 object symbol,        
                 object exchange_name, 
                 int sid,                
                 int product_type,
                 float average_price,
                 object exchange_timestamp,
                 object timestamp):
        '''
            The only agent who can create a trade is the execution 
            platform. All fields are required.
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
            
        self.tid = tid
        self.hashed_tid = hash(tid)
        self.oid = oid
        self.broker_order_id = broker_order_id
        self.exchange_order_id = exchange_order_id
        self.instrument_id = instrument_id
        self.product_type = product_type
        self.average_price = average_price
        self.exchange_timestamp = exchange_timestamp
        self.timestamp = timestamp
        
    def __int__(self):
        return self.hashed_tid
    
    def __hash__(self):
        return self.hashed_tid
    
    def __eq__(x,y):
        try:
            return int(x) == int(y)
        except (TypeError, AttributeError, OverflowError):
            raise TypeError
            
    def __str__(self):
        return 'Trade:sym:%s,qty:%d,average price:%f' % (self.symbol,\
                    self.quantity, self.average_price)
    
    def __repr__(self):
        return self.__str__()
    
    cpdef to_dict(self):
        return {'tid':self.tid,
                'hashed_tid':self.hashed_tid,
                'oid':self.oid,
                'broker_order_id':self.broker_order_id,
                'exchange_order_id':self.exchange_order_id,
                'instrument_id':self.instrument_id,
                'sid':self.sid,
                'symbol':self.symbol,
                'exchange_name':self.exchange_name,
                'side':self.side,
                'product_type':self.product_type,
                'average_price':self.average_price,
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
                                self.sid,
                                self.symbol,
                                self.exchange_name,
                                self.side,
                                self.product_type,
                                self.average_price,
                                self.quantity,
                                self.exchange_timestamp,
                                self.timestamp))
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
        