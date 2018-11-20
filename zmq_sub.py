# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 08:45:17 2018

@author: prodi
"""
from blueshift.alerts.message_brokers import ZeroMQSubscriber
from blueshift.utils.ctx_mgr import MessageBrokerCtxManager
import zmq

subscriber = ZeroMQSubscriber('127.0.0.1',"5556",'myalgo', no_block=False)

with MessageBrokerCtxManager(subscriber, enabled=True) as sub:
    while True:
        try:
            msg = sub.recv()
            if msg == "EOM":
                break
            print(msg)
        except zmq.error.Again as e:
            continue

