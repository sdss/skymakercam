# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: camera.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import glob
import os
import sys
import tempfile
import pathlib
import math
import uuid

#from astropy.utils import iers
#iers.conf.auto_download = False 

from logging import DEBUG, WARNING

from typing import cast

import numpy as np
import json

import astropy.time

from sdsstools import get_logger, read_yaml_file
from sdsstools.logger import SDSSLogger
from sdsstools.logger import StreamFormatter  

from clu import AMQPClient, CommandStatus
from clu.model import Model

from basecam import BaseCamera, CameraSystem, Exposure
#from basecam.actor import CameraActor
from basecam.events import CameraEvent
from basecam.mixins import CoolerMixIn, ExposureTypeMixIn, ImageAreaMixIn, ShutterMixIn, CoolerMixIn
from basecam.notifier import EventListener
from basecam.utils import cancel_task

from lvmtipo.site import Site
from lvmtipo.siderostat import Siderostat
from lvmtipo.fiber import Fiber
from lvmtipo.target import Target

from skymakercam.params import load as params_load
from cluplus.proxy import Proxy, ProxyPartialInvokeException, invoke, unpack

from astropy.coordinates import SkyCoord
import astropy.units as u

from skymakercam.starimage import find_guide_stars, make_synthetic_image

__all__ = ['SkymakerCameraSystem', 'SkymakerCamera']


EXPOSURE_DIR = tempfile.TemporaryDirectory()

class SkymakerCameraSystem(CameraSystem):
    """ A collection of GenICam cameras, possibly online
    :param camera_class : `.BaseCamera` subclass
        The subclass of `.BaseCamera` to use with this camera system.
    :param camera_config : 
        A dictionary with the configuration parameters for the multiple
        cameras that can be present in the system, or the path to a YAML file.
        Refer to the documentation for details on the accepted format.
    :type camera_config : dict or path
    :param logger : ~logging.Logger
        The logger instance to use. If `None`, a new logger will be created.
    :param log_header : A string to be prefixed to each message logged.
    :type log_header : str
    :param log_file : The path to which to log.
    :type log_file : str
    :param verbose : Whether to log to stdout.
    :type verbose : bool
    """

    from skymakercam import __version__
#    __version__ = "0.0.138"

    def list_available_cameras(self):
        """ Gather skymaker camera uids.
        :return: a list of cameras.
        :rtype: list
        """
        return [c.camera_params.get("uid") for c in self.cameras]


class SkymakerCamera(BaseCamera, ExposureTypeMixIn, ImageAreaMixIn, CoolerMixIn):
    """A virtual camera that does not require hardware.

    This class is mostly intended for testing and development. It behaves
    in all ways as a real camera with pre-defined responses that depend on the
    input parameters.

    """

    def config_get(self, key, default=None):
        """ DOESNT work for keys with dots !!! """
        def g(config, key, d=None):
            k = key.split('.', maxsplit=1)
            c = config.get(k[0] if not k[0].isnumeric() else int(k[0]))  # keys can be numeric
            return d if c is None else c if len(k) < 2 else g(c, k[1], d) if type(c) is dict else d
        return g(self.config, key, default)


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.logger.sh.setLevel(DEBUG)
        self.logger.sh.formatter = StreamFormatter(fmt='%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d: \033[1m%(message)s\033[21m') 
        self.logger.debug("construct")

        self.config = kwargs['camera_params']
        self.inst_params = params_load(f"skymakercam.params.{self.config_get('instpar', None)}")
        self.inst_params.catalog_path = os.path.expandvars(self.config_get('catalog_path', tempfile.TemporaryDirectory()))
        if not os.path.exists(self.inst_params.catalog_path):
            self.log(f"Creating catalog path: {self.inst_params.catalog_path}", WARNING)
            pathlib.Path(self.inst_params.catalog_path).mkdir(parents=True, exist_ok=True)

        rmqname = f"proxy-{uuid.uuid4().hex[:8]}"
#        self.logger.debug(f"{rmqname} {self.config_get('rmq.host', 'localhost')}")
        
#        Proxy.setDefaultAmqpc(AMQPClient(name=rmqname, url=os.getenv("RMQ_URL", None)))

        self._tcs = Proxy(self.config_get('tcs', None))
        
        self.tcs_coord = None
        self.tcs_pa = 0
        self.ra_off = 0.0
        self.dec_off = 0.0

        self.guide_stars = None
        
        # we do reuse the AMQPClient
        self._focus_stage = Proxy(self.config_get('focus_stage', None))
        self.sky_flux = self.config_get('default.sky_flux', 15)
        self.seeing_arcsec = self.config_get('default.seeing_arcsec', 3.5)
