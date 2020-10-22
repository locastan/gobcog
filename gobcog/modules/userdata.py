import json
from redbot.core.data_manager import cog_data_path
import random
import discord
import asyncio

class Userdata:
    users = {}
    fp = cog_data_path(None, "gobcog") / 'users.json'  # this looks for users.json inside your RedBot/cogs/gobcog folder. Needs to be setup once: create the folder, make a users.json with just an empty {} inside.
    with fp.open('r') as f:
        users = json.load(f)
    sleepers = set()

    @staticmethod
    async def save():
        with Userdata.fp.open('w') as f:
            json.dump(Userdata.users, f, indent=4, default=lambda o: '<not serializable>', sort_keys=True)

    @staticmethod
    async def saveandreload():
        with Userdata.fp.open('w') as f:
            json.dump(Userdata.users, f, indent=4, default=lambda o: '<not serializable>', sort_keys=True)
            users = {}
            fp = cog_data_path(None, "gobcog") / 'users.json'  # this looks for users.json inside your RedBot/cogs/gobcog folder. Needs to be setup once: create the folder, make a users.json with just an empty {} inside.
            with fp.open('r') as f:
                users = json.load(f)
            sleepers = set()
