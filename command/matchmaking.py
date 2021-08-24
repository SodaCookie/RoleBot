from asyncio.tasks import wait
from os import name
import discord
import constants
import asyncio
import logging
import helpers
from collections import namedtuple


InhouseArgs = namedtuple("InhouseArgs", "message,promise,embed,players,num_players,group_name")

INHOUSE_DESCRIPTION = "Emote on this message if you would like to play an inhouse.\n Available players:\n\t- "
INHOUSE_TIMED_OUT = "This in-house has timed out."

async def add_matchmade_player(reaction, player_id, context):
    inhouse_args = context.active_inhouse_calls.get(reaction.message.id)
    if inhouse_args:
        inhouse_args.players.add(player_id)
        inhouse_args.embed.description = INHOUSE_DESCRIPTION + "\n\t- ".join([helpers.convert_id_to_nick(id, context) for id in inhouse_args.players])
        await inhouse_args.message.edit(embed=inhouse_args.embed)
        # Notify the players that an in-house is ready
        if len(inhouse_args.players) == inhouse_args.num_players:
            await reaction.message.channel.send("%s ready!: " % inhouse_args.group_name + ", ".join(list(map(lambda id: "<@%d>" % id, inhouse_args.players))))
            del context.active_inhouse_calls[reaction.message.id]

async def remove_matchmade_player(reaction, player_id, context):
    inhouse_args = context.active_inhouse_calls.get(reaction.message.id)
    if inhouse_args:
        if player_id in inhouse_args.players:
            inhouse_args.players.remove(player_id)
        inhouse_args.embed.description = INHOUSE_DESCRIPTION + "\n\t- ".join([helpers.convert_id_to_nick(id, context) for id in inhouse_args.players])
        await inhouse_args.message.edit(embed=inhouse_args.embed)

async def wait_for_inhouse_timeout(wait_time, id, context):
    await asyncio.sleep(wait_time)
    inhouse_args = context.active_inhouse_calls.get(id)
    if context.active_inhouse_calls.get(id):
        inhouse_args.embed.set_author(
            name="%s (Timed Out)" % inhouse_args.group_name, 
            icon_url=constants.LEAGUE_ICON_HTTP_URL)
        inhouse_args.embed.description = INHOUSE_TIMED_OUT
        await inhouse_args.message.edit(embed=inhouse_args.embed)
        del context.active_inhouse_calls[id]
    else:
        logging.warning("Timed out inhouse %d no longer exists." % id)

async def _init_matchmaking(message, context, group_name, num_players, wait_time):
    embed = discord.Embed()
    embed.title = "Vote"
    embed.description = INHOUSE_DESCRIPTION + helpers.convert_id_to_nick(message.author.id, context)
    embed.set_author(
        name="%s (Available for %dm)" % (group_name, wait_time / 60), 
        icon_url=constants.LEAGUE_ICON_HTTP_URL)
    sent = await message.channel.send(embed=embed)

    # Create reference for waiting to auto delete the message
    wait_inhouse_promise = asyncio.ensure_future(wait_for_inhouse_timeout(wait_time, sent.id, context))
    context.active_inhouse_calls[sent.id] = InhouseArgs(
        message=sent,
        promise=wait_inhouse_promise,
        embed=embed,
        players=set([message.author.id]),
        num_players=num_players,
        group_name=group_name
    )

async def inhouse(message, context):
    """Starts a vote to see how many people are interested in participating in an inhouse."""
    wait_time = constants.DEFAULT_INHOUSE_WAIT_TIME
    raw_args = message.content.split()
    if len(raw_args) > 1 and raw_args[1].isdigit():
        wait_time = int(raw_args[1]) * 60
    await _init_matchmaking(message, context, "%s's In-House" % helpers.convert_id_to_nick(message.author.id, context), 10, wait_time)

async def gamer_time(message, context):
    """Starts a vote to see how many people are interested in participating in a 5 man."""
    wait_time = constants.DEFAULT_INHOUSE_WAIT_TIME
    raw_args = message.content.split()
    if len(raw_args) > 1 and raw_args[1].isdigit():
        wait_time = int(raw_args[1]) * 60
    await _init_matchmaking(message, context, "%s's Five-Squad" % helpers.convert_id_to_nick(message.author.id, context), 5, wait_time)