#        self.exp_time = self.config_get('default.exp_time',5)
        
        # we do reuse the AMQPClient
        self._kmirror = Proxy(self.config_get('kmirror', None))
        self.kmirror_angle = 0.
        
        self.site = self.config_get('site', "LCO")
        self.sid = Siderostat()
        self.geoloc = Site(name = self.site)

        self._temperature = 25
        self._change_temperature_task = None

        self._gain = self.config_get('default.gain', 1)
        self._binning = self.config_get('default.binning', [1, 1])

        self.log(f"{self.inst_params.chip_size_pix}")
        
        self.width = self.inst_params.chip_size_pix[0]
        self.height = self.inst_params.chip_size_pix[1]

        self._image_area = (1, self.inst_params.chip_size_pix[0], 1, self.inst_params.chip_size_pix[1])

        self.data = False

        self.image_namer.dirname = EXPOSURE_DIR.name

    async def tcs_get_position_j2000(self):
        status = await self._tcs.status()
        return SkyCoord(ra=status["ra_j2000_hours"]*u.hour, dec=status["dec_j2000_degs"]*u.deg), status["field_angle_here_degs"]


    async def _connect_internal(self, **connection_params):
        self.logger.debug(f"connecting ...")
        
        await self._tcs.start()
        await self._focus_stage.start()
        await self._kmirror.start()

        self.tcs_coord = SkyCoord(ra=0.0*u.hour, dec=0.0*u.deg)
        self.tcs_pa = 0.0

        return True

    async def _disconnect_internal(self):
        """Close connection to camera.
        """
        self.logger.debug("disconnect")
        await self._tcs.client.stop()
        await self._focus_stage.client.stop()
        await self._kmirror.client.stop()

    async def create_synthetic_image(self, exposure):
        self.defocus = (math.fabs((await self._focus_stage.getPosition())["Position"] )/100)**2
        self.log(f"defocus {self.defocus}")

        self.kmirror_angle = float((await self._kmirror.getPosition())["Position"])
        self.log(f"kmirror angle (deg): {self.kmirror_angle}")

        tcs_coord_current, self.tcs_pa = await self.tcs_get_position_j2000()
        
        mathar_angle = math.degrees(self.sid.fieldAngle(self.geoloc, Target(tcs_coord_current), None))
        self.log(f"mathar angle (deg): {mathar_angle}")

        sky_angle = self.kmirror_angle - mathar_angle
        self.log(f"sky angle (deg): {sky_angle}")

        separation = self.tcs_coord.separation(tcs_coord_current)
        self.log(f"separation {separation.arcminute }")
        if separation.arcminute > 18 or not self.guide_stars:
            self.tcs_coord = tcs_coord_current
            self.guide_stars = find_guide_stars(self.tcs_coord, sky_angle, self.inst_params, remote_catalog=True)
        else:    
            self.guide_stars = find_guide_stars(tcs_coord_current, sky_angle, self.inst_params, remote_catalog=False, cull_cat=False)
            
        return make_synthetic_image(chip_x=self.guide_stars.chip_xxs,
                                    chip_y=self.guide_stars.chip_yys,
                                    gmag=self.guide_stars.mags,
                                    inst=self.inst_params,
                                    exp_time=exposure.exptime,
                                    seeing_arcsec=self.seeing_arcsec,
                                    sky_flux=self.sky_flux,
                                    defocus=self.defocus)

    async def _expose_internal(self, exposure, **kwargs):

        def rebin(arr, bin):
            new_shape=[int(arr.shape[0]/bin[0]), int(arr.shape[1]/bin[1])]
            shape = (new_shape[0], arr.shape[0] // new_shape[0],
                    new_shape[1], arr.shape[1] // new_shape[1])
            return arr.reshape(shape).sum(-1).sum(1)


        image_type = exposure.image_type

        #if image_type in ["bias", "dark"]:
            #await self.set_shutter(False)
        #else:
            #await self.set_shutter(True)

        data = await self.loop.create_task(self.create_synthetic_image(exposure))

        self.notify(CameraEvent.EXPOSURE_READING)

        # we convert everything to U16 for basecam compatibility
        exposure.data = rebin(data, self._binning).astype(np.uint16)
        exposure.obstime = astropy.time.Time("2000-01-01 00:00:00")
        
#        print(exposure.data.shape)

        #await self.set_shutter(False)

    async def _post_process_internal(self, exposure: Exposure, **kwargs) -> Exposure:
        self.notify(CameraEvent.EXPOSURE_POST_PROCESSING)
        self.notify(CameraEvent.EXPOSURE_POST_PROCESS_DONE)
        return exposure

    #async def _set_shutter_internal(self, shutter_open):
        #self._shutter_position = shutter_open

    #async def _get_shutter_internal(self):
        #return self._shutter_position

    def _status_internal(self):
        return {"temperature": self._temperature, "cooler": math.nan}

    async def _get_binning_internal(self):
        return self._binning

    async def _set_binning_internal(self, hbin, vbin):
        self._binning = (hbin, vbin)

    async def _get_temperature_internal(self):
        return self._temperature

    async def _set_temperature_internal(self, temperature):
        async def change_temperature():
            await asyncio.sleep(0.2)
            self._temperature = temperature

        await cancel_task(self._change_temperature_task)
        self._change_temperature_task = self.loop.create_task(change_temperature())

    async def _get_image_area_internal(self):

        return self._image_area

    async def _set_image_area_internal(self, area=None):
        
        return # not supported

        if area is None:
            self._image_area = (1, self.width, 1, self.height)
        else:
            self._image_area = area

