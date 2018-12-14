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
Created on Wed Dec 12 14:16:49 2018

@author: prodipta
"""

import pandas as pd
from enum import Enum

from requests.exceptions import RequestException

from fxcmpy.fxcmpy import ServerError

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.utils.brokers.fxcm.kiteauth import (FXCMAuth, FXCMPy)
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        BrokerAPIError)
from blueshift.blotter._accounts import ForexAccount
from blueshift.trades._position import Position
from blueshift.trades._order_types import (ProductType,
                                           OrderValidity,
                                           OrderFlag,
                                           OrderSide,
                                           OrderStatus,
                                           OrderType)
from blueshift.trades._order import Order
from blueshift.utils.decorators import api_rate_limit, singleton, blueprint
from blueshift.utils.general_helpers import OnetoOne
from blueshift.utils.types import BrokerType, MODE

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    
product_type_map = OnetoOne({'NRML':ProductType.DELIVERY, 
                    'MIS':ProductType.INTRADAY})
order_validity_map = OnetoOne({'DAY':OrderValidity.DAY,
                    'GTC':OrderValidity.GTC})
order_flag_map = OnetoOne({'NORMAL':OrderFlag.NORMAL, 
                    'AMO':OrderFlag.AMO})
order_side_map = OnetoOne({'BUY':OrderSide.BUY, 
                    'SELL':OrderSide.SELL})
order_status_map = OnetoOne({'COMPLETE':OrderStatus.COMPLETE, 
                    'OPEN':OrderStatus.OPEN,
                    'REJECTED':OrderStatus.REJECTED,
                    'CANCELLED':OrderStatus.CANCELLED})
order_type_map = OnetoOne({'MARKET':OrderType.MARKET,
                  'LIMIT':OrderType.LIMIT,
                  'STOPLOSS':OrderType.STOPLOSS,
                  'STOPLOSS_MARKET':OrderType.STOPLOSS_MARKET})

@singleton
@blueprint
class FXCMBroker(AbstractBrokerAPI):
    '''
        Implements the broker interface functions.
    '''
    def __init__(self, 
                 name:str="kite", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=None,
                 **kwargs):
        self._create(name, broker_type, calendar, **kwargs)
            
    def _create(self, 
                 name:str="fxcm", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=None,
                 **kwargs):
        check_input(FXCMBroker.__init__, locals())
        super(self.__class__, self).__init__(name, broker_type, calendar,
                                             **kwargs)
        self._mode_supports = [MODE.LIVE]
        self._auth = kwargs.pop("auth",None)
        self._asset_finder = kwargs.pop("asset_finder",None)
        self._api = None
        
        if not self._asset_finder:
            msg = "Broker needs a corresponding Asset Finder"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
        if not self._auth:
            msg = "authentication and API missing"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        if not self._trading_calendar:
            self._trading_calendar = self._auth._trading_calendar
        
        if self._auth.__class__ != FXCMAuth.cls:
            msg = "invalid authentication object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._api = self._auth._api
            
        if self._api.__class__ != FXCMPy.cls:
            msg = "invalid kite API object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._closed_orders = {}
        self._open_orders = {}
        self._open_positions = {}
        self._closed_positions = []
        
        self._account = ForexAccount(self._name,0.01)
    
    def __str__(self):
        return 'Blueshift Broker [name:%s, type:%s]'%(self._name, self._type)
    
    def __repr__(self):
        return self.__str__()
    
    def process_response(self, response):
        '''
            We probably do not need this as we use the pyconnect
            package which does this for us already.
        '''
        if response['status'] == ResponseType.SUCCESS.value:
            return response['data']
        else:
            msg = response['data']
            raise BrokerAPIError(msg=msg)
            
    def login(self, *args, **kwargs):
        self._auth.login(*args, **kwargs)
        
    def logout(self, *args, **kwargs):
        self._auth.logout()
    
    @property
    def calendar(self):
        return self._trading_calendar
    
    @property
    def profile(self):
        '''
            Fetch and return the user profile.
        '''
        try:
            default_account = self._api.default_account
            accounts = self._api.account_ids
            return {'default_account':default_account,
                    'account_ids':accounts}
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.LOG
            raise BrokerAPIError(msg=msg, handling=handling)
        
    @property
    @api_rate_limit
    def account(self):
        '''
            This will call positions and update the accounts
            and return.
        '''
        last_version = self._account
        try:
            data = self._api.margins()
            cash = data['equity']['available']['cash'] +\
                data['equity']['available']['intraday_payin']-\
                data['equity']['utilised']['payout'] +\
                data['equity']['utilised']['m2m_realised']
            margin = data['equity']['utilised']['exposure'] +\
                data['equity']['utilised']['span'] +\
                data['equity']['utilised']['option_premium']
            _positions = self.positions
            self._account.update_account(cash, margin,
                                         _positions)
            return self._account.to_dict()
        except KiteException as e:
            if isinstance(e, NetworkException):
                self._account =  last_version
                return self._account.to_dict()
            else:
                msg = str(e)
                handling = ExceptionHandling.WARN
                raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    @api_rate_limit
    def positions(self):
        '''
            Fetch the positions
        '''
        try:
            position_details = self._api.positions()
            if not position_details:
                return self._open_positions
            
            position_details = position_details['net']
            for p in position_details:
                asset, position = self._position_from_dict(p)
                self._open_positions[asset] = position
                if self._open_positions[asset].if_closed():
                    self._closed_positions.append(
                            self._open_positions.pop(asset))
            
            return self._open_positions
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    @api_rate_limit
    def open_orders(self):
        '''
            Call the order method and return the open order dict.
        '''
        _ = self.orders
        return self._open_orders
    
    @property
    @api_rate_limit
    def orders(self, *args, **kwargs):
        '''
            Fetch a list of orders from the broker and update
            internal dicts. Returns both open and closed orders.
        '''
        try:
            orders = self._api.orders()
            if orders is None:
                return {**self._open_orders, **self._closed_orders}
            
            for o in orders:
                # we assume no further updates on closed orders
                if o['order_id'] in self._closed_orders:
                    continue
                
                order_id, order = self._order_from_dict(o)
                if order.status == OrderStatus.OPEN:
                    self._open_orders[order_id] = order
                else:
                    # add to closed orders dict
                    self._closed_orders[order_id] = order
                    # pop from open order if it was there
                    if order_id in self._open_orders:
                        self._open_orders.pop(order_id)
            
            return {**self._open_orders, **self._closed_orders}
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    def tz(self, *args, **kwargs):
        return self._trading_calendar.tz
    
    def order(self, order_id):
        '''
            Fetch the order by id.
        '''
        orders = self.orders
        return orders.get(order_id, None)
    
    @api_rate_limit
    def place_order(self, order):
        '''
            Place a new order. Order asset will be converted to
            an asset understood by the broker.
        '''
        quantity = order.quantity
        
        asset = self._asset_finder.symbol_to_asset(
                order.asset.symbol)
        tradingsymbol = asset.symbol
            
        is_buy = False if order.side > 0 else True
        order_type = order.order_type
        price = order.price
        validity = order.order_validity
        stoploss_price = order.stoploss_price
        trigger_price = order.trigger_price
        # TODO: we track algo by adding a specifc account id
        # generalize this. Must have broker support to implement.
        tag = order.tag
        tag = tag if tag in self._api.account_ids else None
        
        validity = order_validity_map.teg(validity, 'DAY')
        
        #TODO: assumption price cannot be negative
        tick_size = asset.tick_size
        price = price if price > 0 else 0
        trigger_price = trigger_price if trigger_price > 0 else 0
        stoploss_price = stoploss_price if stoploss_price > 0 else 0
        
        lots = quantity/asset.mult
        try:
            if price > 0 and order_type > 0:
                
                order_id = self._api.create_entry_order(
                        symbol = tradingsymbol, is_buy = is_buy, amount =lots, 
                        time_in_force = validity, order_type="Entry", 
                        is_in_pips = False, limit=trigger_price, 
                        stop=stoploss_price, 
                        rate = price, account_id=tag)
            else:
                if is_buy > 0:
                    # we buy!
                    order_obj = self._api.create_market_buy_order(
                            tradingsymbol, lots, account_id=tag)
                else:
                    # we sell!
                    order_obj = self._api.create_market_sell_order(
                            tradingsymbol, lots, account_id=tag)
        except (ValueError, TypeError, ServerError) as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        else:
            order_id, order =  self._order_from_dict(order_obj)
            
            return order_id
    
    @api_rate_limit
    def update_order(self, order_param, *args, **kwargs):
        '''
            Update an existing order.
        '''
        if isinstance(order_param, Order):
            order_id = order_param.oid
            variety = order_param.order_flag
            parent_order_id = order_param.parent_order_id
        else:
            order_id = order_param
            order = self._open_orders.get(order_id,None)
            if order:
                variety = order_param.order_flag
                parent_order_id = order_param.parent_order_id
            else:
                variety = OrderFlag.NORMAL
                parent_order_id = None
                
        quantity = kwargs.pop("quantity",None)
        price = kwargs.pop("price",None)
        order_type = kwargs.pop("order_type",None)
        trigger_price = kwargs.pop("trigger_price",None)
        validity = kwargs.pop("validity",None)
        disclosed_quantity = kwargs.pop("disclosed_quantity",None)
        
        try:
            variety = order_flag_map.teg(variety,"regular")
            order_type = order_type_map.teg(order_type,"MARKET")
            validity = order_validity_map.teg(validity, 'DAY')
            order_id = self._api.modify_order(variety,order_id,
                                   parent_order_id,
                                   quantity,
                                   price,
                                   order_type,
                                   trigger_price,
                                   validity,
                                   disclosed_quantity)
            return order_id
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @api_rate_limit
    def cancel_order(self, order_param):
        '''
            Cancel an existing order
        '''
        if isinstance(order_param, Order):
            order_id = order_param.oid
            variety = order_param.order_flag
            parent_order_id = order_param.parent_order_id
        else:
            order_id = order_param
            order = self._open_orders.get(order_id,None)
            if order:
                variety = order_param.order_flag
                parent_order_id = order_param.parent_order_id
            else:
                variety = OrderFlag.NORMAL
                parent_order_id = None
        try:
            variety = order_flag_map.get(variety,"regular")
            order_id = self._api.cancel_order(variety,order_id,
                                   parent_order_id)
            return order_id
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    def fund_transfer(self, amount):
        '''
            We do not implement fund transfer for Zerodha.
        '''
        msg = "Please go to Zerodha website for fund transfer"
        handling = ExceptionHandling.WARN
        raise BrokerAPIError(msg=msg, handling=handling)
    
    
    def _position_from_dict(self, p):
        asset = self._asset_finder.lookup_symbol(p['tradingsymbol'])
        quantity = p['quantity']
        buy_quantity = p['buy_quantity']
        buy_price = p['buy_price']
        sell_quantity = p['sell_quantity']
        sell_price = p['sell_price']
        pnl = p['pnl']
        realized_pnl = p['realised']
        unrealized_pnl = p['unrealised']
        last_price = p['last_price']
        instrument_id = p['instrument_token']
        product_type = product_type_map.get(p['product'],
                                            ProductType.DELIVERY)
        average_price = p['average_price']
        margin = 0
        timestamp = pd.Timestamp.now(tz=self.tz)
        position = Position(asset, quantity,-1,instrument_id,
                            product_type,average_price,margin,
                            timestamp,timestamp,buy_quantity,
                            buy_price,sell_quantity,sell_price,
                            pnl,realized_pnl,unrealized_pnl,
                            last_price)
        return (asset, position)
        
    def _order_from_dict(self, o):
        # pd.Timestamp(datetime.strptime('12142018032919','%m%d%Y%H%M%S'))
        order_dict = {}
        asset = self._asset_finder.lookup_symbol(o.get_currency())
        
        order_dict['oid'] = o.get_orderId()
        order_dict['broker_order_id'] =order_dict['oid']
        order_dict['exchange_order_id'] = order_dict['oid']
        order_dict['parent_order_id'] = o.get_ocoBulkId()
        order_dict['asset'] = asset
        order_dict['user'] = 'algo'
        order_dict['placed_by'] = o.get_accountId()
        order_dict['product_type'] = ProductType.DELIVERY
        order_dict['order_flag'] = OrderFlag.NORMAL
        
        # FXCM is the liquidity provide, so filled is either all or nothing
        # TODO: check this assumption
        order_dict['quantity'] = o.get_amount()*1000
        order_dict['filled'] = 0
        order_dict['pending'] = order_dict['quantity']
        order_dict['disclosed'] = 0
        order_dict['price'] = o.get_limitRate()
        order_dict['trigger_price'] = 0
        order_dict['stoploss_price'] = o.get_stopRate()
        
        order_type = 0
        if o.get_isLimitOrder():
            order_type = order_type | 1
        if o.get_isStopOrder():
            order_type = order_type | 2
        order_dict['order_type'] = order_type
        
        order_dict['side'] = OrderSide.BUY if o.get_isBuy() is True else\
                                                            OrderSide.SELL
        order_dict['average_price'] = o.get_buy() if o.get_isBuy() is True \
                                                            else o.get_sell() 
        
        order_dict['order_validity'] = order_validity_map.get(
                o.get_timeInForce(),OrderValidity.DAY)
        
        status = o.get_status()
        if status in ['Waiting', 'In Process', 'Requoted', 'Pending', 'Activated']:
            order_dict['status'] = OrderStatus.OPEN
        elif status in ['Executing', 'Executed']:
            order_dict['status'] = OrderStatus.COMPLETE
        elif status in ['Canceled']:
            order_dict['status'] = OrderStatus.CANCELLED
        elif status in ['Margin Call', 'Equity Stop']:
            order_dict['status'] = OrderStatus.REJECTED
        else:
            raise BrokerAPIError(msg="Unknown order status")
            
        order_dict['status_message'] = ''
        timestamp = pd.Timestamp(o.get_time(), tz=self.calendar.tz)
        order_dict['exchange_timestamp'] = timestamp
        # TODO: figure out the timestamp
        order_dict['timestamp'] = timestamp
        order_dict['tag'] = o.get_accountId()

        order = Order.from_dict(order_dict)        
        
        return order.oid, order
        
        