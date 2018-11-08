# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 17:18:02 2018

@author: prodipta
"""

import asyncio
import websockets
import random

async def command_processor(loop):
    timeout = 1
    ws = await websockets.connect('ws://127.0.0.1:60042')
    while True:
        try:
            #command = await ws.recv()
            command = await asyncio.wait_for(ws.recv(), timeout)
            print(f"received command {command}")
            if command == "TERMINATE":
                print("shutting down")
                ws.close()
                break
            await asyncio.sleep(random.random() * 5)
        except KeyboardInterrupt:
            print("keyboard intrrupt, exiting...")
            ws.close()
            break
        except asyncio.futures.TimeoutError:
            print("timeout, continue...")
            continue
            
loop = asyncio.get_event_loop()
loop.run_until_complete(command_processor(loop))
            