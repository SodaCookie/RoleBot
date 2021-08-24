"""Defines the Rolebot context which defines useful values for the rolebot session."""

import os
import json
import logging
from distutils.util import strtobool

class RolebotContext(object):

    def __init__(self, client, **kwargs):
        super().__init__()
        self.client = client
        self.captains = dict()
        self.shady_users = [int(user) for user in kwargs["shady_users"].split(',')] 
        self.guild = client.get_guild(int(kwargs["server_id"]))
        self.channel = client.get_channel(int(kwargs["channel_id"]))
        self.guard_rails = strtobool(kwargs["guard_rails"])
        self.player_constraints_file = kwargs["player_constraints_file"]
        self.active_inhouse_calls = {}

        if not os.path.exists(self.player_constraints_file):
            with open(kwargs["player_constraints_file"], 'w') as file:
                json.dump(dict(), file)
                logging.info('Created new save file since none was found.')
        self.player_constraints = dict()

        with open(self.player_constraints_file, 'r') as file:
            try:
                self.player_constraints = json.load(file)
                # Convert string keys (because JSON doesn't support int keys)
                self.player_constraints = {int(key):value for key, value in self.player_constraints.items()}
                logging.info('Player constraints loaded.')
            except json.decoder.JSONDecodeError:
                logging.info('Constraint file %s improperly formatted. Initializing constraints as empty.' % kwargs["player_constraints_file"])
                self.player_constraints = dict()