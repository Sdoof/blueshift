# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:27:45 2018

@author: prodipta
"""

import pandas as pd
from enum import Enum

from kiteconnect.exceptions import KiteException

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI, BrokerType
from blueshift.utils.brokers.zerodha.kiteauth import (KiteAuth,
                                                      KiteConnect3,
                                                      kite_calendar)
from blueshift.utils.brokers.zerodha.kiteassets import KiteAssetFinder
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        BrokerAPIError,
                                        ZeroCashBalance)
from blueshift.blotter._accounts import EquityAccount
from blueshift.trades._position import Position
from blueshift.trades._order_types import (ProductType,
                                           OrderValidity,
                                           OrderFlag,
                                           OrderSide,
                                           OrderStatus,
                                           OrderType)
from blueshift.trades._order import Order
from blueshift.utils.decorators import api_rate_limit, singleton

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    
product_type_map = {'NRML':ProductType.DELIVERY, 
                    'MIS':ProductType.INTRADAY}
order_validity_map = {'DAY':OrderValidity.DAY, 
                    'IOC':OrderValidity.IOC,
                    'GTC':OrderValidity.GTC}
order_flag_map = {'NORMAL':OrderFlag.NORMAL, 
                    'AMO':OrderFlag.AMO}
order_side_map = {'BUY':OrderSide.BUY, 
                    'SELL':OrderSide.SELL}
order_status_map = {'COMPLETE':OrderStatus.COMPLETE, 
                    'OPEN':OrderStatus.OPEN,
                    'REJECTED':OrderStatus.REJECTED,
                    'CANCELLED':OrderStatus.CANCELLED}
order_type_map = {'MARKET':OrderType.MARKET,
                  'LIMIT':OrderType.LIMIT,
                  'STOPLOSS':OrderType.STOPLOSS,
                  'STOPLOSS_MARKET':OrderType.STOPLOSS_MARKET}

@singleton
class KiteBroker(AbstractBrokerAPI):
    
    def __init__(self, 
                 name:str="kite", 
                 broker_type:BrokerType=BrokerType.RESTBROKER, 
                 calendar:TradingCalendar=kite_calendar,
                 **kwargs):
        
        check_input(KiteBroker.__init__, locals())
        super(self.__class__, self).__init__(name, broker_type, calendar,
                                             **kwargs)
        self._auth = kwargs.get("auth",None)
        self._asset_finder = kwargs.get("asset_finder",None)
        self._api = None
        
        if not self._asset_finder:
            msg = "Broker needs a corresponding Asset Finder"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
        if not self._auth:
            msg = "authentication and API missing"
            handling = ExceptionHandling.TERMINATE
            raise AuthenticationError(msg=msg, handling=handling)
        
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
        if self._account.cash == 0 or self._account.liquid_value == 0:
            raise ZeroCashBalance()
            
    def __str__(self):
        return 'Broker:name:%s, type:%s'%(self._name, self._type)
    
    def __repr__(self):
        return self.__str__()
    
    def process_response(self, response):
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
    @api_rate_limit
    def profile(self):
        try:
            return self._api.profile()
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.LOG
            raise BrokerAPIError(msg=msg, handling=handling)
        
    @property
    @api_rate_limit
    def account(self):
        try:
            margins = self._api.margins()
            account = EquityAccount()
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    @api_rate_limit
    def positions(self):
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
    
    @property
    @api_rate_limit
    def open_orders(self):
        _ = self.orders
        return self._open_orders
    
    @property
    @api_rate_limit
    def orders(self, *args, **kwargs):
        try:
            orders = self._api.orders()
            if orders is None:
                return {**self._open_orders, **self._closed_orders}
            
            for o in orders:
                order_id, order = self._order_from_dict(o)
                if order.status == OrderStatus.OPEN:
                    self._open_orders[order_id] = order
                else:
                    self._closed_orders[order_id] = order
            return {**self._open_orders, **self._closed_orders}
        except KiteException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    def tz(self, *args, **kwargs):
        return self._calendar.tz
    
    def order(self, order_id):
        orders = self.orders
        return orders.get(order_id, None)
    
    def place_order(self, order):
        pass
    
    def update_order(self, order_id, *args, **kwargs):
        pass
    
    def cancel_order(self, order_id):
        pass
    
    def fund_transfer(self, amount):
        pass
    
    
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
        order_dict['side'] = order_side_map.get(o['transaction_type'])
        order_dict['status'] = order_status_map.get(o['status'])
        order_dict['status_message'] = o['status_message']
        order_dict['exchange_timestamp'] = pd.Timestamp(
                o['exchange_timestamp'])
        order_dict['timestamp'] = pd.Timestamp(o['order_timestamp'])
        order_dict['tag'] = o['tag']

        order = Order.from_dict(order_dict)        
        
        return order.oid, order
        
        
        
        