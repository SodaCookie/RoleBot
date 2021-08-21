# rolebot.py

import copy
import os
import sys
import re
import json
import math
import functools
import discord
import random
import logging
import traceback
import asyncio
from collections import namedtuple
from distutils.util import strtobool

from dotenv import load_dotenv
from django.shortcuts import render

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
log.addHandler(handler)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
load_dotenv()

# TODO: Maybe refactor here to make state into a context and then parse env vars
# define necessary environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('SERVER_NAME')
SERVER_ID = os.getenv('SERVER_ID')
CHANNEL_ID = os.getenv('DRAFT_CHANNEL_ID')
GUARD_RAILS = strtobool(os.getenv('GUARD_RAILS'))
THROW_SHADE = os.getenv('THROW_SHADE')
PLAYER_CONSTRAINTS_FILE = os.getenv('PLAYER_CONSTRAINTS_FILE')

# globals
GUILD = None
CHANNEL = None
CAPTAINS = dict()
ROLES = ["Top", "Jungle", "Mid", "Support", "Bot"]
COMMANDS = dict()
SHADY_USERS = [int(user) for user in THROW_SHADE.split(',')] 
ROLE_SYNONYMS = {
    'Top': ['top', 'top lane', 'toplane'],
    'Jungle': ['jg', 'jungle'],
    'Mid': ['mid', 'middle', 'mid lane', 'middle lane'],
    'Support': ['support', 'sup'],
    'Bot': ['bot', 'bottom', 'bot lane', 'botlane', 'bottom lane'],
}

if not os.path.exists(PLAYER_CONSTRAINTS_FILE):
    with open(PLAYER_CONSTRAINTS_FILE, 'w') as file:
        json.dump(dict(), file)
        log.info('Created new save file since none was found.')

with open(PLAYER_CONSTRAINTS_FILE, 'r') as file:
    try:
        PLAYER_CONSTRAINTS = json.load(file)
        # Convert string keys (because JSON doesn't support int keys)
        PLAYER_CONSTRAINTS = {int(key):value for key, value in PLAYER_CONSTRAINTS.items()}
        log.info('Player constraints loaded.')
    except json.decoder.JSONDecodeError:
        log.info('Constraint file %s improperly formatted. Initializing constraints as empty.' % PLAYER_CONSTRAINTS_FILE)
        PLAYER_CONSTRAINTS = dict()

DETECT_DISCORD_ID_PATTERN = r'<@!([0-9]*)>'
# Regex that flattens the role synonyms into a single list and then checks for the presence
DETECT_ROLE_SYNONYMS_PATTERN = r'|'.join(functools.reduce(lambda acc, syn: acc + syn, [syn for syn in ROLE_SYNONYMS.values()], []))

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

def get_team_role_permutations(team, selected=set(), overrides=[]):
    """Returns the set of valid roles the set of constraints. 
    
    Returns None if not possible. Players can be overridden to not take into
    account their constraint preferences."""
    constraints = set(PLAYER_CONSTRAINTS.get(team[0], ROLES)) if team[0] not in overrides else set(ROLES)
    selected = set(selected)
    if constraints == selected:
        return None
    if len(team) == 1:
        return [[c] for c in PLAYER_CONSTRAINTS.get(team[0], ROLES) if c not in selected]
    if len(team) == 0:
        return []
    permutations = []
    for role in constraints:
        if role in selected:
            continue
        sub_permutations = get_team_role_permutations(team[1:], selected | set([role]))
        if sub_permutations is None:
            continue
        for p in sub_permutations:
            permutations.append([role] + p)
    if not permutations:
        return None
    return permutations

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

def maybe_convert_id_to_nick(token):
    """Converts a token into a the nick name unless its a string"""
    if isinstance(token, int):
        return convert_id_to_nick(token)
    return token

def you_are_dummy_text(message, name):
    if is_member_shady(message.author):
        send_message(message.channel, '%s you\'re not a captain you loser.' % name)
    send_message(message.channel, '%s you\'re not a captain.' % name)

def is_member_shady(member):
    return member.id in SHADY_USERS

def get_member_name(member):
    name = member.name
    if (member.nick):
        name = member.nick
    return name

def send_message(channel, message):
    """Fire and forget send a message to a channel."""
    asyncio.ensure_future(channel.send(message))\

async def save_player_constraints():
    """Save player constraints to disk."""
    with open(PLAYER_CONSTRAINTS_FILE, 'w') as file:
        log.info("Saved player constraints.")
        json.dump(PLAYER_CONSTRAINTS, file)

async def members_list(message):
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
    send_message(message.channel, response)

