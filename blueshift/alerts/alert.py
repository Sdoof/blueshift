# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 13:27:49 2018

@author: prodipta
"""
from os import close, getpid, execl
import sys
from sys import exit as sys_exit
from sys import executable as sys_executable
from psutil import Process

from blueshift.alerts.logging_utils import BlueShiftLogger
from blueshift.utils.exceptions import (ExceptionHandling,
                                        DataError,UserError,
                                        APIError,InternalError,
                                        GeneralException)
from blueshift.utils.decorators import singleton

@singleton
class BlueShiftAlertManager(object):
    '''
        Class to handle all blueshift alert handling. The alert 
        manager should be called in a try/except block, passing
        any necessary arguments. The manager, based on the user
        specified rules, will decide how to handle the exception,
        including re-starts if provisioned.
    '''
    
    ERROR_TYPES = [DataError,UserError,APIError,InternalError,
               GeneralException]

    ERROR_RULES_MAP = {"warn":ExceptionHandling.WARN,
                      "stop":ExceptionHandling.TERMINATE,
                      "re_start":ExceptionHandling.RECOVER,
                      "ignore":ExceptionHandling.IGNORE,
                      "log":ExceptionHandling.LOG}
    
    def __init__(self, config, *args, **kwargs):
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
        self.config = config
        self.logger = BlueShiftLogger(config, *args, **kwargs)
        self.error_rules = {}
        self.callbacks = []
        
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
                self.config.recovery['data_error'], None)
        self.error_rules[APIError] = self.ERROR_RULES_MAP.get(
                self.config.recovery['api_error'], None)
        self.error_rules[UserError] = self.ERROR_RULES_MAP.get(
                self.config.recovery['user_error'], None)
        self.error_rules[InternalError] = self.ERROR_RULES_MAP.get(
                self.config.recovery['internal_error'],None)
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
                
        handling = self.error_rules[error_type]
        handling = handling if handling is not None else e.handling
        
        if handling == ExceptionHandling.IGNORE:
            pass
        elif handling == ExceptionHandling.LOG:
            self.logger.info(str(e),module)
        elif handling == ExceptionHandling.WARN:
            self.logger.warning(str(e),module)
        elif handling == ExceptionHandling.TERMINATE:
            self.logger.error(str(e),module)
            self.graceful_exit(*args, **kwargs)
        elif handling == ExceptionHandling.RECOVER:
            self.logger.error(str(e),module)
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
        execl(python, python, *sys.argv)
        sys_exit(1)