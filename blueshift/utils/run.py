# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 09:00:35 2018

@author: prodipta
"""
from os.path import isabs, join, isfile, expanduser, basename
from os import environ as os_environ
from sys import exit as sys_exit
import pandas as pd
from collections import namedtuple
import click
import json


from blueshift.configs.config import BlueShiftConfig
from blueshift.alerts.alert import BlueShiftAlertManager
from blueshift.algorithm.algorithm import TradingAlgorithm
from blueshift.algorithm.state_machine import MODE
from blueshift.algorithm.api import (get_broker, get_calendar,
                                     register_calendar,
                                     register_broker)
from blueshift.utils.calendars.trading_calendar import (
                                            TradingCalendar)
from blueshift.utils.exceptions import (InitializationError, 
                                        BlueShiftException)
from blueshift.alerts import (register_alert_manager,
                              get_alert_manager)
from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.general_helpers import OnetoOne

TradingEnvironment = namedtuple("TradingEnvironment",
                                ('mode', 'config', 'alert_manager', 
                                 'trading_calendar', 
                                 'broker_tuple','algo_file'))


BROKER_TOKEN_EVNVAR = 'BLUESHIFT_BROKER_TOKEN'

@singleton
@blueprint
class BlueShiftEnvironment(object):
    '''
        The builder class of underlying objects - calendar, broker tuple, 
        configuration and alert manager.
    '''
    RUN_MODE_MAP = OnetoOne({'backtest':MODE.BACKTEST,
                             'live': MODE.LIVE})
    
    def __init__(self):
        self.config = None
        self.alert_manager = None
        self.trading_calendar = None
        self.broker_tuple = None
        self.algo_file = None
        self.mode = None
        self.env_vars = {}
        self._initialized = False
        
    def __str__(self):
        mode = self.RUN_MODE_MAP.teg(self.mode)
        return f"Blueshift Environment: {mode}"
    
    def __repr__(self):
        return self.__str__()
    
    def create_environment(self, *args, **kwargs):
        '''
            Function to create a trading environment with all objects
            necessary to run the algo.
        '''
        try:
            self.create_config(*args, **kwargs)
            self.extract_env_vars()
            self.create_alert_manager(*args, **kwargs)
            
            algo_file = kwargs.get("algo_file", None)
            self.get_algo_file(algo_file)
            
            self.create_calendar()
            
            # create the broker based on config details.
            mode =  kwargs.pop("mode", MODE.BACKTEST)
            mode = self.RUN_MODE_MAP.get(mode,mode)
            self.mode = mode
            self.create_broker(*args, **kwargs)
            
            self.save_env_vars()
        except BlueShiftException as e:
            click.secho(str(e), fg="red")
            sys_exit(1)
        
    def delete_environment(self, *args, **kwargs):
        pass
    
    def create_config(self, *args, **kwargs):
        '''
            create the config object from the config file, default 
            is .blueshift_config.json in the home directory.
        '''
        config_file = kwargs.pop("config_file", None)
        if not config_file:
            config_file = os_environ.get("BLUESHIFT_CONFIG_FILE", None)
        if not config_file:
            config_file = join(expanduser('~'), '.blueshift',
                               '.blueshift_config.json')
        
        self.config = BlueShiftConfig(config_file=config_file, 
                                      *args, **kwargs)
        self.env_vars["BLUESHIFT_API_KEY"] = \
                    self.config.env_vars["BLUESHIFT_API_KEY"]
        self.env_vars["BLUESHIFT_CONFIG_FILE"] = config_file
    
    def extract_env_vars(self, *args, **kwargs):
        '''
            First try to extract the environment variables from the
            list in config. Then over-write if any supplied in the
            kwwargs.
        '''
        for var in self.config.env_vars:
            self.env_vars[var] = os_environ.get(var, None)
        for var in self.env_vars:
            self.env_vars[var] = kwargs.pop(var, self.env_vars[var])
            
    def save_env_vars(self):
        for var in self.env_vars:
            value = self.env_vars[var]
            if value:
                os_environ[var] = value
    
    def create_alert_manager(self, *args, **kwargs):
        '''
            create and register the alert manager.
        '''
        alert_manager = BlueShiftAlertManager(self.config)
        register_alert_manager(alert_manager)
        self.alert_manager = get_alert_manager()
    
    def get_algo_file(self, algo_file):
        '''
            Search the current directory, else go the user config
            directory (code) and search.
        '''
        if not algo_file:
            raise InitializationError(msg="missing algo file.")
        if not isabs(algo_file) and not isfile(algo_file):
            user_root = self.config.user_space['root']
            user_code_dir = self.config.user_space['code']
            algo_file = join(user_root, user_code_dir, algo_file)
            
        if not isfile(algo_file):
            raise InitializationError(msg="algo file does not exists.")
        
        # TODO: add local import replacement to support multi-file
        # projects. No mods required for PYTHONPATH.
        self.algo_file = algo_file

    def create_calendar(self):
        '''
            Create the calendar based on config data. Then register
            the calendar and return the object. This calendar can be
            then fetched using the get_calendar API from user code.
        '''
        name = self.config.calendar['cal_name']
        tz = self.config.calendar['tz']
        opens = self.config.calendar['opens']
        closes = self.config.calendar['closes']
        business_days = self.config.calendar['business_days']
        weekends = self.config.calendar['weekends']
        holidays = self.config.calendar['holidays']
        trading_calendar = None
        
        if business_days:
            if not isabs(business_days) and not isfile(business_days):
                user_root = self.config.user_space['root']
                user_data_dir = self.config.user_space['data']
                business_days = join(user_root, user_data_dir, 
                                     business_days)
            
            if not isfile(business_days):
                msg = "business days file does not exists."
                raise InitializationError(msg=msg)
            
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
                user_root = self.config.user_space['root']
                user_data_dir = self.config.user_space['data']
                holidays = join(user_root, user_data_dir, holidays)
            
            if not isfile(holidays):
                msg = "holidays file does not exists."
                raise InitializationError(msg=msg)
            
            dts = pd.read_csv(holidays, parse_dates=True)
            dts = pd.to_datetime(dts.iloc[:,0].tolist())
            trading_calendar.add_holidays(dts)
            
        register_calendar(name,trading_calendar)
        
        self.trading_calendar = get_calendar(name)

    def create_broker(self, *args, **kwargs):
        '''
            Create the broker object based on name mapping to a 
            particular broker module under utils/brokers/.
        '''                    
        if self.mode == MODE.BACKTEST:
            name = self.config.backtester['backtester_name']
            start_date = self.config.backtester['start']
            end_date = self.config.backtester['end']
            frequency = self.config.backtester['backtest_frequency']
            initial_capital = self.config.backtester['initial_capital']
            
            register_broker(name,start_date=start_date, 
                            end_date=end_date, 
                            trading_calendar=self.trading_calendar,
                            initial_capital=initial_capital,
                            frequency=frequency)
        elif self.mode == MODE.LIVE:
            name = self.config.live_broker['broker_name']
            api_key = self.config.live_broker['api_key']
            api_secret = self.config.live_broker['api_secret']
            user_id = self.config.live_broker['broker_id']
            rate_limit = self.config.live_broker['rate_limit']
            rate_period = self.config.live_broker['rate_period']
            timeout = self.config.live_broker['login_reset_time']
            frequency = self.config.live_broker['live_frequency']
            
            request_token = kwargs.get('request_token',None)
            auth_token = kwargs.get('auth_token',None)
            
            if not request_token and not auth_token:
                # try to getch auth_token from env vars
                auth_token = self.env_vars.get(
                        "BLUESHIFT_BROKER_TOKEN",None)
                if not auth_token:
                    msg = "No authentication info given."
                    raise InitializationError(msg=msg)
            
            if auth_token:
                register_broker(name, api_key=api_key,
                                api_secret=api_secret,
                                user_id=user_id, rate_limit=rate_limit,
                                rate_period=rate_period,timeout=timeout,
                                trading_calendar=self.trading_calendar, 
                                frequency=frequency,
                                auth_token=auth_token)
            else:
                register_broker(name, api_key=api_key,
                                api_secret=api_secret,
                                user_id=user_id, rate_limit=rate_limit,
                                rate_period=rate_period,timeout=timeout,
                                trading_calendar=self.trading_calendar, 
                                frequency=frequency,
                                request_token=request_token)
        else:
            raise InitializationError(msg="Illegal mode supplied.")
            
        
        self.broker_tuple = get_broker(name)
        
        if self.mode == MODE.LIVE:
            broker_token = self.broker_tuple.auth.auth_token
            self.env_vars["BLUESHIFT_BROKER_TOKEN"] = broker_token


def run_algo(name, output, show_progress=False, publish=False, 
             *args, **kwargs):
    trading_environment = kwargs.pop("trading_environment", None)
    
    if not trading_environment:
        trading_environment = BlueShiftEnvironment()
        trading_environment.create_environment(*args, **kwargs)
    
    if not trading_environment:
        click.secho("failed to create a trading environment", fg="red")
        sys_exit(1)
        
    alert_manager = trading_environment.alert_manager
    broker = trading_environment.broker_tuple
    mode = trading_environment.mode
    algo_file = trading_environment.algo_file
    algo = TradingAlgorithm(name=name, broker=broker, algo=algo_file, 
                            mode=mode)
    
    broker_name = str(broker.broker._name)
    tz = broker.clock.trading_calendar.tz
    
    if mode == MODE.BACKTEST:
        '''
            For backtest, run the algo backtest generator, and save 
            the results if required.
        '''        
        length = len(broker.clock.session_nanos)
        click.secho(f"\nStarting backtest with {basename(algo_file)}", 
                                              fg="yellow")
        msg = f"broker:{broker_name}, timezone:{tz}, total sessions:{length}\n"
        click.echo(msg)
        perfs = algo.back_test_run(alert_manager, show_progress,
                                   publish)
        
        click.secho(f"backtest run complete", fg="green")
        
        if output:
            perfs.to_csv(output)
        
        return perfs
        
        
    elif mode == MODE.LIVE:
        '''
            For live run, there is no generator. We run the main 
            async event loop inside the Algorithm object itself.
            So all messaging has to be handled there. Here we just
            call the main function and leave it alone to complete.
        '''
        click.secho("\nstarting LIVE", fg="yellow")
        msg = "starting LIVE, algo:"+ basename(algo_file) +\
                " with broker:" + broker_name + ", timezone:" + tz + "\n"
        click.echo(msg)
        algo._live_run(alert_manager=alert_manager)
        
    else:
        '''
            Somehow we ended up with unknown mode.
        '''
        click.secho(f"illegal mode supplied.", fg="red")
        sys_exit(1)