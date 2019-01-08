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
Created on Mon Jan  7 13:11:51 2019

@author: prodipta
"""
from abc import ABC, abstractmethod 

from blueshift.trades._order_types import OrderSide
from blueshift.utils.decorators import singleton
from blueshift.utils.types import noop

class TradingControl(ABC):
    '''
        implements trading controls and restrictions. The controls are of
        two types - flow based control (applies to each order) and stock based
        control (applies to current state). The class implements `validate`
        function which returns True if the checks are passed. Else it returns
        false.
    '''
    def __init__(self, *args, **kwargs):
        self._on_fail = kwargs.get("on_fail", noop)
        self._metric = 0
        self._limit = 0
        
    def _create(self, dt, max_num_orders=100, on_fail=None):
        '''
            creating a control on-the-fly can potentially reset current
            used up limits. So we do not allow it.
        '''
        pass
    
    @abstractmethod
    def get_error_msg(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_control(self, *args, **kwargs):
        raise NotImplementedError    
    
    @abstractmethod
    def validate(self, asset, amount, dt, context, on_fail=None, 
                 *args, **kwargs):
        raise NotImplementedError
        
@singleton
class TCOrderQtyPerTrade(TradingControl):
    '''
        Class implementing max order quantity per single order.
    '''
    def __init__(self, default_max, max_amount_dict=None,
                 on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = abs(default_max)
        self.add_control({})
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
        for asset in self._max_amount_dict:
            self._max_amount_dict[asset] = abs(self._max_amount_dict[asset])
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        
        if not max_allowed:
            return True
        
        if abs(amount) < max_allowed:
            return True
        
        self._metric = amount
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per trade size control for {asset}"
        msg = msg + f", amount {self._metric} against limit {self._limit}"
        msg = msg + f", on {dt}"
        return msg
    

@singleton
class TCOrderValuePerTrade(TradingControl):
    '''
        Class implementing max order value per single order.
    '''
    def __init__(self, default_max, max_amount_dict=None, 
                 on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = default_max
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        
        if not max_allowed:
            return True
        
        price = context.data_portal.current(asset, 'close')
        value = abs(amount*price)
        
        if value < max_allowed:
            return True
        
        self._metric = value
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per trade value control for {asset}"
        msg = msg + f", value {self._metric} against limit {self._limit}"
        msg = msg + f", on {dt}"
        return msg
    
@singleton
class TCOrderQtyPerDay(TradingControl):
    '''
        Class implementing max order quantity per asset per day.
    '''
    def __init__(self, default_max, max_amount_dict=None, 
                 on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = abs(default_max)
        self.add_control({})
        self._asset_quota = dict((asset,0) for asset in self._max_amount_dict)
        self._current_dt = None
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
        for asset in self._max_amount_dict:
            self._max_amount_dict[asset] = abs(self._max_amount_dict[asset])
    
    def _reset_quota(self):
        for asset in self._asset_quota:
            self._asset_quota[asset] = 0
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        
        if self._current_dt != dt.date():
            self._reset_quota()
            self._current_dt = dt.date()
        
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        
        if not max_allowed:
            return True
        
        max_used = self._asset_quota.get(asset, 0)
        estimated = abs(amount)+max_used
        
        if  estimated < max_allowed:
            self._asset_quota[asset] = estimated
            return True
        
        self._metric = max_used
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per day trade amount control for {asset}"
        msg = msg + f", total amount {self._metric}"
        msg = msg + f" against limit {self._limit}, on {dt}"
        return msg
    
@singleton
class TCOrderValuePerDay(TradingControl):
    '''
        Class implementing max order value per asset per day.
    '''
    def __init__(self, default_max, max_amount_dict=None, 
                 on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = abs(default_max)
        self.add_control({})
        self._asset_quota = dict((asset,0) for asset in self._max_amount_dict)
        self._current_dt = None
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
        for asset in self._max_amount_dict:
            self._max_amount_dict[asset] = abs(self._max_amount_dict[asset])
    
    def _reset_quota(self):
        for asset in self._asset_quota:
            self._asset_quota[asset] = 0
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        
        if self._current_dt != dt.date():
            self._reset_quota()
            self._current_dt = dt.date()
        
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        
        if not max_allowed:
            return True
        
        max_used = self._asset_quota.get(asset, 0)
        price = context.data_portal.current(asset, 'close')
        value = abs(amount*price)
        estimated = abs(value)+max_used
        
        if  estimated < max_allowed:
            self._asset_quota[asset] = estimated
            return True
        
        self._metric = max_used
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per day trade value control for {asset}"
        msg = msg + f", total value {self._metric}"
        msg = msg + f" against limit {self._limit}, on {dt}"
        return msg
    
@singleton
class TCOrderNumPerDay(TradingControl):
    '''
        Class implementing max order number for all assets per day.
    '''
    def __init__(self, max_num_orders, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_num_orders = max_num_orders
        self._used_limit = 0
        self._current_dt = None
        
    def add_control(self, max_num_orders):
        self._max_num_orders = max_num_orders
    
    def _reset_quota(self):
        self._used_limit = 0
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        
        if self._current_dt != dt.date():
            self._reset_quota()
            self._current_dt = dt.date()
        
        if  self._used_limit+1 < self._max_num_orders:
            self._used_limit = self._used_limit+1
            return True
        
        self._metric = self._used_limit
        self._limit = self._max_num_orders
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per day number of orders control"
        msg = msg + f", total orders {self._metric}"
        msg = msg + f" against limit {self._limit}, on {dt}"
        return msg
    
@singleton
class TCGrossLeverage(TradingControl):
    '''
        Class implementing max account gross leverage.
    '''
    def __init__(self, max_leverage, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_leverage = max_leverage
        
    def add_control(self, max_leverage):
        self._max_leverage = max_leverage
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        
        current_exposure = context.account.gross_exposure
        liquid_value = context.account.liquid_value
        trade_value = abs(context.data_portal.current(asset, 'close')*amount)
        estimated_exposure = current_exposure + trade_value
        estimated_leverage = estimated_exposure/liquid_value
        
        if estimated_leverage < self._max_leverage:
            return True
        
        self._metric = estimated_leverage
        self._limit = self._max_leverage
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per max leverage control"
        msg = msg + f", estimated post trade leverage {self._metric}"
        msg = msg + f" against limit {self._limit}, on {dt}"
        return msg
    
class TCGrossExposure(TradingControl):
    '''
        Class implementing max account gross leverage.
    '''
    def __init__(self, max_exposure, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_exposure = max_exposure
        
    def add_control(self, max_exposure):
        self._max_exposure = max_exposure
    
    def validate(self, order, dt, context, on_fail=noop):
        amount = order.quantity
        asset = order.asset
        current_exposure = context.account.gross_exposure
        trade_value = abs(context.data_portal.current(asset, 'close')*amount)
        estimated_exposure = current_exposure + trade_value
        
        if estimated_exposure < self._max_exposure:
            return True
        
        self._metric = estimated_exposure
        self._limit = self._max_exposure
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed per max exposure control"
        msg = msg + f", estimated post trade exposure {self._metric}"
        msg = msg + f" against limit {self._limit}, on {dt}"
        return msg
    
    
class TCLongOnly(TradingControl):
    '''
        Class implementing max account gross leverage.
    '''
    def __init__(self, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        
    def add_control(self, max_exposure):
        pass
    
    def validate(self, order, dt, context, on_fail=noop):
        side = 1 if order.side == OrderSide.BUY else -1
        amount = order.quantity*side
        asset = order.asset
        
        current_pos = context.portfolio.get(asset, None)
        if current_pos:
            current_pos = current_pos.quantity
        else:
            current_pos = 0
        estimated_pos = current_pos + amount
        
        if estimated_pos >0:
            return True
        
        self._metric = estimated_pos
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed long-only control"
        msg = msg + f", estimated post trade position {self._metric}"
        msg = msg + f", on {dt}"
        return msg
    
class TCPositionQty(TradingControl):
    '''
        Class implementing max position size.
    '''
    def __init__(self, default_max, max_amount_dict=None, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = abs(default_max)
        self.add_control({})
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
        for asset in self._max_amount_dict:
            self._max_amount_dict[asset] = abs(self._max_amount_dict[asset])
    
    def validate(self, order, dt, context, on_fail=noop):
        side = 1 if order.side == OrderSide.BUY else -1
        amount = order.quantity*side
        asset = order.asset
        
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        if not max_allowed:
            return True
        
        current_pos = context.portfolio.get(asset, None)
        if current_pos:
            current_pos = current_pos.quantity
        else:
            current_pos = 0
        estimated_pos = abs(current_pos + amount)
        
        if estimated_pos < max_allowed:
            return True
        
        self._metric = estimated_pos
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed max position size control for {asset}"
        msg = msg + f", estimated post trade position {self._metric}"
        msg = msg + f" against limit of {self._limit}, on {dt}"
        return msg

class TCPositionValue(TradingControl):
    '''
        Class implementing max position size.
    '''
    def __init__(self, default_max, max_amount_dict=None, on_fail=None):
        # pylint: disable=bad-super-call
        super(self.__class__, self).__init__(on_fail=on_fail)
        self._max_amount_dict = max_amount_dict if max_amount_dict else {}
        self._default_max = abs(default_max)
        self.add_control({})
        
    def add_control(self, max_amount_dict):
        self._max_amount_dict = {**self._max_amount_dict, **max_amount_dict}
        for asset in self._max_amount_dict:
            self._max_amount_dict[asset] = abs(self._max_amount_dict[asset])
    
    def validate(self, order, dt, context, on_fail=noop):
        side = 1 if order.side == OrderSide.BUY else -1
        amount = order.quantity*side
        asset = order.asset
        
        max_allowed = self._max_amount_dict.get(asset, self._default_max)
        if not max_allowed:
            return True
        
        current_pos = context.portfolio.get(asset, None)
        if current_pos:
            current_pos = current_pos.quantity
        else:
            current_pos = 0
        estimated_pos = abs(current_pos + amount)
        price = context.data_portal.current(asset, 'close')
        value = estimated_pos*price
        
        if value < max_allowed:
            return True
        
        self._metric = value
        self._limit = max_allowed
        
        if self._on_fail:
            self._on_fail(self, asset, dt, amount, context)
        else:
            on_fail(self, asset, dt, amount, context)
            
        return False
    
    def get_error_msg(self, asset, dt):
        msg = f"Failed max position size control for {asset}"
        msg = msg + f", estimated post trade position {self._metric}"
        msg = msg + f" against limit of {self._limit}, on {dt}"
        return msg
    
    
    
    
    