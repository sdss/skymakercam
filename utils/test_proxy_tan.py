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


async def test_single_param_return():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    amqpc.log.warning(sys.argv[0])
        
    amqpc.log.warning(f'#1: {await unpack(lvm_sci_foc.isReachable())}')
    pos, unit = await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))
    amqpc.log.warning(f'#2: {pos}, {unit}')

    amqpc.log.warning(f'#3: {(await invoke(lvm_sci_foc.getPosition())).Position}')

    pos = await invoke(lvm_sci_foc.getDeviceEncoderPosition("UM"))
    amqpc.log.warning(f'#4: {pos.DeviceEncoderPosition}')

    pos = await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))
    amqpc.log.warning(f'#5 {pos}')

    amqpc.log.warning(f'#6: {await invoke(lvm_sci_foc.getNamedPosition(1))}')

    try:
        await invoke(lvm_sci_foc.getNamedPosition(1), lvm_sci_foc.getNamedPosition(10), lvm_sci_foc.getNamedPosition(12))
    except ProxyException as e:
        amqpc.log.warning(f"Exception: {e}")

    try:
        await invoke(lvm_sci_foc.getNamedPosition(10))
    except Exception as e:
        amqpc.log.warning(f"Exception: {e}")

    try:
        await unpack(lvm_sci_foc.getDeviceEncoderPositin("UM"))
    except Exception as e:
        amqpc.log.warning(f"Exception: {e}")


asyncio.run(test_single_param_return())


async def test_single_param_return():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    
    amqpc.log.warning(f'#1: {(await invoke(lvm_sci_foc.isReachable())).Reachable}')
    
    amqpc.log.warning(f'#2: {await unpack(lvm_sci_foc.isReachable())}')
    amqpc.log.warning(f'#3: {await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))}')
    
asyncio.run(test_single_param_return())


async def test_callback_and_blocking():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    
    def toHome_callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    await lvm_sci_foc.moveToHome(callback=toHome_callback)
    
    def toLimit_callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    await lvm_sci_foc.moveToLimit(-1, callback=toLimit_callback)



asyncio.run(test_callback_and_blocking())

async def test_tasks():
    
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy("lvm.sci.foc", amqpc)
    lvm_skye_foc=Proxy("lvm.skye.foc", amqpc)
    lvm_skyw_foc=Proxy("lvm.skyw.foc", amqpc)
    lvm_spec_foc=Proxy("lvm.spec.foc", amqpc)
    
    
    ret = await invoke(
            lvm_sci_foc.moveToHome(),
            lvm_skye_foc.moveToHome(),
            lvm_skyw_foc.moveToHome(),
            lvm_spec_foc.moveToHome(),
          )
    amqpc.log.warning(f"{ret}")
    
    ret = await invoke(
                lvm_sci_foc.moveToLimit(-1),
                lvm_skye_foc.moveToLimit(-1),
                lvm_skyw_foc.moveToLimit(-1),
                lvm_spec_foc.moveToLimit(-1),
            )
    amqpc.log.warning(f"{ret}")

asyncio.run(test_tasks())

async def test_callback_and_parallel_classic():
    
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy("lvm.sci.foc", amqpc)
    lvm_skye_foc=Proxy("lvm.skye.foc", amqpc)
    
    def toHome_callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    lvm_sci_foc_future = await lvm_sci_foc.moveToHome(callback=toHome_callback, blocking=False)
    lvm_skye_foc_future = await lvm_skye_foc.moveToHome(callback=toHome_callback, blocking=False)
    await lvm_sci_foc_future
    await lvm_skye_foc_future
    
    def toLimit_callback(reply): amqpc.log.warning(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    lvm_sci_foc_future = await lvm_sci_foc.moveToLimit(-1, callback=toLimit_callback, blocking=False)
    lvm_skye_foc_future = await lvm_skye_foc.moveToLimit(-1, callback=toLimit_callback, blocking=False)
    await lvm_sci_foc_future
    await lvm_skye_foc_future
    

asyncio.run(test_callback_and_parallel_classic())

async def test_callback_and_gather_raw():
    
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy("lvm.sci.foc", amqpc)
    lvm_skye_foc=Proxy("lvm.skye.foc", amqpc)
    lvm_skyw_foc=Proxy("lvm.skyw.foc", amqpc)
    lvm_spec_foc=Proxy("lvm.spec.foc", amqpc)
    
    
    ret = await asyncio.gather(
            await lvm_sci_foc.moveToHome(blocking=False),
            await lvm_skye_foc.moveToHome(blocking=False),
            await lvm_skyw_foc.moveToHome(blocking=False),
            await lvm_spec_foc.moveToHome(blocking=False),
          )
    amqpc.log.warning(f"{ret}")
    
    ret = await asyncio.gather(
                    await lvm_sci_foc.moveToLimit(-1, blocking=False),
                    await lvm_skye_foc.moveToLimit(-1, blocking=False),
                    await lvm_skyw_foc.moveToLimit(-1, blocking=False),
                    await lvm_spec_foc.moveToLimit(-1, blocking=False),
                  )
    amqpc.log.warning(f"{ret}")

asyncio.run(test_callback_and_gather_raw())





