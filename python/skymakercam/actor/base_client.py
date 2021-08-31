# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: base_client.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import uuid

from clu import AMQPClient, command_parser
from clu.tools import CommandStatus
from clu.model import Model
import logging
import json



class BaseClient():
    """ BaseClient
        :param name : Clu RabbitMQ name.
        :type name : str
    """

    def __init__(
        self, 
        name: str,
        user: str = "guest",
        password: str = "guest",
        host: str = "localhost",
        port: int = 5672,
        ssl: bool = False,
        amqpc: AMQPClient = None
    ):
        self.name = name
        if not amqpc:
            self.amqpc = AMQPClient(name=f"{name}.client-{uuid.uuid4().hex[:8]}", 
                                models=[name],
                                user=user,
                                password=password,
                                host=host,
                                port=port,
                                ssl=ssl,
            )
        else:
            self.amqpc = amqpc
            
        
    async def start(self):
        await self.amqpc.start()
        
    
    def is_connected(self):
        return self.amqpc.connection and self.amqpc.connection.connection is not None


    async def client_send_command_blocking(self, cmd: str, *args):
        future =  await self.amqpc.send_command(self.name, cmd, *args)
        return await future


    async def client_send_command_async(self, cmd: str, *args):
        return await self.amqpc.send_command(self.name, cmd, *args)


