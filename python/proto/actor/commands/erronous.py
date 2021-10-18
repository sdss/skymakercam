# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de
# @Date: 2021-07-06
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


'''
import os
import sys
import logging
import time
import uuid

import asyncio
from proto.actor.exceptions import ProtoActorAPIError

from clu import AMQPClient, CommandStatus
from cluplus.proxy import Proxy, ProxyException, ProxyPlainMessagException, invoke, unpack

loop=asyncio.new_event_loop()

amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
loop.run_until_complete(amqpc.start())

def call(command):
    async def _call(command):
        proxy = amqpc.proxy('proto')
        fut = await proxy.send_command(command)
        return await fut
    return loop.run_until_complete(_call(command))
    
'''



from __future__ import annotations

import click
from clu.command import Command

from . import parser
from proto.actor.exceptions import ProtoActorAPIError


@parser.command()
def err_raise(command: Command):
    """Raise Exception"""

    raise ProtoActorAPIError(message="boom ...")


@parser.command()
def err_pass(command: Command):
    """Pass exception as argument."""

    command.fail(error=ProtoActorAPIError())
