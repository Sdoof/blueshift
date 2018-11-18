# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 11:22:26 2018

@author: prodipta
"""
from blueshift.algorithm.api import symbol, order, set_broker
from blueshift.utils.exceptions import BrokerAPIError
import pandas as pd
import random


def initialize(context):
    context.t1 = pd.Timestamp.now()
    context.asset = symbol("NIFTY-I")
    print(context.asset)
    
def before_trading_start(context, data):
    return
    
def handle_data(context, data):
    order(context.asset, random.randint(10,50))
    if random.randint(1,100000) == 10:
        raise BrokerAPIError(msg="some random error")
    pass

def heartbeat(context):
    print(f"heartbeat {context.timestamp}")
    
def analyze(context):
    t2 = pd.Timestamp.now()
    elapsed = (t2-context.t1).total_seconds()*1000
    
    total_order = len(context.orders)
    orders_per_ms = total_order/elapsed
    msg1 = f"complete in {elapsed} milliseconds,"
    msg2=  f" handled {orders_per_ms} orders per millisecond"
    print(msg1+msg2)
        
        