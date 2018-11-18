# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:17:03 2018

@author: prodipta
"""

import json
from blueshift.configs import _default_config
from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.exceptions import InitializationError

@singleton
@blueprint
class BlueShiftConfig(object):
    
    def __init__(self, config_file=None, *args, **kwargs):
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
                msg='missing config file {config_file}'
                raise InitializationError(msg=msg)
        else:
            config = _default_config
            
        self.algo = config['algo']
        self.owner = config['owner']
        self.platform = config['platform']
        self.contact = config['contact']
        self.user_space = config['user_workspace']
        self.alerts = config['alerts']
        self.backtester = config['backtester']
        self.live_broker = config['live_broker']
        self.calendar = config['calendar']
        self.command_channel = config['command_channel']
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
                    kwargs.get(var, self.__dict__[var]))
        else:
            for key in self.__dict__[var]:
                self.__dict__[var][key] = self.list_to_tuple(
                        kwargs.get(key, self.__dict__[var][key]))
    
    @staticmethod
    def list_to_tuple(val):
        if isinstance(val, list):
            return tuple(val)
        return val
    
    def __str__(self):
        return "Blueshift Config:{}".format(self.algo)
    
    def __repr__(self):
        return self.__str__()