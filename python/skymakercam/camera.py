# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: camera.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import glob
import os
import tempfile
import pathlib
import math

from logging import INFO, WARNING

import numpy
import json

import astropy.time

from sdsstools import read_yaml_file

from clu.tools import CommandStatus
from clu.model import Model

from basecam import BaseCamera, CameraSystem, Exposure
from basecam.actor import CameraActor
from basecam.events import CameraEvent
from basecam.mixins import CoolerMixIn, ExposureTypeMixIn, ImageAreaMixIn, ShutterMixIn
from basecam.notifier import EventListener
from basecam.utils import cancel_task


from skymakercam.params import load as params_load
from skymakercam.focus_stage import Client as FocusStage
#from skymakercam.xy_stage import Client as XYStage
from skymakercam.pwi import Client as Telescope

from astropy.coordinates import SkyCoord
import astropy.units as u

from skymakercam.starimage import find_guide_stars, make_synthetic_image

__all__ = ['SkymakerCameraSystem', 'SkymakerCamera']


#import re
#def to_camel_case(text):
    #return re.sub('[.](.)', lambda x: x.group(1).upper(), text.capitalize())

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

    def __init__(self, camera_class=None, camera_config=None,
                 include=None, exclude=None, logger=None,
                 log_header=None, log_file=None, verbose=False, ip_list=None):
        super().__init__(camera_class=camera_class, camera_config=camera_config,
                         include=include, exclude=exclude, logger=logger, log_header=log_header,
                         log_file=log_file, verbose=verbose)


    def list_available_cameras(self):
        """ Gather skymaker camera uids.
        :return: a list of cameras.
        :rtype: list
        """

        return [c.camera_params.get("uid") for c in self.cameras]


