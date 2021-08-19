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

from skymakercam.camera import SkymakerCameraSystem, SkymakerCamera, asyncio


async def singleFrame(exptim, name, verb=False, config="../etc/cameras.yaml"):
    """ Expose once and write the image to a FITS file.
    :param exptim: The exposure time in seconds. Non-negative.
    :type exptim: float
    :type exptim: float
    :param verb: Verbosity on or off
    :type verb: boolean
    :param config: Name of the YAML file with the cameras configuration
    :type config: string of the file name
    """

    cs = SkymakerCameraSystem(SkymakerCamera, camera_config=config, verbose=verb)
    cam = await cs.add_camera(name=name, uid=cs._config[name]["uid"])

    if verb:
        cs.logger.log(logging.DEBUG, f"config {cs.list_available_cameras()}")

    exp = await cam.expose(exptim, "LAB TEST")
    cs.logger.log(logging.DEBUG, f"config {str(exp.data)}")
    await exp.write()
    if verb:
        cs.logger.log(logging.DEBUG, f"wrote {exp.filename}")

def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", '--exptime', type=float, default=5.0,
                        help="Expose for for exptime seconds")

    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    # Name of an optional YAML file
    parser.add_argument("-c", '--cfg', default="python/skymakercam/etc/cameras.yaml",
                        help="YAML file of lvmt cameras")

    # the last argument is mandatory: must be the name of exactly one camera
    # as used in the configuration file
    parser.add_argument('camname', default="sci.agw")

    args = parser.parse_args()

    asyncio.run(singleFrame(args.exptime, args.camname, verb=args.verbose, config=args.cfg))


if __name__ == '__main__':

    main()
