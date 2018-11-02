# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 09:28:57 2018

@author: prodipta
"""
cimport cython
from cpython cimport bool
from blueshift.trades._trade cimport Trade
from blueshift.trades._position cimport Position
from blueshift.utils.exceptions import InsufficientFund

cdef class Account:
    '''
        Trade object definition. A trade belongs to an order that 
        generated the trade(s)
    '''
    
    def __init__(self,
                 object name,    
                 float cash,                # available cash
                 float margin=0,            # blocked margin
                 float gross_exposure=0,    # existing exposure
                 float net_exposure=0,      # existing exposure
                 float mtm=0,               # unrealized position value
                 float commissions=0,       # cumulative commissions
                 object currency='local'):
        
        self.name = name
        self.cash = cash
        self.gross_exposure = gross_exposure
        self.net_exposure = net_exposure
        self.margin = margin
        self.mtm = mtm
        self.currency = currency
        self.commissions = commissions
        
        self.liquid_value = self.cash + self.margin
        self.net = self.mtm + self.liquid_value
        if self.liquid_value > 0:
            self.gross_leverage = round(self.gross_exposure/self.liquid_value,2)
            self.net_leverage = round(self.net_exposure/self.liquid_value,2)
        else:
            self.gross_leverage = 0
            self.net_leverage = 0
            
    cpdef to_dict(self):
        return {'margin':self.margin,
                'net':self.net,
                'name':self.name,
                'currency':self.currency,
                'gross_leverage':self.gross_leverage,
                'net_leverage':self.net_leverage,
                'gross_exposure':self.gross_exposure,
                'net_exposure':self.net_exposure,
                'cash':self.cash,
                'mtm':self.mtm,
                'liquid_value':self.liquid_value,
                'commissions':self.commissions}
        
    def __str__(self):
        return 'Account:name:%s, net:%.2f, cash:%.2f, mtm:%.2f' % \
                    (self.name,self.net,self.cash, self.mtm)
    
    def __repr__(self):
        return self.__str__()
    
    cpdef __reduce__(self):
        return(self.__class__,( self.margin,
                                self.net,
                                self.name,
                                self.currency,
                                self.gross_leverage,
                                self.net_leverage,
                                self.gross_exposure,
                                self.net_exposure,
                                self.cash,
                                self.mtm,
                                self.liquid_value,
                                self.commissions))
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
cdef class BacktestAccount(Account):
    
    cpdef fund_transfer(self, float amount):
        if amount + self.cash < 0:
            raise InsufficientFund()
            
        self.cash = self.cash + amount
        self.net = self.net + amount
        self.liquid_value = self.liquid_value + amount
        
    cpdef settle_trade(self, Trade t):
        # a trade can require cash flow and/ or margin block
        if t.cash_flow + t.margin > self.cash:
            raise InsufficientFund()
            
        self.cash = self.cash - t.cash_flow
        if t.margin > 0:
            self.block_margin(t.margin)
        else:
            self.release_margin(-t.margin)
        
        # ideally a trade should impact the net value only by commission
        self.net = self.net - t.commission
        self.liquid_value = self.liquid_value - t.commission
        self.commissions = self.commissions + t.commission
        
    cpdef release_margin(self, float amount):
        if self.margin < amount:
            amount = self.margin
            
        self.cash = self.cash + amount
        self.margin = self.margin - amount
        
    cpdef block_margin(self, float amount):
        if self.cash < amount:
            raise InsufficientFund()
            
        self.cash = self.cash - amount
        self.margin = self.margin + amount
        
    cpdef update_accounts(self, float mtm, float gross, float net):
        
        # run all updates in series
        self.mtm = self.mtm + mtm
        self.net = self.net + mtm
        
        self.gross_exposure = self.gross_exposure + gross
        self.net_exposure = self.net_exposure + net
        self.gross_leverage = round(self.gross_exposure/self.liquid_value,2)
        self.net_leverage = round(self.net_exposure/self.liquid_value,2)
        
cdef class EquityAccount(Account):
    
    cpdef reconcile(self, object trades, object positions):
        pass