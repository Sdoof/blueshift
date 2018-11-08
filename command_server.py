# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 17:13:35 2018

@author: prodipta
"""

import asyncio
import websockets
import random

async def send_command(websocket, path):
    print(websocket)
    print(path)
    while True:
        try:
            cmd = input("type a command:")
            await websocket.send(cmd)
            await asyncio.sleep(random.random() * 5)
            if cmd=="TERMINATE":
                print("terminate, exiting...")
                loop.stop()
                pending = asyncio.Task.all_tasks()
                loop.run_until_complete(asyncio.gather(*pending))
                
                break
        except websockets.ConnectionClosed:
            print("client closed connection, exiting...")
#            for task in asyncio.Task.all_tasks():
#                    task.cancel()
            loop.stop()
            break
            
        
start_server = websockets.serve(send_command, '127.0.0.1', 60042)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
loop.close()
