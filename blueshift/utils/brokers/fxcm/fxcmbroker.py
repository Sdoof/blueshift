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
from datetime import datetime
from collections import namedtuple

from requests.exceptions import RequestException

from fxcmpy.fxcmpy import ServerError
from fxcmpy.fxcmpy_order import fxcmpy_order

from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.execution.broker import AbstractBrokerAPI
from blueshift.utils.brokers.fxcm.fxcmauth import (FXCMAuth, FXCMPy)
from blueshift.utils.cutils import check_input
from blueshift.utils.exceptions import (AuthenticationError,
                                        ExceptionHandling,
                                        UnsupportedOrder,
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
## fxcmpy.fxcmpy_order.status_values 
order_status_map = {0: OrderStatus.OPEN, 1: OrderStatus.OPEN,
                    2: OrderStatus.OPEN, 3: OrderStatus.CANCELLED,
                    4: OrderStatus.OPEN, 5: OrderStatus.OPEN,
                    6: OrderStatus.OPEN, 7: OrderStatus.OPEN,
                    8: OrderStatus.OPEN, 9: OrderStatus.COMPLETE,
                    10: OrderStatus.OPEN}
order_type_map = OnetoOne({'MARKET':OrderType.MARKET,
                  'LIMIT':OrderType.LIMIT,
                  'STOPLOSS':OrderType.STOPLOSS,
                  'STOPLOSS_MARKET':OrderType.STOPLOSS_MARKET})

fxcm_status_values = OnetoOne(fxcmpy_order.status_values)

FXCMPosition = namedtuple("FXCMPosition",["asset","amount"])

@singleton
@blueprint
class FXCMBroker(AbstractBrokerAPI):
    '''
        Implements the broker interface functions.
    '''
    def __init__(self, 
                 name:str="fxcm", 
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
        self._processed_positions = []
        self._trading_cache = {}
        
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
        except AttributeError as e:
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
            data = self._api.get_accounts().T
            cash = sum(data.loc['usableMargin',])
            margin = sum(data.loc['usdMr',])
            _positions = self.positions
            self._account.update_account(cash, margin,
                                         _positions)
            return self._account.to_dict()
        except (ValueError, TypeError, ServerError) as e:
            if isinstance(e, ServerError):
                self._account =  last_version
                return self._account.to_dict()
            else:
                self._account =  last_version
                msg = str(e)
                handling = ExceptionHandling.WARN
                raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            self._account =  last_version
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
            last_version = self._open_positions
            # check if there is a new addition to closed position
            position_details = self._api.get_closed_positions(kind='list')
            for p in position_details:
                asset, position = self._position_from_dict(p, closed=True)
                if position:
                    self._closed_positions.append(position)
                    
            # open positions are processed afresh each time
            position_details = self._api.get_open_positions(kind='list')
            if position_details:
                self._create_pos_dict(position_details)
            
            return self._open_positions
        except (ValueError, TypeError, ServerError) as e:
            self._open_positions = last_version
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            self._open_positions = last_version
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    @api_rate_limit
    def trades(self):
        _ = self.positions
        return self._trading_cache
    
    @property
    @api_rate_limit
    def open_orders(self):
        '''
            Call the order method and return the open order dict.
        '''
        try:
            last_version = self._open_orders
            self._open_orders = {}
            orders = self._api.get_orders(kind='list')
            for order in orders:
                order_id, order = self._order_from_dict(order)
                self._open_orders[order.oid] = order
            
            return self._open_orders
        except (ValueError, TypeError, ServerError) as e:
            if isinstance(e, ServerError):
                self._open_orders =  last_version
                return self._open_orders
            else:
                self._open_orders =  last_version
                msg = str(e)
                handling = ExceptionHandling.WARN
                raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            self._open_orders =  last_version
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @property
    @api_rate_limit
    def orders(self, *args, **kwargs):
        '''
            Fetch a list of orders from the broker and update
            internal dicts. Returns both open and closed orders.
        '''
        return self.open_orders
    
    @property
    def tz(self, *args, **kwargs):
        return self._trading_calendar.tz
    
    def order(self, order_id):
        '''
            Fetch the order by id.
        '''
        try:
            order = self._api.get_order(order_id)
            oid, order = self._order_from_dict(self._fxcm_order_to_dict(
                    order))
            return order
        except ValueError as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
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
        
        price = order.price # limit price
        validity = order.order_validity
        # TODO: we track algo by adding a specifc account id
        # generalize this. Must have broker support to implement.
        tag = order.tag
        tag = tag if tag in self._api.account_ids else None
        
        validity = order_validity_map.teg(validity, 'DAY')
        
        #TODO: assumption price cannot be negative - validate.
        price = price if price > 0 else 0
        
        lots = int(quantity/asset.mult)
        try:
            if order_type  > 1:
                raise UnsupportedOrder(msg="Unsupported order type")
            
            if price > 0:
                order_id = self._create_entry_order(symbol=tradingsymbol, 
                                                    is_buy=is_buy, 
                                                    amount=lots, 
                                                    time_in_force=validity,
                                                    limit=price, 
                                                    is_in_pips=False, 
                                                    account_id=tag)
            else:
                if is_buy > 0:
                    # we buy!
                    order_obj = self._api.create_market_buy_order(
                            tradingsymbol, lots, account_id=tag)
                else:
                    # we sell!
                    order_obj = self._api.create_market_sell_order(
                            tradingsymbol, lots, account_id=tag) 
                order_id = order_obj.get_orderId()
            
            return order_id
        except (ValueError, TypeError, ServerError) as e:
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
        else:
            order_id = order_param
        
        try:
            order = self.order(order_id)
            quantity = kwargs.pop("quantity",order.quantity)
            price = kwargs.pop("price",order.price)
            lots = int(quantity/order.asset.mult)
            self._api.change_order(order_id, lots, price)
            return order_id
        except (ValueError, TypeError, ServerError) as e:
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
        else:
            order_id = order_param
        try:
            self._api.delete_order(order_id)
            return order_id
        except (ValueError, TypeError, ServerError) as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
            
    @api_rate_limit
    def close_position(self, trade_id,  amount, time_in_force='DAY', 
                       rate=None):
        '''
            Implement close_trade.
        '''
        try:
            trade_id = str(trade_id)
            if str(trade_id) in self._trading_cache:
                position = self._trading_cache[trade_id]
            else:
                _ = self.positions
                if trade_id not in self._trading_cache:
                    raise UnsupportedOrder(msg="Trade not found")
                position = self._trading_cache[trade_id]
                
            mult = position.asset.mult
            amount = int(amount/mult)
            self._api.close_trade(trade_id, amount, 
                                  order_type='AtMarket',
                                  time_in_force=time_in_force,
                                  rate=rate)
        except (ValueError, TypeError, ServerError) as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    @api_rate_limit
    def square_off(self, symbols=None, time_in_force='GTC', 
                   account_id=None):
        '''
            Do close_all or close_all_for_symbol if symbols are 
            supplied. This will sqaure off all positions for a 
            particular FX pair or all positions.
        '''
        try:
            if symbols:
                for sym in symbols:
                    self._api.close_all_for_symbol(
                            sym, order_type='AtMarket',
                            time_in_force=time_in_force,
                            account_id = account_id)
            else:
                self._api.close_all(order_type='AtMarket',
                                    time_in_force=time_in_force,
                                    account_id=account_id)
        except (ValueError, TypeError, ServerError) as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
        except RequestException as e:
            msg = str(e)
            handling = ExceptionHandling.WARN
            raise BrokerAPIError(msg=msg, handling=handling)
    
    def fund_transfer(self, amount):
        '''
            We do not implement fund transfer for FXCM.
        '''
        msg = "Please go to FXCM website for fund transfer"
        handling = ExceptionHandling.WARN
        raise BrokerAPIError(msg=msg, handling=handling)
    
    
    def _position_from_dict(self, p, closed=True):
        instrument_id = p['tradeId'] # check against double processing.
        
        if instrument_id in self._processed_positions and closed:
            return (None, None)
        
        asset = self._asset_finder.lookup_symbol(p['currency'])
        # TODO: assumed in 1000s, check and confirm.
        quantity = p['amountK']*1000
        pnl = p['grossPL']
        last_price = p['close']
        product_type = ProductType.DELIVERY
        average_price = 0
        side = -1
        
        if closed:
            buy_quantity = sell_quantity = quantity
            buy_price = p['open'] if p['isBuy'] is True else p['close']
            sell_price = p['open'] if p['isBuy'] is False else p['close']
            unrealized_pnl = 0
            realized_pnl = pnl
            timestamp = pd.Timestamp(datetime.strptime(p['closeTime'],
                                                       '%m%d%Y%H%M%S'),
                                     tz=self.tz)
            quantity = 0
            margin = 0
            self._processed_positions.append(instrument_id)
        else:
            buy_quantity = quantity if p['isBuy'] is True else 0
            buy_price = p['open'] if p['isBuy'] is True else 0
            sell_quantity = quantity if p['isBuy'] is False else 0
            sell_price = p['open'] if p['isBuy'] is False else 0
            realized_pnl = 0
            unrealized_pnl = pnl
            timestamp = pd.Timestamp(datetime.strptime(p['time'],
                                                       '%m%d%Y%H%M%S'),
                                     tz=self.tz)
            quantity = quantity if p['isBuy'] is True else -quantity
            margin = p['usedMargin']
        
        position = Position(asset, quantity,side,instrument_id,
                            product_type,average_price,margin,
                            timestamp,timestamp,buy_quantity,
                            buy_price,sell_quantity,sell_price,
                            pnl,realized_pnl,unrealized_pnl,
                            last_price)
        
        return (asset, position)
    
    def _create_pos_dict(self, position_details):
        self._open_positions = {}
        self._trading_cache = {}
        for p in position_details:
            asset, position = self._position_from_dict(p, closed = False)
            self._trading_cache[position.instrument_id] =\
                    FXCMPosition(position.asset, position.quantity)
            pos = self._open_positions.get(asset, None)
            if pos:
                self._open_positions[asset].add_to_position(position)
            else:
                self._open_positions[asset] = position
        
    def _order_from_dict(self, o):
        # pd.Timestamp(datetime.strptime('12142018032919','%m%d%Y%H%M%S'))
        order_dict = {}
        asset = self._asset_finder.lookup_symbol(o['currency'])
        
        order_dict['oid'] = o['orderId']
        order_dict['broker_order_id'] = order_dict['oid']
        order_dict['exchange_order_id'] = order_dict['oid']
        order_dict['parent_order_id'] = o['ocoBulkId']
        order_dict['asset'] = asset
        order_dict['user'] = 'algo'
        order_dict['placed_by'] = o['accountId']
        order_dict['product_type'] = ProductType.DELIVERY
        order_dict['order_flag'] = OrderFlag.NORMAL
        
        # FXCM is the liquidity provide, so filled is either all or nothing
        # TODO: check this assumption
        order_dict['quantity'] = o['amountK']*1000
        order_dict['filled'] = 0
        order_dict['pending'] = order_dict['quantity']
        order_dict['disclosed'] = 0
        
        ''' Entry Orders are by definition limit orders. The stoploss
        and limit rates mimick a bracket order with defined stoploss and
        take profit target respectively. We do not have native support
        for these in Blueshift yet.'''
        order_dict['order_type'] = OrderType.LIMIT
        order_dict['price'] = o['buy'] if o['isBuy'] is True else o['sell']
        # TODO: hack, the stops and the limits are NOT handled properly here.
        order_dict['trigger_price'] = o['limitRate']
        order_dict['stoploss_price'] = o['stopRate']
        
        order_dict['side'] = OrderSide.BUY if o['isBuy'] is True else\
                                                            OrderSide.SELL
        # TODO: assumes order is zero fill. Validate.
        order_dict['average_price'] = 0
        
        order_dict['order_validity'] = order_validity_map.get(
                o['timeInForce'],OrderValidity.DAY)
        
        
        order_dict['status'] = order_status_map[o['status']]
        
            
        order_dict['status_message'] = ''
        timestamp = datetime.strptime(o['time'], '%m%d%Y%H%M%S%f')
        order_dict['exchange_timestamp'] = pd.Timestamp(timestamp, 
                  tz=self.tz)
        # TODO: figure out the timestamp
        order_dict['timestamp'] = timestamp
        order_dict['tag'] = o['accountId']

        order = Order.from_dict(order_dict)        
        
        return order.oid, order
        
    def _create_entry_order(self, symbol, is_buy, amount, time_in_force,
                           limit=0, is_in_pips=False, account_id=None):
        '''
            Implements FXCM entry_order without the pesky `limit` thingy.
        '''
        if account_id is None:
            account_id = self._api.default_account
        else:
            try:
                account_id = int(account_id)
            except:
                raise TypeError('account_id must be an integer.')
                
        if account_id not in self._api.account_ids:
            raise ValueError('Unknown account id %s.' % account_id)
            
        try:
            amount = int(amount)
        except:
            raise TypeError('Order amount must be an integer.')
            
        if symbol not in self._api.instruments:
            raise ValueError('Unknown symbol %s.' % symbol)
            
        try:
            limit = float(limit)
        except:
            raise TypeError('rate must be a number.')
            
        order_type="Entry"
        
        if time_in_force not in ['GTC', 'DAY', 'GTD', 'IOC', 'FOK'] :
            msg = "time_in_force must be 'GTC', 'DAY', 'IOC', 'FOK', or 'GTD'."
            raise ValueError(msg)
            
        if is_in_pips is True:
            is_in_pips = 'true'
        elif is_in_pips is False:
            is_in_pips = 'false'
        else:
            raise ValueError('is_in_pips must be True or False.')
            
        if is_buy is True:
            is_buy = 'true'
        elif is_buy is False:
            is_buy = 'false'
        else:
            raise ValueError('is_buy must be True or False.')
            
        params = {
                  'account_id': account_id,
                  'symbol': symbol,
                  'is_buy': is_buy,
                  'rate': limit,
                  'amount': amount,
                  'order_type': order_type,
                  'is_in_pips': is_in_pips,
                  'time_in_force': time_in_force
                 }
        data = self._api.__handle_request__(method='trading/create_entry_order',
                               params=params, protocol='post')
        
        if 'data' in data and 'orderId' in data['data']:
            order_id = int(data['data']['orderId'])
            return order_id
        
        raise BrokerAPIError(msg='Missing orderId in servers answer.')
        return 0
        
    def _fxcm_order_to_dict(self, order):
        if not isinstance(order, fxcmpy_order):
            return {}
        
        order_dict = {}
        base_dict = order.__dict__
        attributes = order.parameter
        for attrib in attributes:
            order_dict[attrib] = base_dict["__"+str(attrib)+"__"]
        
        if 'time' in order_dict:
            order_dict['time'] = order_dict['time'].strftime('%m%d%Y%H%M%S%f')
            
        if 'status' in order_dict:
            order_dict['status'] = fxcm_status_values.teg(order_dict['status'])
        
        return order_dict