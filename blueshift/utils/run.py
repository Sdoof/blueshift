# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Tue Nov 13 09:00:35 2018

@author: prodipta

does the background object building and defines run_algo.

"""
from os.path import isabs, join, isfile, expanduser, basename, dirname
from os import environ as os_environ
from sys import exit as sys_exit
import pandas as pd
import click

from blueshift.configs import (BlueShiftConfig, register_config,
                               blueshift_source_path,
                               get_config_calendar_details,
                               blueshift_data_path,
                               get_config_broker_details,
                               get_config_env_vars,
                               blueshit_run_set_name)
from blueshift.alerts import (BlueShiftLogger, 
                              BlueShiftAlertManager,
                              register_logger,
                              register_alert_manager, 
                              get_alert_manager)
from blueshift.algorithm import TradingAlgorithm
from blueshift.utils.types import MODE
from blueshift.api import (get_broker, get_calendar,
                                     register_calendar,
                                     register_broker)
from blueshift.utils.exceptions import (InitializationError, 
                                        BlueShiftException)
from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.general_helpers import OnetoOne


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
        self.trading_calendar = None
        self.broker_tuple = None
        self.algo_file = None
        self.mode = None
        self.env_vars = {}
        self._initialized = False
        
    def __str__(self):
        mode = self.RUN_MODE_MAP.teg(self.mode)
        return f"Blueshift Environment [mode:{mode}]"
    
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
            self.create_logger(*args, **kwargs)
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
        
        
        config = BlueShiftConfig(config_file, *args, **kwargs)
        register_config(config)
        
        self.env_vars["BLUESHIFT_API_KEY"] = \
                    get_config_env_vars("BLUESHIFT_API_KEY")
        self.env_vars["BLUESHIFT_CONFIG_FILE"] = config_file
    
    def extract_env_vars(self, *args, **kwargs):
        '''
            First try to extract the environment variables from the
            list in config. Then over-write if any supplied in the
            kwwargs.
        '''
        for var in get_config_env_vars():
            self.env_vars[var] = os_environ.get(var, None)
        for var in self.env_vars:
            self.env_vars[var] = kwargs.pop(var, self.env_vars[var])
            
    def save_env_vars(self):
        for var in self.env_vars:
            value = self.env_vars[var]
            if value:
                os_environ[var] = value
    
    def create_logger(self, *args, **kwargs):
        '''
            create and register the alert manager.
        '''
        logger = BlueShiftLogger(*args, **kwargs)
        register_logger(logger)
    
    def create_alert_manager(self, *args, **kwargs):
        '''
            create and register the alert manager.
        '''
        alert_manager = BlueShiftAlertManager()
        register_alert_manager(alert_manager)
    
    def get_algo_file(self, algo_file):
        '''
            Search the current directory, else go the user config
            directory (code) and search.
        '''
        if not algo_file:
            raise InitializationError(msg="missing algo file.")
        if not isabs(algo_file) and not isfile(algo_file):
            code_dir = blueshift_source_path()
            user_root = dirname(code_dir)
            user_code_dir = basename(code_dir)
            algo_file = join(user_root, user_code_dir, algo_file)
            
        if not isfile(algo_file):
            raise InitializationError(msg=f"algo file {algo_file} does not exists.")
        
        # TODO: add local import replacement to support multi-file
        # projects. No mods required for PYTHONPATH.
        self.algo_file = algo_file

    def create_calendar(self):
        '''
            Create the calendar based on config data. Then register
            the calendar and return the object. This calendar can be
            then fetched using the get_calendar API from user code.
        '''
        cal_dict = get_config_calendar_details()
        name = cal_dict['cal_name']
        tz = cal_dict['tz']
        opens = cal_dict['opens']
        closes = cal_dict['closes']
        business_days = cal_dict['business_days']
        weekends = cal_dict['weekends']
        holidays = cal_dict['holidays']
        
        if business_days:
            if not isabs(business_days) and not isfile(business_days):
                data_dir = blueshift_data_path()
                user_root = dirname(data_dir)
                user_data_dir = basename(data_dir)
                business_days = join(user_root, user_data_dir, 
                                     business_days)
            
            if not isfile(business_days):
                msg = f"business days file {business_days} does not exists."
                raise InitializationError(msg=msg)
            
            business_days = pd.read_csv(business_days, parse_dates=True)
            business_days = pd.to_datetime(business_days.iloc[:,0].tolist())
        
            
        register_calendar(name,tz=tz, bizdays=business_days, opens=opens, 
                          closes=closes, weekends=weekends)
        cal = get_calendar(name)
        
        if holidays:
            if not isabs(holidays) and not isfile(holidays):
                data_dir = blueshift_data_path()
                user_root = dirname(data_dir)
                user_data_dir = basename(data_dir)
                holidays = join(user_root, user_data_dir, holidays)
            
            if not isfile(holidays):
                msg = f"holidays file {holidays} does not exists."
                raise InitializationError(msg=msg)
            
            dts = pd.read_csv(holidays, parse_dates=True)
            dts = pd.to_datetime(dts.iloc[:,0].tolist())
            cal.add_holidays(dts)
        
        self.trading_calendar = cal
        
    def create_broker(self, *args, **kwargs):
        '''
            Create the broker object based on name mapping to a 
            particular broker module under utils/brokers/.
        '''                    
        brkr_dict = get_config_broker_details()
        factory_name = brkr_dict.pop("factory")
        name = brkr_dict["name"]
        
        brkr_dict["trading_calendar"] = self.trading_calendar
        brkr_dict["start_date"] = kwargs.pop("start_date", None)
        brkr_dict["end_date"] = kwargs.pop("end_date", None)
        brkr_dict["initial_capital"] = kwargs.pop("initial_capital", None)
        
        register_broker(name, factory_name, **brkr_dict)
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
        
    blueshit_run_set_name(name)
    alert_manager = get_alert_manager()
    broker = trading_environment.broker_tuple
    mode = trading_environment.mode
    algo_file = trading_environment.algo_file
    algo = TradingAlgorithm(name=name, broker=broker, algo=algo_file, 
                            mode=mode)
    
    broker_name = str(broker.broker._name)
    tz = broker.clock.trading_calendar.tz
    
    if mode == MODE.BACKTEST:
        '''
            print initial messages and run the algo object backtest.
        '''        
        length = len(broker.clock.session_nanos)
        click.secho(f"\nStarting backtest with {basename(algo_file)}", 
                                              fg="yellow")
        msg = f"broker:{broker_name}, timezone:{tz}, total sessions:{length}\n"
        click.echo(msg)
        perfs = algo.back_test_run(alert_manager, publish,
                                   show_progress)
        
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
        algo.live_run(alert_manager=alert_manager,
                      publish_packets=publish)
        
    else:
        '''
            Somehow we ended up with unknown mode.
        '''
        click.secho(f"illegal mode supplied.", fg="red")
        sys_exit(1)