# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 11:22:26 2018

@author: prodipta
"""
from blueshift.algorithm.api import symbol, order
import pandas as pd
import random

def initialize(context):
    context.t1 = pd.Timestamp.now()
    print("initialize {}".format(context.timestamp))
    context.asset = symbol("NIFTY-I")
    
def before_trading_start(context, data):
    return
    
def handle_data(context, data):
    order(context.asset, random.randint(10,50))
    pass
    
def analyze(context):
    print("analyze {}".format(context.timestamp))
    print(context.account)
    t2 = pd.Timestamp.now()
    elapsed_time = (t2-context.t1).total_seconds()*1000
    print("run complete in {} milliseconds".format(elapsed_time))