#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-10-03
# @Filename: conftest.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import glob
import os
import tempfile

import astropy.time
import numpy
import pytest

import clu.testing
from clu.testing import TestCommand
from sdsstools import read_yaml_file

from basecam import BaseCamera, CameraSystem, Exposure
from basecam.actor import CameraActor
from basecam.events import CameraEvent
from basecam.mixins import CoolerMixIn, ExposureTypeMixIn, ImageAreaMixIn, ShutterMixIn
from basecam.notifier import EventListener
from basecam.utils import cancel_task




class VirtualCamera(
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

    # Sets the internal UID for the camera.
    _uid = "DEV_0815"

    def __init__(self, *args, **kwargs):

        self._shutter_position = False

        self.temperature = 25
        self._change_temperature_task = None

        self.width = 640
        self.height = 480

        self._binning = (1, 1)
        self._image_area = (1, 640, 1, 480)

        self.data = False

        super().__init__(*args, **kwargs)

        self.image_namer.dirname = EXPOSURE_DIR.name

    async def _connect_internal(self, **connection_params):

        return True

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

    async def _expose_internal(self, exposure, **kwargs):

        image_type = exposure.image_type

        if image_type in ["bias", "dark"]:
            await self.set_shutter(False)
        else:
            await self.set_shutter(True)

        self.notify(CameraEvent.EXPOSURE_FLUSHING)
        self.notify(CameraEvent.EXPOSURE_INTEGRATING)

        # Creates a spiral pattern
        xx = numpy.arange(-5, 5, 0.1)
        yy = numpy.arange(-5, 5, 0.1)
        xg, yg = numpy.meshgrid(xx, yy, sparse=True)
        tile = numpy.sin(xg ** 2 + yg ** 2) / (xg ** 2 + yg ** 2)

        # Repeats the tile to match the size of the image.
        data = numpy.tile(
            tile.astype(numpy.uint16),
            (self.height // len(yy) + 1, self.width // len(yy) + 1),
        )
        data = data[0 : self.height, 0 : self.width]

        # For some tests, we want to set out custom data.
        if self.data is not False:
            data = self.data

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

    async def _disconnect_internal(self):

        return True

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


