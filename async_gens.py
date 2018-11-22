# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 16:50:02 2018

@author: prodipta
"""

import asyncio
import pandas as pd
import random
from collections import namedtuple

from blueshift.execution.clock import ClockQueue

NANO = 1000000000

queue = ClockQueue()
Command = namedtuple("Command",("cmd","args","kwargs"))

class DummyAlgo():
    
    def __init__(self, clock_tick=1, processing_time=1):
        self.clock_tick = clock_tick
        self.processing_time = processing_time

    async def tick(self):
        while True:
            t = pd.Timestamp.now()
            ts = pd.Timestamp(int(t.value/NANO)*NANO)
            bar = random.randint(1,9)
            await queue.put((ts, bar))
            await asyncio.sleep(self.clock_tick)

    async def process_tick(self):
        loop_count = 0
        while True:
            cmd = yield
            self.process_command(cmd)
            ts, bar = await queue.get_last()
            await asyncio.sleep(self.processing_time)
            yield str(ts)+":"+str(bar)+":"+str(loop_count)
            loop_count += 1
        
    async def run_generator(self):
        g = self.process_tick()
        loop_count = 0
        cmd = Command("some_func",[1,2],{'x':33, 'y':44})
        async for msg in g:
            ret = await g.asend(cmd)
            print(f"results received {ret}, msg:{msg}")
            loop_count += 1
        
    def run_algo(self):
        clock_coro = self.tick()
        algo_coro = self.run_generator()
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(algo_coro,clock_coro)
        try:
            loop.run_until_complete(tasks)
        except BaseException as e:
            print(f"exception {str(e)}")
            tasks.cancel()
        finally:
            loop.close()
            
    def some_func(self, a, b, x=5, y=10):
        return f"called somefunc, {a}, {b}, {x}, {y}"
        
    def process_command(self, cmd):
        fn = getattr(self, cmd.cmd, None)
        if fn:
            print(fn(*cmd.args, **cmd.kwargs))
        else:
            print(str(cmd))
    
algo = DummyAlgo(1,1)
algo.run_algo()