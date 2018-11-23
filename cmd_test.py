# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 11:04:03 2018

@author: prodipta
"""
import time
from blueshift.alerts.message_brokers import ZeroMQCmdPairClient
from blueshift.utils.ctx_mgr import MessageBrokerCtxManager


client = ZeroMQCmdPairClient("127.0.0.1",5557)

with MessageBrokerCtxManager(client, enabled=True) as commander:
    while True:
        commander.send_command()
        time.sleep(2)
    

    