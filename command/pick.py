import wrappers
import helpers
import constants
import re


@wrappers.captain_endpoint
async def pick(message, context):
    """Calling captain adds a user to their team."""
    args = message.content.split()
    # Remove invalid statements
    if len(args) < 2:
        helpers.send_message(message.channel, "Please include a player to include to your pick command.")
        return
    token = args[1]
    username = args[1]
    discord_id = re.match(constants.DETECT_DISCORD_ID_PATTERN, args[1])
    if discord_id:
        token = int(discord_id.group(1))
        member = context.guild.get_member(token)
        username = helpers.get_member_name(member)
    if context.guard_rails:
        # Is themselves
        response = None
        if discord_id and discord_id == token:
            response = 'You cannot add yourself to your own team'
            if helpers.is_member_shady(message.author, context):
                response = '%s you\'re a fucking idiot who tried to add themselves into their own team' % helpers.get_member_name(message.author)
        # If Member is captain
        elif discord_id and token in context.captains:
            response = '%s you cannot add another captain to your team.' % helpers.get_member_name(message.author)
            if helpers.is_member_shady(message.author, context):
                response = '%s thinks they\'re a really funny QA tester who adds another captain to their team' % helpers.get_member_name(message.author)
        # Exists already on a team
        elif any([token in team for team in context.captains.values()]):
            response = '%s already exists on another team' % (helpers.convert_id_to_nick(token, context) if isinstance(token, int) else token)
            if helpers.is_member_shady(message.author, context):
                response = '%s do you feel smart adding an already assigned player? HUH?!?' % helpers.get_member_name(message.author)
        # Is a bot
        elif discord_id and context.guild.get_member(token).bot:
            response = '%s is a bot and cannot be added to a team' % helpers.convert_id_to_nick(token, context)
            if helpers.is_member_shady(message.author, context):
                response = '%s stop adding robots you dunce.' % helpers.get_member_name(message.author)
        if response is not None:
            helpers.send_message(message.channel, response)
            return
    context.captains[message.author.id].append(token)
    helpers.send_message(message.channel, '%s has added %s to their team.' % (helpers.get_member_name(message.author), username))