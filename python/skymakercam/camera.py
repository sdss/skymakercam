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
import abc

#from astropy.utils import iers
#iers.conf.auto_download = False 

from logging import DEBUG, WARNING

from typing import cast
from collections import namedtuple

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
from basecam.mixins import CoolerMixIn, ExposureTypeMixIn, ImageAreaMixIn, ShutterMixIn
from basecam.notifier import EventListener
from basecam.utils import cancel_task
from basecam.models import FITSModel, Card, WCSCards, basic_fits_model
from astropy import wcs

from lvmtipo.site import Site
from lvmtipo.siderostat import Siderostat
from lvmtipo.fiber import Fiber
from lvmtipo.target import Target

from skymakercam.params import load as params_load
from cluplus.proxy import Proxy, ProxyPartialInvokeException, invoke, unpack

from astropy.coordinates import SkyCoord, Angle
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

class GainMixIn(object, metaclass=abc.ABCMeta):
    """A mixin that provides manual control over the camera gain."""

    @abc.abstractmethod
    async def _set_gain_internal(self, gain):
        """Internal method to set the gain."""

        raise NotImplementedError

    @abc.abstractmethod
    async def _get_gain_internal(self):
        """Internal method to get the gain."""

        raise NotImplementedError

    async def set_gain(self, gain):
        """Set the gain of the camera."""

        return await self._set_gain_internal(gain)

    async def get_gain(self):
        """Gets the gain of the camera."""

        return await self._get_gain_internal()


Point = namedtuple('Point', ['x0', 'y0'])
Size = namedtuple('Size', ['wd', 'ht'])
Rect = namedtuple('Rect', ['x0', 'y0', 'wd', 'ht'])

#class ScraperParamMixIn(object):
    #"""A mixin that provides manual control over the camera gain."""

    #def __init__(self, *args, camera_params = None, **kwargs):
        #from sdsstools.logger import get_logger
        #logger = get_logger("ScraperParamCards")
##        logger.warning(f"xxxxxxxxxxxxxxxxx {camera_params}")
        #self.scraper_store = camera_params.get('scraper_store', {})

    #async def set(self, key, value):
        #"""Seta the  param of the camera."""
        #pass

    #async def get(self, key):
        #"""Gets the param of the camera."""
        #return self.scraper_store.get(key, None).val


#def mixedomatic(cls):
    #""" Mixed-in class decorator. """
    #classinit = cls.__dict__.get('__init__')  # Possibly None.
    
    ## Define an __init__ function for the class.
    #def __init__(self, *args, **kwargs):
        ## Call the __init__ functions of all the bases.
        #for base in cls.__bases__:
            #if base.__dict__.get('__init__'):
                #print(base)
                #base.__init__(self, *args, **kwargs)

        ## Also call any __init__ function that was in the class.
        #if classinit:
            #classinit(self, *args, **kwargs)

    ## Make the local function the class's __init__.
    #setattr(cls, '__init__', __init__)
    #return cls

#@mixedomatic
class SkymakerCamera(BaseCamera, ExposureTypeMixIn, ImageAreaMixIn, CoolerMixIn, GainMixIn):
    """A virtual camera that does not require hardware.

    This class is mostly intended for testing and development. It behaves
    in all ways as a real camera with pre-defined responses that depend on the
    input parameters.

    """

    #def config_get(self, key, default=None):
        #""" DOESNT work for keys with dots !!! """
        #def g(config, key, d=None):
            #k = key.split('.', maxsplit=1)
            #c = config.get(k[0] if not k[0].isnumeric() else int(k[0]))  # keys can be numeric
            #return d if c is None else c if len(k) < 2 else g(c, k[1], d) if type(c) is dict else d
        #return g(self.config, key, default)


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.logger.sh.setLevel(DEBUG)
        self.logger.sh.formatter = StreamFormatter(fmt='%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d: \033[1m%(message)s\033[21m') 


#        self.actor = self.params.get('actor', None)
        self.scraper_store = self.camera_params.get('scraper_store', {})

        self.inst_params = params_load(f"skymakercam.params.{self.camera_params.get('instpar', None)}")
        self.inst_params.catalog_path = os.path.expandvars(self.camera_params.get('catalog_path', tempfile.TemporaryDirectory()))
        if not os.path.exists(self.inst_params.catalog_path):
            self.log(f"Creating catalog path: {self.inst_params.catalog_path}", WARNING)
            pathlib.Path(self.inst_params.catalog_path).mkdir(parents=True, exist_ok=True)

        self.tcs_coord = SkyCoord(ra=0.0*u.deg, dec=90.0*u.deg)
        self.tcs_pa = 0.0

        self.guide_stars = None
        
        self.sky_flux = self.camera_params.get('sky_flux', 15)
        self.seeing_arcsec = self.camera_params.get('seeing_arcsec', 3.5)
