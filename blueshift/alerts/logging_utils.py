# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 14:12:07 2018

@author: prodipta
"""

import logging
import sys
import os
import pandas as pd

class BlueShiftLogHandlers(object):
    
    LOG_DEST = ['log', 'console', 'email', 'msg', 'websocket']
    
    def __init__(self, config, *args, **kwargs):
        self.log_root = config.user_space['root']
        self.log_dir = config.user_space['logs']
        
        name = kwargs.get("name","blueshift")
        timestamp = pd.Timestamp.now().normalize()
        logfile = name+"_"+str(timestamp)
        self.log_file = os.path.join(self.log_root, self.log_dir,
                                     logfile)
        
        self.handlers = []
        self.handlers['console'] = logging.StreamHandler(sys.stderr)
        self.handlers['log'] = logging.FileHandler(self.log_file)
        
        self.handlers['email'] = None
        self.handlers['msg'] = None
        self.handlers['websocket'] = None
        
        formatstr = logging.Formatter('%(asctime)s:%(name)s - %(levelname)s:%(message)s')
        
        for d in self.handlers:
            self.handlers[d].setFormatter(formatstr)