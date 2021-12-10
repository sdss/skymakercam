
import os, sys, inspect, io
import logging

from transitions.extensions.states import Timeout, Error, Tags, add_state_features
from transitions.extensions.factory import HierarchicalGraphMachine as Machine

from functools import partial

import matplotlib.pyplot as plt
import matplotlib.image as mpimg



@add_state_features(Timeout, Error)
class CustomStateMachine(Machine):
    pass

class Guider(object):
    def __init__(self):
        self.autostart_guiding = False
        self.have_nominal_focus = False
    def do_proceed(self):
        self.next()
    def do_connect_hw(self):
        pass
    def do_disconnect_hw(self):
        pass
    def do_check_focus(self):
        print("check focus")
        return True
    def do_choose_focus(self, **kwargs):
        print(f"focus sel {kwargs}")
        if 'nominal' in kwargs or self.have_nominal_focus:
            self._focus_nominal()
            return
        self._focus_refocus()
    def do_choose_aquire(self, **kwargs):
        print(f"aquire_sel {kwargs}")
        if 'guidestars' in kwargs:
            self._list()
        self._search_guidestars()
        pass
    def do_auto_start(self, autostart_guiding=True, **kwargs):
        print(f"auto_start {autostart_guiding} {kwargs}")
        if autostart_guiding: 
            self.start()
        pass
    def do_nominal_focus(self, **kwargs):
        print(f"nominal_focus {kwargs}")
        self._focus_done()
        self.show_graph()
        pass
    def do_refocus_focus(self, **kwargs):
        print(f"refocus_focus {kwargs}")
        self.have_nominal_focus = True
        self._focus_done()
        self.show_graph()
        pass
    def to_online(self, **kwargs):
        print(f"to online {kwargs}")
        self.to('online')
        pass
    def show_graph(self, **kwargs):
        stream = io.BytesIO()
        self.get_graph(**kwargs).draw(stream, prog='dot', format='png')
        stream.seek(0)
        im = mpimg.imread(stream, format="png")
        plt.tight_layout()
        plt.imshow(im)
        plt.pause(.01)


extra_args = dict(auto_transitions=False, queued=True, initial='offline', title='Guider Prototype Statemachine',
                  show_conditions=True, show_state_attributes=True)

states = [{'name': 'offline', 'on_enter': ['do_disconnect_hw'], 'on_exit': ['do_connect_hw'], 'timeout': 1, 'on_timeout': 'connect'},
          {'name': 'online'},
          {'name': 'focus',
                'children':[{'name': 'nominal'},
                            {'name': 'refocus'}],},
          {'name': 'aquisition',
                'children':[{'name': 'search'},
                            {'name': 'select'}],},
          {'name': 'guiding',
                'children':[{'name': 'pause'},
                            {'name': 'guide'}],}
         ]

transitions = [
  ['connect', 'offline', 'online'],
  ['disconnect', 'online', 'offline'],
  {'trigger': 'start', 'source': 'online', 'dest': 'focus', 'after': 'do_auto_start'},
  {'trigger': 'start', 'source': 'focus', 'dest': 'aquisition', 'after': 'do_auto_start'},
  {'trigger': 'start', 'source': 'aquisition', 'dest': 'guiding', 'after': 'do_auto_start'},
  ['stop', ['guiding'], 'online'],

  {'trigger': 'focus', 'source': 'online', 'dest': 'focus', 'after': 'do_choose_focus'},
  {'trigger': '_focus_nominal', 'source': 'focus', 'dest': 'focus_nominal', 'after': 'do_nominal_focus'},
  {'trigger': '_focus_refocus', 'source': 'focus', 'dest': 'focus_refocus', 'after': 'do_refocus_focus'},
  {'trigger': '_focus_done', 'source': ['focus_nominal', 'focus_refocus'], 'dest': 'focus', 'after': 'done'},
  {'trigger': 'done', 'source': 'focus', 'dest': 'online'},

  {'trigger': 'aquire', 'source': 'online', 'dest': 'aquisition', 'after': 'do_choose_aquire'},
  {'trigger': '_search_guidestars', 'source': 'aquisition', 'dest': 'aquisition_search'},
  {'trigger': '_next', 'source': 'aquisition_search', 'dest': 'aquisition_select', 'after': '_list'},
  {'trigger': '_list_guidestars', 'source': 'aquisition', 'dest': 'aquisition_select', 'after': '_list'},

  {'trigger': 'guide', 'source': 'online', 'dest': 'guide', 'after': 'start'},
  {'trigger': 'start',  'source': 'guiding', 'dest': 'guiding_guide'},
  ['resume', 'guiding_pause', 'guiding_guide'],
  ['pause', 'guiding_guide', 'guiding_pause'],
]


logging.basicConfig(level=logging.INFO)

model = Guider()
machine = CustomStateMachine(model=model, states=states, transitions=transitions, after_state_change=[model.show_graph], **extra_args)

model.connect()

        
