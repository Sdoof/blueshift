# -*- coding: utf-8 -*-
"""
Created on Fri Oct 26 10:42:50 2018

@author: prodipta
"""

from blueshift.utils.brokers.zerodha import (KiteAuth, 
                                             KiteRestData,
                                             KiteAssetFinder)

from blueshift.utils.exceptions import APIRateLimitCoolOff

kite_auth = KiteAuth(config='kite_config.json',tz='Asia/Calcutta',
                     timeout=(8,45))
try:
    kite_auth.login(auth_token="LSZmMqieDT4aMKlmvN7Fob645w6gy0O5")
except Exception as e:
    print(e)

kite_asset_finder = KiteAssetFinder(auth=kite_auth)

kite_data = KiteRestData(auth=kite_auth)
            

for i in range(10):
    try:
        kite_data.current(1,2)
        print(i)
    except APIRateLimitCoolOff:
        print(f"rate limit exeeded: sleeping now for {kite_data._rate_period}s")
        kite_data.cool_off()
        
