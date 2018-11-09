# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 11:22:26 2018

@author: prodipta
"""
from blueshift.algorithm.api import symbol, order, set_broker
import pandas as pd
import random

def initialize(context):
    start_date = pd.Timestamp('2017-01-04')
    end_date = pd.Timestamp('2018-01-04')
    tz = 'Asia/Calcutta'

    set_broker("backtest",start_date=start_date,
                        end_date=end_date, tz=tz,initial_capital=45000)
    
    context.t1 = pd.Timestamp.now()
    print("initialize {}".format(context.timestamp))
    context.asset = symbol("NIFTY-I")
    
def before_trading_start(context, data):
    return
    
def handle_data(context, data):
    #order(context.asset, random.randint(10,50))
    pass
    
def analyze(context):
    print("analyze {}".format(context.timestamp))
    print(context.account)
    t2 = pd.Timestamp.now()
    elapsed_time = (t2-context.t1).total_seconds()*1000
    print("run complete in {} milliseconds".format(elapsed_time))
    
    pnl = 0
    realized = 0
    unrealized = 0
    portfolio = context.portfolio
    for p in portfolio:
        pnl = pnl + portfolio[p].pnl
        realized = realized + portfolio[p].realized_pnl
        unrealized = unrealized + portfolio[p].unrealized_pnl
        print(portfolio[p])
        
    print(f"realized: {realized}, unrealized: {unrealized}, total {pnl}")
        
        
        