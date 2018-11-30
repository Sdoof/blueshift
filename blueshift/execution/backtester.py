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
Created on Sat Oct  6 12:54:09 2018

@author: prodi
"""

from enum import Enum

from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.execution._clock import BARS
from blueshift.trades._order import Order
from blueshift.trades._position import Position
from blueshift.trades._trade import Trade
from blueshift.trades._order_types import (OrderUpdateType, 
                                           OrderStatus, 
                                           OrderSide)
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.blotter._accounts import BacktestAccount
from blueshift.assets._assets import InstrumentType
from blueshift.utils.exceptions import (InsufficientFund, 
                                        BrokerAPIError,
                                        BacktestUnexpectedExit)
from blueshift.utils.validation import positive_num
from blueshift.utils.cutils import check_input
from blueshift.utils.decorators import blueprint
from blueshift.utils.types import BrokerType, MODE

import random

class ResponseType(Enum):
    '''
        Enum for response from a broker (usually a rest broker)
    '''
    SUCCESS = "success"
    ERROR = "error"
    
class APICommand(Enum):
    '''
        List of acceptable command strings.
    '''
    PLACE_ORDER = 0
    MODIFTY_ORDER = 1
    CANCEL_ORDER = 3
    GET_PROFILE = 4
    GET_ACCOUNT = 5
    GET_ORDER = 6
    GET_OPEN_ORDERS = 7
    GET_ORDERS = 8
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


@blueprint
class BackTester(object):
    '''
        The backtesting engine following the standard API. The return
        values from the API is in the format {'status':status,
        'data':data}. Status can be either 'success' or 'error'
    '''
    
    def __init__(self, name, calendar, initial_capital, 
                 currency = 'local'):
        self.timestamp = None
        self.broker_name = name
        self.authentication_token = -1
        self.calendar = calendar
        self.type = BrokerType.BACKTESTER
        self._closed_orders = {}
        self._open_orders = {}
        self._open_positions = {}
        self._closed_positions = []
        self._account = BacktestAccount(name,initial_capital, 
                                        currency=currency)
        self._profile = {"name":"blueshift"}
        self.tid = 0
        self.dispath_dict = {}
        self.make_dispath_dict()
        self.api = self._api()
        self.api.send(None)
        
    def __str__(self):
        return "Blueshift Backtester [name:%s]" % (self.broker_name)
    
    def __repr__(self):
        return self.__str__()
        
    def make_response(self, status, data):
        return {"status":status.value,"data":data}
    
    def make_dispath_dict(self):
        self.dispath_dict[APICommand.PLACE_ORDER]=self.place_order
        self.dispath_dict[APICommand.MODIFTY_ORDER]=self.update_order
        self.dispath_dict[APICommand.CANCEL_ORDER]=self.cancel_order
        self.dispath_dict[APICommand.GET_PROFILE]=self.get_profile
        self.dispath_dict[APICommand.GET_ACCOUNT]=self.get_account
        self.dispath_dict[APICommand.GET_ORDER]=self.get_order_status
        self.dispath_dict[APICommand.GET_OPEN_ORDERS]=\
                                                self.get_open_orders
        self.dispath_dict[APICommand.GET_ORDERS]=\
                                                self.get_orders
        self.dispath_dict[APICommand.GET_POSITIONS]=self.get_positions
        self.dispath_dict[APICommand.ADD_CAPITAL]=\
                                                self.get_past_positions
        self.dispath_dict[APICommand.LOGIN]=self.login
        self.dispath_dict[APICommand.LOGOUT]=self.logout
        self.dispath_dict[BARS.TRADING_BAR]=self.trading_bar
        self.dispath_dict[BARS.ALGO_START]=self.algo_start
        self.dispath_dict[BARS.ALGO_END]=self.algo_end
        self.dispath_dict[BARS.BEFORE_TRADING_START]=\
                                            self.before_trading_start
        self.dispath_dict[BARS.AFTER_TRADING_HOURS]=\
                                            self.after_trading_hours
        self.dispath_dict[BARS.HEAR_BEAT]=self.heart_beat
        
    def algo_start(self, timestamp):
        self.timestamp = timestamp
        pass
    
    def algo_end(self, timestamp):
        self.timestamp = timestamp
        pass
        
    def before_trading_start(self,timestamp):
        self.timestamp = timestamp
        pass
    
    def after_trading_hours(self, timestamp):
        self.timestamp = timestamp
        self._open_orders = {}
    
    def heart_beat(self, timestamp):
        self.timestamp = timestamp
        pass
        
    def trading_bar(self, timestamp):
        self.timestamp = timestamp
        self.execute_orders(timestamp)
    
    def no_op(self, *args, **kwargs):
        return self.make_response(ResponseType.SUCCESS,
                             None)
        
    def default_op(self, *args, **kwargs):
        return self.make_response(ResponseType.ERROR,
                             "unknown command")
    
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
    
    def get_profile(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS,self._profile)
    
    def get_account(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._account.to_dict())
    
    def get_positions(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._open_positions)
        
    def get_past_positions(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._closed_positions)
    
    def get_open_orders(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        return self.make_response(ResponseType.SUCCESS, 
                                  self._open_orders)
    
    def get_orders(self, *args, **kwargs):
        '''
            This process will always succeed for backtester 
        '''
        d = {**self._open_orders, **self._closed_orders}
        return self.make_response(ResponseType.SUCCESS,d)
    
    def get_timezone(self, *args, **kwargs):
        if isinstance(self.calendar, TradingCalendar):
            return self.make_response(ResponseType.SUCCESS, 
                                      self.calendar.tz)
        else:
            return self.make_response(ResponseType.ERROR, 
                                      "not a valid calendar")
            
    def get_order_status(self, order_id):
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
                self._open_orders[order_id].update(OrderUpdateType.\
                                 MODIFICATION, update_dict)
                return self.make_response(ResponseType.SUCCESS,
                                          order_id)
            else:
                return self.make_response(ResponseType.ERROR,
                                          "order not found")
        else:
            return self.make_response(ResponseType.ERROR,
                                          "invalid parameter")
    
    def cancel_order(self, order_id):
        #TODO: optimize the pop?
        order = self._open_orders.pop(order_id,None)
        if order is not None:
            self._open_orders[order_id] = order.update(OrderUpdateType.\
                             CANCEL)
            return self.make_response(ResponseType.SUCCESS,
                                          order_id)
        else:
            return self.make_response(ResponseType.ERROR,
                                          "order not found")
        
    def execution_model(self, order):
        price = random.randint(20,25)
        
        traded = round(random.randint(100,500))
        return price, traded
        
    def execute_orders(self, timestamp):
        order_ids = list(self._open_orders.keys())
        for order_id in order_ids:
            order = self._open_orders[order_id]
            # obtain the traded quantity and price
            price, traded = self.execution_model(order)
            # ignore if traded is 0. Note traded is without sign
            # the order remains open for next exec opportunity
            if traded == 0:
                continue
            
            # check if quantity traded is valid
            if order.quantity - order.filled <  traded:
                traded = order.quantity - order.filled
            
            # compute the cash and margins required
            margin, cash_flow = self.compute_margin_cashflow(
                    order.asset,price, traded, order.side)
            commission = self.compute_commission(price, traded)
            cash_flow = cash_flow - commission
            
            # create the trade object
            self.tid = self.tid+1
            t = Trade(self.tid, traded, order.side, order_id, 
                      order_id, order_id, -1,  # dummy instrument ID
                      order.asset,order.product_type, price, 
                      cash_flow, margin,commission,timestamp, 
                      timestamp)
            
            # try settling the trade with account
            try:
                self._account.settle_trade(t)
            except InsufficientFund:
                self._open_orders[order_id].update(OrderUpdateType.\
                                 REJECT,{"reason":"insufficient fund"})
                self._closed_orders[order_id] = self._open_orders.\
                                                pop(order_id)
                continue
            
            # update the order in the order book and see if done
            self._open_orders[order_id].update(OrderUpdateType.\
                             EXECUTION,t)
            
            #TODO: optimize the pop?
            if self._open_orders[order_id].status == OrderStatus.\
                    COMPLETE:
                self._closed_orders[order_id] = self._open_orders.\
                                                pop(order_id)
            
            # update the position book
            if t.asset in self._open_positions:
                self._open_positions[t.asset].update(t, margin)
                #TODO: optimize the pop?
                if self._open_positions[t.asset].if_closed():
                    self._closed_positions.append(self._open_positions.\
                                                  pop(t.asset))
            else:
                p = Position.from_trade(t, margin)
                self._open_positions[t.asset] = p
                
            # finally update the account metrics
            cash = self._account.cash + cash_flow
            margin = self._account.margin + margin
            self._account.update_account(cash, margin,
                                         self._open_positions)
    
    def compute_margin_cashflow(self, asset, price, traded, side):
        instrument_type = asset.instrument_type
        pct_margin = MarginDict[instrument_type]
        
        if side == OrderSide.BUY:
            traded_qty = traded
        else:
            traded_qty = - traded
        current_exposure = 0
        new_exposure = traded_qty*price
        
        current_pos = self._open_positions.get(asset, None)
        if current_pos:
            current_exposure = current_pos.quantity*price
            
        square_off = abs(current_exposure) - \
                         abs(current_exposure+new_exposure)
                
        if instrument_type == InstrumentType.SPOT:
            pass
                
        else:
            # for non cash, no price cash flows, only margins
            margin = -pct_margin*square_off
            cash_flow = 0
                
        return margin, cash_flow
                
    def compute_commission(self, price, traded):
        return 0
    
    def _api(self):
        while True:
            order = yield               # recieve the api call
            cmd = order['cmd']
            data = order['payload']
            
            # command dispatching here
            response = self.dispath_dict.get(cmd,self.default_op)(data)
            yield response
    
    def send(self, arg):
        try:
            response = self.api.send(arg)
            next(self.api)
            return response
        except (GeneratorExit,StopIteration) as e:
            raise BacktestUnexpectedExit(msg=self.broker_name)
    
    def close(self):
        return self.api.close()
        
        
@blueprint
class BackTesterAPI(AbstractBrokerAPI):
    '''
        An implementation of the broker interface for backtest.
    '''
    
    def __init__(self, 
                 name:str,
                 broker_type:BrokerType, 
                 calendar:TradingCalendar, 
                 initial_capital:positive_num,
                 **kwargs):
        check_input(BackTesterAPI.__init__, locals())
        super(BackTesterAPI, self).__init__(name, broker_type, calendar,
                                             **kwargs)
        self._mode_supports = [MODE.BACKTEST]
        
        api = kwargs.get("broker",None)
        
        if api:
            if isinstance(api, BackTester):
                self._api = api
            else:
                self._api = BackTester(name, calendar, 
                                         initial_capital)
        else:
            self._api = BackTester(name, calendar, initial_capital)
        
        self._trading_calendar = calendar
        self.initial_capital = initial_capital
        self._name = name
        # backtester is always connected
        self._connected = True
            
    def __str__(self):
        return 'Blueshift Broker [name:%s, type:%s]'%(self._name, self._type)
    
    def __repr__(self):
        return self.__str__()
        
    def make_api_payload(self, command, data):
        return {"cmd":command, "payload":data}
    
    def process_response(self, response):
        if response['status'] == ResponseType.SUCCESS.value:
            return response['data']
        else:
            msg = response['data']
            raise BrokerAPIError(msg=msg)
        
    def login(self, *args, **kwargs):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          LOGIN,
                                          kwargs))
        return self.process_response(response)
    
    def logout(self, *args, **kwargs):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          LOGOUT,
                                          kwargs))
        return self.process_response(response)
    
    @property
    def calendar(self):
        return self._trading_calendar
    
    @property
    def profile(self):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          GET_PROFILE,
                                          {}))
        return self.process_response(response)
    
    @property
    def account(self):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          GET_ACCOUNT,
                                          {}))
        return self.process_response(response)
    
    @property
    def positions(self):
        response = self._api.send(self.make_api_payload(APICommand.\
                                        GET_POSITIONS,
                                        {}))
        return self.process_response(response)
    
    @property
    def open_orders(self):
        response = self._api.send(self.make_api_payload(APICommand.\
                                        GET_OPEN_ORDERS,
                                        {}))
        return self.process_response(response)
    
    @property
    def orders(self):
        response = self._api.send(self.make_api_payload(APICommand.\
                                        GET_ORDERS,
                                        {}))
        return self.process_response(response)
    
    @property
    def tz(self, *args, **kwargs):
        return self._trading_calendar.tz
    
    def order(self, order_id):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          GET_ORDER,
                                          order_id))
        return self.process_response(response)
    
    def place_order(self, order):
        response = self._api.send(self.make_api_payload(APICommand.\
                                                          PLACE_ORDER,
                                          order))
        return self.process_response(response)
    
    def update_order(self, order_param, *args, **kwargs):
        if isinstance(order_param, Order):
            order_id = order_param.oid
        else:
            order_id = order_param
        
        kwargs["order_id"] = order_id
        response = self._api.send(self.make_api_payload(APICommand.\
                                        MODIFTY_ORDER,
                                        kwargs))
        
        return self.process_response(response)
    
    def cancel_order(self, order_param):
        if isinstance(order_param, Order):
            order_id = Order.oid
        else:
            order_id = order_param
            
        response = self._api.send(self.make_api_payload(APICommand.\
                                        CANCEL_ORDER,
                                        order_id))  
        return self.process_response(response)
        
    def fund_transfer(self, amount):
        response = self._api.send(self.make_api_payload(APICommand.\
                                        ADD_CAPITAL,
                                        amount))
        
        return self.process_response(response)
    
    def trading_bar(self, timestamp):
        self._api.send(self.make_api_payload(BARS.TRADING_BAR,
                         timestamp))
        
    def before_trading_start(self, timestamp):
        self._api.send(self.make_api_payload(BARS.\
                                               BEFORE_TRADING_START,
                         timestamp))
        
    def after_trading_hours(self, timestamp):
        self._api.send(self.make_api_payload(BARS.\
                                               AFTER_TRADING_HOURS,
                         timestamp))
        
    def algo_start(self, timestamp):
        self._api.send(self.make_api_payload(BARS.ALGO_START,
                         timestamp))
        
    def algo_end(self, timestamp):
        self._api.send(self.make_api_payload(BARS.ALGO_END,
                         timestamp))
        
    def heart_beat(self, timestamp):
        self._api.send(self.make_api_payload(BARS.HEART_BEAT,
                         timestamp))
        
        