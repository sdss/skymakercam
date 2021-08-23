# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: plot_skymakercam.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# poetry run container_start --name test.xy.stage
# poetry run container_start --name lvm.all
#  poetry run python utils/plot_skymakercam.py -v -c python/skymakercam/etc/cameras.yaml lvm.sci.agw.cam


import argparse
import os
import sys
import logging
import time

from plotit import *

from skymakercam.camera import SkymakerCameraSystem, SkymakerCamera, asyncio

async def plot_skymakercam(exptime, binning, guiderect, camname, verb=False, config="../etc/cameras.yaml"):

    cs = SkymakerCameraSystem(SkymakerCamera, camera_config=config, verbose=verb)
    cam = await cs.add_camera(name=camname, uid=cs._config[camname]["uid"])

    if verb:
        cs.logger.log(logging.DEBUG, f"config {cs.list_available_cameras()}")

    exp = await cam.expose(exptime, camname)
#    plt.title(f"skymaker cam {camname}", fontweight ="bold")
    
    
    p = PlotIt(rebin(exp.data, binning), guiderect, logger=cs.logger.log)
  
    while(True):
       exp = await cam.expose(exptime, "LAB TEST")
       p.update(rebin(exp.data, binning))


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

    #da = DataAnalysis()
    main()