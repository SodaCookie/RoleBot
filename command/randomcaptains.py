import random
import helpers


async def randomcaptains(message, context):
    """Pick two random people from a specific voice channel to be captains."""
    if not message.author.voice or not message.author.voice.channel:
        helpers.send_message("You need to be part of a voice channel to use this command.")
        return
    channel = context.client.get_channel(message.author.voice.channel.id)

    if len(channel.members) < 2:
        helpers.send_message("This channel needs at least 2 people in it to pick captains.")
        return
    captains = random.sample(channel.members, 2)
    helpers.send_message(message.channel, "Team 1's Captain: %s\nTeam 2's Captain: %s" % (helpers.get_member_name(captains[0]), helpers.get_member_name(captains[1])))