# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-11-19
# @Filename: test_00_misc.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import pytest
import asyncio
import logging
import uuid

from cluplus import __version__
from cluplus.proxy import Proxy, unpack


def test_proxy_null_unpack():

    assert(unpack({}) == None)

    
