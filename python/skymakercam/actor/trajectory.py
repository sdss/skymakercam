# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: trajectory.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import logging
import json

from skymakercam.actor.base_client import BaseClient, AMQPClient, CommandStatus, command_parser

from skymakercam.actor.x_stage import Client as XStage

class Client(XStage):
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
    
