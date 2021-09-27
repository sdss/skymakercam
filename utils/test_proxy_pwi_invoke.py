# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: proxy_test.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import uuid
import sys

from clu import AMQPClient, CommandStatus
from cluplus.proxy import Proxy, ProxyException, ProxyPlainMessagException, invoke, unpack

import asyncio

async def test_proxy_pwi_invoke():
    amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_pwi=Proxy("lvm.sci.pwi", amqpc)
    lvm_skye_pwi=Proxy("lvm.skye.pwi", amqpc)
    lvm_skyw_pwi=Proxy("lvm.skyw.pwi", amqpc)
    lvm_spec_pwi=Proxy("lvm.spec.pwi", amqpc)
    
    try:
        await invoke(
                 lvm_sci_pwi.setConnected(True),
                 lvm_skye_pwi.setConnected(True),
                 lvm_skyw_pwi.setConnected(True),
                 lvm_spec_pwi.setConnected(True),
              )
        
        await invoke(
                 lvm_sci_pwi.setEnabled(True),
                 lvm_skye_pwi.setEnabled(True),
                 lvm_skyw_pwi.setEnabled(True),
                 lvm_spec_pwi.setEnabled(True),
              )
        
        # lets define a callback for status updates.
        def callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
        
        rc = await invoke(
                 lvm_sci_pwi.gotoRaDecJ2000(10, 20, callback=callback),
                 lvm_skye_pwi.gotoRaDecJ2000(10, 20),
                 lvm_skyw_pwi.gotoRaDecJ2000(10, 20),
                 lvm_spec_pwi.gotoRaDecJ2000(10, 20),
              )
        
        # we do use send_command/click options without --, it will be added internally
        await lvm_sci_pwi.offset(ra_add_arcsec=10)
        
    except Exception as e:
        amqpc.log.warning(f"Exception: {e}")



asyncio.run(test_proxy_pwi_invoke())

