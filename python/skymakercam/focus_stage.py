# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: camera.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from clu import AMQPClient, AMQPActor, command_parser
from clu.tools import CommandStatus
from clu.model import Model
import logging
import json


class Client:
    """ Simple Focuser
        :param name : Clu RabbitMQ name.
        :type name : str
    """

    def __init__(
        self, name: str,
        user: str = "guest",
        password: str = "guest",
        host: str = "localhost",
        port: int = 5672,
        ssl: bool = False,
    ):
        self.name = name
        self.client = AMQPClient(name=name + ".client", 
                                 models=[name],
                                 user=user,
                                 password=password,
                                 host=host,
                                 port=port,
                                 ssl=ssl,
                                 )
    
    def is_connected(self):
        return self.client.connection and self.client.connection.connection is not None


    async def connect(self):  
        """ Connect
        :param name : Clu RabbitMQ name.
        :type name : str
        """
        if not self.is_connected():
            await self.client.start()


    async def client_send_command_blocking(self, cmd: str, *args):
        future =  await self.client.send_command(self.name, cmd, *args)
        return await future


    async def client_send_command_async(self, cmd: str, *args):
        return await self.client.send_command(self.name, cmd, *args)

