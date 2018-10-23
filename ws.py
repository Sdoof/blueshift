# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 16:48:46 2018

@author: prodipta
"""
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def client():
    session = aiohttp.ClientSession()
    ws = await session.ws_connect('wss://echo.websocket.org')
    
    random_msg = "some random msg"
    msg = await ws.send_str(random_msg)

    async for msg in ws:
        print('message received from server:', msg.data)
        print('type: {}'.format(msg.type))
        if msg.type in (aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR):
            break
        print("sleeping for 5 seconds")
        asyncio.sleep(5)
        msg = await ws.send_str(random_msg)
        


def main(coro):
    loop = asyncio.get_event_loop()
    #task = asyncio.gather(coro,return_exceptions=False)
    loop.run_until_complete(coro)
    

main(client())

#https://stackoverflow.com/questions/49858021/listen-to-multiple-socket-with-websockets-and-asyncio