# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
from enum import Enum

class ExceptionHandling(Enum):
    IGNORE = 0  # print error and continue execution
    LOG = 1     # log error to notify user later, continue
    WARN = 2    # immedeate notification, continue
    RECOVER = 3 # immedeate notification, try to recover
    TERMINATE = 4   # immedeate notification, stop execution

class BlueShiftException(Exception):
    msg = None

    def __init__(self, *args, **kwargs):
        self.handling = kwargs.pop("handling",ExceptionHandling.IGNORE)
        self.kwargs = kwargs
        

    def message(self):
        return str(self)

    def __str__(self):
        msg = self.msg.format(**self.kwargs)
        return msg

    __repr__ = __str__
    
class SessionOutofRange(BlueShiftException):
    msg = "{dt} outside valid sessions range"
    
class IllegalOrderNoSymNoSID(BlueShiftException):
    msg = "could not create order: no symbol or SID specified"
    
class InsufficientFund(BlueShiftException):
    msg = "could not complete transaction: insufficient fund"
    handling = ExceptionHandling.WARN
    
class BrokerAPIError(BlueShiftException):
    msg = "Error received from Backtester: {msg}"
    handling = ExceptionHandling.LOG
    
class InitializationError(BlueShiftException):
    msg = "Error during initialization: {msg}"
    handling = ExceptionHandling.RECOVER 
    
class APIValidationError(BlueShiftException):
    msg = "{msg}"
    
class StateMachineError(BlueShiftException):
    msg = "Error in Algo attempted state change: {msg}"
    handling = ExceptionHandling.RECOVER
    
class ValidationError(BlueShiftException):
    msg = "Validation failed:{msg}"
    handling = ExceptionHandling.WARN
    
class BacktestUnexpectedExit(BlueShiftException):
    msg = "The backtest generator of {msg} exited unexpectedly"
    handling = ExceptionHandling.TERMINATE
    
class ClockError(BlueShiftException):
    msg = "Unexpected Error in Clock:{msg}"
    handling = ExceptionHandling.TERMINATE
    
class AuthenticationError(BlueShiftException):
    msg = "Authentication Error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class APIRateLimitCoolOff(BlueShiftException):
    msg = "Authentication Error: {msg}"
    handling = ExceptionHandling.WARN
    
class APIException(BlueShiftException):
    msg = "API Error: {msg}"
    handling = ExceptionHandling.WARN

