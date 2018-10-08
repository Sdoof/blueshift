# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 12:54:09 2018

@author: prodi
"""
from enum import Enum
from blueshift.execution.broker import AbstractBrokerAPI, BrokerType
from blueshift.trades._order import Order
from blueshift.trades._position import Position
from blueshift.trades._trade import Trade
from blueshift.trades._order_types import OrderUpdateType, OrderStatus, OrderSide
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.blotter._accounts import Account
from blueshift.assets._assets import InstrumentType
from blueshift.utils.exceptions import InsufficientFund

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
    
MarginDict = {
    InstrumentType.SPOT:0.1,
    InstrumentType.FUTURES:0.1,
    InstrumentType.OPT:0.1,
    InstrumentType.FUNDS:0,
    InstrumentType.CFD:0.05,
    InstrumentType.STRATEGY:0}
    

class BackTester(object):
    '''
        The backtesting engine following the standard API. The return
        values from the API is in the format {'status':status,
        'data':data}. Status can be either 'success' or 'error'
    '''
    
    def __init__(self, name, calendar, initial_capital, 
                 currency = 'local'):
        self.broker_name = name
        self.authentication_token = -1
        self.calendar = calendar
        self.type = BrokerType.BACKTESTER
        self._closed_orders = {}
        self._open_orders = {}
        self._open_positions = {}
        self._closed_positions = {}
        self._account = Account(name,initial_capital, currency=currency)
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
                                  self._account.to_dict())
    
    @property
    def positions(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._open_positions)
        
    @property
    def past_positions(self):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._closed_positions)
    
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
                                  self._closed_orders)
    
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
        elif order_id in self._closed_orders:
            return self.make_response(ResponseType.SUCCESS,
                                          self._closed_orders[order_id])
        else:
            return self.make_response(ResponseType.ERROR,
                                          "order not found")
    
    def add_capital(self, amount):
        '''
            Capital addition or withdrawal
        '''
        try:
            self._account.fund_transfer(amount)
        except TypeError:
            return self.make_response(ResponseType.ERROR,
                                          "invalid parameter")
        except InsufficientFund:
            return self.make_response(ResponseType.ERROR,
                                          "insufficient fund")
    
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
            self._open_orders[order_id] = order.update(OrderUpdateType.CANCEL)
            return self.make_response(ResponseType.SUCCESS,
                                          order_id)
        else:
            return self.make_response(ResponseType.ERROR,
                                          "order not found")
        
    def execution_model(self, order):
        price = min(11800,max(11000,11500 + 
                          round((random.random()-0.5)*100,2)))
        
        margin = self.get_margin_requirement(order, price)
        if margin > self._account.available.cash:
            return price, 0
        
        traded = round(random.random()*100)
        return price, traded
        
    def execute_orders(self, timestamp):
        for order_id, order in self._open_orders.items():
            
            # obtain the traded quantity and price
            price, traded = self.execution_model(order)
            
            # ignore if traded is 0. Note traded is without sign
            # the order remains open for next exec opportunity
            if traded == 0:
                return
            
            if order.quantity - order.filled <  traded:
                traded = order.quantity - order.filled
            
            margin, cash_flow = self.compute_margin_cashflow(order.asset,
                                         price, traded, order.side)
            commission = self.compute_commission(price, traded)
            cash_flow = cash_flow - commission
            
            self.tid = self.tid+1
            t = Trade(self.tid, traded, order.side, order_id, 
                      order_id, order_id, -1,  # dummy instrument ID
                      order.asset,order.poduct_type, price, 
                      cash_flow, margin,commission,timestamp, 
                      timestamp)
            
            try:
                self._account.settle_trade
            except InsufficientFund:
                continue
            
            self._open_orders[order_id].update(OrderUpdateType.EXECUTION,t)
            
            if self._open_orders[order_id].status == OrderStatus.COMPLETE:
                self._closed_orders[order_id] = self._open_orders.pop(order_id)
            
            if t.asset in self._open_positions:
                self._open_positions[t.asset].update(t, margin)
                if self._open_positions[t.asset].is_close():
                    self._closed_positions[t.asset] = self._open_positions.pop(t.asset)
            else:
                p = Position.from_trade(t, margin)
                self._open_positions[t.asset] = p
                
    def _api(self):
        while True:
            print("waiting for command...")
            order = yield               # recieve the api call
            print("got {}".format(order))
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
    
    def compute_margin_cashflow(self, asset, price, traded, side):
        instrument_type = asset.instrument_type
        pct_margin = MarginDict[instrument_type]
        
        if side == OrderSide.BUY:
            traded_qty = traded
        else:
            traded_qty = - traded
        current_exposure = 0
        
        current_pos = self._positions.get(asset, None)
        if current_pos:
            current_exposure = current_pos.quantity*price
                
        if instrument_type == InstrumentType.SPOT:
            if current_exposure <= 0 and traded_qty > 0:
                # (partially) squaring short cash positions
                margin = -pct_margin*min(traded,
                                         -current_exposure)
                cash_flow = -price*traded
            elif current_exposure <= 0 and traded_qty < 0:
                #  adding to short positions
                margin = pct_margin*traded
                cash_flow = 0
            else:
                # adding to or reducing long positions
                margin = 0
                if traded_qty < 0:
                    cash_flow = 0
                else:
                    cash_flow = -price*traded
        else:
            # for non cash, no price cash flows, only margins
            square_off = abs(current_exposure) - \
                         abs(current_exposure+traded_qty)
            margin = -pct_margin*square_off
            cash_flow = 0
                
        return margin, cash_flow
                
        
            
    def compute_commission(self, price, traded):
        return 20
    
    def send(self, arg):
        return self.api.send(arg)
    
    def close(self):
        return self.api.close()
        
        
class BackTesterAPI(AbstractBrokerAPI):
    
    def __init__(self, name, broker_type, calendar, 
                 initial_capital = 10000,
                 broker=None):
        super(BackTesterAPI, self).__init__(name, broker_type, calendar)
        
        if broker:
            self.broker = broker
        else:
            self.broker = BackTester(name, calendar, initial_capital)
        
    def make_api_payload(self, command, data, timestamp):
        return {"cmd":command, "payload":data, "timestamp":timestamp}
        
    def login(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.LOGIN,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def logout(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.LOGOUT,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def profile(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_PROFILE,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def account(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_ACCOUNT,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def positions(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_POSITIONS,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def open_orders(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_OPEN_ORDERS,
                                          None,timestamp))
        return response
    
    def orders(self, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.GET_CLOSED_OR_CANCELLED_ORDERS,
                                          None,timestamp))
        self.broker.send(None)
        return response
    
    def timezone(self):
        pass
    
    def place_order(self, order, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.PLACE_ORDER,
                                          order,timestamp))
        self.broker.send(None)
        return response
    
    def update_order(self, order_id, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.MODIFTY_ORDER,
                                          order_id,timestamp))
        
        self.broker.send(None)
        return response
    
    def cancel_order(self, order_id, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.CANCEL_ORDER,
                                          order_id,timestamp))  
        self.broker.send(None)
        return response
        
    def adjust_capital(self, amount, timestamp):
        response = self.broker.send(self.make_api_payload(APICommand.ADD_CAPITAL,
                                          amount, timestamp))
        self.broker.send(None)
        return response
        
        