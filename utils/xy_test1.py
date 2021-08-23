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
import math

import asyncio
import json

from skymakercam.xy_stage import Client as XY
from clu.tools import CommandStatus
        
async def test_xy_stage(args):

    xy_stage = XY(args.xy_stage, user=args.user, password=args.password, host=args.host, port=args.port)
   
    if args.verbose:
        xy_stage.log.sh.setLevel(0)

    await xy_stage.connect()
    xy_stage.log.debug(f"RabbitMQ is connected: {xy_stage.is_connected()}")


    xy_stage.log.debug(f"Is Reachable: {await xy_stage.isReachable()}")

#    await xy_stage.moveToHome()
    
    xy_stage.log.debug(f"DeviceEncoderPosition: {await xy_stage.getDeviceEncoderPosition(unit='DEG')}")

    await xy_stage.moveRelative(22, 33, unit='DEG')
#    await xy_stage.moveAbsolute(201, -47, 'DEG')
    await xy_stage.moveAbsolute(201.70, -47.48, unit='DEG')

    xy_stage.log.debug(f"DeviceEncoderPosition: {await xy_stage.getDeviceEncoderPosition(unit='DEG')}")


    #if not await xy_stage.isAtHome():
        #await xy_stage.moveToHome()

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
    parser.add_argument('xy_stage', default="test.first.xy_stage")

    asyncio.run(test_xy_stage(parser.parse_args()))
    
            
if __name__ == '__main__':

    #da = DataAnalysis()
    main()
