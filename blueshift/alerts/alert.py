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
Created on Tue Nov 13 13:27:49 2018

@author: prodipta
"""
from os import close, getpid, execl
from sys import argv as sys_argv
from sys import exit as sys_exit
from sys import executable as sys_executable
from psutil import Process

from blueshift.alerts.logging_utils import BlueShiftLogger, get_logger
from blueshift.utils.exceptions import (ExceptionHandling,
                                        DataError,UserError,
                                        APIError,InternalError,
                                        ControlException,
                                        GeneralException)
from blueshift.utils.decorators import singleton, blueprint
from blueshift.alerts.message_brokers import (ZeroMQPublisher,
                                              ZeroMQCmdPairServer)
from blueshift.configs import (get_config_recovery, get_config_name,
                               get_config_channel)


@singleton
@blueprint
class BlueShiftAlertManager(object):
    '''
        Class to handle all blueshift alert handling. The alert 
        manager should be called in a try/except block, passing
        any necessary arguments. The manager, based on the user
        specified rules, will decide how to handle the exception,
        including re-starts if provisioned. It also initiates the 
        pub-sub for performance packets as well as external command
        channel to control a live algorithm.
    '''
    
    ERROR_TYPES = [DataError,UserError,APIError,InternalError,
               ControlException, GeneralException]

    ERROR_RULES_MAP = {"warn":ExceptionHandling.WARN,
                      "stop":ExceptionHandling.TERMINATE,
                      "re_start":ExceptionHandling.RECOVER,
                      "ignore":ExceptionHandling.IGNORE,
                      "log":ExceptionHandling.LOG}
    
    def __init__(self, *args, **kwargs):
        '''
            Set up the error rules and logger. The logger does the
            message dispatch. The error rules decide the error
            response. The callback list is available for any object
            to register a callback with alert manager. All such 
            callbacks will be called (in order of registration) once
            the shutdown process is initiated. This is a way to 
            enable any object a method to persist itself, for 
            example.
        '''
        self._create(*args, **kwargs)
        
    def _create(self, *args, **kwargs):
        logger = get_logger()
        if logger:
            self.logger = logger
        else:
            self.logger = BlueShiftLogger(*args, **kwargs)
        
        self.error_rules = {}
        self.callbacks = []
        self.publisher = None
        self.cmd_listener = None
        
        self.set_error_handling()
        
        topic = kwargs.get("topic",get_config_name())
        self.set_up_publisher(topic)
        self.set_up_cmd_listener()
    
    def __str__(self):
        return "Blueshift Alert Manager"
    
    def __repr__(self):
        return self.__str__()
    
    def register_callbacks(self, func):
        '''
            register a callback
        '''
        self.callbacks.append(func)
        
    def set_error_handling(self):
        self.error_rules[DataError] = self.ERROR_RULES_MAP.get(
                get_config_recovery('data_error'), None)
        self.error_rules[APIError] = self.ERROR_RULES_MAP.get(
                get_config_recovery('api_error'), None)
        self.error_rules[UserError] = self.ERROR_RULES_MAP.get(
                get_config_recovery('user_error'), None)
        self.error_rules[InternalError] = self.ERROR_RULES_MAP.get(
                get_config_recovery('internal_error'),None)
        self.error_rules[GeneralException] = ExceptionHandling.\
                                                        TERMINATE
    
    @staticmethod
    def classify_errors(obj, obj_types):
        for obj_type in obj_types:
            if isinstance(obj, obj_type):
                return obj_type
        return None
            
    def handle_error(self, e, module, *args, **kwargs):
        error_type = self.classify_errors(e, self.ERROR_TYPES)
        
        if not error_type:
            self.logger.error(str(e),module)
            self.graceful_exit(*args, **kwargs)
                
        handling = self.error_rules.get(error_type, None)
        handling = handling if handling is not None else e.handling
        
        if handling == ExceptionHandling.IGNORE:
            pass
        elif handling == ExceptionHandling.LOG:
            self.logger.info(str(e),module, *args, **kwargs)
        elif handling == ExceptionHandling.WARN:
            self.logger.warning(str(e),module, *args, **kwargs)
        elif handling == ExceptionHandling.TERMINATE:
            self.logger.error(str(e),module, *args, **kwargs)
            self.graceful_exit(*args, **kwargs)
        elif handling == ExceptionHandling.RECOVER:
            self.logger.error(str(e),module, *args, **kwargs)
            self.restart(*args, **kwargs)
        else:
            self.graceful_exit(*args, **kwargs)

    def graceful_exit(self, *args, **kwargs):
        shutdown_msg = 'cannot recover from error, shutting down...'
        self.logger.error(shutdown_msg,'BlueShift')
        self.run_callbacks()
        sys_exit(1)
    
    def run_callbacks(self, *args, **kwargs):
        for callback in self.callbacks:
            try:
                callback(*args, **kwargs)
            except:
                continue
            
    def restart(self, *args, **kwargs):
        shutdown_msg = 'restart failed, shutting down...'
        try:
            p = Process(getpid())
            for handler in p.get_open_files() + p.connections():
                close(handler.fd)
        except Exception as e:
            self.logger.error(shutdown_msg,'BlueShift')
            self.graceful_exit(*args, **kwargs)

        python = sys_executable
        execl(python, python, *sys_argv)
        sys_exit(1)
        
    def set_up_publisher(self, topic):
        addr, port = get_config_channel('msg_addr').split(':')
        self.publisher = ZeroMQPublisher(addr, port, topic)
        
    def set_up_cmd_listener(self):
        addr, port = get_config_channel('cmd_addr').split(':')
        self.cmd_listener = ZeroMQCmdPairServer(addr, port)
        
@blueprint
class AlertManagerWrapper(object):
    '''
        A wrapper class for alert manager to make access global.
    '''
    
    def __init__(self, alert_manager=None):
        self.instance = alert_manager
    
    def get_alert_manager(self):        
        return self.instance
    
    def register_alert_manager(self, alert_manager):
        self.instance = alert_manager
        
global_alert_manager_wrapper = AlertManagerWrapper()
register_alert_manager = global_alert_manager_wrapper.\
                                            register_alert_manager
                                            
get_alert_manager = global_alert_manager_wrapper.\
                                            get_alert_manager