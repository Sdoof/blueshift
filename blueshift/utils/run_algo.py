# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 09:00:35 2018

@author: prodipta
"""
from os.path import isabs, join, isfile
import pandas as pd
from collections import namedtuple

from blueshift.configs.config import BlueShiftConfig
from blueshift.alerts.alert import BlueShiftAlertManager
from blueshift.algorithm.algorithm import MODE
from blueshift.algorithm.api import (get_broker, get_calendar,
                                     register_calendar,
                                     register_broker)
from blueshift.utils.calendars.trading_calendar import (
                                            TradingCalendar)
from blueshift.utils.exceptions import InitializationError
from blueshift.alerts import (register_alert_manager,
                              get_alert_manager)

TradingEnvironment = namedtuple("TradingEnvironment",
                                ('mode', 'config', 'alert_manager', 
                                 'trading_calendar', 
                                 'broker_tuple','algo_file'))


def start_up(*args, **kwargs):
    '''
        Function to create a trading environment with all objects
        necessary to run the algo.
    '''
    # the config file, default is blueshift_config.json in current
    # directory
    configfile = kwargs.get("configfile", 'blueshift_config.json')
    config = BlueShiftConfig(configfile=configfile, *args, **kwargs)
    
    # create and register alert manager
    alert_manager = BlueShiftAlertManager(config)
    register_alert_manager(alert_manager)
    alert_manager = get_alert_manager()
    
    # algo file, search in the current directory, else look in 
    # the code directory as specified by user config object.
    algo_file = kwargs.get("algo_file", None)
    algo_file = get_algo_file(algo_file, config)
    
    # create the trading calendar based on the config file.
    trading_calendar = create_calendar(config)
    
    # create the broker based on config details.
    mode =  kwargs.get("mode", MODE.BACKTEST)
    broker = create_broker(config, mode, trading_calendar,
                           *args, **kwargs)
    
    trading_environment = TradingEnvironment(mode,config,
                                             alert_manager,
                                             trading_calendar,
                                             broker,
                                             algo_file)
    
    return trading_environment
        
    
def get_algo_file(algo_file, config):
    '''
        Search the current directory, else go the user config
        directory (code) and search.
    '''
    if not isabs(algo_file) and not isfile(algo_file):
        user_root = config.user_space['root']
        user_code_dir = config.user_space['code']
        algo_file = join(user_root, user_code_dir, algo_file)
        
    if not isfile(algo_file):
        raise InitializationError("algo file does not exists.")
    
    # TODO: add local import replacement to support multi-file
    # projects. No mods required for PYTHONPATH.
    return algo_file

def create_calendar(config):
    '''
        Create the calendar based on config data. Then register
        the calendar and return the object. This calendar can be
        then fetched using the get_calendar API from user code.
    '''
    name = config.calendar['cal_name']
    tz = config.calendar['tz']
    opens = config.calendar['opens']
    closes = config.calendar['closes']
    business_days = config.calendar['business_days']
    weekends = config.calendar['weekends']
    holidays = config.calendar['holidays']
    trading_calendar = None
    
    if business_days:
        if not isabs(business_days) and not isfile(business_days):
            user_root = config.user_space['root']
            user_data_dir = config.user_space['data']
            business_days = join(user_root, user_data_dir, 
                                 business_days)
        
        if not isfile(business_days):
            msg = "business days file does not exists."
            raise InitializationError(msg)
        
        dts = pd.read_csv(business_days, parse_dates=True)
        dts = pd.to_datetime(dts.iloc[:,0].tolist())
    
        trading_calendar = TradingCalendar(name,tz=tz, bizdays=dts,
                                   opens=opens, closes=closes,
                                   weekends=weekends)
    else:
        trading_calendar = TradingCalendar(name,tz=tz, opens=opens, 
                                           closes=closes,
                                           weekends=weekends)
    
    if holidays:
        if not isabs(holidays) and not isfile(holidays):
            user_root = config.user_space['root']
            user_data_dir = config.user_space['data']
            holidays = join(user_root, user_data_dir, holidays)
        
        if not isfile(holidays):
            msg = "holidays file does not exists."
            raise InitializationError(msg)
        
        dts = pd.read_csv(holidays, parse_dates=True)
        dts = pd.to_datetime(dts.iloc[:,0].tolist())
        trading_calendar.add_holidays(dts)
        
    register_calendar(name,trading_calendar)
    
    return get_calendar(name)

def create_broker(config, mode, trading_calendar, *args, **kwargs):
    '''
        Create the broker object based on name mapping to a 
        particular broker module under utils/brokers/.
    '''
    
    if mode == MODE.BACKTEST:
        name = config.backtester['backtester_name']
        start_date = config.backtester['start']
        end_date = config.backtester['end']
        frequency = config.backtester['backtest_frequency']
        initial_capital = config.backtester['initial_capital']
        
        register_broker(name,start_date=start_date, 
                        end_date=end_date, 
                        trading_calendar=trading_calendar,
                        initial_capital=initial_capital,
                        frequency=frequency)
    elif mode == MODE.LIVE:
        name = config.live_broker['broker_name']
        api_key = config.live_broker['api_key']
        api_secret = config.live_broker['api_secret']
        user_id = config.live_broker['broker_id']
        rate_limit = config.live_broker['rate_limit']
        rate_period = config.live_broker['rate_period']
        timeout = config.live_broker['login_reset_time']
        frequency = config.live_broker['live_frequency']
        
        request_token = kwargs.get('request_token',None)
        auth_token = kwargs.get('auth_token',None)
        
        if not request_token and not auth_token:
            msg = "No authentication info given."
            raise InitializationError(msg)
        elif auth_token:
            register_broker(name, api_key=api_key,
                            api_secret=api_secret,
                            user_id=user_id, rate_limit=rate_limit,
                            rate_period=rate_period,timeout=timeout,
                            trading_calendar=trading_calendar, 
                            frequency=frequency,
                            auth_token=auth_token)
        else:
            register_broker(name, api_key=api_key,
                            api_secret=api_secret,
                            user_id=user_id, rate_limit=rate_limit,
                            rate_period=rate_period,timeout=timeout,
                            trading_calendar=trading_calendar, 
                            frequency=frequency,
                            request_token=request_token)
    else:
        raise InitializationError("Illegal mode supplied.")
        
    return get_broker(name)


    
    