async def captain_command(message):
    """Assigns the caller as a captain."""
    global CAPTAINS
    if any([message.author.id in team for team in CAPTAINS.values()]):
        send_message(message.channel, 'You\'re already in another team so you can\'t be a captain until the team is disbanded.')
        return
    if message.author.id in CAPTAINS:
        send_message(message.channel, 'You\'re already a captain ya dunce')
        return
    CAPTAINS[message.author.id] = [message.author.id]
    send_message(message.channel, '%s you have created a team.' % get_member_name(message.author))

async def removecaptain_command(message):
    """Removes the caller as a captain."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        del CAPTAINS[message.author.id]
        send_message(message.channel, '%s your team has been disbanded.' % get_member_name(message.author))
    else:
        await you_are_dummy_text(message, get_member_name(message.author))

async def pick_command(message):
    """Calling captain adds a user to their team."""
    global CAPTAINS, GUILD, DETECT_DISCORD_ID_PATTERN
    args = message.content.split()
    # Remove invalid statements
    if len(args) < 2:
        send_message(message.channel, "Please include a player to include to your pick command.")
        return
    if message.author.id not in CAPTAINS:
        await you_are_dummy_text(message, get_member_name(message.author))
        return
    token = args[1]
    username = args[1]
    discord_id = re.match(DETECT_DISCORD_ID_PATTERN, args[1])
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
            send_message(message.channel, response)
            return
    CAPTAINS[message.author.id].append(token)
    send_message(message.channel, '%s has added %s to their team.' % (get_member_name(message.author), username))

async def team_command(message):
    """Displays the calling captain team roster."""
    global CAPTAINS
    if message.author.id in CAPTAINS:
        send_message(message.channel, '%s your team consists of %s.' % \
            (get_member_name(message.author), str([maybe_convert_id_to_nick(token) for token in CAPTAINS[message.author.id]])))
    else:
        await you_are_dummy_text(message, get_member_name(message.author))

async def reset_command(message):
    """Resets all the team state of the bot."""
    global CAPTAINS
    CAPTAINS = {}
    send_message(message.channel, 'All teams and captains have been reset.')

async def assignroles_command(message):
    """Assigns the calling captain's team roles."""
    global ROLES, CAPTAINS
    if message.author.id in CAPTAINS:
        team = CAPTAINS[message.author.id]
        permutations = get_team_role_permutations(team)
        constraints = {player: PLAYER_CONSTRAINTS.get(team[0], ROLES) for player in team}
        if permutations is None:
            # We stumble into an impossible configuration
            # Slowly relax constraints based on number of constraints
            relax_order = {}
            relaxed_players = []
            for player, c in constraints.items():
                if len(c) not in relax_order:
                    relax_order[len(c)] = []
                relax_order[len(c)].append(player)
            for relax_size in reversed(range(1, 5)):
                if relax_size not in relax_order:
                    continue
                if not relax_order[relax_size]:
                    continue
                player = random.choice(relax_order[relax_size])
                relaxed_players.append(player)
                relax_order[relax_size].remove(player)
                print(relaxed_players)
                permutations = get_team_role_permutations(team, overrides=relaxed_players)
                if permutations is not None:
                    break
            
        if permutations is None:
            send_message(message.channel, "No permutation is possible")
            return
        role_order = random.sample(permutations, 1)[0]
        output = zip(team, role_order)
        response = ""
        for token, role in output:
            if role not in constraints[token]:
                response += "%s: %s <autofilled>\n" % (maybe_convert_id_to_nick(token), role)
            else:
                response += "%s: %s\n" % (maybe_convert_id_to_nick(token), role)
        response = response[:-1]
        send_message(message.channel, response)
    else:
        await you_are_dummy_text(message, get_member_name(message.author))

