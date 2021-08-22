"""Defines useful helpers."""

import asyncio
import logging
import json
import constants


def send_message(channel, message):
    """Fire and forget send a message to a channel."""
    asyncio.ensure_future(channel.send(message))

def is_member_shady(member, context):
    """Returns if a member is a shady character."""
    return member.id in context.shady_users

def convert_id_to_nick(id, context):
    return get_member_name(context.guild.get_member(id))

def maybe_convert_id_to_nick(token, context):
    """Converts a token into a the nick name unless its a string"""
    if isinstance(token, int):
        return convert_id_to_nick(token, context)
    return token

def get_member_name(member):
    name = member.name
    if (member.nick):
        name = member.nick
    return name

async def save_player_constraints(context):
    """Save player constraints to disk."""
    with open(context.player_constraints_file, 'w') as file:
        logging.info("Saved player constraints.")
        json.dump(context.player_constraints, file)