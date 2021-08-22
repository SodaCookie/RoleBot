import helpers
import wrappers


@wrappers.captain_endpoint
async def team(message, context):
    """Displays the calling captain team roster."""
    helpers.send_message(message.channel, '%s your team consists of %s.' % \
        (helpers.get_member_name(message.author), str([helpers.maybe_convert_id_to_nick(token, context) for token in context.captains[message.author.id]])))