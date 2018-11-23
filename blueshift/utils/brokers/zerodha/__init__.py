# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:36:06 2018

@author: prodipta
"""

from .kiteauth import KiteAuth
from .kiteassets import KiteAssetFinder
from .kitedata import KiteRestData
from .kitebroker import KiteBroker
from blueshift.utils.types import Broker
from blueshift.execution.clock import RealtimeClock

def make_broker_pack(name, *args, **kwargs):
    frequency = kwargs.get("frequency",1)
    auth = KiteAuth(name = name, *args, **kwargs)
    auth.login(*args, **kwargs)
    asset_finder = KiteAssetFinder(auth=auth, *args, **kwargs)
    data_portal = KiteRestData(name=name, auth=auth, *args, **kwargs)
    broker = KiteBroker(name=name, auth = auth, asset_finder=asset_finder)
    clock = RealtimeClock(auth._trading_calendar,frequency)
    
    return auth, asset_finder, data_portal, broker, clock

def Zerodha(*args, **kwargs):
    name = kwargs.get("name","zerodha")
    auth, asset_finder, data_portal, broker, clock =\
            make_broker_pack(name, *args, **kwargs)
    zerodha = Broker(auth, asset_finder, data_portal, broker, clock)
    
    return zerodha

__all__ = [KiteAuth,
           KiteAssetFinder,
           KiteRestData,
           KiteBroker,
           Zerodha,
           RealtimeClock]