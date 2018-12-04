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
Created on Mon Nov 12 10:17:03 2018

@author: prodipta
"""

import json

from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.exceptions import (InitializationError, 
                                        ValidationError)

@singleton
@blueprint
class BlueShiftConfig(object):
    
    def __init__(self, config_file, *args, **kwargs):
        self._create(config_file, *args, **kwargs)
    
    def to_dict(self):
        '''
            A dict version for persistence as json.
        '''
        config_dict = {}
        for var in self.__dict__:
            config_dict[var] = self.var
            
        return config_dict
    
    def save_config(self, file_path):
        '''
            Write config to a file.
        '''
        try:
            with open(file_path, 'w') as config_file:
                json.dump(self.to_dict(), config_file)
        except FileNotFoundError:
            msg='missing config file {config_file}'
            raise ValidationError(msg=msg)
            
    def _create(self, config_file, *args, **kwargs):
        '''
            Read the supplied config file, or generate a default config,
            In case more named arguments are supplied as keywords, use
            them to replace the config params.
        '''
        if config_file:
            try:
                with open(config_file) as fp:
                    config = json.load(fp)
            except FileNotFoundError:
                msg='config file {config_file} not found'
                raise InitializationError(msg=msg)
        else:
            msg='missing config file {config_file}'
            raise InitializationError(msg=msg)
        
        calendar = kwargs.pop("calendar", None)
        if not calendar:
            calendar = config["defaults"]["calendar"]
        broker = kwargs.pop("broker", None)
        if not broker:
            broker = config["defaults"]["broker"]
        
        self.algo = config['algo']
        self.owner = config['owner']
        self.platform = config['platform']
        self.contact = config['contact']
        self.user_space = config['user_workspace']
        self.alerts = config['alerts']
        self.broker = config['brokers'][broker]
        self.calendar = config['calendars'][calendar]
        self.channels = config['channels']
        self.risk_management = config['risk_management']
        self.recovery = config['error_handling']
        self.env_vars = config['environment']
        
        for key in self.__dict__:
            self.arg_parse(key, *args, **kwargs)
    
    def arg_parse(self, var, *args, **kwargs):
        '''
            Over-write config parameters in case it is supplied. Assumes
            only one level of nesting. Also in case of repeating param
            names, all occurences will be replaced. Also convert any 
            list arguments to tuple.
        '''
        if not isinstance(self.__dict__[var], dict):
            self.__dict__[var] = self.list_to_tuple(
                    kwargs.pop(var, self.__dict__[var]))
        else:
            for key in self.__dict__[var]:
                self.__dict__[var][key] = self.list_to_tuple(
                        kwargs.pop(key, self.__dict__[var][key]))
    
    @staticmethod
    def list_to_tuple(val):
        '''
            To make calendar creation input compatible.
        '''
        if isinstance(val, list):
            return tuple(val)
        return val
    
    def __str__(self):
        return "Blueshift Config [name:{}]".format(self.algo)
    
    def __repr__(self):
        return self.__str__()
    
@blueprint
class BlueShiftConfigWrapper():
    '''
        A wrapper object for Blueshift Configuration object to make 
        access to it global.
    '''
    def __init__(self, config=None):
        self.instance = config
        
    def get_config(self):
        return self.instance
    
    def register_config(self, config):
        self.instance = config
        
global_config_wrapper = BlueShiftConfigWrapper()
register_config = global_config_wrapper.register_config
get_config = global_config_wrapper.get_config

