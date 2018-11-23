# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 16:50:02 2018

@author: prodipta
"""

import asyncio
import pandas as pd
import random

from blueshift.execution.clock import ClockQueue
from blueshift.alerts.message_brokers import ZeroMQCmdPairServer
from blueshift.utils.ctx_mgr import MessageBrokerCtxManager

NANO = 1000000000

queue = ClockQueue()

class DummyAlgo():
    
    def __init__(self, clock_tick=1, processing_time=1):
        self.clock_tick = clock_tick
        self.processing_time = processing_time
        self.c = ZeroMQCmdPairServer("127.0.0.1",5557)

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
            if cmd:
                self.process_command(cmd)
            ts, bar = await queue.get_last()
            await asyncio.sleep(self.processing_time)
            yield str(ts)+": bar "+str(bar)+": loop "+str(loop_count)
            loop_count += 1
        
    async def run_generator(self):
        g = self.process_tick()
        loop_count = 0
        with MessageBrokerCtxManager(self.c, enabled=True) as c:
            async for msg in g:
                cmd = c.get_next_command()
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
            
    def process_command(self, cmd):
        fn = getattr(self, cmd.cmd, None)
        if fn:
            print(fn(*cmd.args, **cmd.kwargs))
        else:
            print(str(cmd))
    
    def start(self):
        return f"called start"
    
    def pause(self):
        return f"called pause"
    
    def stop(self):
        return f"called stop"
    
    def some_func(self, a, b, x=5, y=10):
        return f"called start, {a}, {b}, {x}, {y}"
    
    
    
algo = DummyAlgo(1,1)
algo.run_algo()