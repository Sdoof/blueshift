# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 17:18:02 2018

@author: prodipta
"""

import asyncio
import websockets

async def command_processor():
    ws = await websockets.connect('ws://127.0.0.1:60042')
    while True:
        try:
            command = await ws.recv()
            print(f"received command {command}")
            if command == "TERMINATE":
                print("shutting down")
                ws.close()
                break
        except KeyboardInterrupt:
            ws.close()
            break
            
asyncio.get_event_loop().run_until_complete(command_processor())
            