#        self.exp_time = self.camera_params.get('default.exp_time',5)
        
        self.site = self.camera_params.get('site', "LCO")
        self.sid = Siderostat()
        self.geoloc = Site(name = self.site)

        self.temperature = 25
        self._changetemperature_task = None

        self.pixsize = self.camera_params.get('pixsize', 0.0)
        self.flen = self.camera_params.get('flen', 0.0)
        # pixel scale per arcseconds is focal length *pi/180 /3600
        # = flen * mm *pi/180 /3600
        # = flen * um *pi/180 /3.6, so in microns per arcsec...
        self.pixscale = math.radians(self.flen)/3.6
        self.arcsec_per_pix = self.pixsize / self.pixscale
        self.log(f"arcsec_per_pix {self.arcsec_per_pix}")
        # degrees per pixel is arcseconds per pixel/3600 = (mu/pix)/(mu/arcsec)/3600
        self.degperpix =  self.pixsize/self.pixscale/3600.0

        self.gain = self.camera_params.get('gain', 1)
        self._focus_offset = self.camera_params.get('focus_offset', 42)

        self.cam_type = "skymakercam"
        self.cam_temp = -1

        self.log(f"{self.inst_params.chip_size_pix}")
        
        self.detector_size = Size(*self.inst_params.chip_size_pix)
        self.log(f"{self.detector_size}")

        self.binning = self.camera_params.get('binning', [1, 1])

        self.region_bounds = Size(self.detector_size.wd / self.binning[0], self.detector_size.ht / self.binning[1])
        self.image_area = Rect(0, 0, self.region_bounds.wd, self.region_bounds.ht)

        self.data = None


    async def _connect_internal(self, **connection_params):
        self.logger.debug(f"connecting ...")
        
        #await self._tcs.start()
        #await self._focus_stage.start()
        #await self._kmirror.start()

        return True

    async def _disconnect_internal(self):
        """Close connection to camera.
        """
        self.logger.debug("disconnect")
        #await self._tcs.client.stop()
        #await self._focus_stage.client.stop()
        #await self._kmirror.client.stop()

    async def create_synthetic_image(self, exposure, ra_h=0.0, dec_d=90.0, pa_d=0.0, km_d=0.0, foc_um=0.0, **kwargs):

        self.log(f"focus um {foc_um}")
        defocus = math.fabs((foc_um+self._focus_offset)/100)**2
        self.log(f"defocus {defocus}")

        self.log(f"kmirror angle (deg): {km_d}")

        tcs_coord_current = SkyCoord(ra=ra_h*u.hour, dec=dec_d*u.deg)
        self.log(f"SkyCoord: {tcs_coord_current}")

        mathar_angle_d = math.degrees(self.sid.fieldAngle(self.geoloc, Target(tcs_coord_current), None))
        self.log(f"mathar angle (deg): {mathar_angle_d}")

        sky_angle = km_d - mathar_angle_d
        self.log(f"sky angle (deg): {sky_angle} {pa_d}")

        separation = self.tcs_coord.separation(tcs_coord_current)
        self.log(f"separation {separation.arcminute }")
        if separation.arcminute > 18 or not self.guide_stars:
            self.tcs_coord = tcs_coord_current
            self.guide_stars = find_guide_stars(self.tcs_coord, sky_angle, self.inst_params, remote_catalog=True)
        else:    
            self.guide_stars = find_guide_stars(tcs_coord_current, sky_angle, self.inst_params, remote_catalog=False, cull_cat=False)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: make_synthetic_image(
                chip_x=self.guide_stars.chip_xxs,
                chip_y=self.guide_stars.chip_yys,
                gmag=self.guide_stars.mags,
                inst=self.inst_params,
                exp_time=exposure.exptime,
                seeing_arcsec=self.seeing_arcsec,
                sky_flux=self.sky_flux,
                defocus=defocus
            )
        )
        

    async def _expose_internal(self, exposure, **kwargs):

        def rebin(arr, bin):
            new_shape=[int(arr.shape[0]/bin[0]), int(arr.shape[1]/bin[1])]
            shape = (new_shape[0], arr.shape[0] // new_shape[0],
                    new_shape[1], arr.shape[1] // new_shape[1])
            return arr.reshape(shape).sum(-1).sum(1)

        exposure.scraper_store = self.scraper_store.copy()

        if kmirror_angle := kwargs.get("km_d", None):
            exposure.scraper_store.set("km_d", kmirror_angle)

        if ra_h := kwargs.get("ra_h", None):
            if dec_d := kwargs.get("dec_d", None):
                exposure.scraper_store.set("ra_h", ra_h)
                exposure.scraper_store.set("dec_d", dec_d)

        self.notify(CameraEvent.EXPOSURE_INTEGRATING)

        data = await self.create_synthetic_image(exposure, **exposure.scraper_store)

#        self.notify(CameraEvent.EXPOSURE_READING)

        # we convert everything to U16 for basecam compatibility
        exposure.data = rebin(data, self.binning).astype(np.uint16)
#        exposure.obstime = astropy.time.Time("2000-01-01 00:00:00")
        exposure.obstime = astropy.time.Time.now()

    async def _post_process_internal(self, exposure: Exposure, **kwargs) -> Exposure:
        self.notify(CameraEvent.EXPOSURE_POST_PROCESSING)
        self.notify(CameraEvent.EXPOSURE_POST_PROCESS_DONE)
        return exposure

    def _status_internal(self):
        return {"temperature": self.temperature, "cooler": math.nan}

    async def _get_binning_internal(self):
        return self.binning

    async def _set_binning_internal(self, hbin, vbin):
        self.region_bounds = Size(self.detector_size.wd / hbin, self.detector_size.ht / vbin)
        self.image_area = Rect(0, 0, self.region_bounds.wd, self.region_bounds.ht)
        self.binning = [hbin, vbin]

    async def _get_temperature_internal(self):
        return self.temperature

    async def _set_temperature_internal(self, temperature):
        async def changetemperature():
            await asyncio.sleep(0.2)
            self.temperature = temperature

        await cancel_task(self._changetemperature_task)
        self._changetemperature_task = self.loop.create_task(changetemperature())

    async def _get_image_area_internal(self):

        return self.image_area

    async def _set_image_area_internal(self, area=None):
        return # not supported

    async def _set_gain_internal(self, gain):
        """Internal method to set the gain."""
        self.gain = gain

    async def _get_gain_internal(self):
        """Internal method to get the gain."""
        self.log(f"scraper data {self.scraper_store.data}")
        return self.gain
