from transitions.extensions.asyncio import AsyncMachine
import asyncio

class Dancer:
    
    states = ['start', 'left_food_left', 'left', 'right_food_right']
    
    def __init__(self, name, beat):
        self.my_name = name
        self.my_beat = beat
        self.moves_done = 0
    
    async def on_enter_start(self):
        self.moves_done += 1
    
    async def wait(self):
        print(f'{self.my_name} stepped {self.state}')
        await asyncio.sleep(self.my_beat)
    
    async def dance(self):
        while self.moves_done < 5:
            await self.step()
      
dancer1 = Dancer('Tick', 1)
dancer2 = Dancer('Tock', 2)

m = AsyncMachine(model=[dancer1, dancer2], states=Dancer.states, initial='start', after_state_change='wait')
m.add_ordered_transitions(trigger='step')

async def run():
    await asyncio.gather(dancer1.dance(), dancer2.dance())
    
asyncio.run(run())
