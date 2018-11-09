# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 16:36:33 2018

@author: prodipta
"""

from blueshift.utils.brokers.backtest import BackTest
from blueshift.utils.brokers.zerodha import Zerodha
from blueshift.utils.brokers.core import BrokerDispatch, Broker

_default_broker_factories = {
        'zerodha': Zerodha,
        'backtest': BackTest
        }

_default_broker_aliases = {
        'kite': 'zerodha',
        'bt': 'backtest',
        'back-test': 'backtest'
        }

global_broker_dispatch = BrokerDispatch({},
                                        _default_broker_factories,
                                        _default_broker_aliases)


get_broker = global_broker_dispatch.get_broker
register_broker = global_broker_dispatch.register_broker
unregister_broker = global_broker_dispatch.unregister_broker
                            

__all__ = [get_broker,
           register_broker,
           unregister_broker,
           Broker]