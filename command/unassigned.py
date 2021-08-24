import helpers


async def unassigned(message, context):
    """Returns a list of members that are currently unassigned."""
    if not message.author.voice or not message.author.voice.channel:
        helpers.send_message("You need to be part of a voice channel to use this command.")
        return
    channel = context.client.get_channel(message.author.voice.channel.id)

    assigned_players = set()
    for players in context.captains.values():
        assigned_players.update(players)
    unassigned_players = list(filter(lambda m: m.id not in assigned_players, channel.members))

    if unassigned_players:
        if not helpers.is_member_shady(message.author, context):
            helpers.send_message(message.channel, "Available players: %s" % ", ".join([helpers.convert_id_to_nick(m.id, context) for m in unassigned_players]))
        else:
            helpers.send_message(message.channel, "Wake the fuck up: %s" % ", ".join([helpers.convert_id_to_nick(m.id, context) for m in unassigned_players]))
    else:
        helpers.send_message(message.channel, "There are currently no players that are unassigned in this voice channel.")
