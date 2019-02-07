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
Created on Mon Feb  4 16:59:34 2019

@author: prodipta
"""

from os.path import isabs, join, isfile, expanduser, basename, dirname
from os import environ as os_environ
from os import _exit as os_exit
from sys import exit as sys_exit
import pandas as pd
import uuid

from blueshift.configs.config import BlueShiftConfig, register_config
from blueshift.configs.defaults import (blueshift_source_path,
                                       get_config_calendar_details,
                                       blueshift_data_path,
                                       get_config_broker_details,
                                       get_config_env_vars)

from blueshift.alerts import (BlueShiftLogger, 
                              BlueShiftAlertManager,
                              register_logger,
                              register_alert_manager)


from blueshift.utils.types import MODE
from blueshift.controls import (get_broker, 
                           get_calendar,
                           register_calendar,
                           register_broker)

from blueshift.utils.exceptions import (InitializationError, 
                                        BlueShiftException)

from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.types import OnetoOne
from blueshift.utils.helpers import if_notebook, if_docker, print_msg
from blueshift.utils.types import Platform
from blueshift.configs.runtime import register_env


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
    
    def __init__(self, *args, **kwargs):
        self.name = None
        self.platform = None
        self.trading_calendar = None
        self.broker_tuple = None
        self.algo_file = None
        self.mode = None
        self.env_vars = {}
        self._initialized = False
        
        self._create(*args, **kwargs)
        
    def __str__(self):
        mode = self.RUN_MODE_MAP.teg(self.mode)
        return f"Blueshift Environment [name:{self.name}, mode:{mode}]"
    
    def __repr__(self):
        return self.__str__()
    
    def _create(self, *args, **kwargs):
        '''
            Function to create a trading environment with all objects
            necessary to run the algo.
        '''
        name = kwargs.pop("name", None)
        if name:
            self.name = name
        else:
            self.name = str(uuid.uuid4())

        if if_notebook():
            self.platform = Platform.NOTEBOOK
        elif if_docker():
            self.platform = Platform.CONTAINER
        else:
            self.platform = Platform.CONSOLE
        
        register_env(self)
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
            print_msg(str(e), _type="error", platform=self.platform)
            sys_exit(1)
            os_exit(1)
        
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
        env_vars = get_config_env_vars()
        for var in env_vars:
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
        if not "name" in kwargs:
            kwargs["name"] = self.name
        logger = BlueShiftLogger(*args, **kwargs)
        register_logger(logger)
    
    def create_alert_manager(self, *args, **kwargs):
        '''
            create and register the alert manager.
        '''
        if not "topic" in kwargs:
            kwargs["topic"] = self.name
        
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
            particular broker module under brokers.
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
        
        if self.env_vars["BLUESHIFT_BROKER_TOKEN"]:
            try:
                # try to set the auth token if possible.
                self.broker_tuple.auth.auth_token = \
                    self.env_vars["BLUESHIFT_BROKER_TOKEN"]
            except:
                # not a token auth model. Return silently.
                pass
            