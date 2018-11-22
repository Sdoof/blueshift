# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 16:50:02 2018

@author: prodipta
"""

import asyncio
import pandas as pd
import random

from blueshift.execution.clock import ClockQueue

NANO = 1000000000

queue = ClockQueue()

async def tick():
    while True:
        t = pd.Timestamp.now()
        ts = pd.Timestamp(int(t.value/NANO)*NANO)
        bar = random.randint(1,9)
        await queue.put((ts, bar))
        await asyncio.sleep(2)

async def process_tick():
    while True:
        cmd = yield
        print(f"command received {cmd}")
        ts, bar = await queue.get_last()
        await asyncio.sleep(3)
        yield str(ts)+":"+str(bar)
        
async def run_algo():
    g = process_tick()
    async for msg in g:
        ret = await g.asend("wow")        
        print(f"results received {ret}")
        
def main():
    clock_coro = tick()
    algo_coro = run_algo()
    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(algo_coro,clock_coro)
    try:
        loop.run_until_complete(tasks)
    except BaseException as e:
        print(f"exception {str(e)}")
        tasks.cancel()
    finally:
        loop.close()
    
main()