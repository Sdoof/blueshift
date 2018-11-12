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
  "owner": "user",
  "platform": "blueshift",
  # contact details for alerts and other message dispatch
  "contact":{
    "email":"user@email.com", # MUST BE A VALID EMAIL ID
    "mobile":"+447500000000"
  },
  # user workspace details - for persistance and record keeping
  "user_space": {
    "root": "",
    "performance": "performance",
    "orders": "orders",
    "objects": "objects",
    "logs": "logs",
    "code":"source"
  },
  # alerting configuration
  "alerts": {
    "errors": ["email","msg"],      # 'log', 'console', 'email', 'msg', 'websocket'
    "warnings": "log",
    "logs": "log",
    "platform_msg": "email",
    "third_party_msg": "email",
    "tag": "blueshift"
  },
  # backtest API description for the algo
  "backtester":{
    "name":"blueshift",
    "start": "2010-01-04",
    "end": "2018-01-04",
    "frequency": 1,
    "initial_capital": 10000
  },
  # live broker configuration for the algo
  "live_broker":{
    "name": "kite", 
    "api_key": "xxxxxxxxxxxxxxxx", 
    "api_secret": "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", 
    "id": "ZZZZZZZ",
    "rate_limit": 2,
    "rate_period": 1,
    "login_reset_time": [8,45]
  },
  # calendar configuration for the algo
  "calendar": {
    "tz": "Asia/Calcutta",
    "holidays": "nse_holidays.csv",
    "opens": [9,15,0],
    "closes": [9,15,0],
    "business_days": None,
    "weekends": [5,6]
  },
  # command control channel specification
  "command_channel":{
    "type": "redis",
    "addr": "127.0.0.1:9000"
  },
  # exceptions and restart policy
  "error_handling":{
    "data_error": "warn",
    "api_error": "warn",
    "uesr_error": "stop",
    "internalError": "re_start",
    "error": "stop",
  },        
  # risk management policy
  "risk_management": None
}
  
def generate_default_config(filename=None):
    if not filename:
        filename = "blueshift_config.json"
        
    with open(filename,"w") as fp:
        json.dump(_default_config,fp)
    