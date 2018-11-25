# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 17:59:56 2018

@author: prodipta
"""

from blueshift.utils.exceptions import AlertManagerError
from blueshift.utils.decorators import blueprint
from .alert import BlueShiftAlertManager

@blueprint
class AlertManagerWrapper(object):
    
    def __init__(self, alert_manager=None):
        self.instance = alert_manager
        
    def get_logger(self):
        if not self.instance:
            raise AlertManagerError(msg='missing alert manager')
        
        return self.instance.logger
    
    def get_alert_manager(self):
        if not self.instance:
            raise AlertManagerError(msg='missing alert manager')
        
        return self.instance
    
    def register_alert_manager(self, alert_manager):
        self.instance = alert_manager
        
global_alert_manager_wrapper = AlertManagerWrapper()
register_alert_manager = global_alert_manager_wrapper.\
                                            register_alert_manager
                                            
get_alert_manager = global_alert_manager_wrapper.\
                                            get_alert_manager

get_logger = global_alert_manager_wrapper.get_logger

__all__ = [register_alert_manager,
           get_alert_manager,
           get_logger,
           BlueShiftAlertManager]