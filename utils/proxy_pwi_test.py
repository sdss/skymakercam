# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: proxy_test.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import uuid
import sys

from clu import AMQPClient, CommandStatus
from skymakercam.proxy import Proxy, ProxyException, ProxyPlainMessagException, invoke, unpack

import asyncio


async def test_simple_pwi_ctrl():
    
    consumer = "lvm.sci.pwi"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_pwi=Proxy(consumer, amqpc)
#    amqpc.log.warning(sys.argv[0])
        

    try:
        
        await lvm_sci_pwi.setConnected(True)
        
        await lvm_sci_pwi.setEnabled(True)
        
        isTracking = await unpack(lvm_sci_pwi.setTracking(True))
        assert isTracking == True
        
        # lets define a callback for status updates.
        def callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")

        await lvm_sci_pwi.park(callback=callback)
        
        await lvm_sci_pwi.gotoRaDecJ2000(10, 20, callback=callback)
        
        # we do use send_command/click options without --, it will be added internally
        await lvm_sci_pwi.offset(ra_add_arcsec=10)
        
    except Exception as e:
        amqpc.log.warning(f"Exception: {e}")

asyncio.run(test_simple_pwi_ctrl())

