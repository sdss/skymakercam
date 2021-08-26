# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: camera.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import logging
import json

from skymakercam.actor.base_client import BaseClient, AMQPClient, CommandStatus, command_parser

class Client(BaseClient):
    """ Simple Focuser
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
        super().__init__(name=name, 
                         user=user,
                         password=password,
                         host=host,
                         port=port,
                         ssl=ssl,
                         amqpc=amqpc
        )
    
    async def isReachable(self):
        cmd = await self.client_send_command_blocking('isreachable')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['Reachable']


    async def isAtHome(self):
        cmd = await self.client_send_command_blocking('isathome')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['AtHome']


    async def isMoving(self):
        cmd = await self.client_send_command_blocking('ismoving')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['Moving']


    async def isAtLimit(self):
        cmd = await self.client_send_command_blocking('isatlimit')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['AtLimit']


    async def getDeviceEncoderPosition(self, unit = 'STEPS'):
        cmd = await self.client_send_command_blocking('getdeviceencoderposition', unit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['DeviceEncoderPosition']


    async def moveToHome(self):
        cmd = await self.client_send_command_blocking('movetohome')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['AtHome']


    async def moveRelative(self, pos, unit = 'STEPS'):
        cmd = await self.client_send_command_blocking('moverelative', pos, unit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body


    async def moveAbsolute(self, pos, unit = 'STEPS'):
        cmd = await self.client_send_command_blocking('moveabsolute', pos, unit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body


    async def moveToLimit(self, limit):
        cmd = await self.client_send_command_blocking('movetolimit', limit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body




