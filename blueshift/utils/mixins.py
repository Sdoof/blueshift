# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 16:19:35 2018

@author: prodipta
"""
from blueshift.utils.exceptions import StateMachineError

class StateMachine(object):
    '''
        A simple state machine
    '''
    def __init__(self, init_state, transition_dict):
        self._current_state = init_state
        self._transition_dict = transition_dict
        
    
    @property
    def state(self):
        return self._current_state
    
    @state.setter
    def state(self, to_state):
        if to_state not in self._transition_dict[self._current_state]:
            strmsg = f"Illegal state change from {self._current_state}\
                        to {to_state}"
            raise StateMachineError(msg=strmsg)
            
        self._current_state = to_state
        
    