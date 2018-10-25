# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 16:48:46 2018

@author: prodipta
"""
import asyncio
import websockets
            
async def echo():
    i = 1
    ws = await websockets.connect('wss://echo.websocket.org')
    while True:
        msg_s = yield
        await ws.send(msg_s)
        msg_r = await ws.recv()
        yield 2*msg_r
        i = i + 1
            

async def main():
    coro = echo()
    await coro.asend(None)
    i = 1
    while True:
        msg = f"msg {i}"
        print(f"main{i}: msg sent {msg}")
        res = await coro.asend(msg)
        print(f"main{i}: msg rcvd {res}")
        i = i + 1

        if i > 5:
            print("main: finished")
            await coro.aclose()
            break
        
        await asyncio.sleep(5)
        await coro.__anext__()
        
        
asyncio.get_event_loop().run_until_complete(main())