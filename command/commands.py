import constants
import helpers

from collections import namedtuple

CommandsTuple = namedtuple('CommandsTuple', 'commands, function')

async def commands(message, context):
    """Returns a list of commands to the user."""
    global COMMANDS
    command_tuples = {}
    for key, value in constants.COMMANDS.items():
        if id(value) not in command_tuples:
            command_tuples[id(value)] = CommandsTuple([], value)
        command_tuples[id(value)].commands.append(key)
    lines = []
    for cmd_tuple in command_tuples.values():
        commands = str.ljust(', '.join(cmd_tuple.commands), 30)
        doc = cmd_tuple.function.__doc__
        lines.append("%s- %s" % (commands, doc))
    lines.sort()
    response = '```\n' + '\n'.join(lines) + '\n```'
    helpers.send_message(message.channel, response)