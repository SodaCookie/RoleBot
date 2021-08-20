# rolebot.py

import os
import re
import discord
import random
from discord.utils import CachedSlotProperty

from dotenv import load_dotenv
from django.shortcuts import render, redirect
from discord.ext import commands

load_dotenv()
# define necessary environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('SERVER_NAME')

# globals
CAPTAINS = dict()

DISCORD_ID_PATTERN = r'<@!([0-9]*)>'

# print message when bot connects to disc client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents) #define client
@client.event
async def on_ready():
    pass
    print("Enter")
    # print(f'{client.user.name} has connected to Epic Gamer Friends!')

# get members list for voice channel INHOUSE
async def members_list(request):
    channel = client.get_channel(877295337012879392)
    curMembers = []
    for member in channel.members:
        curMembers.append(member)
    inhouseMembers = render(request, "discordTool/discordTool.html", {
        'members_list': curMembers,})
    return inhouseMembers

def you_are_dummy_text(message, name):
    return message.channel.send('%s you\'re not a captain you idiot.' % name)

# randomly generate a set of roles and ( assign them to group in chronological order )
def league_roles():
    possible_roles = ['top', 'jungle', 'mid', 'bot', 'support']
    randomize_roles = []
    for i in range(len(possible_roles)):
        currRole = random.choice(possible_roles)
        randomize_roles.append(currRole)
        possible_roles.remove(currRole)
    return randomize_roles

# randomly select captains and roles
@client.event
async def on_message(message):
    global CAPTAINS
    if message.author == client.user: #checks to
        return
    if message.content == '!commands':
        response = 'Type "!cat" for captains, "members!" for members and "roles!" to assign roles.'
        await message.channel.send(response)
    if message.content == '!captain':
        if message.author.id in CAPTAINS:
            await message.channel.send('You\'re already a captain ya dunce')
        else:
            CAPTAINS[message.author.id] = []
            await message.channel.send('%s you have created a team.' % message.author.nick)
    if message.content == '!removecaptain':
        if message.author.id in CAPTAINS:
            del CAPTAINS[message.author.id]
            await message.channel.send('%s your team has been disbanded.' % message.author.nick)
        else:
            await message.channel.send('%s you have created a team.' % message.author.nick)
    if message.content.startswith('!pick'):
        if message.author.id in CAPTAINS:
            args = message.content.split()
            discord_id = re.match(DISCORD_ID_PATTERN, args[1]).group(1)
            username = client.get_user(int(discord_id))
            print(username)
        else:   
            await you_are_dummy_text(message, message.author.nick)
    if message.content.startswith('!team'):
        if message.author.id in CAPTAINS:
            await message.channel.send('%s your team consists of %s.' % (message.author.nick, str(CAPTAINS[message.author.id])))
        else:
            await you_are_dummy_text(message, message.author.nick)
    if message.content in ('!rebase', '!reset'):
        CAPTAINS = []
        await message.channel.send('started to create a team')
    if message.content == '!assignroles':
        pass
    if message.content == '!members':
        inhouse_members = members_list()
        response = inhouse_members
        await message.channel.send(response)
    if message.content == '!randomcaptains':
        everyone = members_list()
        captain1 = random.choice(everyone)
        everyone.remove(captain1)
        captain2 = random.choice(everyone)
        response = print('Our esteemed captains for this round are:', captain1, 'and', captain2)
        await message.channel.send(response)
    if message.content == '!team':
        teamlist = []
        response = 'Enter the names of the people in your team, one name per message.'



client.run(TOKEN)
