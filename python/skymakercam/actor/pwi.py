# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: camera.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import logging
import json

from astropy.coordinates import SkyCoord
import astropy.units as u

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
    
    async def connect(self):
        cmd = await self.client_send_command_blocking('connect')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body

    async def status(self):
        cmd = await self.client_send_command_blocking('status')
        assert(cmd.status == CommandStatus.DONE)
        return cmd.replies[-1].body
        
    async def get_position_j2000(self):
        status = await self.status()
        ra0 = status['ra_j2000_hours']
        dec0 = status['dec_j2000_degs']
        return SkyCoord(ra=ra0*u.hour, dec=dec0*u.deg), status['field_angle_here_degs']

    async def setTrackingOn(self, on:bool):
        cmd = await self.client_send_command_blocking('tracking-on' if on else 'tracking-off')
        assert(cmd.status == CommandStatus.DONE)
        
