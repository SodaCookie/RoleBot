import helpers
import copy
import asyncio
import constants
import re


async def role(message, context):
    """Define the roles that you would like to play. You can add a -d -p -a -r -o flag to delete, print, add, remove or override your roles."""
    if message.author.id not in context.player_constraints:
        context.player_constraints[message.author.id] = copy.deepcopy(constants.ROLES)
    args = message.content.split()
    # Remove invalid statements
    if len(args) < 2:
        helpers.send_message(message.channel, 'Please include roles you would like to play with your roles command.')
        return
    if len(args) > 3:
        helpers.send_message(message.channel, 'Expected 1 - 2 arguments for this command.')
        return
    
    modifier = 'OVERRIDE'
    if len(args) == 3:
        # Modifier detected the roles will be in the third arg
        raw_roles = args[2]
        raw_modifier = args[1]
        if raw_modifier == '-a':
            modifier = 'ADD'
        elif raw_modifier == '-r':
            modifier = 'REMOVE'
        elif raw_modifier == '-o':
            modifier = 'OVERRIDE'
        else:
            helpers.send_message(message.channel, 'Unknown flag found %s.' % raw_modifier)
            return
    else:
        if args[1] == '-d':
            if message.author.id in context.player_constraints:
                del context.player_constraints[message.author.id]
                helpers.send_message(message.channel, '%s your roles have been deleted.' % (helpers.convert_id_to_nick(message.author.id, context)))
                asyncio.ensure_future(helpers.save_player_constraints(context))
            else:
                helpers.end_message(message.channel, '%s you currently don\'t have any roles configured. Nothing was deleted.' % (helpers.convert_id_to_nick(message.author.id, context)))
            return
        elif args[1] == '-p':
            helpers.send_message(message.channel, '%s your roles are currently: %s' % (helpers.convert_id_to_nick(message.author.id, context), str(context.player_constraints.get(message.author.id, constants.ROLES))))
            return
        raw_roles = args[1]
    raw_roles = raw_roles.lower()

    # Determine the roles
    roles = set()
    matches = re.findall(constants.DETECT_ROLE_SYNONYMS_PATTERN, raw_roles)
    if matches:
        # Match based on keywords
        for g in matches:
            for role, syns in constants.ROLE_SYNONYMS.items():
                if g in syns:
                    roles.add(role)
                    break
            else:
                helpers.send_message(message.channel, 'Unknown role found: %s' % g)
                return
    else:
        # Match based on abbreviations
        raw_roles = raw_roles.replace(',','')
        for r in raw_roles:
            if r == 't':
                roles.add('Top')
            elif r == 'j':
                roles.add('Jungle')
            elif r == 'm':
                roles.add('Mid')
            elif r == 's':
                roles.add('Support')
            elif r == 'b':
                roles.add('Bot')
            else:
                helpers.send_message(message.channel, 'Unknown role abbreviation role found: %s' % r)
                return

    if message.author.id not in context.player_constraints:
        context.player_constraints[message.author.id] == []
    if modifier == 'ADD':
        role_set = set(context.player_constraints.get(message.author.id, constants.ROLES))
        role_set = role_set.union(roles)
        context.player_constraints[message.author.id] = list(role_set)
    elif modifier == 'REMOVE':
        role_set = set(context.player_constraints.get(message.author.id, constants.ROLES))
        role_set = role_set.difference(roles)
        context.player_constraints[message.author.id] = list(role_set)
    elif modifier == 'OVERRIDE':
        context.player_constraints[message.author.id] = list(roles)
    
    asyncio.ensure_future(helpers.save_player_constraints(context))
    if helpers.is_member_shady(message.author, context) and len(roles) < 5:
        helpers.send_message(message.channel, 'Looks like you\'re not playing all the roles. Are you feeling a little self conscious? Here are you roles: %s' % (helpers.convert_id_to_nick(message.author.id, context), str(context.player_constraints[message.author.id])))
    else:
        helpers.send_message(message.channel, '%s your roles have been updated to: %s' % (helpers.convert_id_to_nick(message.author.id, context), str(context.player_constraints[message.author.id])))