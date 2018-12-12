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
Created on Mon Nov 12 14:12:07 2018

@author: prodipta
"""

import logging
from sys import stderr as sys_stderr
from os import path as os_path
import pandas as pd

from blueshift.utils.decorators import singleton, blueprint
from blueshift.utils.types import MODE
from blueshift.configs import (blueshift_log_path, 
                               get_config_alerts, get_config_tz)

@blueprint
class BlueShiftLogHandlers(object):
    
    LOG_DEST = ['log', 'console', 'email', 'msg', 'websocket']
    
    def __init__(self, *args, **kwargs):
        log_path = blueshift_log_path()
        self.log_root = os_path.dirname(log_path)
        self.log_dir = os_path.basename(log_path)
        
        name = kwargs.get("name","blueshift")
        timestamp = pd.Timestamp.now().normalize()
        logfile = (name+"_"+str(timestamp)+".log").strip().\
                        replace(' ','_').replace(':','-')
        self.log_file = os_path.join(self.log_root, self.log_dir,
                                     logfile)
        
        self.handlers = {}
        self.handlers['console'] = logging.StreamHandler(sys_stderr)
        self.handlers['log'] = logging.FileHandler(self.log_file)
        self.handlers['email'] = None
        self.handlers['msg'] = None
        self.handlers['websocket'] = None
        
        formatstr = 'BlueShift Alert[%(myasctime)s] '\
                        '%(levelname)s %(message)s'
        formatstr = logging.Formatter(formatstr)
        
        for key in self.handlers:
            if self.handlers[key]:
                self.handlers[key].setFormatter(formatstr)
            
        # set up alert levels according to the rules in config
        alert_rules = get_config_alerts()
        
        # set level for errors
        for dest in alert_rules['error']:
            if self.handlers[dest]:
                self.handlers[dest].setLevel(logging.ERROR)
        # set level for warning
        for dest in alert_rules['warning']:
            if self.handlers[dest]:
                self.handlers[dest].setLevel(logging.WARNING)
        # info handler setting
        info_set = set([*alert_rules['platform_msg'],
                    *alert_rules['log']])
        for dest in info_set:
            if self.handlers[dest]:
                self.handlers[dest].setLevel(logging.INFO)
                
    def __str__(self):
        return "Blueshift Log Handler"
    
    def __repr__(self):
        return self.__str__()
        
@singleton
@blueprint
class BlueShiftLogger(object):
    
    def __init__(self, *args, **kwargs):
        self._create(*args, **kwargs)
                
    def _create(self, *args, **kwargs):
        self.logger = logging.getLogger("blueshift")
        
        self.handler_obj = BlueShiftLogHandlers(*args, **kwargs)
        self.handlers = self.handler_obj.handlers
        
        for tag, handler in self.handlers.items():
            if handler:
                self.logger.addHandler(handler)
                
        self.logger.setLevel(logging.INFO)
        
        tz = kwargs.get('tz', None)
        if tz:
            self.tz = tz
        else:
            self.tz = get_config_tz()
    
    def __str__(self):
        return "Blueshift Logger"
    
    def __repr__(self):
        return self.__str__()
    
    def info(self, msg, module=None, *args, **kwargs):
        msg="in "+module+":"+msg
        
        mode = kwargs.pop('mode', None)
        if mode == MODE.BACKTEST:
            asctime = str(kwargs.pop('timestamp'))
        else:
            asctime = str(pd.Timestamp.now(tz=self.tz))
            
        self.logger.info(msg, extra={'myasctime':asctime})
        
    def warning(self, msg, module=None, *args, **kwargs):
        msg="in "+module+":"+msg
        
        mode = kwargs.pop('mode', None)
        if mode == MODE.BACKTEST:
            asctime = kwargs.pop('timestamp')
        else:
            asctime = str(pd.Timestamp.now(tz=self.tz))
            
        self.logger.warn(msg, extra={'myasctime':asctime})
        
    def warn(self, msg, module=None, *args, **kwargs):
        self.warning(msg, module, *args, **kwargs)
        
    def error(self, msg, module=None, *args, **kwargs):
        msg="in "+module+":"+msg
        
        mode = kwargs.pop('mode', None)
        if mode == MODE.BACKTEST:
            asctime = kwargs.pop('timestamp')
        else:
            asctime = str(pd.Timestamp.now(tz=self.tz))
            
        self.logger.error(msg, extra={'myasctime':asctime})
        
    def daily_log(self):
        pass
    
@blueprint
class BlueShiftLoggerWrapper():
    '''
        A wrapper object for Blueshift Configuration object to make 
        access to it global.
    '''
    def __init__(self, logger=None):
        self.instance = logger
        
    def get_logger(self):
        return self.instance
    
    def register_logger(self, logger):
        self.instance = logger
        
global_logger_wrapper = BlueShiftLoggerWrapper()
register_logger = global_logger_wrapper.register_logger
get_logger = global_logger_wrapper.get_logger
    