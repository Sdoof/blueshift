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
Created on Wed Jan  9 10:17:29 2019

@author: prodipta
"""
from os import path as os_path
import pandas as pd
import json
from collections import OrderedDict
#import empyrical
#import bottleneck
from blueshift.utils.decorators import singleton
from blueshift.utils.types import MaxSizedOrderedDict, NANO_SECOND
from blueshift.utils.exceptions import (InitializationError,
                                        BlueShiftException,
                                        ValidationError,
                                        ExceptionHandling,
                                        DataWriteException)
from blueshift.utils.helpers import (read_positions_from_dict,
                                     read_transactions_from_dict,
                                     read_orders)
from blueshift.utils.cutils import cdict_diff
from blueshift.configs.defaults import (blueshift_saved_orders_path,
                                        blueshift_save_perfs_path)
from blueshift.trades._position import Position


@singleton
class TransactionsTracker(object):
    """ class to track and save historical transactions record. """
    MAX_TRANSACTIONS = 50000
    TRANSACTIONS_FILE = 'transactions.json'
    OPEN_ORDERS_FILE = 'open_orders.json'
    
    def __init__(self, blotter_root=None):
        self._create(blotter_root)
        
    def _create(self, blotter_root):
        self._blotter_root = blotter_root
        self._txn_fname = os_path.expanduser(os_path.realpath(
                os_path.join(self._blotter_root,self.TRANSACTIONS_FILE)))
        self._oo_fname = os_path.expanduser(os_path.realpath(
                os_path.join(self._blotter_root,self.OPEN_ORDERS_FILE)))
        
        self._transactions = OrderedDict()
        self._open_orders = {}
        self._unprocessed_orders = {}
        self._known_orders = set()
        
        self._last_reconciled = None
        self._last_saved = None
        self._needs_reconciliation = False
    
    @classmethod
    def _prefix_fn(cls, timestamp=None):
        if timestamp is None:
            return ''
        return str(pd.Timestamp(timestamp.date())).replace(' ', '_').\
                                                    replace(':','-')
    
    def _save_transactions_list(self, timestamp=None):
        txns_write = OrderedDict()
        open_orders = {}
        
        def skip_ts(ts, timestamp):
            if timestamp is None:
                return False
            if ts.date() == timestamp.date():
                return False
            else:
                return True
        
        # process the closed transactions. Filter for date if timestapm
        # is provided, else save all.
        for ts in self._transactions:
            if skip_ts(ts, timestamp):
                continue
            txns = self._transactions[ts]
            txns_list = []
            for txn in txns:
                txns_list.append(txn.to_json())
            txns_write[str(ts)] = txns_list
        # process the open orders, if any
        for order_id in self._open_orders:
            open_orders[str(order_id)] = self._open_orders[order_id].to_json()
        try:
            if txns_write:
                # dated output if timestamp is provided, else all.
                fname = self._prefix_fn(timestamp) + self._txn_fname
                with open(fname, 'w') as fp:
                    json.dump(txns_write, fp)
                fname = self._oo_fname
                with open(fname, 'w') as fp:
                    json.dump(open_orders, fp)
        except (TypeError, OSError):
            msg = f"failed to write blotter data to {self._pos_fname}"
            handling = ExceptionHandling.WARN
            raise DataWriteException(msg=msg, handling=handling)
            
        self._last_saved = timestamp if timestamp is not None else\
                            pd.Timestamp.now()
            
    def _read_transactions_list(self, asset_finder, timestamp=None):
        transactions = MaxSizedOrderedDict(
                max_size=self.MAX_TRANSACTIONS, chunk_size=1)
        
        fname = self._prefix_fn(timestamp) + self._txn_fname
        if os_path.exists(fname):
            # expected transactions keyed to date-time
            try:
                with open(self._txn_fname) as fp:
                    txns_dict = dict(json.load(fp))
                txns, ids = read_transactions_from_dict(
                        txns_dict, asset_finder, pd.Timestamp)
                
                transactions = MaxSizedOrderedDict(
                        txns, max_size=self.MAX_TRANSACTIONS, chunk_size=1)
                self._known_orders.union(ids)
                
            except (TypeError, KeyError, BlueShiftException):
                raise InitializationError(msg="illegal transactions data.")
        
        self._transactions = transactions
        
        if os_path.exists(self._oo_fname):
            with open(self._oo_fname) as fp:
                open_orders = dict(json.load(fp))
            self._open_orders, ids = read_orders(open_orders, asset_finder)
            self._known_orders.union(ids)
    
    def add_transaction(self, order_id, order):
        """ log a transaction with the tracker """
        self._unprocessed_orders[order_id] = order
        self._known_orders.add(order_id)
        self._needs_reconciliation = True
    
    def reconcile_transactions(self, orders, timestamp=None):
        """
            process the un-processed orders list. If missing order add it
            back to the un-processed list to check in the next run.
        """
        missing_orders = extra_orders = []
        matched_orders = {}
        unprocessed_orders = list(self._unprocessed_orders.keys())
        
        for order_id in unprocessed_orders:
            if order_id in orders:
                order = orders[order_id]
                if not order.is_open():
                    # they can no longer change resulting positions
                    order_list = self._transactions.get(order.timestamp,[])
                    order_list.append(order)
                    self._transactions[order.timestamp] = order_list
                    self._unprocessed_orders.pop(order_id)
                    matched_orders[order_id] = order
                else:
                    # these still can as they get filled.
                    self._open_orders[order_id] = order
            else:
                missing_orders.append[order]
        
        for key in orders:
            if key not in self._known_orders:
                extra_orders.append(orders[key])
        
        if missing_orders or extra_orders:
            matched = False
        else:
            matched = True
        
        self._needs_reconciliation = False
        self._last_reconciled = timestamp if timestamp is not None else\
                                pd.Timestamp.now()
        
        return matched, missing_orders, extra_orders, matched_orders
    
    def update_positions_from_orders(self, orders, positions):
        """ 
            create a list of positions from orders - NOTE: they may not have
            the correct price and pnl information.
        """
        # first loop through the matched orders
        keys = list(orders.keys())
        for key in keys:
            order = orders.pop(key)
            asset = order.asset
            pos = Position.from_order(order)
            if asset in positions:
                positions[asset].add_to_position(pos)
            else:
                positions[asset] = pos
        # now if there is any open orders, add to positions from them
        for key in self._open_orders:
            order = self._open_orders[key]
            if order.filled > 0:
                pos = Position.from_order(order)
                if asset in positions:
                    positions[asset].add_to_position(pos)
                else:
                    positions[asset] = pos
                    
        return positions

@singleton
class Blotter(object):
    '''
        Blotter tracks the order generated by the algo and matches them
        from the order status received from the broker API. It also computes
        the positions that should arise out of those algo orders and matches
        against the positions from broker API. Cumulative sum of the realized
        and unrealized pnls from these positions are algo pnl. This helps us
        avoid computing algo performance solely based on account information,
        as the account can also be affected by other means (manual trades or
        capital withdrawals etc.).
    '''
    MAX_TRANSACTIONS = 50000
    POSITIONS_FILE = 'positions.json'
    TRANSACTIONS_FILE = 'transactions.json'
    PERFORMANCE_FILE = 'performance.json'
    RISKS_FILE = 'risk_metrics.json'
    
    def __init__(self, mode, asset_finder, data_portal, broker_api,
                 logger=None, blotter_root=None, account_net=None, 
                 starting_positions={}, timestamp=None, alert_manager=None):
        # initialize the start positions and historical records of 
        # transactions. If a start position is suppplied, that will 
        # overwrite the saved positions.
        self._blotter_root = blotter_root if blotter_root is not None \
                                else blueshift_saved_orders_path()
        self._mode = mode
        self._asset_finder = asset_finder
        self._data_portal = data_portal
        self._broker = broker_api
        self._txn_fname = os_path.expanduser(os_path.realpath(
                os_path.join(self._blotter_root,self.TRANSACTIONS_FILE)))
        self._pos_fname = os_path.expanduser(os_path.realpath(
                os_path.join(self._blotter_root,self.POSITIONS_FILE)))
        
        self.reset(timestamp, account_net, starting_positions)
        
        if alert_manager:
            alert_manager.register_callback(self.save)
        
    
    def reset(self, timestamp, account_net=None, starting_positions={}):
        self._transactions = MaxSizedOrderedDict(
                    max_size=self.MAX_TRANSACTIONS, chunk_size=1)
        self._current_pos = {}
        self._unprocessed_orders = {}
        self._known_orders = set()
        
        self._commisions = 0
        self._trading_charges = 0
        self._pnl = 0
        self._current_net = 0
        self._account_view = {}
        
        self._last_reconciled = None
        self._last_saved = None
        self._needs_reconciliation = False    
        
        self._init_positions_transactions(starting_positions)
        self._current_date = pd.Timestamp(
                timestamp.date()) if timestamp else pd.Timestamp(
                        pd.Timestamp.now().date())
    
    def _init_positions_transactions(self, positions):
        txns, pos = self._read_positions_transactions()
        if positions:
            positions = {**pos, **positions}
        
        self._transactions = txns
        self._current_pos = positions
            
    def _read_positions_transactions(self):        
        positions = {}
        transactions = MaxSizedOrderedDict(
                max_size=self.MAX_TRANSACTIONS, chunk_size=1)
        
        if os_path.exists(self._pos_fname):
            # expect jsonified data of positions keyed to assets.
            try:
                with open(self._pos_fname) as fp:
                    positions_dict = dict(json.load(fp))
                positions = read_positions_from_dict(
                        positions_dict, self._asset_finder)
            except (TypeError, KeyError, BlueShiftException):
                raise InitializationError(msg="illegal positions data.")
                
        if os_path.exists(self._txn_fname):
            # expected transactions keyed to date-time
            try:
                with open(self._txn_fname) as fp:
                    txns_dict = dict(json.load(fp))
                txns, _ = read_transactions_from_dict(
                        txns_dict, self._asset_finder, pd.Timestamp)
                
                transactions = MaxSizedOrderedDict(
                        txns, max_size=self.MAX_TRANSACTIONS, chunk_size=1)
                
            except (TypeError, KeyError, BlueShiftException):
                raise InitializationError(msg="illegal transactions data.")
                
        return transactions, positions
    
    def _save_position_transactions(self, write_version=True):
        pos_write = {}
        try:
            for pos in self._current_pos:
                pos_write[pos.symbol] = self._current_pos[pos].to_json()
        except (TypeError, KeyError, BlueShiftException):
            raise ValidationError(msg="corrupt positions data in blotter.")
            
        txns_write = OrderedDict()
        try:
            for ts in self._transactions:
                txns = self._transactions[ts]
                txns_list = []
                for txn in txns:
                    txns_list.append(txn.to_json())
                txns_write[str(ts)] = txns_list
        except (TypeError, KeyError, BlueShiftException) as e:
            raise e
            msg = "corrupt transactions data in blotter."
            handling = ExceptionHandling.WARN
            raise ValidationError(msg=msg, handling=handling)
            
        try:
            if pos_write:
                with open(self._pos_fname, 'w') as fp:
                    json.dump(pos_write, fp)
            
            if txns_write:
                with open(self._txn_fname, 'w') as fp:
                    json.dump(txns_write, fp)
        except (TypeError, OSError):
            msg = f"failed to write blotter data to {self._pos_fname}"
            handling = ExceptionHandling.WARN
            raise DataWriteException(msg=msg, handling=handling)
    
    def save(self):
        account = self._broker.account
        positions = self._broker.positions
        orders = self._broker.orders
        
        if self._needs_reconciliation:
            print("calling reconciliation")
            self._reconcile(positions, orders, account)
        self._save_position_transactions()
    
    def add_transactions(self, order_id, order, fees, charges):
        """ add entry to blotter to be verified"""
        self._unprocessed_orders[order_id] = order
        self._known_orders.add(order_id)
        self._commisions = self._commisions + fees
        self._trading_charges = self._trading_charges + charges
        self._needs_reconciliation = True
    
    def _reconcile_orders(self, orders):
        """
            process the un-processed orders list. If missing order add it
            back to the un-processed list to check in the next run.
        """
        missing_orders = extra_orders = []
        matched_orders = {}
        unprocessed_orders = list(self._unprocessed_orders.keys())
        
        for order_id in unprocessed_orders:
            if order_id in orders:
                order = orders[order_id]
                if not order.is_open():
                    order_list = self._transactions.get(order.timestamp,[])
                    order_list.append(order)
                    self._transactions[order.timestamp] = order_list
                    self._unprocessed_orders.pop(order_id)
                    matched_orders[order_id] = order
                else:
                    # open orders treated separetely, they may have 
                    # some fill, but adding them to transactions may 
                    # lead to double-counting. We track open orders not
                    # to 
                    pass
            else:
                missing_orders.append[order]
        
        for key in orders:
            if key not in self._known_orders:
                extra_orders.append(orders[key])
        
        if missing_orders or extra_orders:
            matched = False
        else:
            matched = True
        
        return matched, missing_orders, extra_orders, matched_orders
    
    def _update_positions_from_orders(self, orders):
        keys = list(orders.keys())
        for key in keys:
            order = orders.pop(key)
            asset = order.asset
            pos = Position.from_order(order)
            if asset in self._current_pos:
                self._current_pos[asset].add_to_position(pos)
            else:
                self._current_pos[asset] = pos
    
    def _reconcile_positions(self, positions):
        unexplained_pos = cdict_diff(self._current_pos, positions)
        if unexplained_pos:
            matched = False
        else:
            matched = True
        
        return matched, unexplained_pos
    
    def _reconcile_account(self, account):
        net_value = (self._current_net + self._pnl)
        net_difference = account['net'] - net_value
        self._current_net = account['net']
        
        self._account_view = {"net": account['net'],
                              "cash": account['cash'],
                              "margin": account['margin'],
                              "net_difference": net_difference}
    
    def _reconcile(self, positions, orders, account, timestamp=None):
        order_matched, missing_orders, extra_orders, matched_orders = \
                        self._reconcile_orders(orders)
        self._update_positions_from_orders(matched_orders)
        pos_matched, unexplained_pos = \
                        self._reconcile_positions(positions)
        self._reconcile_account(account)                                                    
        self._needs_reconciliation = False
        
        if not order_matched:
            msg =f"Orders reconciliation failed. Missing: {missing_orders}."
            msg = msg + f" Extra:{extra_orders}"
            print(msg)
        if not pos_matched:
            msg =f"Positions reconciliation failed."
            msg = msg + f" Unexplained:{unexplained_pos}"
            print(msg)
                    
        
        if not timestamp:
            timestamp = pd.Timestamp.now().value
            timestamp = pd.Timestamp(int(timestamp/NANO_SECOND)*NANO_SECOND)
            
        self._last_reconciled = timestamp
    
    
    def _compute_pnl(self, open_pos, closed_pos):
        self._pnl = 0
        
        for pos in closed_pos:
            self._pnl = self._pnl + pos.pnl
        
        for key in open_pos:
            self._pnl = self._pnl + pos[key].pnl
    
    
    