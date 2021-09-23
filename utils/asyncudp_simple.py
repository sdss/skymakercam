import uuid   
import struct   
import time
import numpy as np
from enum import Enum

import asyncio
import asyncudp

class AsyncBase(object):
    class HEADER(Enum):
        UID = 0 
        TIMESTAMP = 1
        SIZE = 2
        WIDTH = 3
        HEIGHT = 4
        OFFSET = 5
        PKGSIZE = 6
        
    def __init__(self):
        # uid, timestamp, len(data), width, height, offset, size
        self.packer_header = struct.Struct('I f I I I I I')
        self.sock = None
    
    async def start(self, *args, **kwargs):
        self.sock = await asyncudp.create_socket(*args, **kwargs)
    
    def stop(self):
        self.sock.close()

class AsyncSend(AsyncBase):
    def __init__(self, camname: str="camera", remote_addr=('224.0.0.1', 9999), max_data=1000):
        super().__init__()
        self.uid=uuid.uuid4().int%10000000
        self.camname=camname
        self.remote_addr=remote_addr
        self.max_data = max_data
    
    async def start(self):
        await super().start(remote_addr=self.remote_addr)
    
    async def send(self, data, width, height):
        timestamp = time.time()
        send_data = data.tobytes() 
        data_to_send=len(send_data)
        data_offset=0
        while(data_offset < data_to_send):
            size = self.max_data if data_to_send - data_offset > self.max_data else data_to_send - data_offset
            header = [self.uid, timestamp, len(send_data), width, height, data_offset, size]
            packed_data = self.packer_header.pack(*header)
            packed_data += send_data[data_offset:data_offset+size]
            data_offset += self.max_data
            
            self.sock.sendto(packed_data)

class AsyncRecv(AsyncBase):
    def __init__(self, local_addr=('224.0.0.1', 9999), max_data=1000):
        super().__init__()
        self.local_addr=local_addr
    
    async def start(self):
        await super().start(local_addr=self.local_addr)
    
    async def recv(self):
        # get first part, wait for first block
        while True:
            data, addr = await self.sock.recvfrom()
            header = self.packer_header.unpack(data[:self.packer_header.size])
            width = header[AsyncBase.HEADER.WIDTH.value]
            height = header[AsyncBase.HEADER.HEIGHT.value]
            if not header[AsyncBase.HEADER.OFFSET.value]: 
                break
        recvd_data = data[self.packer_header.size:]
        for part in range(round(header[AsyncBase.HEADER.SIZE.value]/header[AsyncBase.HEADER.PKGSIZE.value]+0.5)-1):
            data, addr = await self.sock.recvfrom()
            header = self.packer_header.unpack(data[:self.packer_header.size])
            recvd_data += data[self.packer_header.size:]
        return np.frombuffer(recvd_data, dtype=float), width, height     
            
