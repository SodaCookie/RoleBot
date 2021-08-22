import wrappers
import helpers


@wrappers.captain_endpoint
async def removecaptain(message, context):
    """Removes the caller as a captain."""
    del context.captains[message.author.id]
    helpers.send_message(message.channel, '%s your team has been disbanded.' % helpers.get_member_name(message.author))