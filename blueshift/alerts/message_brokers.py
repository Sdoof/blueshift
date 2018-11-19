# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 13:34:00 2018

@author: prodipta
"""
import zmq

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
        conn_srting = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.bind(conn_srting)
    
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
        conn_srting = "%s://%s:%s" % (self._protocol, 
                                      self._addr, 
                                      self._port)
        self._socket.connect(conn_srting)
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