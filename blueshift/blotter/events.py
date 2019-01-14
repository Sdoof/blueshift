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
Created on Fri Jan 11 17:13:25 2019

@author: prodipta
"""

"""
blotter scheme

1. keep track of unreconciled orders
2. at each `order` function call, add to the list
3. at each `reconcile` call process the items remaining on the list

blotter func

1. add_orders
2. todays_perf
3. todays_risk
4. todays_report (perf + risk + reconciliation)
5. reconcile
6. save
7. load
8. roll_over
9. ammend ( dividends/ intereset recievd or updated cost/ margins paid etc.)


accounts events:
change account data or positions data or both.
1. margin call -> adjust cash (-) and margin (+)
2. interest payments -> adjust cash (+/-)
3. capital transfer -> adjust cash (+/-)
4. corporate actions -> adjust cash (dividends+), positions (split, bonuses, mergers)
5. commissions -> adjust cash (reduce)

"""

from abc import ABC, abstractmethod

class AccountEvent(ABC):
    """
        Encapsulation of accounts events like margin calls, corporate 
        actions etc. The responsibility to emit this events is with the
        broker object of the algorithm. The responsibility to handle these
        events are with the blotter object.
    """
    def __init__(self, *args, **kwargs):
        self._applied = False
    
    @abstractmethod
    def apply(self):
        raise NotImplementedError
        
class RollOver(AccountEvent):
    """
        Roll-over applied to assets, typically Forex positions. This can 
        also include any other interest accrued.
    """
    def __init__(self, asset, effective_dt, pct_long_cost):
        """
            pct_long_cost: rollover cost for a long position in percentage.
        """
        self._asset = asset
        self._effective_dt = effective_dt
        self._cost = pct_long_cost
        super(RollOver, self).__init__()
        
    def apply(self, account, blotter):
        if self._applied:
            return
        
        if self._asset in blotter._positions:
            cash = blotter._positions[self._asset].quantity*self._cost
        account.cashflow(cash=cash, margin=0)
        self._applied = True
        
class CapitalChange(AccountEvent):
    """
        Roll-over applied to assets, typically Forex positions. This can 
        also include any other interest accrued.
    """
    def __init__(self, asset, effective_dt, amount):
        """
            pct_long_cost: rollover cost for a long position in percentage.
        """
        self._asset = asset
        self._effective_dt = effective_dt
        self._amount = amount
        super(CapitalChange, self).__init__()
        
    def apply(self, account, blotter):
        if self._applied:
            return
        
        account.cashflow(cash=self._amount, margin=0)
        self._applied = True
        
class CorporateAction(AccountEvent):
    """
        Class for corporate actions
    """
    def __init__(self, asset, effective_dt, announcement_dt, *args, **kwargs):
        self._asset = asset
        self._effective_dt = effective_dt
        self._announcement_dt = announcement_dt
        super(CorporateAction, self).__init__()
        
    @abstractmethod
    def apply(self):
        raise NotImplementedError
        
class StockDividend(AccountEvent):
    """
        Class for corporate actions
    """
    def __init__(self, asset, effective_dt, announcement_dt, div_ratio):
        self.div_ratio = div_ratio
        super(StockDividend, self).__init__(asset, effective_dt, announcement_dt)
        
    def apply(self, account, blotter):
        if self._applied:
            return
        
        if self._asset in blotter._positions:
            cash = blotter._positions[self._asset].quantity*self.div_ratio
        account.cashflow(cash=cash, margin=0)
        self._applied = True

class StockSplit(AccountEvent):
    """
        Class for corporate actions
    """
    def __init__(self, asset, effective_dt, announcement_dt, split_ratio):
        self._split_ratio = split_ratio
        super(StockSplit, self).__init__(asset, effective_dt, announcement_dt)
        
    def apply(self, account, blotter):
        if self._applied:
            return
        
        if self._asset in blotter._positions:
            cash = blotter._positions[self._asset].apply_split(self._split_ratio)
        account.cashflow(cash=cash, margin=0)
        self._applied = True
            
class StockMerger(AccountEvent):
    """
        Class for corporate actions
    """
    def __init__(self, asset, effective_dt, announcement_dt, acquirer,
                 exchange_ratio, offer_price=0, cash_pct = 0):
        self._exchange_ratio = exchange_ratio
        self._acquirer = acquirer
        self._offer_price = offer_price
        self._cash_pct = cash_pct
        super(StockMerger, self).__init__(asset, effective_dt, announcement_dt)
        
    def apply(self, account, blotter):
        if self._applied:
            return
        
        if self._asset in blotter._positions:
            cash1 = blotter._positions[self._asset].quantity\
                    *self._cash_pct*self._offer_price
            
            cash2 = blotter._positions[self._asset].apply_merger(
                    self._acquirer, self._exchange_ratio, self._cash_pct)
            blotter._positions[self._target] = blotter._positions.pop(
                    self._asset)
            account.cashflow(cash=cash1+cash2, margin=0)
            self._applied = True
            
        
        
        
        
        
        
        
        
        
        
        
        