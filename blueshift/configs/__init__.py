# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 11:25:53 2018

@author: academy
"""
import json

#default_config
_default_config =\
{
 # general section
  "algo": "myalgo",
  "owner": "prodipta",
  "platform": "blueshift",
  "api_key": None,
  # contact details for alerts and other message dispatch
  "contact":{
    "email":"user@email.com", # MUST BE A VALID EMAIL ID
    "mobile":"+447500000000"
  },
  # user workspace details - for persistance and record keeping
  "user_workspace": {
    "root": "C:/Users/academy.academy-72/Documents/blueshift",
    "performance": "performance",
    "orders": "orders",
    "objects": "objects",
    "logs": "logs",
    "code":"source",
    "data":"data"
  },
  # alerting configuration
  "alerts": {
    "error": ["email","msg","console"], # 'log', 'console', 'email', 'msg', 'websocket'
    "warning": ["log","console"],
    "log": ["log"],
    "platform_msg": ["email"],
    "third_party_msg": ["email"],
    "tag": "blueshift"
  },
  # backtest API description for the algo
  "backtester":{
    "backtester_name":"blueshift",
    "start": "2010-01-04",
    "end": "2018-01-04",
    "backtest_frequency": 1,
    "initial_capital": 10000
  },
  # live broker configuration for the algo
  "live_broker":{
    "broker_name": "zerodha", 
    "api_key": "xxx", 
    "api_secret": "yyy", 
    "broker_id": "zzz",
    "rate_limit": 2,
    "rate_period": 1,
    "login_reset_time": [8,45],
    "live_frequency": 1
  },
  # calendar configuration for the algo
  "calendar": {
    "tz": "Asia/Calcutta",
    "cal_name": "NSE_EQ",
    "holidays": "nse_holidays.csv",
    "opens": [9,15,0],
    "closes": [9,15,0],
    "business_days": None,
    "weekends": [5,6]
  },
  # command control channel specification
  "command_channel":{
    "cmd_type": "redis",
    "cmd_addr": "127.0.0.1:9000"
  },
  # exceptions and restart policy
  "error_handling":{
    "data_error": "warn",
    "api_error": "warn",
    "user_error": "stop",
    "internal_error": "re_start",
    "error": "stop",
  },        
  # risk management policy
  "risk_management": None,
  # blueshift environmental variables
  "environment":{
    "BLUESHIFT_BROKER_TOKEN": None,
    "BLUESHIFT_API_KEY": None,
    "BLUESHIFT_CONFIG_FILE": None
  }
}
  
def generate_default_config(filename=None):
    if not filename:
        return json.dumps(_default_config)
        
    with open(filename,"w") as fp:
        json.dump(_default_config,fp)
    