# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: __main__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


import argparse
import os
import sys
import logging
import time

import asyncio
import json

from skymakercam.focus_stage import Client as FocusStage
from clu.tools import CommandStatus
        
async def test_focus_stage(args):

    if args.verbose:
        focus_stage.log.sh.setLevel(0)

    focus_stage = FocusStage(args.focus_stage, user=args.user, password=args.password, host=args.host, port=args.port)
   
    await focus_stage.connect()
    focus_stage.log.debug(f"RabbitMQ is connected: {focus_stage.is_connected()}")


    focus_stage.log.debug(f"Is Reachable: {focus_stage.isReachable()}")

    focus_stage.log.debug(f"DeviceEncoderPosition: {await focus_stage.getDeviceEncoderPosition('UM')}")

    if not await focus_stage.isAtHome():
        await focus_stage.moveToHome()

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    parser.add_argument("-u", '--user', type=str, default="guest",
                        help="user for RabbitMQ server")

    parser.add_argument("-p", '--password', type=str, default="guest",
                        help="password for RabbitMQ server")

    parser.add_argument("-H", '--host', type=str, default="localhost",
                        help="host for RabbitMQ server")

    parser.add_argument("-P", '--port', type=int, default=5672,
                        help="port for RabbitMQ server")

    # the last argument is mandatory: must be the name of exactly one camera
    # as used in the configuration file
    parser.add_argument('focus_stage', default="test.first.focus_stage")

    asyncio.run(test_focus_stage(parser.parse_args()))
    
            
if __name__ == '__main__':

    #da = DataAnalysis()
    main()
