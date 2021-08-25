import helpers


async def reset(message, context):
    """Resets all the team state of the bot."""
    context.captains = dict()
    context.active_inhouse_calls = dict()
    helpers.send_message(message.channel, 'All teams, lobbies and captains have been reset.')