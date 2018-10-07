# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 12:54:09 2018

@author: prodi
"""
from enum import Enum
from blueshift.execution.broker import AbstractBrokerAPI, BrokerType
from blueshift.assets._assets import Asset
from blueshift.trades._order import Order
from blueshift.trades._position import Position
from blueshift.trades._trade import Trade
from blueshift.trades._order_types import OrderUpdateType, OrderStatus
from blueshift.utils.calendars.trading_calendar import TradingCalendar

import random

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    
class APICommand(Enum):
    PLACE_ORDER = 0
    MODIFTY_ORDER = 1
    CANCEL_ORDER = 3
    GET_PROFILE = 4
    GET_ACCOUNT = 5
    GET_ORDER = 6
    GET_OPEN_ORDERS = 7
    GET_CLOSED_OR_CANCELLED_ORDERS = 8
    GET_POSITIONS = 9
    ADD_CAPITAL = 10
    LOGIN = 11
    LOGOUT = 12

class BackTester(object):
    '''
        The backtesting engine following the standard API. The return
        values from the API is in the format {'status':status,
        'data':data}. Status can be either 'success' or 'error'
    '''
    
    def __init__(self, name, calendar, initial_capital):
        self.broker_name = name
        self.authentication_token = -1
        self.calendar = calendar
        self.type = BrokerType.BACKTESTER
        self._orders = {}
        self._open_orders = {}
        self._positions = {}
        self._account = initial_capital
        self._profile = {"name":"algo"}
        self.tid = 0
        self.api = self._api()
        self.send(None)
        
    def make_response(self, status, data):
        return {"status":status.value,"data":data}
    
    def login(self, *args, **kwargs):
        '''
            This process will always succeed for backtester
        '''
        self.authentication_token = True
        return self.make_response(ResponseType.SUCCESS,
                             self.authentication_token)
    
    def logout(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        self.authentication_token = False
        return self.make_response(ResponseType.SUCCESS,
                             self.authentication_token)
    
    @property
    def profile(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS,self._profile)
    
    @property
    def account(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._account)
    
    @property
    def positions(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._positions)
    
    @property
    def open_orders(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._open_orders)
    
    @property
    def orders(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._orders)
    
    @property
    def timezone(self):
        if isinstance(self.calendar, TradingCalendar):
            return self.make_response(ResponseType.SUCCESS, 
                                      self.calendar.tz)
        else:
            return self.make_response(ResponseType.ERROR, 
                                      "not a valid calendar")
            
    def order_status(self, order_id):
        '''
            Query for a particular order ID
        '''
        if order_id in self._open_orders:
            return self.make_response(ResponseType.SUCCESS,
                                          self._open_orders[order_id])
        elif order_id in self._orders:
            return self.make_response(ResponseType.SUCCESS,
                                          self._orders[order_id])
        else:
            return self.make_response(ResponseType.ERROR,
                                          "order not found")
    
    def add_capital(self, amount):
        '''
            Capital addition or withdrawal
        '''
        try:
            if self.account.cash + amount > 0:
                self.account.cash = self.account.cash + amount
                return self.make_response(ResponseType.SUCCESS,
                                          self.account.cash)
            else:
                return self.make_response(ResponseType.ERROR,
                                          "not enough cash")
        except TypeError:
            return self.make_response(ResponseType.ERROR,
                                          "invalid parameter")
    
    def place_order(self, order):
        '''
            New order placed
        '''
        if(isinstance(order, Order)):
            self._open_orders[order.oid] = order
            return self.make_response(ResponseType.SUCCESS,
                                          order.oid)
        else:
            return self.make_response(ResponseType.ERROR,
                                          "not a valid order")
    
    def update_order(self, order_id, update_dict):
        '''
            Modify an existing open order
        '''
        if(isinstance(update_dict, dict)):
            if order_id in self._open_orders:
                self._open_orders[order_id].update(OrderUpdateType.MODIFICATION,
                                update_dict)
                return self.make_response(ResponseType.SUCCESS,
                                          order_id)
            else:
                return self.make_response(ResponseType.ERROR,
                                          "order not found")
        else:
            return self.make_response(ResponseType.ERROR,
                                          "invalid parameter")
    
    def cancel_order(self, order_id):
        order = self._open_orders.pop(order_id,None)
        if order is not None:
            self._orders[order_id] = order.update(OrderUpdateType.CANCEL)
            return self.make_response(ResponseType.SUCCESS,
                                          order_id)
        else:
            return self.make_response(ResponseType.ERROR,
                                          "order not found")
        
    def execution_model(self):
        price = min(11800,max(11000,11500 + 
                          round((random.random()-0.5)*100,2)))
        traded = round(random.random()*100)
        return price, traded
        
    def execute_orders(self, timestamp):
        for order_id, order in self._open_orders.items():
            price, traded = self.execution_model()
            
            if order.quantity - order.filled <  traded:
                traded = order.quantity - order.filled
            
            self.tid = self.tid+1
            t = Trade(self.tid, traded, order.side, order_id, 
                      order_id, order_id, -1,  # dummy instrument ID
                      order.asset,order.poduct_type, price, timestamp, 
                      timestamp)
            
            self._open_orders[order_id].update(OrderUpdateType.EXECUTION,t)
            
            if self._open_orders[order_id].status == OrderStatus.COMPLETE:
                self._orders[order_id] = self._open_orders.pop(order_id)
            
            if t.asset in self.positions:
                self._positions[t.asset].update(t)
            else:
                p = Position.from_trade(t)
                self._positions[t.asset] = p
                
    def _api(self):
        while True:
            order = yield               # recieve the api call
            cmd = order['cmd']
            data = order['payload']
            timestamp = order['timestamp']
            self.execute_orders(timestamp)
            
            # command parsing in the order of expected frequency
            if cmd == APICommand.PLACE_ORDER :
                response = self.place_order(data)
            elif cmd == APICommand.MODIFTY_ORDER:
                response = self.update_order(data)
            elif cmd == APICommand.CANCEL_ORDER:
                response = self.cancel_order(data)
            elif cmd == APICommand.GET_OPEN_ORDERS:
                response = self.open_orders()
            elif cmd == APICommand.GET_CLOSED_OR_CANCELLED_ORDERS:
                response = self.orders()
            elif cmd == APICommand.GET_ORDER:
                response = self.order_status(data)
            elif cmd == APICommand.GET_POSITIONS:
                response = self.positions
            elif cmd == APICommand.ADD_CAPITAL:
                response = self.add_capital(data)
            elif cmd == APICommand.LOGIN:
                response = self.login()
            elif cmd == APICommand.LOGOUT:
                response = self.logout()
            else:
                response = self.make_response(ResponseType.ERROR,
                                         "unknown command")
            yield response
            
    def send(self, arg):
        return self.api.send(arg)
    
    def close(self):
        return self.api.close()
        
        
class BackTesterAPI(AbstractBrokerAPI):
    
    def __init__(self, name, broker_type, calendar, broker):
        super(BackTesterAPI, self).__init__(name, broker_type, calendar)
        self.broker = BackTester(name, calendar, 0)
        
    def make_api_payload(self, command, data, timestamp):
        return {"cmd":command, "payload":data, "timestamp":timestamp}
        
    def login(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.LOGIN,
                                          None,timestamp))
        return response
    
    def logout(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.LOGOUT,
                                          None,timestamp))
        return response
    
    def profile(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_PROFILE,
                                          None,timestamp))
        return response
    
    def account(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_ACCOUNT,
                                          None,timestamp))
        return response
    
    def positions(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_POSITIONS,
                                          None,timestamp))
        return response
    
    def open_orders(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_OPEN_ORDERS,
                                          None,timestamp))
        return response
    
    def orders(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_CLOSED_OR_CANCELLED_ORDERS,
                                          None,timestamp))
        return response
    
    def timezone(self):
        pass
    
    def place_order(self, order, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.PLACE_ORDER,
                                          order,timestamp))
        return response
    
    def update_order(self, order_id, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.MODIFTY_ORDER,
                                          order_id,timestamp))
        return response
    
    def cancel_order(self, order_id, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.CANCEL_ORDER,
                                          order_id,timestamp))  
        return response
        
    def adjust_capital(self, amount, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.ADD_CAPITAL,
                                          amount, timestamp))
        return response
        
        