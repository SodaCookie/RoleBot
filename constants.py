"""Defines constants for the RoleBot"""

import functools
import command

ROLES = ["Top", "Jungle", "Mid", "Support", "Bot"]
ROLE_SYNONYMS = {
    'Top': ['top', 'top lane', 'toplane'],
    'Jungle': ['jg', 'jungle'],
    'Mid': ['mid', 'middle', 'mid lane', 'middle lane'],
    'Support': ['support', 'sup'],
    'Bot': ['bot', 'bottom', 'bot lane', 'botlane', 'bottom lane'],
}
DETECT_DISCORD_ID_PATTERN = r'<@!([0-9]*)>'
# Regex that flattens the role synonyms into a single list and then checks for the presence
DETECT_ROLE_SYNONYMS_PATTERN = r'|'.join(functools.reduce(lambda acc, syn: acc + syn, [syn for syn in ROLE_SYNONYMS.values()], []))
# Repeated because command imports modules not the functions themselves
COMMANDS = {
    '!commands': command.commands.commands,
    '!help': command.commands.commands,
    '!captain': command.captain.captain,
    '!removecaptain': command.removecaptain.removecaptain,
    '!pick': command.pick.pick,
    '!team': command.team.team,
    '!reset': command.reset.reset,
    '!rebase': command.reset.reset,
    '!assignroles': command.assignroles.assignroles,
    '!role': command.role.role,
    '!randomcaptains': command.randomcaptains.randomcaptains,
}