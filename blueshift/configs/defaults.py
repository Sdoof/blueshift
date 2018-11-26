# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 08:43:56 2018

@author: prodipta
"""
from os import path as os_path
from os import makedirs as os_makedirs
import errno

from blueshift.utils.exceptions import BlueShiftPathException
from blueshift.configs.config import get_config

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
    "closes": [3,30,0],
    "business_days": None,
    "weekends": [5,6]
  },
  # command control channel specification
  "channels":{
    "cmd_addr": "127.0.0.1:9001",
    "msg_addr": "127.0.0.1:9000",
    "timeout": 10
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
    "BLUESHIFT_CONFIG_FILE": None,
    "BLUESHIFT_ROOT": None
  }
}
    
def ensure_directory(path):
    if os_path.isdir(path):
        return
    try:
        os_makedirs(path)
        return
    except OSError as e:
        if e.errno == errno.EEXIST:
            return
    
    msg = f"directory {path} not found and failed to create."
    raise BlueShiftPathException(msg=msg)

def blueshift_root(environ=None):
    config = get_config()
    if config:
        root = config.user_space['root']
    elif environ:
        root = environ.get("BLUESHIFT_ROOT", None)
    else:
        root = os_path.expanduser('~/.blueshift')
    
    ensure_directory(root)
    return root

def blueshift_dir(path, environment=None):
    root = blueshift_root(environment)
    if isinstance(path, (list, set)):
        path = os_path.join(root, *path)
    else:
        path = os_path.join(root, path)
    
    ensure_directory(path)
    return path

def blueshift_log_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['logs']
    else:
        target_dir = "logs"
    
    return blueshift_dir(target_dir)

def blueshift_data_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['data']
    else:
        target_dir = "data"
    
    return blueshift_dir(target_dir)

def blueshift_source_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['code']
    else:
        target_dir = "source"
    
    return blueshift_dir(target_dir)

def blueshift_save_perfs_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['performance']
    else:
        target_dir = "performance"
    
    return blueshift_dir(target_dir)

def blueshift_saved_objs_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['objects']
    else:
        target_dir = "objects"
    
    return blueshift_dir(target_dir)

def blueshift_saved_orders_path():
    config = get_config()
    
    if config:
        target_dir = config.user_space['orders']
    else:
        target_dir = "orders"
    
    return blueshift_dir(target_dir)


def get_config_alerts():
    config = get_config()
    
    if config:
        alerts = config.alerts
    else:
        alerts = _default_config["alerts"]
        
    return alerts

def get_config_tz():
    config = get_config()
    
    if config:
        tz = config.calendar.get('tz','Etc/UTC')
    else:
        tz = 'Etc/UTC'
        
    return tz

def get_config_recovery(error_type):
    config = get_config()
    
    if config:
        recovery = config.recovery.get(error_type, None)
    else:
        recovery = _default_config["recovery"].get(error_type, None)
        
    return recovery

def get_config_name():
    config = get_config()
    
    if config:
        name = config.algo
    else:
        name = _default_config["algo"]
        
    return name

def get_config_channel(channel_name):
    config = get_config()
    
    if config:
        channel = config.channels[channel_name]
    else:
        channel = _default_config["channels"][channel_name]
        
    return channel

def get_config_calendar_details():
    config = get_config()
    
    if config:
        cal_dict = config.calendar
    else:
        cal_dict = _default_config["calendar"]
        
    return cal_dict

def get_config_backtest_details():
    config = get_config()
    
    if config:
        bt_dict = config.backtester
    else:
        bt_dict = _default_config["backtester"]
        
    return bt_dict

def get_config_livetrade_details():
    config = get_config()
    
    if config:
        lt_dict = config.live_broker
    else:
        lt_dict = _default_config["live_broker"]
        
    return lt_dict

def get_config_env_vars(var_name=None):
    config = get_config()
    
    if config:
        if not var_name:
            var = config.env_vars
        else:
            var = config.env_vars[var_name]
    else:
        if not var_name:
            var = _default_config["environment"]
        else:
            var = _default_config["environment"][var_name]
        
    return var

def blueshit_run_set_name(name):
    config = get_config()
    if config:
        config.algo = name
    
def blueshift_run_get_name():
    config = get_config()
    if config:
        return config.algo

    return "blueshift"

