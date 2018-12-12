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
        return 'Blueshift Account [name:%s, net:%.2f, cash:%.2f, mtm:%.2f]' % \
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
    
    cpdef update_account(self, float cash, float margin, 
                         dict positions):
        # run all updates in series
        self.cash = cash
        self.margin = margin
        self.liquid_value = self.cash + self.margin
        
        self.update_from_positions(positions)
    
    cdef update_from_positions(self, dict positions):
        net_exposure = 0
        gross_exposure = 0
        mtm = 0
        for pos in positions:
            position = positions[pos]
            if position.if_closed():
                continue
            net_exposure = net_exposure + (position.buy_quantity - \
                            position.sell_quantity)*position.last_price
            gross_exposure = position.quantity*position.last_price +\
                                gross_exposure
            mtm = position.unrealized_pnl + mtm
        
        if self.liquid_value > 0:
            self.gross_leverage = gross_exposure/self.liquid_value
            self.net_leverage = net_exposure/self.liquid_value
        
        self.gross_exposure = gross_exposure
        self.net_exposure = net_exposure
        self.mtm = mtm
        self.net = self.mtm + self.liquid_value
    
cdef class BacktestAccount(Account):
    '''
        back-testing account.
    '''
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
        
        
cdef class TradingAccount(Account):
    '''
        real trading account. Most of the stuff is already done by the 
        broker.
    '''
    cpdef reconcile(self, object trades, object positions):
        pass
        
cdef class EquityAccount(TradingAccount):
    '''
        Trading account for equity trading.
    '''
    pass
    
cdef class ForexAccount(TradingAccount):
    '''
        Trading account for equity trading.
    '''
    cpdef convert_currency(self, object currency):
        pass
    