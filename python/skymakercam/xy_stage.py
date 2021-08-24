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


class Client(AMQPClient):
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
    ):
        self.svc_name = name
        super().__init__(name=name + ".client", 
                         models=[name],
                         user=user,
                         password=password,
                         host=host,
                         port=port,
                         ssl=ssl,
        )
    
    def is_connected(self):
        return self.connection and self.connection.connection is not None


    async def client_send_command_blocking(self, cmd: str, *args):
        future =  await self.send_command(self.svc_name, cmd, *args)
        return await future


    async def client_send_command_async(self, cmd: str, *args):
        return await self.send_command(self.svc_name, cmd, *args)


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
        cmd = await self.client_send_command_blocking('getdeviceencoderpositionxy', unit)
        assert(cmd.status == CommandStatus.DONE)
        return [cmd.replies[-1].body['DeviceEncoderPosition_X'],
                cmd.replies[-1].body['DeviceEncoderPosition_Y']]


    async def moveToHome(self):
        cmd = await self.client_send_command_blocking('movetohomexy')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body['AtHome']


    async def moveRelative(self, posx: float, posy: float, unit = 'STEPS'):
        cmd = await self.client_send_command_blocking('moverelativexy', posx, posy, unit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body


    async def moveAbsolute(self, posx: float, posy: float, unit = 'STEPS'):
        cmd = await self.client_send_command_blocking('moveabsolutexy', posx, posy, unit)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body


    async def moveToLimit(self, limitx, limity):
        cmd = await self.client_send_command_blocking('movetolimitxy', limitx, limity)
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body




