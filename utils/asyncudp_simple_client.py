from asyncudp_simple import *

async def arecv():
    asyncrecv = AsyncRecv(max_data=20000)
    await asyncrecv.start()
    while True:
        data, width, height = await asyncrecv.recv()
        raw_data = np.arange(width * height, dtype=float)
        assert(np.array_equal(raw_data, data))
        print(f"received {width}x{height}")
    asyncrecv.stop()

asyncio.run(arecv())
