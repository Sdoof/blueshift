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
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""
from enum import Enum

class ExceptionHandling(Enum):
    IGNORE = 0      # continue execution silently
    LOG = 1         # continue execution, log message
    WARN = 2        # continue execution, log warning
    RECOVER = 3     # log error, save context, re-start with context
    TERMINATE = 4   # log error, save context, re-start fresh

class BlueShiftException(Exception):
    msg = "{msg}"
    handling = ExceptionHandling.TERMINATE

    def __init__(self, *args, **kwargs):
        handling = kwargs.pop("handling", None)
        if handling:
            self.handling = handling
        self.kwargs = kwargs
        

    def message(self):
        return str(self)

    def __str__(self):
        msg = self.msg.format(**self.kwargs)
        return msg

    __repr__ = __str__
    
class ControlException(BlueShiftException):
    msg = "User error: {msg}"
    handling = ExceptionHandling.TERMINATE

class DataError(BlueShiftException):
    msg = "User error: {msg}"
    handling = ExceptionHandling.WARN

class UserError(BlueShiftException):
    msg = "User error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class APIError(BlueShiftException):
    msg = "API error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class InternalError(BlueShiftException):
    msg = "Internal error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class GeneralException(BlueShiftException):
    msg = "Unknown error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
# Control Exception
class CommandShutdownException(ControlException):
    '''
        Raised when a shutdown command received.
    '''
    msg = "Shutdown command: {msg}"
    handling = ExceptionHandling.TERMINATE

# Data Errors    
class MissingDataError(DataError):
    '''
        Raised if missing or stale data.
    '''
    msg = "Missing data error: {msg}"
    handling = ExceptionHandling.TERMINATE

# API Errors
class AuthenticationError(APIError):
    '''
        Raised during exception in login or log-out flows.
    '''
    msg = "API authentication Error: {msg}"
    handling = ExceptionHandling.TERMINATE

class APIRateLimitCoolOff(APIError):
    '''
        Raised when API rate limit is breached.
    '''
    msg = "API rate limit exceeded: {msg}"
    handling = ExceptionHandling.WARN

class APIException(APIError):
    '''
        Raised when we have an API exception, either from the broker
        back-end or some HTTP error. Such errors are not recoverable.
    '''
    msg = "Unrecoverable API Error: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class BrokerAPIError(APIError):
    '''
        Raised when we have an API exception, either from the broker
        back-end or some HTTP error. Such errors may be recoverable.
    '''
    msg = "Error received from API: {msg}"
    handling = ExceptionHandling.WARN
    

# User Errors
class SessionOutofRange(UserError):
    '''
        User date input is out of range of the calendar.
    '''
    msg = "Session out of range: {dt} outside valid sessions range"
    handling = ExceptionHandling.WARN
    
class InsufficientFund(UserError):
    '''
        Not enough fund in user trading account.
    '''
    msg = "Insufficient fund: could not complete transaction"
    handling = ExceptionHandling.WARN
    
class InitializationError(UserError):
    '''
        Initialization of objects failed.
    '''
    msg = "Error during initialization: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class ValidationError(UserError):
    msg = "Validation failed:{msg}" 
    handling = ExceptionHandling.TERMINATE
    
class SymbolNotFound(UserError):
    '''
        Illegal symbols
    '''
    msg = "Symbol not found {msg}"
    handling = ExceptionHandling.LOG
    
class UnsupportedFrequency(UserError):
    '''
        Wrong or unsupported frequency is requested in data fetch.
    '''
    msg = "Frequency not supported {msg}"
    handling = ExceptionHandling.TERMINATE
    
class NotValidBroker(UserError):
    '''
        Not a valid broker, broker dispatch failed.
    '''
    msg = "name supplied is not a valid registered broker"
    handling = ExceptionHandling.TERMINATE
    
class NotValidCalendar(UserError):
    '''
        Not a valid broker, broker dispatch failed.
    '''
    msg = "name supplied is not a valid registered calendar"
    handling = ExceptionHandling.TERMINATE
    
# Internal Errors
class StateMachineError(InternalError):
    '''
        Illegal state transition attempted in a state machine.
    '''
    msg = "Error in attempted state change: {msg}"
    handling = ExceptionHandling.TERMINATE
    
class BacktestUnexpectedExit(InternalError):
    '''
        Unexpected generator exit from the backtest.
    '''
    msg = "The backtest generator of {msg} exited unexpectedly"
    handling = ExceptionHandling.TERMINATE
    
class ClockError(InternalError):
    '''
        Unexpected termination of clock.
    '''
    msg = "Unexpected Error in Clock:{msg}"
    handling = ExceptionHandling.TERMINATE
    
class AlertManagerError(InternalError):
    '''
        Unexpected error about alert manager.
    '''
    msg = "Unexpected Error in alert manager:{msg}"
    handling = ExceptionHandling.TERMINATE

class ConfigurationError(InternalError):
    '''
        Unexpected error about config object.
    '''
    msg = "Unexpected Error in config:{msg}"
    handling = ExceptionHandling.TERMINATE
    
class BlueShiftPathException(InternalError):
    '''
        Unexpected error about path handling.
    '''
    msg = "Unexpected Error in Blueshift:{msg}"
    handling = ExceptionHandling.TERMINATE
