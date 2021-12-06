# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: test_proxy_pwi.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import sys
import uuid

from logging import DEBUG

from clu import AMQPClient, CommandStatus
from test_lvm_actors import LVM

from cluplus.proxy import Proxy, invoke, unpack


amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")

lvm_sci_pwi = Proxy(amqpc, LVM.SCI.PWI).start()

lvm_sci_pwi.setConnected(True)

isEnabled = unpack(lvm_sci_pwi.setEnabled(True), "is_enabled")
assert isEnabled == True
        
isTracking = unpack(lvm_sci_pwi.setTracking(True))
assert isTracking == True

amqpc.log.sh.setLevel(DEBUG)        
        
def callback(reply): 
    amqpc.log.warning(f"{CommandStatus.code_to_status(reply.message_code)} {reply.body}")

lvm_sci_pwi.gotoRaDecJ2000(10, 20, callback=callback)

lvm_sci_pwi.offset(ra_add_arcsec = 10)
        

