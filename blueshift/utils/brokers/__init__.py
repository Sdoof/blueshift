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
        'back-test': 'backtest',
        'blueshift': 'backtest'
        }

global_broker_dispatch = BrokerDispatch({},
                                        _default_broker_factories,
                                        _default_broker_aliases)


get_broker = global_broker_dispatch.get_broker
register_broker = global_broker_dispatch.register_broker
deregister_broker = global_broker_dispatch.deregister_broker
register_broker_alias = global_broker_dispatch.register_alias
deregister_broker_alias = global_broker_dispatch.deregister_alias
                            

__all__ = [get_broker,
           register_broker,
           deregister_broker,
           register_broker_alias,
           deregister_broker_alias,
           Broker]