# rolebot.py

import os
import re
import math
import discord
import random
from collections import namedtuple
from discord import channel
from discord.utils import CachedSlotProperty

from dotenv import load_dotenv
from django.shortcuts import render, redirect
from discord.ext import commands

load_dotenv()
# define necessary environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('SERVER_NAME')
SERVER_ID = os.getenv('SERVER_ID')
CHANNEL_ID = os.getenv('DRAFT_CHANNEL_ID')

# globals
GUILD = None
CHANNEL = None
CAPTAINS = dict()
ROLES = ["Top", "Jungle", "Mid", "Support", "Bot"]
COMMANDS = {}

DISCORD_ID_PATTERN = r'<@!([0-9]*)>'

# print message when bot connects to disc client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents) #define client

CommandsTuple = namedtuple('CommandsTuple', 'commands, function')

###================================= HELPERS ========================================###

def shuffle(array):
    tmp_array = list(array)
    for i in range(len(array)):
        j = math.floor(random.random() * (i + 1))
        tmp_array[i], tmp_array[j] = tmp_array[j], tmp_array[i]
    return tmp_array

def convert_ids_to_nicks(team):
    nicks = []
    for name in team:
        if isinstance(name, int):
            nicks.append(GUILD.get_member(name).nick)
        else:
            nicks.append(name)
    return nicks

def you_are_dummy_text(message, name):
    return message.channel.send('%s you\'re not a captain you idiot.' % name)

async def members_list(request):
    channel = client.get_channel(877295337012879392)
    curMembers = []
    for member in channel.members:
        curMembers.append(member)
    inhouseMembers = render(request, "discordTool/discordTool.html", {
        'members_list': curMembers,})
    return inhouseMembers

###================================= COMMANDS ========================================###

async def commands_command(message):
    """Returns a list of commands to the user."""
    global COMMANDS
    command_tuples = {}
    for key, value in COMMANDS.items():
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
    await message.channel.send(response)

async def captain_command(message):
    """Assigns the caller as a captain."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        await message.channel.send('You\'re already a captain ya dunce')
    else:
        CAPTAINS[message.author.id] = []
        await message.channel.send('%s you have created a team.' % message.author.nick)

async def removecaptain_command(message):
    """Removes the caller as a captain."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        del CAPTAINS[message.author.id]
        await message.channel.send('%s your team has been disbanded.' % message.author.nick)
    else:
        await message.channel.send('%s you have created a team.' % message.author.nick)

async def pick_command(message):
    """Calling captain adds a user to their team."""
    global CAPTAINS, GUILD, DISCORD_ID_PATTERN
    if message.author.id in CAPTAINS:
        args = message.content.split()
        token = args[1]
        username = args[1]
        discord_id = re.match(DISCORD_ID_PATTERN, args[1])
        if discord_id:
            token = int(discord_id.group(1))
            member = GUILD.get_member(token)
            username = member.nick
        CAPTAINS[message.author.id].append(token)
        await message.channel.send('%s has added %s to their team.' % (message.author.nick, username))
    else:   
        await you_are_dummy_text(message, message.author.nick)

async def team_command(message):
    """Displays the calling captain team roster."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        await message.channel.send('%s your team consists of %s.' % (message.author.nick, str(convert_ids_to_nicks(CAPTAINS[message.author.id]))))
    else:
        await you_are_dummy_text(message, message.author.nick)

async def reset_command(message):
    """Resets all the team state of the bot."""
    global CAPTAINS
    CAPTAINS = []
    await message.channel.send('All teams and captains have been reset.')

async def assignroles_command(message):
    """Assigns the calling captain's team roles."""
    global ROLES, CAPTAINS
    if message.author.id in CAPTAINS:
        role_order = shuffle(ROLES)
        output = zip(convert_ids_to_nicks(CAPTAINS[message.author.id]), role_order)
        response = ""
        for name, role in output:
            response += "%s: %s\n" % (name, role)
        response = response[:-1]
        await message.channel.send(response)
    else:
        await message.channel.send('%s you have created a team.' % message.author.nick)

async def randomcaptains_command(message):
    """Pick two random people from a specific voice channel to be captains."""
    everyone = members_list()
    captain1 = random.choice(everyone)
    everyone.remove(captain1)
    captain2 = random.choice(everyone)
    response = print('Our esteemed captains for this round are:', captain1, 'and', captain2)
    await message.channel.send(response)

###================================= CALLBACKS ========================================###

@client.event
async def on_ready():
    global GUILD, CHANNEL
    GUILD = client.get_guild(int(SERVER_ID))
    CHANNEL = client.get_channel(int(CHANNEL_ID))
    await CHANNEL.send('What is my purpose?')

# randomly select captains and roles
@client.event
async def on_message(message):
    global COMMANDS
    if message.author == client.user: #checks to
        return
    # Only work on channel specficied by CHANNEL_ID
    if (CHANNEL.id != message.channel.id):
        return

    # Easter egg
    if message.content.strip().lower() == 'you draft teams':
        await message.channel.send("Oh my god...")
    args = message.content.strip().split()
    command = COMMANDS.get(args[0])
    if command is not None:
        await command(message)


if __name__ == '__main__':
    COMMANDS = {
        '!commands': commands_command,
        '!captain': captain_command,
        '!removecaptain': removecaptain_command,
        '!pick': pick_command,
        '!team': team_command,
        '!reset': reset_command,
        '!rebase': reset_command,
        '!assignroles': assignroles_command,
        '!randomcaptains': randomcaptains_command,
    }
    client.run(TOKEN)
