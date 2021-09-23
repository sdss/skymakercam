from asyncudp_simple import *

async def asend():
    width=500
    height=80 
    raw_data = np.arange(width * height, dtype=float)
    asyncsend = AsyncSend(max_data=20000)
    await asyncsend.start()
    while True:
        print(f"send {width}x{height}")
        await asyncsend.send(raw_data, width, height)
        await asyncio.sleep(1.0)
    asend.stop()

asyncio.run(asend())


