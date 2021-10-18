import os

import click
from click_default_group import DefaultGroup
from clu.tools import cli_coro

from sdsstools.daemonizer import DaemonGroup

from proto.actor.actor import ProtoActor


@click.group(cls=DefaultGroup, default="actor", default_if_no_args=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the user configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Debug mode. Use additional v for more details.",
)
@click.pass_context
def proto(ctx, config_file, verbose):
    """proto controller"""

    ctx.obj = {"verbose": verbose, "config_file": config_file}


@proto.group(cls=DaemonGroup, prog="pwi_actor", workdir=os.getcwd())
@click.pass_context
@cli_coro
async def actor(ctx):
    """Runs the actor."""

    default_config_file = os.path.join(os.path.dirname(__file__), "etc/proto.yml")
    config_file = ctx.obj["config_file"] or default_config_file

    proto_obj = ProtoActor.from_config(config_file, verbose=ctx.obj["verbose"])

    await proto_obj.start()
    await proto_obj.run_forever()

