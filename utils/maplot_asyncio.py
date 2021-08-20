import matplotlib.pyplot as plt
import asyncio
import matplotlib.cbook
import warnings
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)


class DataAnalysis():
    def __init__(self):
        # asyncio so we can plot data and run simulation in parallel
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.plot_reward())
        finally:
            loop.run_until_complete(
                loop.shutdown_asyncgens())  # see: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.AbstractEventLoop.shutdown_asyncgens
            loop.close()
            # keep plot window open
            plt.show()

    async def async_generator(self):
        for i in range(3):
            await asyncio.sleep(.4)
            yield i * i

    async def plot_reward(self):
        #plt.ion()  # enable interactive mode

        # receive dicts with training results
        async for i in self.async_generator():
            print(i)
            # update plot
            if i == 0:
                plt.plot([2, 3, 4])
            elif i == 1:
                plt.plot([3, 4, 5])

            #plt.draw()
            plt.pause(0.1)
            #await asyncio.sleep(0.4)


if __name__ == '__main__':
    da = DataAnalysis()

Notes
