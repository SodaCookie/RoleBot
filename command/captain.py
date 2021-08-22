import helpers


async def captain(message, context):
    """Assigns the caller as a captain."""
    if any([message.author.id in team for team in context.captains.values()]):
        helpers.send_message(message.channel, 'You\'re already in another team so you can\'t be a captain until the team is disbanded.')
        return
    if message.author.id in context.captains:
        helpers.send_message(message.channel, 'You\'re already a captain ya dunce')
        return
    context.captains[message.author.id] = [message.author.id]
    helpers.send_message(message.channel, '%s you have created a team.' % helpers.get_member_name(message.author))