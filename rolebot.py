# rolebot.py

import os
import re
import math
import discord
import random
from collections import namedtuple
from distutils.util import strtobool
from discord import channel
from discord.utils import CachedSlotProperty

from dotenv import load_dotenv
from django.shortcuts import render, redirect
from discord.ext import commands

load_dotenv()

# TODO: Maybe refactor here to make state into a context and then parse env vars
# define necessary environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('SERVER_NAME')
SERVER_ID = os.getenv('SERVER_ID')
CHANNEL_ID = os.getenv('DRAFT_CHANNEL_ID')
GUARD_RAILS = strtobool(os.getenv('GUARD_RAILS'))
THROW_SHADE = os.getenv('THROW_SHADE')

# globals
GUILD = None
CHANNEL = None
CAPTAINS = dict()
PLAYER_CONSTRAINTS = dict()
ROLES = ["Top", "Jungle", "Mid", "Support", "Bot"]
COMMANDS = dict()
SHADY_USERS = [int(user) for user in THROW_SHADE.split(',')] 

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
            nicks.append(get_member_name(GUILD.get_member(name)))
        else:
            nicks.append(name)
    return nicks

def convert_id_to_nick(id):
    return get_member_name(GUILD.get_member(id))

def you_are_dummy_text(message, name):
    if is_member_shady(message.author):
        return message.channel.send('%s you\'re not a captain you loser.' % name)
    return message.channel.send('%s you\'re not a captain.' % name)

def is_member_shady(member):
    return member.id in SHADY_USERS

def get_member_name(member):
    name = member.name
    if (member.nick):
        name = member.nick
    return name

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
    if any([message.author.id in team for team in CAPTAINS.values()]):
        await message.channel.send('You\'re already in another team so you can\'t be a captain until the team is disbanded.')
        return
    if message.author.id in CAPTAINS:
        await message.channel.send('You\'re already a captain ya dunce')
        return
    CAPTAINS[message.author.id] = [message.author.id]
    await message.channel.send('%s you have created a team.' % get_member_name(message.author))

async def removecaptain_command(message):
    """Removes the caller as a captain."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        del CAPTAINS[message.author.id]
        await message.channel.send('%s your team has been disbanded.' % get_member_name(message.author))
    else:
        await you_are_dummy_text(message, get_member_name(message.author))

async def pick_command(message):
    """Calling captain adds a user to their team."""
    global CAPTAINS, GUILD, DISCORD_ID_PATTERN
    args = message.content.split()
    # Remove invalid statements
    if len(args) < 2:
        await message.channel.send("Please include a player to include to your pick command.")
        return
    if message.author.id not in CAPTAINS:
        await you_are_dummy_text(message, get_member_name(message.author))
    token = args[1]
    username = args[1]
    discord_id = re.match(DISCORD_ID_PATTERN, args[1])
    if discord_id:
        token = int(discord_id.group(1))
        member = GUILD.get_member(token)
        username = get_member_name(member)
    if GUARD_RAILS:
        # Is themselves
        response = None
        if discord_id and discord_id == token:
            response = 'You cannot add yourself to your own team'
            if is_member_shady(message.author):
                response = '%s you\'re a fucking idiot who tried to add themselves into their own team' % get_member_name(message.author)
        # If Member is captain
        elif discord_id and token in CAPTAINS:
            response = '%s you cannot add another captain to your team.' % get_member_name(message.author)
            if is_member_shady(message.author):
                response = '%s thinks they\'re a really funny QA tester who adds another captain to their team' % get_member_name(message.author)
        # Exists already on a team
        elif any([token in team for team in CAPTAINS.values()]):
            response = '%s already exists on another team' % (convert_id_to_nick(token) if isinstance(token, int) else token)
            if is_member_shady(message.author):
                response = '%s do you feel smart adding an already assigned player? HUH?!?' % get_member_name(message.author)
        # Is a bot
        elif discord_id and GUILD.get_member(token).bot:
            response = '%s is a bot and cannot be added to a team' % convert_id_to_nick(token)
            if is_member_shady(message.author):
                response = '%s stop adding robots you dunce.' % get_member_name(message.author)
        if response is not None:
            await message.channel.send(response)
            return
    CAPTAINS[message.author.id].append(token)
    await message.channel.send('%s has added %s to their team.' % (get_member_name(message.author), username))

async def team_command(message):
    """Displays the calling captain team roster."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        await message.channel.send('%s your team consists of %s.' % (get_member_name(message.author), str(convert_ids_to_nicks(CAPTAINS[message.author.id]))))
    else:
        await you_are_dummy_text(message, get_member_name(message.author))

async def reset_command(message):
    """Resets all the team state of the bot."""
    global CAPTAINS
    CAPTAINS = {}
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
        await message.channel.send('%s you have created a team.' % get_member_name(message.author))

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
    if not args:
        return
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
