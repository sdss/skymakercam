# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de
# @Date: 2021-07-06
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
from contextlib import suppress

from clu.actor import AMQPActor
from cluplus.configloader import Loader

from proto.actor.commands import parser as proto_command_parser


__all__ = ["ProtoActor"]


class ProtoActor(AMQPActor):
    """PWI actor.
    """

    parser = proto_command_parser
    
    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        

    async def start(self):
        await super().start()

        assert len(self.parser_args) == 0
       
        try:
            self.log.debug(f"Start proto ...")


        except Exception as ex:
            self.log.error(f"Unexpected exception {type(ex)}: {ex}")

        self.log.debug("Start done")

    async def stop(self):
        return super().stop()

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        """Creates an actor from hierachical configuration file(s)."""

        instance = super(ProtoActor, cls).from_config(config, loader=Loader, *args, **kwargs)

        if kwargs["verbose"]:
            instance.log.fh.setLevel(0)
            instance.log.sh.setLevel(0)

        instance.log.debug("Hello world")

        assert isinstance(instance, ProtoActor)
        assert isinstance(instance.config, dict)
        
        return instance
