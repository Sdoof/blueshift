# -*- coding: utf-8 -*-
"""
Created on Sun Nov 25 11:48:50 2018

@author: prodi
"""
import pandas as pd
from blueshift.api import symbol, order_target_percent, order

def initialize(context):
    context.t1 = pd.Timestamp.now()
    context.asset = symbol('NIFTY-I')
    
def handle_data(context, data):
    order_target_percent(context.asset, 0.5)
    pass
    
def before_trading_start(context, data):
    pass

def analyze(context):
    ts = (pd.Timestamp.now() - context.t1).total_seconds()*1000
    print(f"backtest completed in {ts} milliseconds")
    total_order = len(context.orders)
    print(f"total orders {total_order}")