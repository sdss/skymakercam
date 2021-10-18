# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de
# @Date: 2021-07-06
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import click
from clu.command import Command

from . import parser


@parser.command()
@click.pass_context
def commands(ctx, *args):
    """Shows the help."""

    print(type(ctx.command))
    print(type(ctx.command.commands))

    print(ctx.command.commands)
    print(ctx.command.commands['bigdata'].name)
    command = args[0]

    # The parser_command arrives wrapped in quotes to make sure is a single
    # value. Strip it and unpack it in as many groups and commands as needed.
#    parser_command = parser_command.strip('"').split()

    command.info("commands")

    return command.finish()

    #help_lines = ""
    #command_name = args[0].actor.name  # Actor name

    ## Gets the help lines for the command group or for a specific command.
    #if len(parser_command) > 0:

        #ctx_commands = ctx.command.commands

        #for ii in range(len(parser_command)):
            #ctx_command_name = parser_command[ii]
            #command_name += f" {ctx_command_name}"
            #if ctx_command_name not in ctx_commands:
                #return command.fail(error=f"command {ctx_command_name} not found.")
            #ctx_command = ctx_commands[ctx_command_name]
            #if ii == len(parser_command) - 1:
                ## This is the last element in the command list
                ## so we want to actually output this help lines.
                #help_lines = ctx_command.get_help(ctx)
            #else:
                #ctx_commands = ctx_command.commands

    #else:

        #help_lines: str = ctx.get_help()

    #message = []
    #for line in help_lines.splitlines():
        ## Remove the parser name.
        #match = re.match(r"^Usage: ([A-Za-z-_]+)", line)
        #if match:
            #line = line.replace(match.groups()[0], command_name)

        #message.append(line)

    #if isinstance(command.actor, (actor.AMQPActor, actor.JSONActor)):
        #return command.finish(help=message)
    #else:
        #for line in message:
            #command.warning(help=line)
        #return command.finish()

