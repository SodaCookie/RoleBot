import helpers
import wrappers
import helpers
import constants
import random

def _get_team_role_permutations(team, context, overrides=[], selected=set()):
    """Returns the set of valid roles the set of constraints. 
    
    Returns None if not possible. Players can be overridden to not take into
    account their constraint preferences."""
    constraints = set(context.player_constraints.get(team[0], constants.ROLES)) if team[0] not in overrides else set(constants.ROLES)
    selected = set(selected)
    if constraints == selected:
        return None
    if len(team) == 1:
        return [[c] for c in constraints if c not in selected]
    if len(team) == 0:
        return []
    permutations = []
    for role in constraints:
        if role in selected:
            continue
        sub_permutations = _get_team_role_permutations(team[1:], context, overrides, selected | set([role]))
        if sub_permutations is None:
            continue
        for p in sub_permutations:
            permutations.append([role] + p)
    if not permutations:
        return None
    return permutations

@wrappers.captain_endpoint
async def assignroles(message, context):
    """Assigns the calling captain's team roles."""
    team = context.captains[message.author.id]
    if "-f" in message.content:
        permutations = _get_team_role_permutations(team, context, overrides=team)
    else:
        permutations = _get_team_role_permutations(team, context)
    constraints = {player: context.player_constraints.get(player, constants.ROLES) for player in team}
    if permutations is None:
        # We stumble into an impossible configuration
        # Slowly relax constraints based on number of constraints
        relax_order = {}
        relaxed_players = []
        for player, c in constraints.items():
            if len(c) not in relax_order:
                relax_order[len(c)] = []
            relax_order[len(c)].append(player)
        for relax_size in reversed(range(1, 5)):
            if relax_size not in relax_order:
                continue
            if not relax_order[relax_size]:
                continue
            player = random.choice(relax_order[relax_size])
            relaxed_players.append(player)
            relax_order[relax_size].remove(player)
            permutations = _get_team_role_permutations(team, context, overrides=relaxed_players)
            if permutations is not None:
                break
        
    if permutations is None:
        helpers.send_message(message.channel, "No permutation is possible")
        return
    role_order = random.sample(permutations, 1)[0]
    output = zip(team, role_order)
    response = ""
    print(constraints)
    for token, role in output:
        if role not in constraints[token]:
            response += "%s: %s <autofilled>\n" % (helpers.maybe_convert_id_to_nick(token, context), role)
        else:
            response += "%s: %s\n" % (helpers.maybe_convert_id_to_nick(token, context), role)
    response = response[:-1]
    helpers.send_message(message.channel, response)