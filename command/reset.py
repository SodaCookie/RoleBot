import helpers


async def reset(message, context):
    """Resets all the team state of the bot."""
    context.captains = dict()
    helpers.send_message(message.channel, 'All teams and captains have been reset.')