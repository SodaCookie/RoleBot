# rolebot.py

import os
import sys
import discord
import logging
import traceback
import constants
import helpers
from rolebot_context import RolebotContext
from dotenv import load_dotenv

# print message when bot connects to disc client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents) #define client

### Global
CONTEXT = None

###================================= CALLBACKS ========================================###

@client.event
async def on_ready():
    global CONTEXT
    CONTEXT = RolebotContext(client, 
        shady_users=os.getenv('THROW_SHADE'),
        server_id=os.getenv('SERVER_ID'),
        channel_id=os.getenv('DRAFT_CHANNEL_ID'),
        guard_rails=os.getenv('GUARD_RAILS'),
        player_constraints_file=os.getenv('PLAYER_CONSTRAINTS_FILE'))

    # TODO: Refactor this to have sys args be handled better
    if len(sys.argv) > 1 and sys.argv[1] == '--silent':
        logging.info("RoleBot is ready.")
    else:
        await CONTEXT.channel.send('What is my purpose?')

# randomly select captains and roles
@client.event
async def on_message(message):
    global CONTEXT
    if message.author == client.user: #checks to
        return
    if CONTEXT.channel is None:
        logging.warning("Command fired when channel is None:\n%s" % message.content)
        return
    # Only work on channel specficied by CHANNEL_ID
    if (CONTEXT.channel.id != message.channel.id):
        return

    # Easter egg
    if message.content.strip().lower() == 'you draft teams':
        helpers.send_message(message.channel, "Oh my god...")
    args = message.content.strip().split()
    if not args:
        return
    command = constants.COMMANDS.get(args[0])
    try:
        if command is not None:
            await command(message, CONTEXT)
    except:
        print('Error has occurred\n' + message.content)
        traceback.print_exc()


if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    # TODO: Maybe refactor here to make state into a context and then parse env vars
    # define necessary environment variables
    client.run(os.getenv('DISCORD_TOKEN'))