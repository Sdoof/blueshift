# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 17:14:42 2018

@author: prodipta
"""

class BlueShiftException(Exception):
    msg = None

    def __init__(self, **kwargs):
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
    
class BackTestAPIError(BlueShiftException):
    msg = "Error received from Backtester: {msg}"