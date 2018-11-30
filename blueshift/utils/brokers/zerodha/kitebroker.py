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
Created on Mon Oct 29 16:27:45 2018

@author: prodipta
"""

import pandas as pd
from enum import Enum

from requests.exceptions import RequestException

from kiteconnect.exceptions import KiteException, NetworkException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.utils.brokers.zerodha.kiteauth import (KiteAuth,
                                                      KiteConnect3)
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        BrokerAPIError)
from blueshift.blotter._accounts import EquityAccount
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
                    'IOC':OrderValidity.IOC,
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
class KiteBroker(AbstractBrokerAPI):
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
                 name:str="kite", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=None,
                 **kwargs):
        check_input(KiteBroker.__init__, locals())
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
        
        if self._auth.__class__ != KiteAuth.cls:
            msg = "invalid authentication object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._api = self._auth._api
            
        if self._api.__class__ != KiteConnect3.cls:
            msg = "invalid kite API object"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
            
        self._closed_orders = {}
        self._open_orders = {}
        self._open_positions = {}
        self._closed_positions = []
        
        self._account = EquityAccount(self._name,0.01)
    
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
    @api_rate_limit
    def profile(self):
        '''
            Fetch and return the user profile.
        '''
        try:
            return self._api.profile()
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
        variety = order.order_flag
        
        asset = self._aset_finder.symbol_to_asset(
                order.asset.symbol)
        exchange = asset.exchange_name
        tradingsymbol = asset.symbol
            
        transaction_type = order.side
        product = order.product_type
        order_type = order.order_type
        price = order.price
        validity = order.order_validity
        disclosed_quantity = order.disclosed
        trigger_price = order.trigger_price
        stoploss_price = order.stoploss_price
        tag = order.tag
        
        variety = order_flag_map.teg(variety,"regular")
        transaction_type = order_side_map.teg(
                transaction_type, None)
        order_type = order_type_map.teg(order_type,"MARKET")
        product = product_type_map.teg(product,'NRML')
        validity = order_validity_map.teg(validity, 'DAY')
        
        #TODO: assumption price cannot be negative
        price = price if price > 0 else None
        trigger_price = trigger_price if price > 0 else None
        stoploss_price = stoploss_price if price > 0 else None
        
        try:
            order_id = self._api.place_order(variety, exchange,
                                  tradingsymbol,
                                  transaction_type,
                                  quantity, product,
                                  order_type, price=price,
                                  validity=validity,
                                  disclosed_quantity=\
                                      disclosed_quantity,
                                  trigger_price=trigger_price,
                                  stoploss=stoploss_price, 
                                  tag=tag)
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
        order_dict = {}
        asset = self._asset_finder.lookup_symbol(o['tradingsymbol'])
        
        order_dict['oid'] = o['order_id']
        order_dict['broker_order_id'] = o['order_id']
        order_dict['exchange_order_id'] = o['exchange_order_id']
        order_dict['parent_order_id'] = o['parent_order_id']
        order_dict['asset'] = asset
        order_dict['user'] = 'algo'
        order_dict['placed_by'] = o['placed_by']
        order_dict['product_type'] = product_type_map.get(o['product'])
        order_dict['order_flag'] = OrderFlag.NORMAL
        order_dict['order_type'] = order_type_map.get(o['order_type'])
        order_dict['order_validity'] = order_validity_map.get(
                o['validity'])
        order_dict['quantity'] = o['quantity']
        order_dict['filled'] = o['filled_quantity']
        order_dict['pending'] = o['pending_quantity']
        order_dict['disclosed'] = o['disclosed_quantity']
        order_dict['price'] = o['price']
        order_dict['average_price'] = o['average_price']
        order_dict['trigger_price'] = o['trigger_price']
        order_dict['stoploss_price'] = o['stoploss_price']
        order_dict['side'] = order_side_map.get(o['transaction_type'])
        order_dict['status'] = order_status_map.get(o['status'])
        order_dict['status_message'] = o['status_message']
        order_dict['exchange_timestamp'] = pd.Timestamp(
                o['exchange_timestamp'])
        order_dict['timestamp'] = pd.Timestamp(o['order_timestamp'])
        order_dict['tag'] = o['tag']

        order = Order.from_dict(order_dict)        
        
        return order.oid, order
        
        
        
        