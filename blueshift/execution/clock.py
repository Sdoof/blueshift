# Copyright 2018 QuantInsti Quantitative Learnings Pvt Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Mon Oct 22 10:14:47 2018

@author: prodipta
"""

import asyncio
import pandas as pd
import time
from enum import Enum

from blueshift.execution._clock import TradingClock, BARS
from blueshift.utils.exceptions import ClockError
from blueshift.utils.calendars.trading_calendar import TradingCalendar
from blueshift.utils.cutils import check_input
from blueshift.utils.decorators import blueprint

NANO = 1000000000


class ClockState(Enum):
    '''
        State of the realtime clock
    '''
    START_ALGO = 0
    BEFORE_SESSION = 1
    IN_SESSION = 2
    AFTER_SESSION = 3
    IN_RECESS = 4
    ALGO_END = 5
    
STATE_BARS_DICT = {ClockState.START_ALGO: BARS.ALGO_START,
                   ClockState.BEFORE_SESSION: BARS.BEFORE_TRADING_START,
                   ClockState.IN_SESSION: BARS.TRADING_BAR,
                   ClockState.AFTER_SESSION: BARS.AFTER_TRADING_HOURS,
                   ClockState.IN_RECESS: BARS.HEAR_BEAT,
                   ClockState.ALGO_END: BARS.ALGO_END}

@blueprint
class ClockQueue(asyncio.Queue):
    '''
        Extend the asyncio Queue to add a method to pop the last
        item and clear the queue properly
    '''
    async def get_last(self):
        elem = await self.get()
        n = self.qsize()
        if n == 0:
            return elem
        for i in range(n):
            elem = self.get_nowait()
        return elem

@blueprint
class RealtimeClock(TradingClock):
    '''
        Realtime clock to generate clock events to control the algo
        process. It is modelled as a state machine with states in
        ClockState enum and transition defined in a class method.
    '''
    def __init__(self, trading_calendar:TradingCalendar, 
                 emit_frequency:int, queue:ClockQueue=None):
        check_input(RealtimeClock.__init__, locals())
        super(RealtimeClock,self).__init__(trading_calendar,
             emit_frequency)
        
        self.clock_state = None
        self.last_emitted = None
        self.reset(queue,emit_frequency)
        
    def __str__(self):
        return f"Blueshift Realtime Clock [tick:{self.emit_frequency}, \
                    tz:{self.trading_calendar.tz}]"
                    
    def __repr__(self):
        return self.__str__()
        
    def reset(self,queue:ClockQueue=None, emit_frequency:int=None):
        '''
            Reset the clock, updating emit freq, queue etc.
        '''
        self.emit_frequency = emit_frequency
        # TODO: make sure the queue is not unbound
        self.queue = queue
        self.clock_state = ClockState.START_ALGO
        self.last_emitted = None
        
    def synchronize(self):
        '''
            At the start-up we must wait (blocking wait) to sync
            with the nearest (next) match of emission rate. For
            example, with 5 mins frequency and getting created at
            10:28:00 AM, we wait for 2 minutes before emitting the
            first event.
        '''                
        t = pd.Timestamp.now()
        minutes = t.minute + t.second/60
        miniutes_to_sync = self.emit_frequency - \
                        (minutes % self.emit_frequency)
        time.sleep(miniutes_to_sync*60)
    
    async def tick(self):
        '''
            The tick generator. It runs in the same thread as the
            algo and put the bars in a queue in async manner. This
            enables us to ensure a deterministic sleep time 
            irrespective of how long the algo takes to complete a 
            single processing loop. If clock runs faster than the
            algo can process, the clock events will get piled up 
            in the async queue. It is the responsibility of the 
            algo to handle that.
        '''
        if self.queue is None:
            raise ClockError("missing queue object for live clock")
            
        self.synchronize()
        
        try:
            while True:
                # emit the tuple
                t1 = pd.Timestamp.now(tz=self.trading_calendar.tz)
                bar = self.emit(self.clock_state)
                t = pd.Timestamp(int(t1.value/NANO)*NANO,
                                 tz=self.trading_calendar.tz)
                await self.queue.put((t, bar))
                
                # update the current state
                elapsed = t1.value - t1.normalize().value
                self.update_state(elapsed)
                
                # prepare to sleep
                t2 = pd.Timestamp.now(tz=self.trading_calendar.tz)
                timeleft = max(0,self.emit_frequency*60 - \
                               (t2 - t1).total_seconds())
                await asyncio.sleep(timeleft)
        except Exception as e:
            raise ClockError(msg='unexpected error {}'.format(str(e)))
            
    def update_state(self, elapsed_time):
        '''
            The state transiotion login. This determines the BAR
            that is sent to the algorithm.
        '''
        if not self.trading_calendar.is_session(pd.Timestamp.now(
                tz=self.trading_calendar.tz).normalize()):
            self.clock_state = ClockState.IN_RECESS
            return
        
        if elapsed_time < self.before_trading_start_nano:
            self.clock_state = ClockState.IN_RECESS
            return
        
        if elapsed_time < self.open_nano:
            if self.clock_state == ClockState.START_ALGO:
                self.clock_state = ClockState.BEFORE_SESSION
                return
            
            if self.clock_state == ClockState.IN_RECESS \
                and self.last_emitted != ClockState.BEFORE_SESSION:
                self.clock_state = ClockState.BEFORE_SESSION
            else:
                self.clock_state = ClockState.IN_RECESS
            return
        
        if elapsed_time < self.close_nano:
            if self.clock_state == ClockState.START_ALGO:
                self.clock_state = ClockState.BEFORE_SESSION
                return
            
            self.clock_state = ClockState.IN_SESSION
            return
        
        else:
            if self.clock_state == ClockState.IN_SESSION\
                and self.last_emitted != ClockState.AFTER_SESSION:
                self.clock_state = ClockState.AFTER_SESSION
            else:
                self.clock_state = ClockState.IN_RECESS
            return
    
    def emit(self, tick):
        '''
            Emit a clock signal. Also keep track of the last non
            hearbeat signal send to coordinate start and end of 
            sessions signals.
        '''
        if tick != ClockState.IN_RECESS:
            self.last_emitted = tick
        return STATE_BARS_DICT[tick]
    
    
    
    
    
    
    
    
    
    
    