class SkymakerCamera(
    BaseCamera,
    ExposureTypeMixIn,
    ShutterMixIn,
    CoolerMixIn,
    ImageAreaMixIn,
):
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

        self.config = kwargs['camera_params']
        self.inst_params = params_load(f"skymakercam.params.{self.config_get('instpar', None)}")
        self.inst_params.catalog_path = os.path.expandvars(self.config_get('catalog_path', tempfile.TemporaryDirectory()))
        if not os.path.exists(self.inst_params.catalog_path):
            self.log(f"Creating catalog path: {self.inst_params.catalog_path}", WARNING)
            pathlib.Path(self.inst_params.catalog_path).mkdir(parents=True, exist_ok=True)


        self._tcs = Telescope(self.config_get('tcs', None))
        ra0  =  (13+26./60+47.24/3600)*15   #13:26:47.24
        dec0 = -(47+28./60+46.45/3600)  #−47:28:46.
        self.tcs_coord = SkyCoord(ra=ra0, dec=dec0, unit="deg")
        self.tcs_pa = 0
        self.ra_off = 0.0
        self.dec_off = 0.0

        self._ra_stage = FocusStage('lvm.skye.foc')
        self._dec_stage = FocusStage('lvm.skyw.foc')
        self._xy_stage = XYStage(self.config_get('xy_stage', None))
        
        self.guide_stars = None
        
        self._focus_stage = FocusStage(self.config_get('focus_stage', None))
        self.defocus = self.config_get('default.defocus', 0)
        self.sky_flux = self.config_get('default.sky_flux', 15)
        self.seeing_arcsec = self.config_get('default.seeing_arcsec', 3.5)
        self.exp_time = self.config_get('default.exp_time',5)
        

        self._shutter_position = False

        self.temperature = 25
        self._change_temperature_task = None

        self._gain = self.config_get('default.gain', 1)
        self._binning = self.config_get('default.binning', [1, 1])

        self.log(f"{self.inst_params.chip_size_pix}")
        
        self.width = self.inst_params.chip_size_pix[0]
        self.height = self.inst_params.chip_size_pix[1]

        self._image_area = (1, self.inst_params.chip_size_pix[0], 1, self.inst_params.chip_size_pix[1])

        self.data = False

        self.image_namer.dirname = EXPOSURE_DIR.name

    async def _connect_internal(self, **connection_params):
        self.log(f"connecting ...")
        if not self._focus_stage.is_connected():
            await self._focus_stage.start()

        await self._focus_stage.getDeviceEncoderPosition(unit='UM')

        if not self._ra_stage.is_connected():
            await self._ra_stage.start()

        await self._ra_stage.getDeviceEncoderPosition()

        if not self._dec_stage.is_connected():
            await self._dec_stage.start()

        await self._dec_stage.getDeviceEncoderPosition()

        if not self._tcs.is_connected():
            await self._tcs.start()

        return True

    async def _disconnect_internal(self):
        """Close connection to camera.
        """
        self.tcs.stop()
        self.focus_stage.stop()

    def _status_internal(self):
        return {"temperature": self.temperature, "cooler": 10.0}

    async def _get_temperature_internal(self):
        return self.temperature

    async def _set_temperature_internal(self, temperature):
        async def change_temperature():
            await asyncio.sleep(0.2)
            self.temperature = temperature

        await cancel_task(self._change_temperature_task)
        self._change_temperature_task = self.loop.create_task(change_temperature())

    async def create_synthetic_image(self):
        if not self.guide_stars:
            self.guide_stars = find_guide_stars(self.tcs_coord, self.tcs_pa, self.inst_params, remote_catalog=True)

        ra_off = await self._ra_stage.getDeviceEncoderPosition()
        dec_off = await self._dec_stage.getDeviceEncoderPosition()
        if ra_off != self.ra_off or dec_off != self.dec_off:
             self.log(f"target {self.ra_off} {self.dec_off}")
             tcs_coord = self.tcs_coord
             self.guide_stars = find_guide_stars(tcs_coord.spherical_offsets_by(self.ra_off*u.arcsec, self.dec_off*u.arcsec), self.tcs_pa, self.inst_params, remote_catalog=False, cull_cat=False)
             self.ra_off = ra_off
             self.dec_off = dec_off
            
        self.defocus = (math.fabs(await self._focus_stage.getDeviceEncoderPosition(unit='UM'))/100)**2
        self.log(f"defocus {self.defocus}")

        return make_synthetic_image(chip_x=self.guide_stars.chip_xxs,
                                    chip_y=self.guide_stars.chip_yys,
                                    gmag=self.guide_stars.mags,
                                    inst=self.inst_params,
                                    exp_time=self.exp_time,
                                    seeing_arcsec=self.seeing_arcsec,
                                    sky_flux=self.sky_flux,
                                    defocus=self.defocus)


#    data = create_synthetic_image(self.tcs_coord, self.tcs_pa, self.inst_params, self.guide_stars)

    async def _expose_internal(self, exposure, **kwargs):

        image_type = exposure.image_type

        if image_type in ["bias", "dark"]:
            await self.set_shutter(False)
        else:
            await self.set_shutter(True)

        self.notify(CameraEvent.EXPOSURE_FLUSHING)
        self.notify(CameraEvent.EXPOSURE_INTEGRATING)

        data = await self.loop.create_task(self.create_synthetic_image())

        self.notify(CameraEvent.EXPOSURE_READING)

        exposure.data = data
        exposure.obstime = astropy.time.Time("2000-01-01 00:00:00")

        await self.set_shutter(False)

    async def _post_process_internal(self, exposure: Exposure, **kwargs) -> Exposure:
        self.notify(CameraEvent.EXPOSURE_POST_PROCESSING)
        self.notify(CameraEvent.EXPOSURE_POST_PROCESS_DONE)
        return exposure

    async def _set_shutter_internal(self, shutter_open):
        self._shutter_position = shutter_open

    async def _get_shutter_internal(self):
        return self._shutter_position

    async def _get_binning_internal(self):
        return self._binning

    async def _set_binning_internal(self, hbin, vbin):
        self._binning = (hbin, vbin)

    async def _get_image_area_internal(self):

        return self._image_area

    async def _set_image_area_internal(self, area=None):

        if area is None:
            self._image_area = (1, self.width, 1, self.height)
        else:
            self._image_area = area

