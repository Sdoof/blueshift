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
    cpdef update_account(self, float cash, float margin, 
                         dict positions)
    cdef update_from_positions(self, dict positions)
    
cdef class BacktestAccount(Account):
    cpdef settle_trade(self, Trade t)
    cpdef fund_transfer(self, float amount)
    cpdef block_margin(self, float amount)
    cpdef release_margin(self, float amount)
    
cdef class TradingAccount(Account):
    cpdef reconcile(self, object trades, object positions)

cdef class EquityAccount(TradingAccount):
    pass

cdef class ForexAccount(TradingAccount):
    cpdef convert_currency(self, object currency)