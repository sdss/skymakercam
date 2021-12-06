# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: proxy_test.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import sys
import uuid
from logging import DEBUG

from clu import AMQPClient, CommandStatus
from test_lvm_actors import LVM

from cluplus.proxy import Proxy, invoke, unpack


amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")

lvm_sci_foc = Proxy(amqpc, LVM.SCI.FOC).start()
lvm_skyw_foc = Proxy(amqpc, LVM.SKYW.FOC).start()
lvm_skye_foc = Proxy(amqpc, LVM.SKYE.FOC).start()
lvm_spec_foc = Proxy(amqpc, LVM.SPEC.FOC).start()

invoke(
    lvm_sci_foc.async_moveToLimit(-1),
    lvm_skye_foc.async_moveToLimit(1),
    lvm_skyw_foc.async_moveToLimit(-1),
    lvm_spec_foc.async_moveToLimit(1),
)

amqpc.log.sh.setLevel(DEBUG)


def callback(reply):
    amqpc.log.debug(f"{CommandStatus.code_to_status(reply.message_code)}"
                    f"{reply.sender}:  {reply.body}")


rc = invoke(
    lvm_sci_foc.async_moveToHome(callback=callback),
    lvm_skye_foc.async_moveToHome(callback=callback),
    lvm_skyw_foc.async_moveToHome(callback=callback),
    lvm_spec_foc.async_moveToHome(callback=callback),
)

amqpc.log.info(f"{unpack(rc, 'AtHome')}")
