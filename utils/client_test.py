# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: base_client.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import uuid
import sys

from clu import AMQPClient, CommandStatus
from skymakercam.client import Proxy, invoke, unpack

import asyncio


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
    print(ret)
    
    ret = await invoke(
                lvm_sci_foc.moveToLimit(-1),
                lvm_skye_foc.moveToLimit(-1),
                lvm_skyw_foc.moveToLimit(-1),
                lvm_spec_foc.moveToLimit(-1),
            )
    print(ret)

asyncio.run(test_tasks())


async def test_single_param_return():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    print(sys.argv[0])
        
    print(f'#2: {await unpack(lvm_sci_foc.isReachable())}')
    print(f'#2: {await invoke(lvm_sci_foc.getPosition())}')
    pos, unit = await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))
    print(f'#2: {pos, unit}')

    pos = await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))
    print(f'#2: {pos}')


asyncio.run(test_single_param_return())


async def test_single_param_return():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    
    print(f'#1: {(await invoke(lvm_sci_foc.isReachable()))["Reachable"]}')
    
    print(f'#2: {await unpack(lvm_sci_foc.isReachable())}')
    print(f'#2: {await unpack(lvm_sci_foc.getDeviceEncoderPosition("UM"))}')
    print(f'#2: {await unpack(lvm_sci_foc.getDeviceEncoderPositin("UM"))}')
    
asyncio.run(test_single_param_return())


async def test_callback_and_blocking():
    
    consumer = "lvm.sci.foc"
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy(consumer, amqpc)
    
    def toHome_callback(reply): print(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    await lvm_sci_foc.moveToHome(callback=toHome_callback)
    
    def toLimit_callback(reply): print(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    await lvm_sci_foc.moveToLimit(-1, callback=toLimit_callback)



asyncio.run(test_callback_and_blocking())


async def test_callback_and_parallel():
    
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    await amqpc.start()
    
    lvm_sci_foc=Proxy("lvm.sci.foc", amqpc)
    lvm_skye_foc=Proxy("lvm.skye.foc", amqpc)
    
    def toHome_callback(reply): print(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    lvm_sci_foc_future = await lvm_sci_foc.moveToHome(callback=toHome_callback, blocking=False)
    lvm_skye_foc_future = await lvm_skye_foc.moveToHome(callback=toHome_callback, blocking=False)
    await lvm_sci_foc_future
    await lvm_skye_foc_future
    
    def toLimit_callback(reply): print(f"Reply: {CommandStatus.code_to_status(reply.message_code)} {reply.body}")
    lvm_sci_foc_future = await lvm_sci_foc.moveToLimit(-1, callback=toLimit_callback, blocking=False)
    lvm_skye_foc_future = await lvm_skye_foc.moveToLimit(-1, callback=toLimit_callback, blocking=False)
    await lvm_sci_foc_future
    await lvm_skye_foc_future
    

asyncio.run(test_callback_and_parallel())


async def test_callback_and_gather():
    
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
    print(ret)
    
    ret = await asyncio.gather(
                    await lvm_sci_foc.moveToLimit(-1, blocking=False),
                    await lvm_skye_foc.moveToLimit(-1, blocking=False),
                    await lvm_skyw_foc.moveToLimit(-1, blocking=False),
                    await lvm_spec_foc.moveToLimit(-1, blocking=False),
                  )
    print(ret)

asyncio.run(test_callback_and_gather())





