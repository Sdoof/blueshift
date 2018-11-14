# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 14:12:07 2018

@author: prodipta
"""

import logging
from sys import stderr as sys_stderr
from os import path as os_path
import pandas as pd

from blueshift.utils.decorators import singleton, blueprint

@blueprint
class BlueShiftLogHandlers(object):
    
    LOG_DEST = ['log', 'console', 'email', 'msg', 'websocket']
    
    def __init__(self, config, *args, **kwargs):
        self.log_root = config.user_space['root']
        self.log_dir = config.user_space['logs']
        
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
        
        formatstr = 'BlueShift Alert[%(asctime)s] '\
                        '%(levelname)s %(message)s'
        formatstr = logging.Formatter(formatstr)
        
        for key in self.handlers:
            if self.handlers[key]:
                self.handlers[key].setFormatter(formatstr)
            
        # set up alert levels according to the rules in config
        alert_rules = config.alerts
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
    
    def __init__(self, config, *args, **kwargs):
        self.logger = logging.getLogger("blueshift")
        self.handler_obj = BlueShiftLogHandlers(config, 
                                                *args, **kwargs)
        self.handlers = self.handler_obj.handlers
        
        for tag, handler in self.handlers.items():
            if handler:
                self.logger.addHandler(handler)
                
        self.logger.setLevel(logging.INFO)
                
    def __str__(self):
        return "Blueshift Logger"
    
    def __repr__(self):
        return self.__str__()
    
    def info(self, msg, module):
        msg="in "+module+":"+msg
        self.logger.info(msg)
        
    def warning(self, msg, module):
        msg="in "+module+":"+msg
        self.logger.warning(msg)
        
    def error(self, msg, module):
        msg="in "+module+":"+msg
        self.logger.error(msg)
        
    def daily_log(self):
        pass