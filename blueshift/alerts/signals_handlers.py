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
Created on Thu Oct  4 18:00:23 2018

@author: prodipta
from https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
"""

import signal
from blueshift.utils.decorators import blueprint

@blueprint
class BlueshiftInterruptHandler(object):

    def __init__(self, algo):
        self.sig_int = signal.SIGINT
        self.sig_term = signal.SIGTERM
        self.algo = algo

    def __enter__(self):
        self.interrupted = False
        self.terminated = False
        self.released = False
        self.original_handler_int = signal.getsignal(self.sig_int)
        self.original_handler_term = signal.getsignal(self.sig_term)
        
        signal.signal(self.sig_int, self.handler)
        signal.signal(self.sig_term, self.handler)
        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):
        if self.released:
            return False
        signal.signal(self.sig_int, self.original_handler_int)
        signal.signal(self.sig_term, self.original_handler_term)
        self.released = True
        return True
    
    def handler(self, signum, frame):
        self.release()
        if signum == signal.SIGINT:
            self.interrupted = True
            self.algo_pause()
        else:
            self.terminated = True
            self.algo_stop()
            
    def algo_pause(self):
        print("pausing the algo, context:{}...".format(self.algo.context))
        pass
    
    def algo_stop(self):
        print("shutting down the algo, context:{}...".format(self.algo.context))
        pass

### test ##
#import time
#class TestAlgo():
#    def __init__(self):
#        self.context = {"1":1, "2":3}
#        
#algo = TestAlgo()        
#with BlueshiftInterruptHandler(algo) as h:
#    for i in range(1000):
#        print("...")
#        time.sleep(1)
#        if h.interrupted:
#            print("interrupted!...")
#            break
### end test ##