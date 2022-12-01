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
    async def load():
        users = {}
        fp = cog_data_path(None, "gobcog") / 'users.json'  # this looks for users.json inside your RedBot/cogs/gobcog folder. Needs to be setup once: create the folder, make a users.json with just an empty {} inside.
        with fp.open('r') as f:
            users = json.load(f)
        sleepers = set()

    @staticmethod
    async def saveandreload():
        await Userdata.save()
        await Userdata.load()

    async def debuff(ctx, userID, debuff_name, penalty, duration, type):
        a = type #debuff routine
        if a == 'att' or a == 'cha':
            bonus = -1 * penalty
            if a in Userdata.users[userID]['buffs'].keys():
                bonus += Userdata.users[userID]['buffs'].get(a, {'bonus':0})['bonus']
                duration += Userdata.users[userID]['buffs'].get(a, {'duration':0})['duration']
            Userdata.users[userID]['buffs'].update({a:{'bonus':bonus, 'duration':duration}})
            attb = int(Userdata.users[userID]['skill']['att']) + int(Userdata.users[userID]['buffs'].get('att', {'bonus':0})['bonus'])
            chab = int(Userdata.users[userID]['skill']['cha']) + int(Userdata.users[userID]['buffs'].get('cha', {'bonus':0})['bonus'])
            signa = "+" if attb > 0 else ""
            signc = "+" if chab > 0 else ""
            if duration == 1:
                await ctx.send("{} causes -{} {} for the next fight.".format(debuff_name,bonus,a.upper()))
            else:
                await ctx.send("{} causes -{} {} for the next {} fights.".format(debuff_name,bonus,a.upper(),duration))
            await ctx.send("Your new stats: **Attack**: {} [{}{}], **Diplomacy**: {} [{}{}].".format(Userdata.users[userID]['att'],signa,attb,Userdata.users[userID]['cha'],signc,chab))
