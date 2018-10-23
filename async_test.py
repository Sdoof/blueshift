# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 08:56:26 2018

@author: prodipta
"""
import asyncio
import pandas as pd

import random

class Clock(object):
    
    def __init__(self, queue=None, delay=None):
        self.reset(queue,delay)
        
    def reset(self,queue=None, delay=None):
        self.delay = delay
        self.queue = queue
        
    async def tick(self):
        if self.delay is None:
            raise ValueError
        if self.queue is None:
            raise ValueError
        
        try:
            while True:
                t1 = pd.Timestamp.now()
                await self.queue.put((t1,1))
                t2 = pd.Timestamp.now()
                timeleft = max(0,self.delay - (t2 - t1).total_seconds())
                await asyncio.sleep(timeleft)
        except Exception as e:
            print(e)
        
from blueshift.execution.clock import RealtimeClock, ClockQueue
from blueshift.configs.defaults import default_calendar

class Consumer(object):
    
    def __init__(self):
        self.clock = RealtimeClock(default_calendar(),1)
        self.loop = None
        self.i = 0
        
    async def get_tick(self):
        while True:
            #tick = await self.queue.get()
            tick = await self.queue.get_last()
            t = pd.Timestamp.now()
            print("{}: got {}".format(t, tick))
            await asyncio.sleep(0)
            self.i = self.i + 1
            if self.i == 1:
                raise ValueError("some message")
            
    def reset_clock(self, delay=1):
        self.get_event_loop()
        #self.queue = asyncio.Queue(loop=self.loop)
        self.queue = ClockQueue(loop=self.loop)
        self.clock.reset(self.queue, delay)
            
    def run(self):
        self.reset_clock(1)
        ticker_coro = self.clock.tick()
        consumer_coro = self.get_tick()
        
        try:
            tasks = asyncio.gather(ticker_coro,consumer_coro,
                                   return_exceptions=False)
            self.loop.run_until_complete(tasks)
        except Exception as e:
            print("exception {}".format(e))
        finally:
            print("closing gracefully")
            for task in asyncio.Task.all_tasks():
                task.cancel()
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()
        
    def get_event_loop(self):
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        if self.loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.loop = asyncio.get_event_loop()
            
        

cons = Consumer()
print("1st run")
try:
    cons.run()
except:
    print("interrupted")
#print("second run")
#cons.run()
            



