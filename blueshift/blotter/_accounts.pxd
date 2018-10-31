# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 09:28:57 2018

@author: prodipta
"""

cimport cython
from blueshift.trades._trade cimport Trade
from cpython cimport bool
    
cdef class Account:
    cdef readonly float margin      
    cdef readonly float net         
    cdef readonly object name
    cdef readonly object currency
    cdef readonly float gross_leverage
    cdef readonly float net_leverage
    cdef readonly float gross_exposure
    cdef readonly float net_exposure
    cdef readonly float cash
    cdef readonly float mtm
    cdef readonly float liquid_value
    cdef readonly float commissions
    
    cpdef to_dict(self)
    cpdef __reduce__(self)
    
cdef class BacktestAccount(Account):
    cpdef settle_trade(self, Trade t)
    cpdef fund_transfer(self, float amount)
    cpdef block_margin(self, float amount)
    cpdef release_margin(self, float amount)
    cpdef update_accounts(self,float mtm, float gross, float net)
    
cdef class EquityAccount(Account):
    cpdef reconcile(self, object trades, object positions)