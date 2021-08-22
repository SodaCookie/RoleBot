"""Defines wrappers that help annotate """

import helpers


def _captain_error_text(message, context, name):
    if helpers.is_member_shady(message.author, context):
        helpers.send_message(message.channel, '%s you\'re not a captain you loser.' % name)
    helpers.send_message(message.channel, '%s you\'re not a captain.' % name)

def admin_endpoint(func):
    """Requires being an admin to call"""
    def admin_wrapper(message, context):
        if message.author.id in context.captains:
            return func(message)
        else:
            _captain_error_text(message, context, helpers.get_member_name(message.author))
    admin_wrapper.__doc__ = func.__doc__
    return admin_wrapper

def captain_endpoint(func):
    """Requires being a captain to call"""
    def captain_wrapper(message, context):
        return func(message, context)
    captain_wrapper.__doc__ = func.__doc__
    return captain_wrapper