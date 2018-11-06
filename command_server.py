# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 17:13:35 2018

@author: prodipta
"""

import asyncio
import websockets
import random

async def send_command(websocket, path):
    while True:
        try:
            cmd = input("type a command:")
            await websocket.send(cmd)
            await asyncio.sleep(random.random() * 5)
        except websockets.ConnectionClosed:
            continue
        
start_server = websockets.serve(send_command, '127.0.0.1', 60042)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()