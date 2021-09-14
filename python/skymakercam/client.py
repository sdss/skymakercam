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
import asyncio

from typing import Any, Callable, Optional, Awaitable
from clu import AMQPReply



class ProxyMethod:
    __slots__ = (
        "_amqpc",
        "_consumer",
        "_command",
    )
    
    def __init__(self, amqpc, consumer, command):
        self._amqpc = amqpc
        self._consumer = consumer
        self._command = command
    
    def __getattr__(self, item) -> "ProxyMethod":
        return ProxyMethod(".".join((self._consumer, item)), func=self.func)
    
    async def __call__(
        self, 
        *args,
        blocking: bool = True,
        callback: Callable[[Any], Awaitable[None]] = None,
        timeout = 1.4142,
    ):
        command =  await asyncio.wait_for(self._amqpc.send_command(self._consumer, self._command.lower(), *args, callback=callback), timeout) 
        if blocking:
            return await command 
        return command


class Proxy:
    __slots__ = (
        "_consumer",
        "_amqpc"
    )
    
    def __init__(
        self, 
        consumer: str,
        amqpc: AMQPClient
    ):
        self._consumer = consumer
        self._amqpc = amqpc
    
    def __getattr__(self, command) -> ProxyMethod:
        return ProxyMethod(self._amqpc, self._consumer, command)
    

async def gather(*argv):
    if len(argv) > 1:
        ret = await asyncio.gather(*[await cmd for cmd in argv])
        return [r.replies[-1].body for r in ret]
    else:
        ret = await argv[0]
        if ret.status.did_fail:
            print("failed") # FixMe: add an exception
        else:
            return ret.replies[-1].body
    
async def unpack(cmd, key: str = None):
    ret = await cmd
    #print(ret)
    #print(ret.status)
    #print(ret.status.did_fail)
    if ret.status.did_fail:
        print("failed") # FixMe: add an exception
    else:
        if key:
            return ret.replies[-1].body["key"]
        else:
#            print(type(list(ret.replies[-1].body.values())))
            ret = list(ret.replies[-1].body.values())
            if len(ret) > 1:
                return ret
            else:
                return ret[0]

