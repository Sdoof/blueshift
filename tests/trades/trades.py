# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 09:32:51 2018

@author: academy
"""

import pandas as pd
import unittest
from blueshift.trades._trade import Trade
from blueshift.trades._order import Order
from blueshift.trades._position import Position
from blueshift.trades._order_types import (
        OrderSide,
        OrderUpdateType)
from blueshift.assets._assets import Asset
import random

orders = {}
positions = {}
pnls = {}

def order_stuff(qty, side, asset):
    global orders
    global positions
    o = Order(qty,side, asset)
    orders[o.oid] = o
    execute_order(o)
    return o.oid
    
def execute_order(order):
    global orders
    global positions
    tid=1
    executed = 0
    
    while executed < order.quantity:
        price = min(11800,max(11000,11500 + 
                          round((random.random()-0.5)*100,2)))
    
        traded = round(random.random()*100)
        if traded <= 0:
            continue
        
        if order.quantity - executed < traded:
            traded = order.quantity - executed
            
        ts = pd.Timestamp.now()
        t = Trade(tid, traded, order.side, order.oid, 
                  order.broker_order_id, order.exchange_order_id, 42, 
                  order.asset,1, price, ts, ts)
        orders[order.oid].update(OrderUpdateType.EXECUTION,t)
        
        if t.asset in positions:
            positions[t.asset].update(t)
        else:
            p = Position.from_trade(t)
            positions[t.asset] = p
        
        executed = traded + executed
        tid = tid + 1


asset = Asset(-1,"NIFTY18OCTFUT", exchange_name="NSE")
o1 = order_stuff(1500,OrderSide.BUY,asset)
o2 = order_stuff(1000,OrderSide.SELL,asset)

pos = list(positions.values())[0]
average_buy = orders[o1].average_price
average_sell = orders[o2].average_price
last_price = pos.last_price

realized_pnl = round(1000*(average_sell - average_buy),2)
unrealized_pnl = round(500*(last_price - average_buy),2)
total_pnl = round(realized_pnl + unrealized_pnl,2)


class TestAssets(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_pnls(self):
        self.assertEqual(realized_pnl, round(pos.realized_pnl,2))
        self.assertEqual(unrealized_pnl, round(pos.unrealized_pnl,2))
        self.assertEqual(total_pnl, round(pos.pnl,2))
        
if __name__ == '__main__':
    unittest.main()