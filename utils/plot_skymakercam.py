# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: plot_skymakercam.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# from lvmtan run:
# poetry run container_start --name lvm.all
# from lvmpwi run:
# poetry run container_start --name=lvm.sci.pwi --simulator
# from skymakercam run:
# poetry run python utils/plot_skymakercam.py -v -c python/skymakercam/etc/cameras.yaml lvm.sci.agw.cam


import argparse
import os
import sys
import logging
import time
import uuid

from astropy.utils import iers
iers.conf.auto_download = False 

from plotit import PlotIt
from keyreader import KeyReader

from clu import AMQPClient, CommandStatus
from cluplus.proxy import Proxy, invoke, unpack

from skymakercam.camera import SkymakerCameraSystem, SkymakerCamera, asyncio, rebin


async def plot_skymakercam(exptime, binning, guiderect, camname, verb=False, config="../etc/cameras.yaml"):

    cs = SkymakerCameraSystem(SkymakerCamera, camera_config=config, verbose=verb)
    cam = await cs.add_camera(name=camname, uid=cs._config[camname]["uid"])

    if verb:
        cs.logger.log(logging.DEBUG, f"cameras {cs.list_available_cameras()}")
#        cs.logger.log(logging.DEBUG, f"config {cs._config[camname]['tcs']}")

    ## client interfaces to TCS, focus stage and kmirror are optional and not needed for skymakercam - it connects internally to them.
    amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    pwi_tcs = Proxy(amqpc, cs._config[camname]['tcs'])
    await pwi_tcs.start()
    await pwi_tcs.setConnected(True)
    await pwi_tcs.setTracking(True)

    focus_stage = Proxy(amqpc, cs._config[camname]['focus_stage'])
    await focus_stage.start()
    await focus_stage.moveToHome()

    kmirror = Proxy(amqpc, cs._config[camname]['kmirror'])
    await kmirror.start()
    exp = await cam.expose(exptime, camname)
    p = PlotIt(rebin(exp.data, binning), guiderect, logger=cs.logger.log)

    keyreader = KeyReader(echo=False, block=False)
    while(True):
        find_objects = False
        
        key = keyreader.getch()
        if key == 'q':
            cs.logger.log(logging.DEBUG, f"Goodbye and thanks for all the fish.")
            break
        elif key == 'o':
            cs.logger.log(logging.DEBUG, f"Find objects.")
            find_objects = True
        elif key:
            cs.logger.log(logging.DEBUG, f"-{key}-")

        exp = await cam.expose(exptime, "LAB TEST")
        p.update(rebin(exp.data, binning), find_objects)

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", '--exptime', type=float, default=5.0,
                        help="Expose for for exptime seconds")

    parser.add_argument("-b", '--binning', type=int, default=1,
                        help="Image Binning")

    parser.add_argument("-g", '--guiderect', type=int, default=60,
                        help="Size of guide rectangle")

    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    # Name of an optional YAML file
    parser.add_argument("-c", '--cfg', default="python/skymakercam/etc/cameras.yaml",
                        help="YAML file of lvmt cameras")

    # the last argument is mandatory: must be the name of exactly one camera
    # as used in the configuration file
    parser.add_argument('camname', default="sci.agw")

    args = parser.parse_args()

    asyncio.run(plot_skymakercam(args.exptime, args.binning, args.guiderect, args.camname, verb=args.verbose, config=args.cfg))
    
            
if __name__ == '__main__':

    main()
