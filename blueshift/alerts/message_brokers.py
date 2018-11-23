# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 13:34:00 2018

@author: prodipta
"""
import json
import zmq
from zmq.asyncio import Context as async_Context

from blueshift.utils.types import Command

class ZeroMQPublisher(object):
    '''
        ZeroMQ publisher class.
    '''
    def __init__(self, addr, port, topic, protocol="tcp", EOM = "EOM",
                 encoding = "utf-8"):
        self._protocol = protocol
        self._addr = addr
        self._port = port
        self._topic = topic
        self._EOM = EOM
        self._encoding = encoding
        self._encoded_topic = bytes(self._topic, self._encoding)
        self._encoded_EOM = bytes(self._EOM, self._encoding)
        
    def connect(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PUB)
        conn_string = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.bind(conn_string)
    
    def send(self, msg):
        msg = bytes(msg, self._encoding)
        self._socket.send_multipart([self._encoded_topic, msg])
        
    def close(self):
        if self._socket:
            self._socket.send_multipart([self._encoded_topic,
                                         self._encoded_EOM])
            self._socket.close()
        if self._context:
            self._context.term()    
        self._context = self._socket = None
        
class ZeroMQSubscriber(object):
    '''
        ZeroMQ subscriber class.
    '''
    def __init__(self, addr, port, topic, protocol="tcp", EOM = "EOM",
                 no_block=False, encoding="utf-8"):
        self._protocol = protocol
        self._addr = addr
        self._port = port
        self._topic = topic
        self._EOM = EOM
        self._no_block = no_block
        self._encoding = encoding
        self._encoded_topic = bytes(self._topic, self._encoding)
        self._encoded_EOM = bytes(self._EOM, self._encoding)
    
    def connect(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.SUB)
        conn_string = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.connect(conn_string)
        self._socket.setsockopt(zmq.SUBSCRIBE, self._encoded_topic)
    
    def recv(self, *args, **kwargs):
        if self._no_block:
            [topic, msg] = self._socket.recv_multipart(zmq.NOBLOCK)
        else:
            [topic, msg] = self._socket.recv_multipart()
        
        topic = topic.decode(self._encoding)
        msg = msg.decode(self._encoding)
        
        if topic == self._topic:
            if msg == self._EOM:
                self.close()
        
        return msg
                
    def recv_all(self, *args, **kwargs):
        while True:
            if self._no_block:
                [topic, msg] = self._socket.recv_multipart(
                        zmq.NOBLOCK)
            else:
                [topic, msg] = self._socket.recv_multipart()
            
            topic = topic.decode(self._encoding)
            msg = msg.decode(self._encoding)
            
            if topic == self._topic:
                if msg == self._EOM:
                    self.close()
                    break
                else:
                    self.handle_msg(msg, *args, **kwargs)
        
    def close(self):
        if self._socket:
            self._socket.close()
        
        if self._context:
            self._context.term()
        
        self._context = self._socket = None
        
    def handle_msg(self, msg, *args, **kwargs):
        print(msg)
        
class ZeroMQCmdPairServer(object):
    '''
        ZeroMQ PAIR socket server for receiving on the command channel
        and processing + forwarding the input. This should go in the
        algo class that receives and executes a command. Commands are
        interpreted as jasonified strings cast in to the Command type.
    '''
    def __init__(self, addr, port, protocol="tcp", no_block=True):
        self._protocol = protocol
        self._addr = addr
        self._port = port
        self._no_block = no_block
        
    def connect(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.SUB)
        conn_string = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.bind(conn_string)
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
    def get_next_command(self):
        try:
            strcmd = self._socket.recv_string(flags=zmq.NOBLOCK)
            cmd_dict = json.loads(strcmd)
            cmd = cmd_dict['cmd']
            args = cmd_dict['args']
            kwargs = cmd_dict['kwargs']
            cmd = Command(cmd, args, kwargs)
            return cmd
        except zmq.Again as e:
            return None
    
    def close(self):
        if self._socket:
            self._socket.close()
        
        if self._context:
            self._context.term()
        
        self._context = self._socket = None
        
class ZeroMQCmdPairClient(object):
    '''
        ZeroMQ PAIR socket client for sending commands on the command
        channel. Commands are of Command type, sent as jasonified 
        strings. This should be part of the system controlling the 
        running algo, locally or from a remote machine.
    '''
    def __init__(self, addr, port, protocol="tcp", no_block=False):
        self._protocol = protocol
        self._addr = addr
        self._port = port
        self._no_block = no_block
        
    def connect(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PUB)
        conn_string = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.connect(conn_string)
        
    def send_command(self):
        cmd = str(input("enter a command") or "contine")
        args = list(input("enter argument lists") or [])
        kwargs = dict(input("enter keyword argument lists") or {})
        cmd = Command(cmd,args,kwargs)
        strcmd = json.dumps(cmd._asdict())
        self._socket.send_string(strcmd)
    
    def close(self):
        if self._socket:
            self._socket.close()
        
        if self._context:
            self._context.term()
        
        self._context = self._socket = None
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    