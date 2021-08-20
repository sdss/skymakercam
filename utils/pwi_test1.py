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

from skymakercam.pwi import Client as Pwi
from clu.tools import CommandStatus

from astropy import units as u

from astropy.coordinates import SkyCoord
        
async def test_pwi(args):

    pwi = Pwi(args.pwi, user=args.user, password=args.password, host=args.host, port=args.port)

    if args.verbose:
        pwi.log.sh.setLevel(0)
   
    await pwi.connect()
    pwi.log.debug(f"RabbitMQ is connected: {pwi.is_connected()}")

    status = await pwi.status()
    pwi.log.debug(f"Position deg, ra: {status},")

    ra = status['ra_j2000_hours']
    dec = status['dec_j2000_degs']
    c = SkyCoord(ra=ra * u.hour, dec=dec * u.degree, frame='icrs')
    pwi.log.info(f"SkyCoord: {c} in deg")
    assert(c.ra.hour == ra)


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
    parser.add_argument('pwi', default="test.first.pwi")

    asyncio.run(test_pwi(parser.parse_args()))
    
            
if __name__ == '__main__':

    #da = DataAnalysis()
    main()