async def role_command(message):
    """Define the roles that you would like to play. You can add a -d -p -a -r -o flag to delete, print, add, remove or override your roles."""
    global PLAYER_CONSTRAINTS
    if message.author.id not in PLAYER_CONSTRAINTS:
        PLAYER_CONSTRAINTS[message.author.id] = copy.deepcopy(ROLES)
    args = message.content.split()
    # Remove invalid statements
    if len(args) < 2:
        send_message(message.channel, 'Please include roles you would like to play with your roles command.')
        return
    if len(args) > 3:
        send_message(message.channel, 'Expected 1 - 2 arguments for this command.')
        return
    
    modifier = 'OVERRIDE'
    if len(args) == 3:
        # Modifier detected the roles will be in the third arg
        raw_roles = args[2]
        raw_modifier = args[1]
        if raw_modifier == '-a':
            modifier = 'ADD'
        elif raw_modifier == '-r':
            modifier = 'REMOVE'
        elif raw_modifier == '-o':
            modifier = 'OVERRIDE'
        else:
            send_message(message.channel, 'Unknown flag found %s.' % raw_modifier)
            return
    else:
        if args[1] == '-d':
            if message.author.id in PLAYER_CONSTRAINTS:
                del PLAYER_CONSTRAINTS[message.author.id]
                send_message(message.channel, '%s your roles have been deleted.' % (convert_id_to_nick(message.author.id)))
                asyncio.ensure_future(save_player_constraints())
            else:
                send_message(message.channel, '%s you currently don\'t have any roles configured. Nothing was deleted.' % (convert_id_to_nick(message.author.id)))
            return
        elif args[1] == '-p':
            send_message(message.channel, '%s your roles are currently: %s' % (convert_id_to_nick(message.author.id), str(PLAYER_CONSTRAINTS.get(message.author.id, ROLES))))
            return
        raw_roles = args[1]
    raw_roles = raw_roles.lower()

    # Determine the roles
    roles = set()
    matches = re.findall(DETECT_ROLE_SYNONYMS_PATTERN, raw_roles)
    if matches:
        # Match based on keywords
        for g in matches:
            for role, syns in ROLE_SYNONYMS.items():
                if g in syns:
                    roles.add(role)
                    break
            else:
                send_message(message.channel, 'Unknown role found: %s' % g)
                return
    else:
        # Match based on abbreviations
        raw_roles = raw_roles.replace(',','')
        for r in raw_roles:
            if r == 't':
                roles.add('Top')
            elif r == 'j':
                roles.add('Jungle')
            elif r == 'm':
                roles.add('Mid')
            elif r == 's':
                roles.add('Support')
            elif r == 'b':
                roles.add('Bot')
            else:
                send_message(message.channel, 'Unknown role abbreviation role found: %s' % r)
                return

    if message.author.id not in PLAYER_CONSTRAINTS:
        PLAYER_CONSTRAINTS[message.author.id] == []
    if modifier == 'ADD':
        role_set = set(PLAYER_CONSTRAINTS.get(message.author.id, ROLES))
        role_set = role_set.union(roles)
        PLAYER_CONSTRAINTS[message.author.id] = list(role_set)
    elif modifier == 'REMOVE':
        role_set = set(PLAYER_CONSTRAINTS.get(message.author.id, ROLES))
        role_set = role_set.difference(roles)
        PLAYER_CONSTRAINTS[message.author.id] = list(role_set)
    elif modifier == 'OVERRIDE':
        PLAYER_CONSTRAINTS[message.author.id] = list(roles)
    
    asyncio.ensure_future(save_player_constraints())
    if is_member_shady(message.author) and len(roles) < 5:
        send_message(message.channel, 'Looks like you\'re not playing all the roles. Are you feeling a little self conscious? Here are you roles: %s' % (convert_id_to_nick(message.author.id, str(PLAYER_CONSTRAINTS[message.author.id]))))
    else:
        send_message(message.channel, '%s your roles have been updated to: %s' % (convert_id_to_nick(message.author.id), str(PLAYER_CONSTRAINTS[message.author.id])))

async def randomcaptains_command(message):
    """Pick two random people from a specific voice channel to be captains."""
    everyone = members_list()
    captain1 = random.choice(everyone)
    everyone.remove(captain1)
    captain2 = random.choice(everyone)
    response = print('Our esteemed captains for this round are:', captain1, 'and', captain2)
    send_message(message.channel, response)

###================================= CALLBACKS ========================================###

@client.event
async def on_ready():
    global GUILD, CHANNEL
    GUILD = client.get_guild(int(SERVER_ID))
    CHANNEL = client.get_channel(int(CHANNEL_ID))
    # TODO: Refactor this to have sys args be handled better
    if len(sys.argv) > 1 and sys.argv[1] == '--silent':
        log.info("RoleBot is ready.")
        return
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
        send_message(message.channel, "Oh my god...")
    args = message.content.strip().split()
    if not args:
        return
    command = COMMANDS.get(args[0])
    try:
        if command is not None:
            await command(message)
    except:
        print('Error has occurred\n' + message.content)
        traceback.print_exc()


if __name__ == '__main__':
    COMMANDS = {
        '!commands': commands_command,
        '!help': commands_command,
        '!captain': captain_command,
        '!removecaptain': removecaptain_command,
        '!pick': pick_command,
        '!team': team_command,
        '!reset': reset_command,
        '!rebase': reset_command,
        '!assignroles': assignroles_command,
        '!role': role_command,
        '!randomcaptains': randomcaptains_command,
    }
    client.run(TOKEN)