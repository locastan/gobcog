import json
from redbot.core.data_manager import cog_data_path
import random
import discord
import asyncio
import time
import copy
import logging
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.commands.context import Context
from redbot.core import commands, bank, checks
from .modules.custompredicate import CustomPredicate
from .modules.adventure import Adventure
from .modules.quest import Quest
from .modules.treasure import Treasure
from .modules.classes import Classes
from .modules.userdata import Userdata
from .modules.consumables import Consumables
from .modules.explore import Explore
from .modules.alchemy import Alchemy
from .modules.color import Color

BaseCog = getattr(commands, "Cog", object)
client = discord.Client()

def charge(amount: int):
    async def pred(ctx):
        try:
            await bank.withdraw_credits(ctx.author, amount)
        except ValueError:
            await ctx.send("You don't have enough copperpieces.")
            return False
        else:
            return True
    return commands.check(pred)

def has_hp():
    async def pred(ctx):
        if Userdata.users[str(ctx.author.id)]['hp'] > 0:
            return True
        else:
            if Userdata.users[str(ctx.author.id)]['resting'] != {}:
                if Userdata.users[str(ctx.author.id)]['resting']['rest_end'] <= time.time():
                    Userdata.users[str(ctx.author.id)]['hp'] = int(Userdata.users[str(ctx.author.id)]['base_hp'])
                    Userdata.users[str(ctx.author.id)]['resting'] = {}
                    expired = []
                    for buff in Userdata.users[str(ctx.author.id)]['buffs'].keys(): #reduce duration of active buffs
                        if buff == "rest":
                            if Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] <= 1:
                                expired.append(buff)
                            else:
                                Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] = Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] - 1
                    for buff in expired: #remove buffs outside loop not to change size during iteration
                        Userdata.users[str(ctx.author.id)]['buffs'].pop(buff)
                    await Userdata.save()
                    await ctx.send("You awake fully recovered from your rest.")
                    return True
                else:
                    now = time.time()
                    needed = Userdata.users[str(ctx.author.id)]['resting']['rest_end'] - Userdata.users[str(ctx.author.id)]['resting']['rest_start']
                    lapsed = now - Userdata.users[str(ctx.author.id)]['resting']['rest_start']
                    togo = Userdata.users[str(ctx.author.id)]['resting']['rest_end'] - now
                    m, s = divmod(togo, 60)
                    h, m = divmod(m, 60)
                    s = int(s)
                    m = int(m)
                    h = int(h)
                    if h == 0 and m == 0:
                        out = "{:02d}s".format(s)
                    elif h == 0:
                        out = "{:02d}m:{:02d}s".format(m, s)
                    else:
                        out = "{:01d}h:{:02d}m:{:02d}s".format(h, m, s)
                    if lapsed >= needed:
                        r_perc = 100
                    else:
                        r_perc = round(lapsed/needed*100)
                    msg = await ctx.send("```css\n You are currently resting ({} remaining). Do you want to break your rest and only regain {}% of your health? ```".format(out, r_perc))
                    start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                    pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                    try:
                        await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                        try:
                            await msg.delete()
                        except discord.Forbidden:  # cannot remove message try remove emojis
                            for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                                await msg.remove_reaction(key, ctx.bot.user)
                    except asyncio.TimeoutError:
                        try:
                            await msg.delete()
                        except discord.Forbidden:  # cannot remove message try remove emojis
                            for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                                await msg.remove_reaction(key, ctx.bot.user)
                    if pred.result: #user reacted with Yes.
                        Userdata.users[str(ctx.author.id)]['hp'] += int((Userdata.users[str(ctx.author.id)]['base_hp']-Userdata.users[str(ctx.author.id)]['hp'])*(r_perc/100))
                        Userdata.users[str(ctx.author.id)]['resting'] = {}
                        expired = []
                        for buff in Userdata.users[str(ctx.author.id)]['buffs'].keys(): #reduce duration of active buffs
                            if buff == "rest":
                                if Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] <= 1:
                                    expired.append(buff)
                                else:
                                    Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] = Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] - 1
                        for buff in expired: #remove buffs outside loop not to change size during iteration
                            Userdata.users[str(ctx.author.id)]['buffs'].pop(buff)
                        await ctx.send("You broke your rest. Your hitpoints are currently at {}/{} (+{}%)".format(Userdata.users[str(ctx.author.id)]['hp'],Userdata.users[str(ctx.author.id)]['base_hp'],r_perc))
                        if Userdata.users[str(ctx.author.id)]['hp'] > 0:
                            return True
                        else:
                            await ctx.send("You are still too injured to do anything.")
                            return False
                    else:
                        await ctx.send("You are too injured to do anything.")
                        return False
            else:
                await ctx.send("You are too injured to do anything. You need to rest a bit.")
                return False
    return commands.check(pred)

def not_resting():
    async def pred(ctx):
        if Userdata.users[str(ctx.author.id)]['resting'] != {}:
            if Userdata.users[str(ctx.author.id)]['resting']['rest_end'] <= time.time():
                Userdata.users[str(ctx.author.id)]['hp'] = int(Userdata.users[str(ctx.author.id)]['base_hp'])
                Userdata.users[str(ctx.author.id)]['resting'] = {}
                expired = []
                for buff in Userdata.users[str(ctx.author.id)]['buffs'].keys(): #reduce duration of active buffs
                    if buff == "rest":
                        if Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] <= 1:
                            expired.append(buff)
                        else:
                            Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] = Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] - 1
                for buff in expired: #remove buffs outside loop not to change size during iteration
                    Userdata.users[str(ctx.author.id)]['buffs'].pop(buff)
                await Userdata.save()
                await ctx.send("You awake fully recovered from your rest.")
                return True
            else:
                now = time.time()
                needed = Userdata.users[str(ctx.author.id)]['resting']['rest_end'] - Userdata.users[str(ctx.author.id)]['resting']['rest_start']
                lapsed = now - Userdata.users[str(ctx.author.id)]['resting']['rest_start']
                togo = Userdata.users[str(ctx.author.id)]['resting']['rest_end'] - now
                m, s = divmod(togo, 60)
                h, m = divmod(m, 60)
                s = int(s)
                m = int(m)
                h = int(h)
                if h == 0 and m == 0:
                    out = "{:02d}s".format(s)
                elif h == 0:
                    out = "{:02d}m:{:02d}s".format(m, s)
                else:
                    out = "{:01d}h:{:02d}m:{:02d}s".format(h, m, s)
                if lapsed >= needed:
                    r_perc = 100
                else:
                    r_perc = round(lapsed/needed*100)
                msg = await ctx.send("```css\n You are currently resting ({} remaining). Do you want to break your rest and only regain {}% of your health? ```".format(out, r_perc))
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                except asyncio.TimeoutError:
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                if pred.result: #user reacted with Yes.
                    Userdata.users[str(ctx.author.id)]['hp'] += int((Userdata.users[str(ctx.author.id)]['base_hp']-Userdata.users[str(ctx.author.id)]['hp'])*(r_perc/100))
                    Userdata.users[str(ctx.author.id)]['resting'] = {}
                    expired = []
                    for buff in Userdata.users[str(ctx.author.id)]['buffs'].keys(): #reduce duration of active buffs
                        if buff == "rest":
                            if Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] <= 1:
                                expired.append(buff)
                            else:
                                Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] = Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] - 1
                    for buff in expired: #remove buffs outside loop not to change size during iteration
                        Userdata.users[str(ctx.author.id)]['buffs'].pop(buff)
                    await ctx.send("You broke your rest. Your hitpoints are currently at {}/{} (+{}%)".format(Userdata.users[str(ctx.author.id)]['hp'],Userdata.users[str(ctx.author.id)]['base_hp'],r_perc))
                    return True
                else:
                    return False
        else:
            return True
    return commands.check(pred)

class GobCog(BaseCog):

    global users
    global looting
    users = Userdata.users
    last_trade = 0
    looting = []
    bot = None

    """Goblins Adventure bot"""

    @commands.command()
    @commands.guild_only()
    async def cp(self, ctx, user: discord.Member=None):
        """This shows the bank balance of you or an optionally specified member.
            !cp @locastan
            will bring up locastans balance.
            !cp without user will display your balance.
        """
        if user is None:
            user = ctx.author
        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```css\n{} owns {} {}```".format(
                user.display_name, bal, currency
            )
        )

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    async def brew(self, ctx):
        """This allows you to brew something from ingredients.
            !brew
            will bring up the brewing dialogue.
        """
        Done, inbrew = await Alchemy.brew(ctx, ctx.author)
        if Done:
            for ingredient in inbrew:
                amount = int(Userdata.users[str(ctx.author.id)]['ingredients'][ingredient].get('uses'))
                if amount <= 1:
                    del Userdata.users[str(ctx.author.id)]['ingredients'][ingredient]
                else:
                    Userdata.users[str(ctx.author.id)]['ingredients'][ingredient]['uses'] = Userdata.users[str(ctx.author.id)]['ingredients'][ingredient]['uses'] - 1
            await Userdata.save()
        else:
            ctx.command.reset_cooldown(ctx)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    async def distill(self, ctx):
        """This allows you to distill ingredients into concentrated forms for exchange trade with the alchemists guild.
            !distill
            will bring up the destillation dialogue.
        """
        Done = await Alchemy.distill(ctx, ctx.author)
        if Done:
            await Userdata.save()
        else:
            ctx.command.reset_cooldown(ctx)

    @commands.command(name="rest", aliases=['re'])
    @commands.guild_only()
    async def _rest(self, ctx):
        """This allows you to rest to cure your wounds over time.
            !rest or !r
            Resting time depends on severity of wounds.
        """
        user = ctx.author
        if Userdata.users[str(user.id)]['resting'] == {}:
            if Userdata.users[str(user.id)]['hp'] == Userdata.users[str(user.id)]['base_hp']:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("You are already at full health.".format(user.display_name))
            else:
                hp_ratio = 1-(Userdata.users[str(user.id)]['hp']/Userdata.users[str(user.id)]['base_hp'])
                if "rest" in Userdata.users[str(user.id)]['buffs'].keys():
                    heal_duration = round(28800*hp_ratio/Userdata.users[str(user.id)]['buffs']['rest']['bonus'])
                else:
                    heal_duration = round(28800*hp_ratio)
                now = time.time()
                Userdata.users[str(user.id)]['resting'].update({'rest_start': now, 'rest_end': now+heal_duration})
                togo = heal_duration
                m, s = divmod(togo, 60)
                h, m = divmod(m, 60)
                s = int(s)
                m = int(m)
                h = int(h)
                if h == 0 and m == 0:
                    out = "{:02d}s".format(s)
                elif h == 0:
                    out = "{:02d}m:{:02d}s".format(m, s)
                else:
                    out = "{:01d}h:{:02d}m:{:02d}s".format(h, m, s)
                await ctx.send("```css\n You are now resting for {}.```".format(out))
                await Userdata.save()
        else:
            if Userdata.users[str(ctx.author.id)]['resting']['rest_end'] <= time.time():
                Userdata.users[str(ctx.author.id)]['hp'] = int(Userdata.users[str(ctx.author.id)]['base_hp'])
                Userdata.users[str(ctx.author.id)]['resting'] = {}
                expired = []
                for buff in Userdata.users[str(ctx.author.id)]['buffs'].keys(): #reduce duration of active buffs
                    if buff == "rest":
                        if Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] <= 1:
                            expired.append(buff)
                        else:
                            Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] = Userdata.users[str(ctx.author.id)]['buffs'][buff]['duration'] - 1
                for buff in expired: #remove buffs outside loop not to change size during iteration
                    Userdata.users[str(ctx.author.id)]['buffs'].pop(buff)
                await Userdata.save()
                await ctx.send("You awake fully recovered from your rest.")
                return True
            else:
                now = time.time()
                needed = Userdata.users[str(user.id)]['resting']['rest_end'] - Userdata.users[str(user.id)]['resting']['rest_start']
                lapsed = now - Userdata.users[str(user.id)]['resting']['rest_start']
                togo = Userdata.users[str(user.id)]['resting']['rest_end'] - now
                m, s = divmod(togo, 60)
                h, m = divmod(m, 60)
                s = int(s)
                m = int(m)
                h = int(h)
                if h == 0 and m == 0:
                    out = "{:02d}s".format(s)
                elif h == 0:
                    out = "{:02d}m:{:02d}s".format(m, s)
                else:
                    out = "{:01d}h:{:02d}m:{:02d}s".format(h, m, s)
                if lapsed >= needed:
                    r_perc = 100
                else:
                    r_perc = round(lapsed/needed*100)
                msg = await ctx.send("```css\n You are currently resting ({} remaining). Do you want to break your rest and only regain {}% of your health? ```".format(out, r_perc))
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                except asyncio.TimeoutError:
                    try:
                        await msg.delete()
                    except discord.Forbidden or asyncio.TimeoutError:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                if pred.result: #user reacted with Yes.
                    Userdata.users[str(user.id)]['hp'] += int((Userdata.users[str(user.id)]['base_hp']-Userdata.users[str(user.id)]['hp'])*(r_perc/100))
                    Userdata.users[str(user.id)]['resting'] = {}
                    expired = []
                    for buff in Userdata.users[str(user.id)]['buffs'].keys(): #reduce duration of active buffs
                        if buff == "rest":
                            if Userdata.users[str(user.id)]['buffs'][buff]['duration'] <= 1:
                                expired.append(buff)
                            else:
                                Userdata.users[str(user.id)]['buffs'][buff]['duration'] = Userdata.users[str(user.id)]['buffs'][buff]['duration'] - 1
                    for buff in expired: #remove buffs outside loop not to change size during iteration
                        Userdata.users[str(user.id)]['buffs'].pop(buff)
                    await ctx.send("You broke your rest. Your hitpoints are currently at {}/{} (+{}%)".format(Userdata.users[str(user.id)]['hp'],Userdata.users[str(user.id)]['base_hp'],r_perc))

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    async def unequip(self, ctx, item: str="None"):
        """This stashes a specifed equipped item
            into your backpack.

            !unequip "name of item"
        """
        await GobCog.sub_unequip(ctx,item)

    @staticmethod
    async def sub_unequip(ctx, item: str="None"):
        global users
        user = ctx.author
        equipped = {}
        for slot in Userdata.users[str(user.id)]['items']:
            if Userdata.users[str(user.id)]['items'][slot] and slot != "backpack":
                equipped.update(Userdata.users[str(user.id)]['items'][slot])
        if item == "None" or not any([x for x in equipped if item in x.lower()]):
            if item == "{.:'":
                return
            else:
                return await ctx.send("You do not have an item matching {} equipped.".format(item))
        else:
            lookup = list(x for x in equipped if item in x.lower())
            for olditem in lookup:
                for slot in equipped[olditem].get('slot'):
                    Userdata.users[str(user.id)]['items'][slot] = {}
                    Userdata.users[str(user.id)]['att'] -= int(equipped[olditem].get('att'))     # keep in mind that double handed items grant their bonus twice so they remove twice
                    Userdata.users[str(user.id)]['cha'] -= int(equipped[olditem].get('cha'))
                if olditem in Userdata.users[str(user.id)]['items']['backpack'].keys():
                    price = await GobCog.sell(user,{'itemname': olditem,'item':equipped[olditem]})
                    await ctx.send("**{}** already in backpack: Sold for {} copperpieces.".format(olditem,price))
                else:
                    Userdata.users[str(user.id)]['items']['backpack'].update({olditem: equipped[olditem]}) # TODO: Change data structure of items dict so you can have duplicate items because of key duplicate overwrite in dicts.
                    await ctx.send("You removed {} and put it into your backpack.".format(olditem))
        await GobCog.calcstats(ctx,user.id)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=43200, type=commands.BucketType.user)
    async def explore(self, ctx):
        """This sends you on an exploration trip
            on a graphical map. Move with the arrow buttons.
        """
        if Explore.mapmsg != None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Sorry somebody is exploring at the moment.")
        else:
            await Explore.explore(ctx,ctx.author)

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def adminexplore(self, ctx, type: str="Ocean of Opportunity"):
        """This sends you on an exploration trip
            on a graphical map. Move with the arrow buttons.
        """
        if Explore.mapmsg != None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Sorry somebody is exploring at the moment.")
        else:
            await Explore.adminexplore(ctx,ctx.author, type)

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def give_loot(self, ctx, type: str="normal", user: discord.Member=None, amount: int=1):
        """[Admin] This rewards a treasure chest to a specified member.
            !give_loot normal @locastan
            will give locastan a normal chest.
            (Adding "rare" or "epic" to command, creates rare and epic chests.)
        """
        global users
        if user is None:
            user = ctx.author
        if not 'treasure' in Userdata.users[str(user.id)].keys():
            Userdata.users[str(user.id)]['treasure'] = [0,0,0,0]
        if type == "rare":
            Userdata.users[str(user.id)]['treasure'][1] += amount
        elif type == "epic":
            Userdata.users[str(user.id)]['treasure'][2] += amount
        elif type == "quest":
            Userdata.users[str(user.id)]['treasure'][3] += amount
        else:
            Userdata.users[str(user.id)]['treasure'][0] += amount
        await ctx.send(
            "```{} now owns {} normal, {} rare, {} epic and {} quest chests.```".format(
                user.display_name, str(Userdata.users[str(user.id)]['treasure'][0]),str(Userdata.users[str(user.id)]['treasure'][1]),str(Userdata.users[str(user.id)]['treasure'][2]),str(Userdata.users[str(user.id)]['treasure'][3])))
        await GobCog.save()

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def clean_stats(self, ctx):
        """[Admin] This recalulates each members stats based on equipped items.
            (Meant for stat cleanup after a messup error appeared.)
        """
        global users
        deadsies = []
        for user in users:
            member = discord.utils.find(lambda m: m.id == int(user), ctx.guild.members)
            if member == None: #member left the discord.
                deadsies.append(str(user))
                continue
            i = iter(Userdata.users[str(user)]['items'])
            attack = 0
            diplomacy = 0
            for slot in i:
                if Userdata.users[str(user)]['items'][slot] and slot != "backpack":
                    item = list(Userdata.users[str(user)]['items'][slot].keys())[0]
                    attack += Userdata.users[str(user)]['items'][slot][item]['att']
                    diplomacy += Userdata.users[str(user)]['items'][slot][item]['cha']
            Userdata.users[str(user)]['att'] = attack
            Userdata.users[str(user)]['cha'] = diplomacy
            Userdata.users[str(user)]['base_hp'] = 5 + Userdata.users[str(user)]['lvl']
            Userdata.users[str(user)]['hp'] = int(Userdata.users[str(user)]['base_hp'])
            Userdata.users[str(user)]['name'] = {}
            Userdata.users[str(user)]['resting'] = {}
            Userdata.users[str(user)]['name'] = member.display_name
            if 'lootfilter' not in Userdata.users[str(user)]:
                Userdata.users[str(user)]['lootfilter'] = []
            if 'ingredients' not in Userdata.users[str(user)]:
                Userdata.users[str(user)]['ingredients'] = {}
            if 'consumables' not in Userdata.users[str(user)]:
                Userdata.users[str(user)]['consumables'] = {}
                Userdata.users[str(user)]['buffs'] = {}
            if Userdata.users[str(user)]['class'] == {}:
                Userdata.users[str(user)]['class'] = {'name': "Hero", 'ability': False, 'desc': "Your basic adventuring hero."}
            if Userdata.users[str(user)]['class']['name']=="Berserker":
                Userdata.users[str(user)]['class']['desc'] = "Berserkers have the option to rage and add big bonuses to attacks, but fumbles hurt and following attacks are clouded by rage for a certain time.\n Use !rage when attacking in an adventure.\n They also receive a bonus when using two handed weapons."
            if 'skill' not in Userdata.users[str(user)]:
                Userdata.users[str(user)]['skill'] = {}
                Userdata.users[str(user)]['skill'] = {'pool': 0, 'att': 0, 'cha': 0}
            #print(Userdata.users[str(user)]['name']+": "+str(int(Userdata.users[str(user)]['lvl'] / 5)) + "-" + str(Userdata.users[str(user)]['skill']['att']+Userdata.users[str(user)]['skill']['cha']))
            Userdata.users[str(user)]['skill']['pool'] = int(Userdata.users[str(user)]['lvl'] / 5) - (Userdata.users[str(user)]['skill']['att']+Userdata.users[str(user)]['skill']['cha'])
        for userID in deadsies:
            users.pop(userID)
        await GobCog.save()
        await ctx.send("Command run successful. {} inactive users removed.".format(str(len(deadsies))))


    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def pet(self,ctx, switch:str=None):
        """This allows a Ranger to tame or set free a pet or send it foraging (every 2 hours).
            !pet
            !pet forage
            !pet free
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Ranger":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Ranger to do this.")
        else:
            if switch == None or Userdata.users[str(user)]['class']['ability'] == False:
                pet = await Classes.pet(ctx, None)
                if pet != None:
                    ctx.command.reset_cooldown(ctx) #reset cooldown so ppl can forage right after taming a new pet.
                    Userdata.users[str(user)]['class']['ability'] = {'active': True, 'pet': pet}
                    await GobCog.save()
            elif switch == "pet":
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Your {} enjoyed this very much.".format(Userdata.users[str(user)]['class']['ability']['pet']['name']))
            elif switch == 'forage':
                item = await Classes.pet(ctx, switch)
                if item != None:
                    if item['equip'] == "sell":
                        price = await GobCog.sell(ctx.author,item)
                        await ctx.send("{} sold the {} for {} copperpieces.".format(ctx.author.display_name,item['itemname'],price))
                    elif item['equip'] == "equip":
                        if item['item']['slot'] == ['consumable']:
                            if item['itemname'] in Userdata.users[str(user)]['consumables'].keys():
                                Userdata.users[str(user)]['consumables'][item['itemname']]['uses'] = Userdata.users[str(user)]['consumables'][item['itemname']].get("uses", 0) + item['item']['uses']
                            else:
                                Userdata.users[str(user)]['consumables'].update({item['itemname']:item['item']})
                            await Consumables.use_con(ctx, ctx.author, item['itemname'])
                        else:
                            equip = {"itemname": item['itemname'],"item": item['item']}
                            await self.equip_item(ctx, equip, False)
                    else:
                        if item['item']['slot'] == ['consumable']:
                            if item['itemname'] in Userdata.users[str(user)]['consumables'].keys():
                                Userdata.users[str(user)]['consumables'][item['itemname']]['uses'] = Userdata.users[str(user)]['consumables'][item['itemname']].get("uses", 0) + item['item']['uses']
                            else:
                                Userdata.users[str(user)]['consumables'].update({item['itemname']:item['item']})
                            await ctx.send("{} put the {} into the backpack.".format(ctx.author.display_name,item['itemname']))
                        else:
                            if item['itemname'] in Userdata.users[str(user)]['items']['backpack'].keys() or item['itemname'] in Userdata.users[str(user)]['lootfilter']:
                                price = await GobCog.sell(ctx.author,item)
                                await ctx.send("**{}** sold {} for {} copperpieces.".format(ctx.author.display_name,item['itemname'],price))
                            else:
                                Userdata.users[str(user)]['items']['backpack'].update({item['itemname']: item['item']})
                                await ctx.send("{} put the {} into the backpack.".format(ctx.author.display_name,item['itemname']))
                        await GobCog.save()
            elif switch == 'free':
                await Classes.pet(ctx, switch)
                await GobCog.save()
            else:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Check your spelling.")

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=900, type=commands.BucketType.user)
    async def rage(self,ctx):
        """This allows a Berserker to add substantial attack bonuses for one battle.
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Berserker":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Berserker to do this.")
        else:
            await Classes.rage(ctx)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=900, type=commands.BucketType.user)
    async def meditate(self,ctx):
        """This skill allows a Monk to prevent fumbles (natural 1 roll) in battle.
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Monk":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Monk to do this.")
        else:
            await Classes.meditate(ctx)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=900, type=commands.BucketType.user)
    async def bless(self,ctx):
        """This allows a praying Cleric to add substantial bonuses for heroes fighting the battle.
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Cleric":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Cleric to do this.")
        else:
            await Classes.bless(ctx)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=3, per=3600, type=commands.BucketType.user) #can heal 4 times per hour
    async def heal(self,ctx, user: discord.Member=None):
        """This allows a Cleric to heal himself or others up to 3 times per hour.
            Use !heal to heal yourself. !heal @user to heal others.
            (1d8 + 1 every 5 levels)
        """
        global users
        if user == None:
            user = ctx.author
        if str(user.id) not in Userdata.users.keys():
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("That user does not play the game.")
        if 'name' in Userdata.users[str(ctx.author.id)]['class'] and Userdata.users[str(ctx.author.id)]['class']['name'] != "Cleric":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Cleric to do this.")
        else:
            if int(Userdata.users[str(user.id)]['hp']) == int(Userdata.users[str(user.id)]['base_hp']):
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("**{}** is already at full health.".format(user.display_name))
            else:
                await Classes.heal(ctx,ctx.author,user)
                await GobCog.save()

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=900, type=commands.BucketType.user)
    async def sing(self,ctx, *args):
        """This allows a Bard to add substantial diplomacy bonuses for one battle.
            You can also type in a songname or phrase you want to sing affecting your bonus.
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Bard":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Bard to do this.")
        else:
            if Userdata.users[str(user)]['class']['ability'] == True:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Ability already in use.")
            else:
                await Classes.sing(ctx, *args)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def forge(self,ctx):
        """This allows a Tinkerer to forge two items into a device.
        """
        global users
        user = ctx.author.id
        if 'name' in Userdata.users[str(user)]['class'] and Userdata.users[str(user)]['class']['name'] != "Tinkerer":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Tinkerer to do this.")
        else:
            bkpk = []
            consumed = []
            forgeables = len(Userdata.users[str(user)]['items']['backpack']) - sum("{.:'" in x for x in Userdata.users[str(user)]['items']['backpack'])- sum("[wanderring]" in x for x in Userdata.users[str(user)]['items']['backpack'])
            if forgeables <= 1:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("You need at least two forgeable items in your backpack to forge.")
            for item in Userdata.users[str(user)]['items']['backpack'].keys():
                if "{.:'" not in item and "[wanderring]" not in item:
                    if len(Userdata.users[str(user)]['items']['backpack'][item]['slot']) == 1:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['att']) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['cha']) + Color.none +")"+ Color.yellow + " ["+ Userdata.users[str(user)]['items']['backpack'][item]['slot'][0] + " slot]\n")
                    else:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['att']*2) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['cha']*2) + Color.none +")"+ Color.yellow + " [two handed]\n")
            pile = " - " + " - ".join(bkpk)
            if len(pile) > 1900: #split dangerously long texts into chunks.
                chunks = []
                while pile:
                    if len(pile) <= 1900:
                        chunks.append(pile)
                        break
                    split_index = pile.rfind("\n", 0, 1900)
                    if split_index == -1:
                        # The chunk is too big, so everything until the next newline is deleted
                        try:
                            pile = pile.split("\n", 1)[1]
                        except IndexError:
                            # No "\n" in textline, i.e. the end of the input text was reached
                            break
                    else:
                        chunks.append(pile[:split_index+1])
                        pile = pile[split_index+1:]
                await ctx.send("```ansi\n"+Color.blue+"[{}´s forgeables] \n\n```".format(ctx.author.display_name))
                for chunk in chunks:
                    await ctx.send("```ansi\n" + chunk + "```")
                    await asyncio.sleep(0.3)
            else:
                await ctx.send("```ansi\n"+Color.blue+"[{}´s forgeables] \n\n".format(ctx.author.display_name) + pile + " \n\n```")
            await ctx.send("```ansi\n\n (Reply with the full or partial name of item 1 to select for forging. Try to be specific.)```")
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("I don't have all day, you know.")
            item1 = {}
            lookup = list(x for x in Userdata.users[str(user)]['items']['backpack'] if reply.content.lower() in x.lower())
            if len(lookup) > 1:
                text = "```ansi\n"
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    ctx.command.reset_cooldown(ctx)
                    return
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    if  "{.:'" not in lookup[idx] and "[wanderring]" not in lookup[idx]:
                        item1 = Userdata.users[str(user)]['items']['backpack'].get(lookup[idx])
                        consumed.append(lookup[idx])
                    else:
                        await ctx.send("That item cannot be forged.")
                        ctx.command.reset_cooldown(ctx)
                        return
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    ctx.command.reset_cooldown(ctx)
                    return
            elif len(lookup) == 0:
                await ctx.send("I could not find that item, check your spelling.")
                ctx.command.reset_cooldown(ctx)
                return
            else: #len(lookup) equals 1 item
                if  "{.:'" not in lookup[0] and "[wanderring]" not in lookup[0]:
                    item1 = Userdata.users[str(user)]['items']['backpack'].get(lookup[0])
                    consumed.append(lookup[0])
                else:
                    await ctx.send("That item cannot be forged.")
                    ctx.command.reset_cooldown(ctx)
                    return
            bkpk = []
            for item in Userdata.users[str(user)]['items']['backpack'].keys():
                if item not in consumed and "{.:'" not in item and "[wanderring]" not in item:
                    if len(Userdata.users[str(user)]['items']['backpack'][item]['slot']) == 1:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['att']) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['cha']) + Color.none +")"+ Color.yellow + " ["+ Userdata.users[str(user)]['items']['backpack'][item]['slot'][0] + " slot]\n")
                    else:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['att']*2) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user)]['items']['backpack'][item]['cha']*2) + Color.none +")"+ Color.yellow + " [two handed]\n")
            pile = " - " + " - ".join(bkpk)
            if len(pile) > 1900: #split dangerously long texts into chunks.
                chunks = []
                while pile:
                    if len(pile) <= 1900:
                        chunks.append(pile)
                        break
                    split_index = pile.rfind("\n", 0, 1900)
                    if split_index == -1:
                        # The chunk is too big, so everything until the next newline is deleted
                        try:
                            pile = pile.split("\n", 1)[1]
                        except IndexError:
                            # No "\n" in textline, i.e. the end of the input text was reached
                            break
                    else:
                        chunks.append(pile[:split_index+1])
                        pile = pile[split_index+1:]
                await ctx.send("```ansi\n"+Color.blue+"[{}´s forgeables] \n\n```".format(ctx.author.display_name))
                for chunk in chunks:
                    await ctx.send("```ansi\n" + chunk + "```")
                    await asyncio.sleep(0.3)
            else:
                await ctx.send("```ansi\n"+Color.blue+"[{}´s forgeables] \n\n".format(ctx.author.display_name) + pile + " \n\n```")
            await ctx.send("```ansi\n\n (Reply with the full or partial name of item 2 to select for forging. Try to be specific.)```")
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("I don't have all day, you know.")
            item2 = {}
            lookup = list(x for x in Userdata.users[str(user)]['items']['backpack'] if reply.content.lower() in x.lower())
            if len(lookup) > 1:
                text = "```ansi\n"
                lookup = [x for x in lookup if x not in consumed]
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    ctx.command.reset_cooldown(ctx)
                    return
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    if  "{.:'" not in lookup[idx] and "[wanderring]" not in lookup[idx]:
                        item2 = Userdata.users[str(user)]['items']['backpack'].get(lookup[idx])
                        consumed.append(lookup[idx])
                    else:
                        await ctx.send("That item cannot be forged.")
                        ctx.command.reset_cooldown(ctx)
                        return
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    ctx.command.reset_cooldown(ctx)
                    return
            elif len(lookup) == 0:
                await ctx.send("I could not find that item, check your spelling.")
                ctx.command.reset_cooldown(ctx)
                return
            else: #len(lookup) equals 1 item
                if  "{.:'" not in lookup[0] and "[wanderring]" not in lookup[0]:
                    item2 = Userdata.users[str(user)]['items']['backpack'].get(lookup[0])
                    consumed.append(lookup[0])
                else:
                    await ctx.send("That item cannot be forged.")
                    ctx.command.reset_cooldown(ctx)
                    return
            newitem = await Classes.forge(ctx, item1, item2)
            for scrapping in consumed:
                Userdata.users[str(user)]['items']['backpack'].pop(scrapping)
            await GobCog.sub_unequip(ctx,"{.:'")
            lookup = list(x for x in Userdata.users[str(user)]['items']['backpack'] if "{.:'" in x.lower())
            if len(lookup) > 0:
                msg = await ctx.send("```ansi\n You already have a device. Do you want to replace {}? ```".format(Color.get_color(str(lookup))))
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                except asyncio.TimeoutError:
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove message try remove emojis
                        for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                            await msg.remove_reaction(key, ctx.bot.user)
                if pred.result: #user reacted with Yes.
                    for item in lookup:
                        del Userdata.users[str(user)]['items']['backpack'][item]
                        Userdata.users[str(user)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
                        await ctx.send('```ansi\n Your new {} consumed {} and is now lurking in your backpack. ```'.format(Color.get_color(newitem['itemname']), Color.get_color(lookup)))
                else:
                    roll = random.randint(1,3)
                    if roll == 3:
                        await ctx.send('```ansi\n You carefully dismantle the {} and salvage its '+Color.orange+'[soul essence]. ```'.format(Color.get_color(newitem['itemname'])))
                        if "[soul essence]" in Userdata.users[str(user)]['consumables'].keys():
                            Userdata.users[str(user)]['consumables']['[soul essence]']['uses'] = Userdata.users[str(user)]['consumables']['[soul essence]'].get("uses", 0) + 1
                        else:
                            Userdata.users[str(user)]['consumables'].update({'[soul essence]':{"slot":["consumable"],"uses":1}})
                    else:
                        await ctx.send('```ansi\n {} got mad at your rejection and blew itself up. ```'.format(Color.get_color(newitem['itemname'])))
                    await GobCog.save()
            else:
                Userdata.users[str(user)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
                await ctx.send('```ansi\n Your new {} is lurking in your backpack. ```'.format(Color.get_color(newitem['itemname'])))
                await GobCog.save()


    @commands.command()
    @commands.guild_only()
    @not_resting()
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def heroclass(self, ctx, clz:str=None, action:str=None):
        """This allows you to select a class.
            You need to be level 10 to select one.
            For information on class use: !heroclass "classname" info
        """
        global users
        classes = {'Tinkerer': {'name': "Tinkerer", 'ability': False, 'desc': "Tinkerers can forge two different items into a device bound to their very soul.\nThey also have a chance to reclaim soul essence from dismantling devices.\n Use !forge."},
                    'Berserker':{'name': "Berserker", 'ability': False, 'desc': "Berserkers have the option to rage and add big bonuses to attacks, but fumbles hurt and following attacks are clouded by rage for a certain time.\n Use !rage when attacking in an adventure.\n They also receive a bonus when using two handed weapons."},
                    'Cleric': {'name': "Cleric", 'ability': False, 'desc': "Clerics can bless the entire group when praying and have the power to !heal.\n Use !bless when fighting in an adventure."},
                    'Ranger': {'name': "Ranger", 'ability': False, 'desc': "Rangers can gain a special pet, which can find items and give reward bonuses.\n Use !pet.\n They also receive a bonus when using bows."},
                    'Bard': {'name': "Bard", 'ability': False, 'desc': "Bards can perform to aid their comrades in diplomacy.\n Use !sing and maybe add a song when being diplomatic in an adventure."},
                    'Monk': {'name': "Monk", 'ability': False, 'desc': "Monks are masters of improvisation and draw power from flaws and imperfections of their chosen weapons. They value weapon balance over sheer power or prestige. They can use !meditate to prevent a fumble for a fight."}}
        user = ctx.author
        if clz == None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("So you feel like taking on a class, **{}**?\nAvailable classes are: Tinkerer, Berserker, Cleric, Ranger and Bard.\n Use !heroclass \"name-of-class\" to choose one.".format(user.display_name))
        else:
            clz = clz[:1].upper() + clz[1:]
            if clz in classes and action == None:
                if Userdata.users[str(user.id)]['lvl'] >= 10:
                    if 'name' in Userdata.users[str(user.id)]['class']:
                        if Userdata.users[str(user.id)]['class']['name'] == 'Tinkerer' or Userdata.users[str(user.id)]['class']['name'] == 'Ranger':
                            curclass = Userdata.users[str(user.id)]['class']['name']
                            if curclass == 'Tinkerer':
                                msg = await ctx.send("```css\n You will lose your forged device if you change your class.\nShall I proceed? ```")
                            else:
                                msg = await ctx.send("```css\n You will lose your pet if you change your class.\nShall I proceed? ```")
                            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                            try:
                                await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                                try:
                                    await msg.delete()
                                except discord.Forbidden or asyncio.TimeoutError:  # cannot remove message try remove emojis
                                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                                        await msg.remove_reaction(key, ctx.bot.user)
                            except asyncio.TimeoutError:
                                try:
                                    await msg.delete()
                                except discord.Forbidden or asyncio.TimeoutError:  # cannot remove message try remove emojis
                                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                                        await msg.remove_reaction(key, ctx.bot.user)
                            if pred.result: #user reacted with Yes.
                                if curclass == 'Tinkerer':
                                    await GobCog.sub_unequip(ctx,"{.:'")
                                    if any([x for x in Userdata.users[str(user.id)]['items']['backpack'] if "{.:'" in x.lower()]):
                                        lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if "{.:'" in x.lower())
                                        for item in lookup:
                                            del Userdata.users[str(user.id)]['items']['backpack'][item]
                                            await ctx.send('```ansi\n {} has run off to find a new master. ```'.format(Color.get_color(lookup)))
                            else:
                                ctx.command.reset_cooldown(ctx)
                                return
                    Userdata.users[str(user.id)]['class'] = {}
                    Userdata.users[str(user.id)]['class'] = classes[clz]
                    await ctx.send("Congratulations. You are now a {}.".format(classes[clz]['name']))
                    await GobCog.save()
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send("You need to be at least level 10 to choose a class.")
            elif clz in classes and action == "info":
                ctx.command.reset_cooldown(ctx)
                await ctx.send("{}".format(classes[clz]['desc']))
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send("{} may be a class somewhere, but not on my watch.".format(clz))

    @commands.command()
    @commands.guild_only()
    @not_resting()
    async def skill(self, ctx, spend:str=None):
        """This allows you to spend skillpoints.
            !skill attack/diplomacy
        """
        global users
        user = ctx.author
        if Userdata.users[str(user.id)]['skill']['pool'] == 0:
            return await ctx.send("You do not have unspent skillpoints.")
        if spend == None:
            await ctx.send("You currently have **{}** unspent skillpoints.\nIf you want to put them towards a permanent attack or diplomacy bonus,\nuse !skill attack or !skill diplomacy".format(str(Userdata.users[str(user.id)]['skill']['pool'])))
        else:
            if spend not in ['attack','diplomacy']:
                return await ctx.send("Don't try to fool me! There is no such thing as {}.".format(spend))
            elif spend == "attack":
                Userdata.users[str(user.id)]['skill']['pool'] -= 1
                Userdata.users[str(user.id)]['skill']['att'] += 1
            elif spend == "diplomacy":
                Userdata.users[str(user.id)]['skill']['pool'] -= 1
                Userdata.users[str(user.id)]['skill']['cha'] += 1
            await ctx.send("You permanently raised your {} value by one.".format(spend))
            await GobCog.save()

    @commands.command()
    @commands.guild_only()
    @not_resting()
    async def use(self, ctx, *consgreed: str):
        """This allows you to use consumables.
            !use "partial name(s) of consumable(s)"
            Get a description of the consumable with:
            !use "partial name(s) of consumable(s)" info
        """
        global users
        user = ctx.author
        gotcons = False
        if Userdata.users[str(user.id)]['consumables'] != {}:
            gotcons = True
        if gotcons == False:
            return await ctx.send("You do not have any consumables.")
        if len(consgreed) == 0:
            return await ctx.send("You did not mention what to use.")
        if "info" in consgreed:
            consgreed = consgreed[:-1] #remove info as last parameter from tuple
            for consi in consgreed:
                if not any([x for x in Userdata.users[str(user.id)]['consumables'] if consi.lower() in x.lower()]):
                    await ctx.send("You do not own {}.".format(consi))
                    continue
                lookup = list(x for x in Userdata.users[str(user.id)]['consumables'] if consi.lower() in x.lower())
                consi = lookup[0]
                await ctx.send("{}: {}".format(consi,Consumables.consbles[consi]['desc']))
            return
        for consumable in consgreed:
            if not any([x for x in Userdata.users[str(user.id)]['consumables'] if consumable.lower() in x.lower()]):
                await ctx.send("You do not own {}.".format(consumable))
                continue
            lookup = list(x for x in Userdata.users[str(user.id)]['consumables'] if consumable.lower() in x.lower())
            if len(lookup) > 1:
                await ctx.send("I found multiple consumables ({}) matching that name.\nPlease be more specific.".format(" and ".join([", ".join(lookup[:-1]),lookup[-1]] if len(lookup) > 2 else lookup)))
                continue
            else:
                cons = lookup[0]
                if len(Consumables.consbles[cons]['attrib']) < 2 and Consumables.consbles[cons]['attrib'][0] in Userdata.users[str(user.id)]['buffs'].keys():
                    await ctx.send("You already have the buff of {} in effect.".format(cons))
                    continue
                if len(Consumables.consbles[cons]['attrib']) == 2 and Consumables.consbles[cons]['attrib'][0] in Userdata.users[str(user.id)]['buffs'].keys() and Consumables.consbles[cons]['attrib'][1] in Userdata.users[str(user.id)]['buffs'].keys():
                    await ctx.send("You already have both buffs of {} in effect.".format(cons))
                    continue
                Done = await Consumables.use_con(ctx, user, cons)
                if Done:
                    amount = int(Userdata.users[str(user.id)]['consumables'][cons].get('uses'))
                    if amount <= 1:
                        del Userdata.users[str(user.id)]['consumables'][cons]
                    else:
                        Userdata.users[str(user.id)]['consumables'][cons]['uses'] = Userdata.users[str(user.id)]['consumables'][cons]['uses'] - 1
        await GobCog.save()

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    async def loot(self, ctx, type: str="normal", many: int=1):
        """This opens one of your precious treasure chests.
            (specify "rare", "epic" or "quest" and
            if you want to open multiple how many.)
        """
        global looting
        if ctx.author.id in looting:
            await ctx.send("**{}**, you are currently looting, please finish that session first.".format(ctx.author.display_name))
            return
        else:
            looting.append(ctx.author.id)
        if type.isdigit():
            many = int(type)
            type = "normal"
        if type == "normal":
            redux = [1,0,0,0]
        elif type == "rare":
            redux = [0,1,0,0]
        elif type == "epic":
            redux = [0,0,1,0]
        elif type == "quest":
            redux = [0,0,0,1]
        else:
            await ctx.send("There is talk of a {} treasure chest but nobody ever saw one.".format(type))
            if ctx.author.id in looting:
                looting.remove(ctx.author.id)
            return
        if many > 1:
            await GobCog.autoloot(self,ctx,type,many)
            return
        elif many <= 0:
            await ctx.send("Maybe there are negative or zero space chests somewhere, but I am not having that here!".format(type))
            if ctx.author.id in looting:
                looting.remove(ctx.author.id)
            return
        user = ctx.author
        if not 'treasure' in Userdata.users[str(user.id)].keys():
            Userdata.users[str(user.id)]['treasure'] = [0,0,0,0]
        treasure = Userdata.users[str(user.id)]['treasure'][redux.index(1)]
        if treasure <= 0:
            await ctx.send("You have no {} treasure chest to open.".format(type))
            if user.id in looting:
                looting.remove(user.id)
        else:
            item = await Treasure.open_chest(ctx, user, type)
            Userdata.users[str(user.id)]['treasure'] = [x-y for x,y in zip(Userdata.users[str(user.id)]['treasure'], redux)]
            if item['itemname'] == "[wanderring]":
                await GobCog.move_wanderring(ctx,user.id)
            elif item['equip'] == "sell":
                price = await GobCog.sell(user,item)
                await ctx.send("**{}** sold the {} for {} copperpieces.".format(user.display_name,item['itemname'],price))
            elif item['equip'] == "equip":
                if item['item']['slot'] == ['consumable']:
                    if item['itemname'] in Userdata.users[str(user.id)]['consumables'].keys():
                        Userdata.users[str(user.id)]['consumables'][item['itemname']]['uses'] = Userdata.users[str(user.id)]['consumables'][item['itemname']].get("uses", 0) + item['item']['uses']
                    else:
                        Userdata.users[str(user.id)]['consumables'].update({item['itemname']:item['item']})
                    await Consumables.use_con(ctx, user, item['itemname'])
                else:
                    equip = {"itemname": item['itemname'],"item": item['item']}
                    await self.equip_item(ctx, equip, False)
            else:
                if item['item']['slot'] == ['consumable']:
                    if item['itemname'] in Userdata.users[str(user.id)]['consumables'].keys():
                        Userdata.users[str(user.id)]['consumables'][item['itemname']]['uses'] = Userdata.users[str(user.id)]['consumables'][item['itemname']].get("uses", 0) + item['item']['uses']
                    else:
                        Userdata.users[str(user.id)]['consumables'].update({item['itemname']:item['item']})
                else:
                    if item['itemname'] in Userdata.users[str(user.id)]['items']['backpack'].keys() or item['itemname'] in Userdata.users[str(user.id)]['lootfilter']:
                        price = await GobCog.sell(user,item)
                        await ctx.send("**{}** sold {} for {} copperpieces.".format(user.display_name,item['itemname'],price))
                    else:
                        Userdata.users[str(user.id)]['items']['backpack'].update({item['itemname']: item['item']})
                        await ctx.send("**{}** put the {} into the backpack.".format(user.display_name,item['itemname']))
            await ctx.send("```ansi\n You own {} normal, [2;34m{} rare[0m, [2;32m{} epic[0m and [2;33m{} quest[0m chests.```".format(
                str(Userdata.users[str(user.id)]['treasure'][0]),str(Userdata.users[str(user.id)]['treasure'][1]),str(Userdata.users[str(user.id)]['treasure'][2]),str(Userdata.users[str(user.id)]['treasure'][3])))
            if item['equip'] == "cancel":
                await ctx.send("**{}** cancelled the looting session.".format(user.display_name))
        if user.id in looting:
            looting.remove(user.id)
        await Userdata.save()

    @staticmethod
    async def autoloot(self, ctx, type: str="normal", many: int=1):
        global looting
        if type == "normal":
            redux = [many,0,0,0]
        elif type == "rare":
            redux = [0,many,0,0]
        elif type == "epic":
            redux = [0,0,many,0]
        elif type == "quest":
            redux = [0,0,0,many]
        else:
            await ctx.send("There is talk of a {} treasure chest but nobody ever saw one.".format(type))
            if ctx.author.id in looting:
                looting.remove(ctx.author.id)
            return
        user = ctx.author
        if not 'treasure' in Userdata.users[str(user.id)].keys():
            Userdata.users[str(user.id)]['treasure'] = [0,0,0,0]
        treasure = Userdata.users[str(user.id)]['treasure'][redux.index(many)]
        if treasure <= 0 or treasure < many:
            await ctx.send("You do not have enough {} treasure chests to open.".format(type))
        else:
            itempile = await Treasure.autoopen_chest(ctx, user, type, many)
            Userdata.users[str(user.id)]['treasure'] = [x-y for x,y in zip(Userdata.users[str(user.id)]['treasure'], redux)]
            for thing in itempile.keys():
                item = itempile[thing]
                if item['item']['slot'] == ['consumable']:
                    if item['itemname'] in Userdata.users[str(user.id)]['consumables'].keys():
                        Userdata.users[str(user.id)]['consumables'][thing]['uses'] = Userdata.users[str(user.id)]['consumables'][thing].get("uses", 0) + item['item']['uses']
                    else:
                        Userdata.users[str(user.id)]['consumables'].update({item['itemname']:item['item']})
                elif item['itemname'] == "[wanderring]":
                            await GobCog.move_wanderring(ctx,user.id)
                else:
                    if item['itemname'] in Userdata.users[str(user.id)]['items']['backpack'].keys() or item['itemname'] in Userdata.users[str(user.id)]['lootfilter']:
                        price = await GobCog.sell(user,item)
                        await ctx.send("**{}** sold {} for {} copperpieces.".format(user.display_name,item['itemname'],price))
                    else:
                        Userdata.users[str(user.id)]['items']['backpack'].update({item['itemname']: item['item']})
            await ctx.send("```ansi\n You own {} normal, [2;34m{} rare[0m, [2;32m{} epic[0m and [2;33m{} quest[0m chests.```".format(
                str(Userdata.users[str(user.id)]['treasure'][0]),str(Userdata.users[str(user.id)]['treasure'][1]),str(Userdata.users[str(user.id)]['treasure'][2]),str(Userdata.users[str(user.id)]['treasure'][3])))
        if ctx.author.id in looting:
            looting.remove(ctx.author.id)
        await Userdata.save()

    @staticmethod
    async def move_wanderring(ctx, new_holder_id):
        found = False
        for id in Userdata.users:
            if id == new_holder_id:  # this check doesn't work because numbers vs strings, users owever prefer the ring to have a mind of its own. :)
                continue
            if "[wanderring]" in list(Userdata.users[str(id)]['items'].get('ring', "Empty_slot")):
                moveitem = Userdata.users[str(id)]['items']['ring'].pop('[wanderring]')
                Userdata.users[str(id)]['att'] -= 20
                Userdata.users[str(id)]['cha'] -= 20
                Userdata.users[str(new_holder_id)]['items']['backpack'].update({"[wanderring]": moveitem})
                found = True
                await ctx.send("The wanderring slipped from {}s finger into {}s backpack.".format(Userdata.users[str(id)]['name'],Userdata.users[str(new_holder_id)]['name']))
                return
            elif Userdata.users[str(id)]['items']['backpack'].get('[wanderring]', "Empty_slot") != "Empty_slot":
                moveitem = Userdata.users[str(id)]['items']['backpack'].pop('[wanderring]')
                Userdata.users[str(new_holder_id)]['items']['backpack'].update({"[wanderring]": moveitem})
                found = True
                await ctx.send("The wanderring found its way from {} to {}s backpack.".format(Userdata.users[str(id)]['name'],Userdata.users[str(new_holder_id)]['name']))
                return
        if not found:
            Userdata.users[str(new_holder_id)]['items']['backpack'].update({"[wanderring]":{"slot":["ring"],"att":+20,"cha":+20}})
            await ctx.send("{} found the wanderring!".format(Userdata.users[str(id)]['name']))
            return

    @commands.command(name="stats", aliases=['s'])
    @commands.guild_only()
    async def _stats(self, ctx, user: discord.Member=None):
        """This draws up a charsheet of you or an optionally specified member.
            !stats @locastan
            will bring up locastans stats.
            !stats without user will open your stats.
        """
        if user is None:
            user = ctx.author
        if user.bot:
            return
        if user.id not in Userdata.users:
            await self.update_data(Userdata.users, user)
        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)
        global users
        xp = round(Userdata.users[str(user.id)]['exp'])
        lvl = Userdata.users[str(user.id)]['lvl']
        att = Userdata.users[str(user.id)]['att']
        satt = Userdata.users[str(user.id)]['skill']['att'] + Userdata.users[str(user.id)]['buffs'].get('att', {'bonus':0})['bonus']
        cha = Userdata.users[str(user.id)]['cha']
        scha = Userdata.users[str(user.id)]['skill']['cha'] + Userdata.users[str(user.id)]['buffs'].get('cha', {'bonus':0})['bonus']
        pool = Userdata.users[str(user.id)]['skill']['pool']
        hp_perc = round((Userdata.users[str(user.id)]['hp']/Userdata.users[str(user.id)]['base_hp'])*100)
        if hp_perc <= 25:
            hp_color = Color.red
        elif hp_perc <= 50:
            hp_color = Color.orange
        else:
            hp_color = Color.green
        hitpoints = "HP {}/{} ({}{}%{})".format(Userdata.users[str(user.id)]['hp'],Userdata.users[str(user.id)]['base_hp'],hp_color,hp_perc,Color.none)
        buffs = ""
        signa = "+" if satt > 0 else ""
        signc = "+" if scha > 0 else ""
        if Userdata.users[str(user.id)]['buffs'] != {}:
            buffs = "\n- Active Buffs:"
            for key in Userdata.users[str(user.id)]['buffs'].keys():
                if key == "luck":
                    buffs += " 🍀 (+{}%/{}⏳) ".format(Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "att":
                    buffs += " 🗡️ ({}{}/{}⏳) ".format(signa,Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "cha":
                    buffs += " 🗨️ ({}{}/{}⏳) ".format(signc,Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "money":
                    buffs += " 💰 (+{}%/{}⏳) ".format(Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "xp":
                    buffs += " 📚 (+{}%/{}⏳) ".format(Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "monster":
                    buffs += " 🦖 (🗡️️{}|🗨️{}/{}⏳) ".format(Userdata.users[str(user.id)]['buffs'][key]['bonus']['att'],Userdata.users[str(user.id)]['buffs'][key]['bonus']['cha'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
                elif key == "rest":
                    buffs += " 💤 ({}x/{}⏳) ".format(Userdata.users[str(user.id)]['buffs'][key]['bonus'],Userdata.users[str(user.id)]['buffs'][key]['duration'])
            buffs += " -"
        equip = "Equipped Items \n"
        i = iter(Userdata.users[str(user.id)]['items'])
        for slot in i:
            if Userdata.users[str(user.id)]['items'][slot] and slot != "backpack":
                item = list(Userdata.users[str(user.id)]['items'][slot].keys())[0]
                if len(Userdata.users[str(user.id)]['items'][slot][item]['slot']) == 1:
                    equip += Color.get_color(item) + " ("+Color.red+"ATT "+Color.none+ str(Userdata.users[str(user.id)]['items'][slot][item]['att']) + " / "+Color.blue+"DPL "+Color.none+ str(Userdata.users[str(user.id)]['items'][slot][item]['cha']) +") "+Color.green+"["+ Userdata.users[str(user.id)]['items'][slot][item]['slot'][0] + " slot]"+Color.none+"\n"
                else:
                    equip += Color.get_color(item) + " ("+Color.red+"ATT "+Color.none+ str(Userdata.users[str(user.id)]['items'][slot][item]['att']*2) + " / "+Color.blue+"DPL "+Color.none+ str(Userdata.users[str(user.id)]['items'][slot][item]['cha']*2) +") "+Color.green+"[two handed]"+Color.none+"\n"
                    next(i, None)
        next_lvl = int((lvl+1) ** 4)
        if Userdata.users[str(user.id)]['class'] != {} and 'name' in Userdata.users[str(user.id)]['class']:
            clazz = Color.pink + Userdata.users[str(user.id)]['class']['name'] +Color.yellow + "\n\n" + Userdata.users[str(user.id)]['class']['desc']+Color.none
            if Userdata.users[str(user.id)]['class']['name'] == "Ranger" and type(Userdata.users[str(user.id)]['class']['ability']) != bool:
                if 'pet' in Userdata.users[str(user.id)]['class']['ability']:
                    bonus = int(Userdata.users[str(user.id)]['lvl']/10)*2
                    bow_bonus = "{}🏹".format(bonus)
                    clazz += "\n- Current pet: {}".format(Userdata.users[str(user.id)]['class']['ability']['pet']['name'])
                    clazz += "\n\nYou get a +{} bonus to attacks when using a bow.".format(bow_bonus)
            elif Userdata.users[str(user.id)]['class']['name']=="Berserker" and Userdata.users[str(user.id)]['items']['right'] != {}:
                if len(Userdata.users[str(user.id)]['items']['right'][list(Userdata.users[str(user.id)]['items']['right'].keys())[0]]["slot"]) == 2 and "bow" not in list(Userdata.users[str(user.id)]['items']['right'].keys())[0]:
                    bonus = Userdata.users[str(user.id)]['items']['right'][list(Userdata.users[str(user.id)]['items']['right'].keys())[0]]["att"]*2
                    bow_bonus = " {}🀄".format(bonus)
                    clazz += "\n\nYou currently get a +{} bonus to attacks for using a two handed item.".format(bow_bonus)
            elif Userdata.users[str(user.id)]['class']['name']=="Monk":
                bonus = await Classes.calc_monkbonus(ctx,user.id)
                bow_bonus = "⚖️(🗡️{}/🗨️{})".format(bonus[0],bonus[1])
                clazz += "\n\nYou can currently achieve {} as maximum monkbonus from your choice of weapons.".format(bow_bonus)
        else:
            clazz = "Hero."
        await ctx.send(
            "```ansi\n"+Color.red+"[{}´s Character Sheet] \n\n```".format(user.display_name) + "```ansi\nA level"+Color.blue+" {}".format(lvl) +" {}".format(clazz) + " \n\n- [2;31mATTACK[0m [2;41m{} [{}{}][0m - [2;34mDIPLOMACY[0m [2;45m{} [{}{}][0m - {} -{}\n\n- Credits:".format(att, signa, satt, cha, signc, scha, hitpoints,buffs)+Color.blue+" {} ".format(bal)+Color.none+"{}".format(currency)+Color.none+" \n- Experience:"+Color.blue+" {}".format(xp)+Color.none+"/"+Color.blue+"{} ".format(next_lvl)+Color.none+"\n- Unspent skillpoints:"+Color.blue+" {} ".format(pool)+Color.none+"\n```"
            + "```ansi\n" + equip + "```" + "```ansi\n You own {} normal, [2;34m{} rare[0m, [2;32m{} epic[0m and [2;33m{} quest[0m chests.```".format(
            str(Userdata.users[str(user.id)]['treasure'][0]),str(Userdata.users[str(user.id)]['treasure'][1]),str(Userdata.users[str(user.id)]['treasure'][2]),str(Userdata.users[str(user.id)]['treasure'][3]))
        )

    @commands.command(name="backpack", aliases=['b'])
    @commands.guild_only()
    async def _backpack(self, ctx, switch: str="None", item: str="None", asking: int=0, buyer: discord.Member=None, quant: int=1):
        """This draws up the contents of your backpack.
            Selling: !backpack sell "(partial) name of item"
            Trading: !backpack trade "name of item" cp @buyer amount
            Equip:   !backpack equip "(partial) name of item"
            or respond with "name of item" to backpack.
        """
        user = ctx.author
        if user.bot:
            return
        global users
        bkpk = "Items in Backpack \n"
        bkpklist = []
        cspouch = "🍱 Consumables "
        conslist = []
        inpouch = "⚗️ Ingredients "
        inslist = []
        if Userdata.users[str(user.id)]['consumables'] == {}:
            cspouch = "No Consumables owned."
        if switch == "None" or switch == "cons" or switch == "ingr":
            for item in Userdata.users[str(user.id)]['items']['backpack']: # added second if level for two handed weapons so their slots show properly.
                if len(Userdata.users[str(user.id)]['items']['backpack'][item]['slot']) == 1:
                    bkpklist.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']) + Color.none +")"+ Color.yellow + " ["+ Userdata.users[str(user.id)]['items']['backpack'][item]['slot'][0] + " slot]\n")
                else:
                    bkpklist.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']*2) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']*2) + Color.none +")"+ Color.yellow + " [two handed]\n")
            for item in Userdata.users[str(user.id)]['consumables']: # added second if level for two handed weapons so their slots show properly.
                    conslist.append(" - " + Color.get_color(item) + " ({}x)\n".format(Userdata.users[str(user.id)]['consumables'][item]['uses']))
            for item in Userdata.users[str(user.id)]['ingredients']:
                    inslist.append(" - {} ({}x)\n".format(Color.get_color(item),Userdata.users[str(user.id)]['ingredients'][item]['uses']))
            conslist.sort()
            bkpklist.sort()
            inslist.sort()
            if switch == "None":
                textline = Color.blue + "[{}´s baggage] \n\n".format(user.display_name) + Color.none + bkpk + "".join(bkpklist) + "\n (Reply with the name of an item or use !backpack equip \"name of item\" to equip it.)\n\n"
                if len(textline) > 1900: #split dangerously long texts into chunks.
                    chunks = []
                    while textline:
                        if len(textline) <= 1900:
                            chunks.append(textline)
                            break
                        split_index = textline.rfind("\n", 0, 1900)
                        if split_index == -1:
                            # The chunk is too big, so everything until the next newline is deleted
                            try:
                                textline = textline.split("\n", 1)[1]
                            except IndexError:
                                # No "\n" in textline, i.e. the end of the input text was reached
                                break
                        else:
                            chunks.append(textline[:split_index+1])
                            textline = textline[split_index+1:]
                    for chunk in chunks:
                        await ctx.send("```ansi\n" + chunk + "```")
                        await asyncio.sleep(0.3)
                else:
                    await ctx.send("```ansi\n"+ textline +"```")
                await ctx.send("```ansi\n"+ cspouch + "\n" + "".join(conslist) + "\n```")
                await ctx.send("```ansi\n"+ inpouch + "\n" + "".join(inslist) + "\n```")
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    return
                if not reply:
                    return
                else:
                    if not " sell " in reply.content.lower() and not " trade " in reply.content.lower():
                        equip = {}
                        for item in Userdata.users[str(user.id)]['items']['backpack']:
                            if reply.content.lower() in item:
                                equip = {"itemname": item,"item": Userdata.users[str(user.id)]['items']['backpack'][item]}
                                break
                        if equip != {}: #not good to change dict size during iteration so I moved this outside the for loop.
                            await self.equip_item(ctx, equip, True)
            elif switch == "cons":
                await ctx.send("```ansi\n" + Color.blue + "[{}´s ".format(user.display_name) + cspouch + "bag] \n\n" + Color.none + "".join(conslist) + "\n```")
            elif switch == "ingr":
                await ctx.send("```ansi\n" + Color.blue + "[{}´s ".format(user.display_name) + inpouch + "bag] \n\n" + Color.none + "".join(inslist) + "\n```")
        elif switch == "equip":
            if item == "None" or not any([x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower()]):
                await ctx.send("You have to specify an item from your backpack to equip.")
                return
            lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower())
            if len(lookup) > 1:
                text = "```ansi\n"
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    return
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    equip = {"itemname": lookup[idx],"item": Userdata.users[str(user.id)]['items']['backpack'][lookup[idx]]}
                    await self.equip_item(ctx, equip, True)
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    return
            elif len(lookup) == 0:
                await ctx.send("I could not find that item, check your spelling.")
                return
            else:
                item = lookup[0]
                equip = {"itemname": item,"item": Userdata.users[str(user.id)]['items']['backpack'][item]}
                await self.equip_item(ctx, equip, True)
        elif switch == "sell": #new logic allows for bulk sales. It also always confirms the sale by yes/no query to avoid accidents.
            item = item.lower() #lowercasing in case some german put in captialized items. ;)
            if item == "None" or not any([x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower()]+[x for x in Userdata.users[str(user.id)]['consumables'] if item in x.lower()]+[x for x in Userdata.users[str(user.id)]['ingredients'] if item in x.lower()]):
                await ctx.send("You have to specify an item (or partial name) from your backpack to sell.")
                return
            lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower())
            lookup += list(x for x in Userdata.users[str(user.id)]['consumables'] if item in x.lower())
            lookup += list(x for x in Userdata.users[str(user.id)]['ingredients'] if item in x.lower())
            if any([x for x in lookup if "{.:'" in x.lower()]):
                device = [x for x in lookup if "{.:'" in x.lower()]
                await ctx.send("```ansi\n Your {} is refusing to be sold and bit your finger for trying. ```".format(Color.get_color(device)))
                return
            msg = await ctx.send("Do you want to sell these items {}?\n[If you are selling consumables and did not specify how many (eg. !b sell 'consumable' 3), all will be sold!]".format(str(lookup)))
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            try:
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
                try:
                    await msg.delete()
                except discord.Forbidden:  # cannot remove message try remove emojis
                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                        await msg.remove_reaction(key, ctx.bot.user)
            except asyncio.TimeoutError:
                try:
                    await msg.delete()
                except discord.Forbidden:  # cannot remove message try remove emojis
                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                        await msg.remove_reaction(key, ctx.bot.user)
            if pred.result: #user reacted with Yes.
                moneypile = 0
                if asking < 0:
                    await ctx.send("```css\n Hey! Don't let me catch you selling negative items again! ```")
                    return
                for item in lookup:
                    if item in Consumables.consbles.keys() and asking > 0:
                        if int(Userdata.users[str(user.id)]['consumables'][item]['uses']) > asking:
                            queryitem = {'itemname': item,'item': copy.deepcopy(Userdata.users[str(user.id)]['consumables'][item])}
                            queryitem['item']['uses'] = asking
                        else:
                            queryitem = {'itemname': item,'item': Userdata.users[str(user.id)]['consumables'].get(item)}
                    elif item in Userdata.users[str(user.id)]['ingredients'].keys() and asking > 0:
                        if int(Userdata.users[str(user.id)]['ingredients'][item]['uses']) > asking:
                            queryitem = {'itemname': item,'item': copy.deepcopy(Userdata.users[str(user.id)]['ingredients'][item])}
                            queryitem['item']['uses'] = asking
                        else:
                            queryitem = {'itemname': item,'item': Userdata.users[str(user.id)]['ingredients'].get(item)}
                    else:
                        queryitem = {'itemname': item,'item': Userdata.users[str(user.id)]['items']['backpack'].get(item, Userdata.users[str(user.id)]['consumables'].get(item, Userdata.users[str(user.id)]['ingredients'].get(item)))} #multiple fallbacks to other inventories needed when no sell amount is specified.
                    moneypile += await GobCog.sell(user,queryitem)
                    if item in Consumables.consbles.keys():
                        if int(Userdata.users[str(user.id)]['consumables'][item]['uses']) > asking and asking > 0:
                            Userdata.users[str(user.id)]['consumables'][item]['uses'] = int(Userdata.users[str(user.id)]['consumables'][item]['uses']) - asking
                        else:
                            Userdata.users[str(user.id)]['consumables'].pop(item)
                    elif item in Userdata.users[str(user.id)]['ingredients'].keys():
                        if int(Userdata.users[str(user.id)]['ingredients'][item]['uses']) > asking and asking > 0:
                            Userdata.users[str(user.id)]['ingredients'][item]['uses'] = int(Userdata.users[str(user.id)]['ingredients'][item]['uses']) - asking
                        else:
                            Userdata.users[str(user.id)]['ingredients'].pop(item)
                    else:
                        Userdata.users[str(user.id)]['items']['backpack'].pop(item)
                await ctx.send("Sold {} for {} copperpieces.".format(str(lookup),moneypile))
                await GobCog.save()
        elif switch == "trade":
            item = item.lower() #lowercasing in case some german put in captialized items. ;)
            if item == "None" or not any([x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower()]+[x for x in Userdata.users[str(user.id)]['consumables'] if item in x.lower()]+[x for x in Userdata.users[str(user.id)]['ingredients'] if item in x.lower()]):
                await ctx.send("You have to specify an item from your backpack to trade.")
                return
            if buyer == None:
                await ctx.send("You have to @ somebody to trade with.")
                return
            lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if item in x.lower())
            lookup += list(x for x in Userdata.users[str(user.id)]['consumables'] if item in x.lower())
            lookup += list(x for x in Userdata.users[str(user.id)]['ingredients'] if item in x.lower())
            if len(lookup) > 1:
                text = "```ansi\n"
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    return
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    item = lookup[idx]
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    return
            else:
                item = lookup[0]
            if "{.:'" in item:
                await ctx.send("```ansi\n Your {} does not want to leave you. ```".format(Color.get_color(item)))
                return
            if item in Consumables.consbles.keys():
                if quant <= 0:
                    await ctx.send("We don't deal with imaginary amounts of items, here.")
                    return
                elif Userdata.users[str(user.id)]['consumables'].get(item)['uses'] >= quant:
                    await ctx.send("{} wants to sell {}x {}.".format(user.display_name,quant,item))
                else:
                    await ctx.send("You only have {} doses of {} to sell.".format(Userdata.users[str(user.id)]['consumables'].get(item)['uses'],item))
                    return
            elif item in Userdata.users[str(user.id)]['ingredients'].keys():
                if quant <= 0:
                    await ctx.send("We don't deal with imaginary amounts of items, here.")
                    return
                elif Userdata.users[str(user.id)]['ingredients'][item].get('uses', 0) >= quant:
                    await ctx.send("{} wants to sell {}x {}.".format(user.display_name,quant,item))
                else:
                    await ctx.send("You only have {} doses of {} to sell.".format(Userdata.users[str(user.id)]['consumables'].get(item)['uses'],item))
                    return
            else:
                if len(Userdata.users[str(user.id)]['items']['backpack'][item]["slot"]) == 2: # two handed weapons add their bonuses twice
                    hand = "two handed"
                    att = Userdata.users[str(user.id)]['items']['backpack'][item]["att"]*2
                    cha = Userdata.users[str(user.id)]['items']['backpack'][item]["cha"]*2
                else:
                    if Userdata.users[str(user.id)]['items']['backpack'][item]["slot"][0] == "right" or Userdata.users[str(user.id)]['items']['backpack'][item]["slot"][0] == "left":
                        hand = Userdata.users[str(user.id)]['items']['backpack'][item]["slot"][0] + " handed"
                    else:
                        hand = Userdata.users[str(user.id)]['items']['backpack'][item]["slot"][0] + " slot"
                    att = Userdata.users[str(user.id)]['items']['backpack'][item]["att"]
                    cha = Userdata.users[str(user.id)]['items']['backpack'][item]["cha"]
                await ctx.send("{} wants to sell {}. (Attack: {}, Charisma: {} [{}])".format(user.display_name,item,str(att),str(cha),hand))
            msg = await ctx.send("Do you want to buy this item for {} cp?".format(str(asking)))
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, buyer)
            try:
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send("Trade timed out after one minute.")
            try:
                await msg.delete()
            except discord.Forbidden:  # cannot remove message try remove emojis
                for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                    await msg.remove_reaction(key, ctx.bot.user)
            if pred.result: #buyer reacted with Yes.
                spender = buyer
                to = user
                tradeitem = {}
                if await bank.can_spend(spender,asking):
                    bal = await bank.transfer_credits(spender, to, asking)
                    currency = await bank.get_currency_name(ctx.guild)
                    if item in Consumables.consbles.keys():
                        #logging.error("Trade Log: From: {}, To: {}, ToID: {}, Item: {}, Quantity: {}, Price: {}".format(buyer.display_name,user.display_name,str(user.id),item,str(quant),str(asking)))
                        if Userdata.users[str(user.id)]['consumables'][item]['uses'] > quant:
                            Userdata.users[str(user.id)]['consumables'][item]['uses'] = Userdata.users[str(user.id)]['consumables'][item]['uses'] - quant
                            tradeitem = copy.deepcopy(Userdata.users[str(user.id)]['consumables'][item])
                            tradeitem['uses'] = quant
                            if item in Userdata.users[str(buyer.id)]['consumables'].keys():
                                Userdata.users[str(buyer.id)]['consumables'][item]['uses'] = Userdata.users[str(buyer.id)]['consumables'][item].get("uses", 0) + int(tradeitem['uses'])
                            else:
                                Userdata.users[str(buyer.id)]['consumables'].update({item: tradeitem})
                        else:
                            tradeitem = Userdata.users[str(user.id)]['consumables'].pop(item)
                            if item in Userdata.users[str(buyer.id)]['consumables'].keys():
                                Userdata.users[str(buyer.id)]['consumables'][item]['uses'] = Userdata.users[str(buyer.id)]['consumables'][item].get("uses", 0) + int(tradeitem['uses'])
                            else:
                                Userdata.users[str(buyer.id)]['consumables'].update({item: tradeitem})
                    elif item in Userdata.users[str(user.id)]['ingredients'].keys():
                        #logging.error("Trade Log: From: {}, To: {}, ToID: {}, Item: {}, Quantity: {}, Price: {}".format(buyer.display_name,user.display_name,str(user.id),item,str(quant),str(asking)))
                        if Userdata.users[str(user.id)]['ingredients'][item]['uses'] > quant:
                            Userdata.users[str(user.id)]['ingredients'][item]['uses'] = Userdata.users[str(user.id)]['ingredients'][item]['uses'] - quant
                            tradeitem = copy.deepcopy(Userdata.users[str(user.id)]['ingredients'][item])
                            tradeitem['uses'] = quant
                            if item in Userdata.users[str(buyer.id)]['ingredients'].keys():
                                Userdata.users[str(buyer.id)]['ingredients'][item]['uses'] = Userdata.users[str(buyer.id)]['ingredients'][item].get("uses", 0) + int(tradeitem['uses'])
                            else:
                                Userdata.users[str(buyer.id)]['ingredients'].update({item: tradeitem})
                        else:
                            tradeitem = Userdata.users[str(user.id)]['ingredients'].pop(item)
                            if item in Userdata.users[str(buyer.id)]['ingredients'].keys():
                                Userdata.users[str(buyer.id)]['ingredients'][item]['uses'] = Userdata.users[str(buyer.id)]['ingredients'][item].get("uses", 0) + int(tradeitem['uses'])
                            else:
                                Userdata.users[str(buyer.id)]['ingredients'].update({item: tradeitem})
                    else:
                        tradeitem = Userdata.users[str(user.id)]['items']['backpack'].pop(item)
                        Userdata.users[str(buyer.id)]['items']['backpack'].update({item: tradeitem})
                    await GobCog.save()
                    await ctx.send(
                        "```ansi\n" + "{} traded to {} for {} {}```".format(
                            Color.get_color(item), buyer.display_name, asking, currency
                        ))
                else:
                    await ctx.send("You do not have enough copperpieces.")

    @commands.command(name="equip", aliases=['e'])
    @commands.guild_only()
    async def _equip(self, ctx, item: str="None"):
        """This directly equips an item from your backpack.
        """
        await GobCog._backpack(self,ctx,"equip",item,0,None,1)

    @commands.command(name="consumable", aliases=['c'])
    @commands.guild_only()
    async def _consumable(self, ctx):
        """This draws up a list of all your consumables.
        """
        await GobCog._backpack(self,ctx,"cons","None",0,None,1)

    @commands.command(name="ingredients", aliases=['i'])
    @commands.guild_only()
    async def _ingredients(self, ctx):
        """This draws up a list of all your alchemy ingredients.
        """
        await GobCog._backpack(self,ctx,"ingr","None",0,None,1)

    @commands.command()
    @commands.guild_only()
    @not_resting()
    @has_hp()
    async def give(self, ctx, amount: int=1, to: discord.Member=None):
        """This will transfer cp from you to a specified member.
            !give 10 @Elder Aramis
            will transfer 10 cp to Elder Aramis.
        """
        if to is None:
            await ctx.send("You need to specify who you want me to give your money to, " + ctx.author.display_name + ".")
        spender = ctx.author
        if await bank.can_spend(spender,amount):
            bal = await bank.transfer_credits(spender, to, amount)
        else:
            return await ctx.send("You do not have enough copperpieces.")
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```You transferred {3} {2}. {0} now has {1} {2}```".format(
                to.display_name, bal, currency, amount
            )
        )

    @commands.command()
    @commands.guild_only()
    async def lootfilter(self, ctx, comm: str="add", filteritem: str=None):
        """This will set up a lootfilter autoselling undesired items.
            !lootfilter add/remove dagger
            will add/remove "dagger" to/from the filter list. Use "!lootfilter clear" to empty filter.
        """
        user = ctx.author
        if filteritem is None:
            if comm == "clear":
                Userdata.users[str(user.id)]['lootfilter'] = []
                return await ctx.send("Lootfilter cleared.")
            if Userdata.users[str(user.id)]["lootfilter"] != []:
                Userdata.users[str(user.id)]['lootfilter'].sort()
                filteritems = []
                for item in Userdata.users[str(user.id)]['lootfilter']:
                    filteritems.append(Color.get_color(item))
                textline = "```ansi\n" + Color.blue + "[" + ctx.author.display_name + "s lootfilter]"+Color.none+"\n\n" + ",\n".join(filteritems) + "\n```"
                if len(textline) > 1900: #split dangerously long texts into chunks.
                    chunks = []
                    while textline:
                        if len(textline) <= 1900:
                            chunks.append(textline)
                            break
                        split_index = textline.rfind("\n", 0, 1900)
                        if split_index == -1:
                            # The chunk is too big, so everything until the next newline is deleted
                            try:
                                textline = textline.split("\n", 1)[1]
                            except IndexError:
                                # No "\n" in textline, i.e. the end of the input text was reached
                                break
                        else:
                            chunks.append(textline[:split_index+1])
                            textline = textline[split_index+1:]
                    for chunk in chunks:
                        await ctx.send("```ansi\n" + chunk + "```")
                        await asyncio.sleep(0.3)
                    return
                else:
                    return await ctx.send("```ansi\n" + Color.blue + "[" + ctx.author.display_name + "s lootfilter]\n\n" + ",\n".join(Userdata.users[str(user.id)]['lootfilter']) + "\n```")
            else:
                return await ctx.send("```ansi\n" + Color.blue + "[" + ctx.author.display_name + "s lootfilter is currently empty.]" + "\n```")
        else:
            if comm == "add":
                lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if filteritem.lower() in x.lower())
            elif comm == "remove":
                lookup = list(x for x in Userdata.users[str(user.id)]['lootfilter'] if filteritem.lower() in x.lower())
            if len(lookup) > 1:
                text = "```ansi\n"
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    ctx.command.reset_cooldown(ctx)
                    return
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    if  "{.:'" not in lookup[idx]:
                        filteritem = lookup[idx]
                    else:
                        await ctx.send("Tinkered devices cannot be on the filter.")
                        return
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    return
            elif len(lookup) == 0:
                lookup.append(filteritem)
            else: #len(lookup) equals 1 item
                if  "{.:'" not in lookup[0]:
                    filteritem = lookup[0]
                else:
                    await ctx.send("Tinkered devices cannot be on the filter.")
                    return
            if comm == "add":
                Userdata.users[str(user.id)]['lootfilter'].append(filteritem)
                await ctx.send(filteritem + " successfully added to lootfilter.")
                if filteritem in Userdata.users[str(user.id)]['items']['backpack'].keys():
                    litem = Userdata.users[str(user.id)]['items']['backpack'].get(filteritem)
                    price = await GobCog.sell(user, {"itemname": filteritem,"item":litem})
                    await ctx.send("**{}** autosold {} for {} copperpieces.".format(user.display_name,filteritem,price))
                    del Userdata.users[str(user.id)]['items']['backpack'][filteritem]
                return
            elif comm == "remove":
                if filteritem in Userdata.users[str(user.id)]['lootfilter']:
                    Userdata.users[str(user.id)]['lootfilter'].remove(filteritem)
                    return await ctx.send(filteritem + " removed from lootfilter.")
                else:
                    return await ctx.send(filteritem + " was never on your list. Maybe check your spelling.")
            elif comm == "clear":
                Userdata.users[str(user.id)]['lootfilter'] = []
                return await ctx.send("Lootfilter cleared.")

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def fund(self, ctx, amount: int=1, to: discord.Member=None):
        """[Admin] This will create cp for a specified member.
            !fund 10 @Elder Aramis
            will create 10 cp and add to Elder Aramis.
        """
        if to is None:
            return await ctx.send("You need to specify a receiving member, " + ctx.author.display_name + ".")
        bal = await bank.deposit_credits(to, amount)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```You funded {3} {2}. {0} now has {1} {2}```".format(
                to.display_name, bal, currency, amount
            )
        )

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def setbalance(self, ctx, amount: int=1, to: discord.Member=None):
        """[Admin] This will SET cp for a specified member.
            !setbalance 10 @Elder Aramis
            will set balance at 10 cp for Elder Aramis.
        """
        if to is None:
            return await ctx.send("You need to specify a receiving member, " + ctx.author.display_name + ".")
        bal = await bank.set_balance(to, amount)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```You set {0}s balance. {0} now has {1} {2}```".format(
                to.display_name, bal, currency, amount
            )
        )

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def getyerassoverhere(self, ctx):
        """[Admin] This will summon the trader asap.
        """
        await self.trader(ctx, True)

    '''
    @commands.command()                 # just used for playtesting quests.
    @checks.admin_or_permissions(administrator=True)
    async def testquest(self, ctx):
        """This will send you on a quest with 1 player.
        """
        await ctx.send("A valiant party assembled! **" + ctx.author.display_name + "** is going on a soloquest!")
        reward, participants, dead = await Quest.queste(ctx, [ctx.author.display_name])
        if reward is not None:
            for user in reward.keys():
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                await self.add_rewards(ctx, member, reward[user]["xp"], reward[user]["cp"], reward[user]["special"])
            for user in participants: #reset activated abilities
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if 'name' in Userdata.users[str(member.id)]['class']:
                    if Userdata.users[str(member.id)]['class']['name'] != "Ranger" and Userdata.users[str(member.id)]['class']['ability']:
                        Userdata.users[str(member.id)]['class']['ability'] = False
                    songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                    if Userdata.users[str(member.id)]['class']['name'] == "Bard" and songbonus != 0:
                        Userdata.users[str(member.id)]['class'].pop('basebonus')
                expired = []
                for buff in Userdata.users[str(member.id)]['buffs'].keys(): #reduce duration of active buffs
                    if Userdata.users[str(member.id)]['buffs'][buff]['duration'] <= 1:
                        expired.append(buff)
                    else:
                        Userdata.users[str(member.id)]['buffs'][buff]['duration'] = Userdata.users[str(member.id)]['buffs'][buff]['duration'] - 1
                for buff in expired: #remove buffs outside loop not to change size during iteration
                    Userdata.users[str(member.id)]['buffs'].pop(buff)
            if len(dead) > 0:
                casualties = " and ".join([", ".join(dead[:-1]),dead[-1]] if len(dead) > 2 else dead)
                await ctx.send("**" + casualties + "**" + " came back empty handed.")
            await GobCog.save()
    '''

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def compensate(self, ctx, xp: int=0, cp: int=0, normal: int=0, rare: int=0, epic: int=0, quest: int=0):
        """[Admin] This will award xp, cp and chests to all players.
            !compensate 10 12 1 0 0 0
            will give all users 10xp, 12cp and a normal chest.
        """
        global users
        for user in users:
            member = discord.utils.find(lambda m: m.id == int(user), ctx.guild.members)
            if member != None:
                await self.add_rewards(ctx, member, xp, cp, [normal,rare,epic,quest])
        await ctx.send("All users were compensated with {} xp, {} cp and [{},{},{},{}] [normal, rare, epic, quest] chests.".format(xp,cp,normal,rare,epic,quest))

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def compuser(self, ctx, xp: int=0, cp: int=0, normal: int=0, rare: int=0, epic: int=0, quest: int=0, user: discord.Member=None):
        """[Admin] This will award xp, cp and chests to the specified user.
            !compuser 10 12 1 0 0 0 @Elder_aramis
            will give the user 10xp, 12cp and a normal chest.
        """
        global users
        if user != None:
            await self.add_rewards(ctx, user, xp, cp, [normal,rare,epic,quest])
        else:
            user = ctx.author
            await self.add_rewards(ctx, ctx.author, xp, cp, [normal,rare,epic,quest])
        await ctx.send("**" + user.display_name + "** was compensated with {} xp, {} cp and [{},{},{},{}] [normal, rare, epic, quest] chests.".format(xp,cp,normal,rare,epic,quest))

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def saveandreload(self, ctx):
        """[Admin]
            This will save and reinitialize userdata.
        """
        await Userdata.saveandreload()
        await ctx.send('Userdata saved to and reloaded from text based database.')

    @commands.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def purgelooting(self, ctx):
        """[Admin/Moderator]
            This will clear the loot session list.
        """
        global looting
        looting.clear()
        await ctx.send('The active loot session list has been cleared.')

    @commands.command(require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def mod_reload(self, ctx: commands.Context):
        """Reloads goblinscomic cog.
        This will unload and then load the goblinscomic bot cog.
        """
        name = "gobcog"
        if name in ctx.bot.extensions:
                ctx.bot.unload_extension(name)
                await ctx.bot.remove_loaded_package(name)
                spec = await ctx.bot._cog_mgr.find_cog(name)
                await ctx.bot.load_extension(spec)
                await ctx.send('Bot module has been reloaded.')

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def additem(self, ctx, type: str=None, item: str=None, user: discord.Member=None):
        """[Admin] This will add/set a certain item, consumable or ingredient for a specified user.
            !additem consumable "{'.dust_of_midas':{'slot':['consumable'],'uses':12}}" @Elder_aramis
            !additem item "{'shiny sword':{'slot':['right'],'att':1,'cha':1}}" @Elder_aramis
            !additem ingredient "{'Daisy':{'uses':6}}" @Elder_aramis
        """
        # Note that only with items and ingredients with spaces in the name, the json bit ({}) needs to be wrapped as "{}".
        global users
        await ctx.send("{},{},{}".format(type,item,user))
        if item == None:
            return
        else:
            data = item.replace("'",'"')
            itemdict = json.loads(data)
        if user == None:
            user = ctx.author
        if type == "item":
            Userdata.users[str(user.id)]['items']['backpack'].update(itemdict)
        elif type == "consumable":
            Userdata.users[str(user.id)]['consumables'].update(itemdict)
        elif type == "ingredient":
            Userdata.users[str(user.id)]['ingredients'].update(itemdict)
        else:
            return
        await ctx.send("{} added/set for **".format(list(itemdict.keys())[0]) + user.display_name + "**")
        await Userdata.save()

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def delitem(self, ctx, type: str=None, item: str=None, user: discord.Member=None):
        """[Admin] This will remove a certain item, consumable or ingredient for a specified user.
            !delitem consumable .dust_of_midas @Elder_aramis
            !delitem item 'shiny sword' @Elder_aramis
            !delitem ingredient 'Daisy' @Elder_aramis
        """
        global users
        await ctx.send("{},{},{}".format(type,item,user))
        if item == None:
            return
        if user == None:
            user = ctx.author
        if type == "item":
            Userdata.users[str(user.id)]['items']['backpack'].pop(item)
        elif type == "consumable":
            Userdata.users[str(user.id)]['consumables'].pop(item)
        elif type == "ingredient":
            Userdata.users[str(user.id)]['ingredients'].pop(item)
        else:
            return
        await ctx.send("{} deleted for **".format(item) + user.display_name + "**")
        await Userdata.save()

    @commands.command(name="adventure", aliases=['a'])
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=125, type=commands.BucketType.guild)
    async def _adventure(self, ctx):
        """This will send you on an adventure!
            You play by reacting with the offered emojis.
        """
        global users
        await ctx.send("You feel adventurous, " + ctx.author.display_name + "?")
        reward, participants = await Adventure.simple(ctx)
        if reward is not None:
            print(reward, participants)
            for user in reward.keys():
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member != None:
                    await self.add_rewards(ctx, member, reward[user]["xp"], reward[user]["cp"], reward[user]["special"])
            for user in participants: #reset activated abilities
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member != None:
                    if 'name' in Userdata.users[str(member.id)]['class']:
                        if Userdata.users[str(member.id)]['class']['name'] != "Ranger" and Userdata.users[str(member.id)]['class']['ability']:
                            Userdata.users[str(member.id)]['class']['ability'] = False
                        songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                        if Userdata.users[str(member.id)]['class']['name'] == "Bard" and songbonus != 0:
                            Userdata.users[str(member.id)]['class'].pop('basebonus')
                            Userdata.users[str(member.id)]['class']['ability'] = False
                    expired = []
                    for buff in Userdata.users[str(member.id)]['buffs'].keys(): #reduce duration of active buffs
                        if buff != "rest":
                            if Userdata.users[str(member.id)]['buffs'][buff]['duration'] <= 1:
                                expired.append(buff)
                            else:
                                Userdata.users[str(member.id)]['buffs'][buff]['duration'] = Userdata.users[str(member.id)]['buffs'][buff]['duration'] - 1
                    for buff in expired: #remove buffs outside loop not to change size during iteration
                        Userdata.users[str(member.id)]['buffs'].pop(buff)
            await GobCog.save()

    @commands.command()
    @charge(amount=500)
    @not_resting()
    @has_hp()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def quest(self, ctx):
        """This will send you on a mighty quest!
            You play by reacting with the offered emojis.
            Available once per 10 minutes and costing 500 cp.
        """
        global users
        party = []
        modRole = discord.utils.get(ctx.guild.roles, name='Goblin Adventurer!')
        if modRole is not None:
            msg = await ctx.send(modRole.mention + "\n" + "**" + ctx.author.display_name + "** just spent 500 copperpieces in the inn, looking for a party to do a mighty quest. Do you accept (2 mins)?", allowed_mentions=discord.AllowedMentions(roles=True))
        else:
            msg = await ctx.send("**" + ctx.author.display_name + "** just spent 500 copperpieces in the inn, looking for a party to do a mighty quest. Do you accept (2 mins)?")
        start_adding_reactions(msg, "✅")
        await asyncio.sleep(120)
        message = await ctx.message.channel.fetch_message(msg.id)
        try:
            reaction = next(filter(lambda x: x.emoji == "✅", message.reactions), None)
        except AttributeError:
            return await ctx.send("The message id provided is either invalid or is not from that channel.")
        wannabees = await reaction.users().flatten()
        for user in wannabees:
            if not user.bot:
                party.append(user.display_name)
        if ctx.author.display_name not in party:
            party.append(ctx.author.display_name)
        try:
            await msg.delete()
        except discord.Forbidden:  # cannot remove message try remove emoji
            await msg.remove_reaction("✅", ctx.bot.user)
        for user in party:
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member != None:
                if Userdata.users[str(member.id)]['lvl'] < 15:
                    party.remove(user)
                    await ctx.send("Sorry **{}**. You need to be at least level 15 to go on a quest.".format(user))
        if len(party) <= 1:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Not enough heroes are willing or able to go on this quest. Try again later.")
        await asyncio.sleep(1.5)
        text_party = " and ".join([", ".join(party[:-1]),party[-1]] if len(party) > 2 else party)
        await ctx.send("A valiant party assembled! **" + text_party + "** are going on a quest!")
        reward, participants, dead = await Quest.queste(ctx, party)
        if reward is not None:
            for user in reward.keys():
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member != None:
                    await self.add_rewards(ctx, member, reward[user]["xp"], reward[user]["cp"], reward[user]["special"])
                else:
                    await ctx.send("There was a problem retrieving user information for **" + user + "**. Please tell locastan.")
            for user in participants: #reset activated abilities
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member != None:
                    if 'name' in Userdata.users[str(member.id)]['class']:
                        if Userdata.users[str(member.id)]['class']['name'] != "Ranger" and Userdata.users[str(member.id)]['class']['ability']:
                            Userdata.users[str(member.id)]['class']['ability'] = False
                        songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                        if Userdata.users[str(member.id)]['class']['name'] == "Bard" and songbonus != 0:
                            Userdata.users[str(member.id)]['class'].pop('basebonus')
                            Userdata.users[str(member.id)]['class']['ability'] = False
                expired = []
                for buff in Userdata.users[str(member.id)]['buffs'].keys(): #reduce duration of active buffs
                    if buff != "rest":
                        if Userdata.users[str(member.id)]['buffs'][buff]['duration'] <= 1:
                            expired.append(buff)
                        else:
                            Userdata.users[str(member.id)]['buffs'][buff]['duration'] = Userdata.users[str(member.id)]['buffs'][buff]['duration'] - 1
                for buff in expired: #remove buffs outside loop not to change size during iteration
                    Userdata.users[str(member.id)]['buffs'].pop(buff)
            if len(dead) > 0:
                casualties = " and ".join([", ".join(dead[:-1]),dead[-1]] if len(dead) > 2 else dead)
                await ctx.send("**" + casualties + "**" + " came back empty handed.")
            await GobCog.save()


    @commands.command(name="negaverse", aliases=['nv'])
    @commands.guild_only()
    @not_resting()
    @has_hp()
    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    async def _negaverse(self, ctx, amount: int = None):
        """This will send you to fight a nega-member!
            !nv amount_of_cp
        """
        spender = ctx.message.author
        if amount == None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to specify some cp to convert into energy before entering.")
        if await bank.can_spend(spender,amount):
            await bank.withdraw_credits(spender, amount)
        else:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You don't have enough copperpieces.")
        negachar = "**Nega-" + random.choice(ctx.message.guild.members).name + "**"
        await ctx.send("You enter the negaverse and meet " + negachar + ".")
        roll = random.randint(1,20)
        versus = random.randint(1,20)
        if roll== 1:
            await ctx.send("**" + ctx.author.display_name + "**" + " fumbled and died to " + negachar + "'s savagery.")
        elif roll == 20:
            await ctx.send("**" + ctx.author.display_name + "**" + " decapitated " + negachar + ". You gain {} xp and {} cp.".format(amount*2, amount))
            await self.add_rewards(ctx, ctx.message.author, amount*2, amount, False)
        elif roll > versus:
            await ctx.send("**" + ctx.author.display_name + "** 🎲({})".format(roll) + " bravely defeated " + negachar + " 🎲({}). You gain {} xp.".format(versus, amount))
            await self.add_rewards(ctx, ctx.message.author, amount, 0, False)
        elif roll == versus:
            await ctx.send("**" + ctx.author.display_name + "** 🎲({})".format(roll) + " almost killed " + negachar + " 🎲({}).".format(versus))
        else:
            await ctx.send("**" + ctx.author.display_name + "** 🎲({})".format(roll) + " was killed by " + negachar + " 🎲({}).".format(versus))

    '''  #uncomment once the custom error handler has been released.
    @commands.error
    async def commands_error_handler(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            s = int(s)
            m = int(m)
            h = int(h)
            if h == 0 and m == 0:
                out = "{:02d}s".format(s)
            elif h == 0:
                out = "{:02d}:{:02d}s".format(m, s)
            else:
                out = "{:01d}:{:02d}:{:02d}s".format(h, m, s)
            if ctx.command.qualified_name == "brew":
                lookup = list(Userdata.users[str(ctx.author.id)]['ingredients'])
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {} ({}x)\n".format(num, name, Userdata.users[str(user.id)]['ingredients'][name].get('uses', 0)))
                await ctx.send("⏳ " + "Don't be hasty, {}. You can use !{} again in: ".format(ctx.author.display_name, ctx.command.qualified_name) + out + "\n Here is a list of your ingredients for reference: \n" + text)
            elif h == 0 and m < 3:
                await Adventure.countdown(ctx, error.retry_after, "I feel a little tired now. !{} is available again in: ".format(ctx.command.qualified_name))
            else:
                await ctx.send("⏳ " + "Don't be hasty, {}. You can use !{} again in: ".format(ctx.author.display_name, ctx.command.qualified_name) + out)
        else:
            await ctx.bot.on_command_error(ctx, error, unhandled_by_cog=True)
        '''

    @commands.Cog.listener()
    async def on_message(self, message):
        global users
        if not message.author.bot:
            await self.update_data(Userdata.users, message.author)
            if GobCog.last_trade == 0: #this shuts hawls bro up for 3 hours after a cog reload
                GobCog.last_trade = time.time()
            if "rpg-game" in message.channel.name: #restrict hawls bro to rpg-game channel.
                roll = random.randint(1,20)
                if roll == 20:
                    ctx = await self.bot.get_context(message)
                    await self.trader(ctx, False)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        global users
        await self.update_data(Userdata.users, member)

        await GobCog.save()

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        global users
        Userdata.users.pop(str(member.id))

        await GobCog.save()

    @staticmethod
    async def equip_item(ctx, item, from_backpack):
        global users
        user = ctx.author
        if not 'items' in Userdata.users[str(user.id)].keys(): # if the user has an older account or something went wrong, create empty items slot.
            Userdata.users[str(user.id)]['items'] = {"left":{},"right":{},"ring":{},"charm":{},"backpack": {}}
        for slot in item['item']["slot"]:
            if Userdata.users[str(user.id)]['items'][slot] == {}:
                Userdata.users[str(user.id)]['items'][slot][item['itemname']] = item['item']
                Userdata.users[str(user.id)]['att'] += item['item']['att']
                Userdata.users[str(user.id)]['cha'] += item['item']['cha']
                await ctx.send("You equipped {}.".format(item['itemname']))
            else:
                olditem = Userdata.users[str(user.id)]['items'][slot]
                olditemname = list(olditem.keys())[0]
                for oslot in olditem[list(olditem.keys())[0]]['slot']:
                    Userdata.users[str(user.id)]['items'][oslot] = {}
                    Userdata.users[str(user.id)]['att'] -= olditem[list(olditem.keys())[0]]['att']     # keep in mind that double handed items grant their bonus twice so they remove twice
                    Userdata.users[str(user.id)]['cha'] -= olditem[list(olditem.keys())[0]]['cha']
                Userdata.users[str(user.id)]['items'][slot][item['itemname']] = item['item']
                Userdata.users[str(user.id)]['att'] += item['item']['att']
                Userdata.users[str(user.id)]['cha'] += item['item']['cha']
                if olditemname in Userdata.users[str(user.id)]['items']['backpack'].keys():
                    price = await GobCog.sell(user,{'itemname': olditemname,'item':olditem.get(olditemname)})
                    await ctx.send("**{}** already in backpack: Sold for {} copperpieces.".format(olditemname,price))
                else:
                    Userdata.users[str(user.id)]['items']['backpack'].update(olditem)
                    await ctx.send("You equipped {} and put {} into your backpack.".format(item['itemname'],list(olditem.keys())[0]))
        if from_backpack:
            del Userdata.users[str(user.id)]['items']['backpack'][item['itemname']]
        await GobCog.calcstats(ctx,user.id)
        await GobCog.save()

    @staticmethod
    async def calcstats(ctx,userID):
        userID = str(userID)
        attb = int(Userdata.users[userID]['skill']['att']) + int(Userdata.users[userID]['buffs'].get('att', {'bonus':0})['bonus'])
        chab = int(Userdata.users[userID]['skill']['cha']) + int(Userdata.users[userID]['buffs'].get('cha', {'bonus':0})['bonus'])
        signa = "+" if attb > 0 else ""
        signc = "+" if chab > 0 else ""
        if Userdata.users[str(userID)]['class']['name']=="Monk":
            # calculate monk passive bonus
            monkbonus = [0,0]
            monkbonus = await Classes.calc_monkbonus(ctx,userID)
            await ctx.send("Your new stats: **Attack**: {} [{}{}], **Diplomacy**: {} [{}{}]{}.".format(Userdata.users[userID]['att'],signa,attb,Userdata.users[userID]['cha'],signc,chab," Max. Monkbonus: ({}ATT/{}DIPL)".format(str(monkbonus[0]),str(monkbonus[1]))))
        else:
            await ctx.send("Your new stats: **Attack**: {} [{}{}], **Diplomacy**: {} [{}{}].".format(Userdata.users[userID]['att'],signa,attb,Userdata.users[userID]['cha'],signc,chab))

    @staticmethod
    async def update_data(users, user):
        if str(user.id) not in users:
            print('Setting up account for', user.display_name + '.')
            Userdata.users[str(user.id)] = {}
            Userdata.users[str(user.id)]['exp'] = 0
            Userdata.users[str(user.id)]['lvl'] = 1
            Userdata.users[str(user.id)]['hp'] = 5
            Userdata.users[str(user.id)]['base_hp'] = 5
            Userdata.users[str(user.id)]['resting'] = {}
            Userdata.users[str(user.id)]['att'] = 0
            Userdata.users[str(user.id)]['cha'] = 0
            Userdata.users[str(user.id)]['treasure'] = [0,0,0,0]
            Userdata.users[str(user.id)]['lootfilter'] = []
            Userdata.users[str(user.id)]['items'] = {"left":{},"right":{},"ring":{},"charm":{},"backpack": {}}
            Userdata.users[str(user.id)]['consumables'] = {}
            Userdata.users[str(user.id)]['ingredients'] = {}
            Userdata.users[str(user.id)]['buffs'] = {}
            Userdata.users[str(user.id)]['name'] = {}
            Userdata.users[str(user.id)]['name'] = user.display_name
            Userdata.users[str(user.id)]['class'] = {}
            Userdata.users[str(user.id)]['class'] = {'name': "Hero", 'ability': False, 'desc': "Your basic adventuring hero."}
            Userdata.users[str(user.id)]['skill'] = {}
            Userdata.users[str(user.id)]['skill'] = {'pool': 0, 'att': 0, 'cha': 0}
            await GobCog.save()


    @staticmethod
    async def add_rewards(ctx, user, exp, cp, special):
        global users
        Userdata.users[str(user.id)]['exp'] += exp
        await bank.deposit_credits(user, cp)
        await GobCog.level_up(ctx, users, user)
        if special != False and special != [0,0,0,0]:
            if not 'treasure' in Userdata.users[str(user.id)].keys():
                Userdata.users[str(user.id)]['treasure'] = [0,0,0,0]
            Userdata.users[str(user.id)]['treasure'] = [sum(x) for x in zip(Userdata.users[str(user.id)]['treasure'], special)]

    @staticmethod
    async def save():
        await Userdata.save()

    @staticmethod
    async def level_up(ctx, users, user):
        exp = Userdata.users[str(user.id)]['exp']
        lvl_start = Userdata.users[str(user.id)]['lvl']
        lvl_end = int(exp ** (1/4))

        if lvl_start < lvl_end: #recalculate free skillpoint pool based on new level and already spent points.
            await ctx.send('{} is now level {}!'.format(user.display_name,lvl_end))
            Userdata.users[str(user.id)]['lvl'] = lvl_end
            Userdata.users[str(user.id)]['base_hp'] = 5 + lvl_end
            Userdata.users[str(user.id)]['hp'] = 5 + lvl_end
            Userdata.users[str(user.id)]['skill']['pool'] = int(lvl_end / 5) - (Userdata.users[str(user.id)]['skill']['att']+Userdata.users[str(user.id)]['skill']['cha'])
            if Userdata.users[str(user.id)]['skill']['pool'] > 0:
                await ctx.send('You have skillpoints available.')

    @staticmethod
    async def sell(user,item):
        if "[" in item['itemname']:
            base = (500,1000)
        elif "." in item['itemname']:
            base = (200,500)
        else:
            base = (10,200)
        if "(+1)*" in item['itemname']:
            magicmod = 2
        elif "(+2)*" in item['itemname']:
            magicmod = 3
        elif "(+3)*" in item['itemname']:
            magicmod = 4
        elif "(+4)*" in item['itemname']:
            magicmod = 6
        elif "(+5)*" in item['itemname']:
            magicmod = 10
        else:
            magicmod = 1
        if 'slot' not in item['item']:
            price = random.randint(base[0]*2,base[1]*2)*max(item['item']['uses'],1)
        elif item['item']['slot'] == ['consumable']:
            price = random.randint(base[0],base[1])*max(item['item']['uses'],1)
        else:
            price = random.randint(base[0],base[1])*max(item['item']['att']+item['item']['cha'],1)*magicmod
        await bank.deposit_credits(user, price)
        return(price)

    @staticmethod
    async def trader(ctx,summoned):

        async def handle_buy(itemindex, user, stock, msg):
            global users
            titem = copy.deepcopy(stock[itemindex])
            #print("copyitem: {}".format(item))
            spender = user
            react = None
            reply = None
            channel = ctx.bot.get_channel(865203053777780766) #restrict trader to dodo channel on live server
            #channel = ctx.bot.get_channel(504934418289262597) #restrict trader to general channel on test server
            if channel is not None:
                calcprice = 0
                await channel.send("Tell me **{}**, how many {} do you want?".format(user.display_name, titem['itemname']))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx,channel,user), timeout=30)
                except asyncio.TimeoutError:
                    await channel.send("I don't have all day, you know.")
                if reply != None:
                    if reply.content.isdigit() and int(reply.content) > 0:
                        calcprice = int(titem['price'])*int(reply.content)
                    else:
                        await channel.send("Sorry, but that is not a proper number. Try again.")
                if calcprice != 0 and await bank.can_spend(spender,calcprice):
                    await bank.withdraw_credits(spender, calcprice)
                    if 'chest' in titem['itemname']:
                        if titem['itemname'] == ".rare_chest":
                            Userdata.users[str(user.id)]['treasure'][1] += int(reply.content)
                        elif titem['itemname'] == "[epic chest]":
                            Userdata.users[str(user.id)]['treasure'][2] += int(reply.content)
                        else:
                            Userdata.users[str(user.id)]['treasure'][0] += int(reply.content)
                    elif titem['itemname'] in Consumables.consbles.keys():
                            if titem['itemname'] in Userdata.users[str(user.id)]['consumables'].keys():
                                #print("Cons in pouch before: {}".format(Userdata.users[str(user.id)]['consumables'][item['itemname']]['uses']))
                                Userdata.users[str(user.id)]['consumables'][titem['itemname']]['uses'] = Userdata.users[str(user.id)]['consumables'][titem['itemname']].get("uses", 0) + int(reply.content)
                                #print("Uses added: {}, Uses in userpouch: {}".format(item['item']['uses'],Userdata.users[str(user.id)]['consumables'][item['itemname']]['uses']))
                            else:
                                titem['item']['uses'] = int(reply.content)
                                Userdata.users[str(user.id)]['consumables'].update(copy.deepcopy({titem['itemname']:titem['item']}))
                    else:
                        if titem['itemname'] in Userdata.users[str(user.id)]['items']['backpack'].keys() or titem['itemname'] in Userdata.users[str(user.id)]['lootfilter']:
                            price = await GobCog.sell(user,titem)
                            price = price * int(reply.content)
                            await channel.send("**{}** sold for {} copperpieces.".format(titem['itemname'],price))
                        else:
                            Userdata.users[str(user.id)]['items']['backpack'].update(copy.deepcopy({titem['itemname']:titem['item']}))
                            price = await GobCog.sell(user,titem)
                            price = price * (int(reply.content)-1)
                            await channel.send("Excess **{}** sold for {} copperpieces.".format(titem['itemname'],price))
                    await GobCog.save()
                    if titem['itemname'] in Consumables.consbles.keys():
                        await channel.send("{} paid {} cp and put {}x {} into the backpack.".format(user.display_name,str(calcprice),int(reply.content),titem['itemname']))
                    else:
                        await channel.send("{} bought the {} for {} cp and put it into the backpack.".format(user.display_name,titem['itemname'],str(calcprice)))
                elif calcprice != 0 and not await bank.can_spend(spender,calcprice):
                    await channel.send("You do not have enough copperpieces.")
                try:
                    timeout = GobCog.last_trade+1200-time.time()
                    if timeout <= 0:
                        timeout = 0
                    react, user = await ctx.bot.wait_for(
                        "reaction_add",
                        check=CustomPredicate.with_emojis(tuple(controls.keys()), msg),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
                    try:
                        await msg.delete()
                    except discord.Forbidden:  # cannot remove all reactions
                        for key in controls.keys():
                            await message.remove_reaction(key, ctx.bot.user)
                if react != None and user:
                    #print(stock)
                    await handle_buy(controls[react.emoji], user, stock, msg)

        em_list = ReactionPredicate.NUMBER_EMOJIS[:5]
        react = False
        controls = {em_list[1]: 0, em_list[2]: 1, em_list[3]: 2, em_list[4]: 3}
        modRole = discord.utils.get(ctx.guild.roles, name='Goblin Adventurer!')
        if modRole is not None:
            text = modRole.mention + "\n" + "```ansi\n"+ Color.red + "[Alchemist Dodo is bringing the cart around!]```"
        else:
            text = "```ansi\n" + Color.red + "[Alchemist Dodo is bringing the cart around!]```"
        if GobCog.last_trade == 0 or summoned:
            GobCog.last_trade = time.time()
        elif GobCog.last_trade >= time.time()-21600: #trader can return after 6 hours have passed since last visit.
            return #silent return.
        GobCog.last_trade = time.time()
        stock = await Treasure.trader_get_items()
        for index, name in enumerate(stock):
            sitem = copy.deepcopy(stock[index])
            if "chest" not in sitem['itemname']:
                if sitem['item']['slot'] == ['consumable']:
                    text += "```ansi\n" + "[{}] {} for {} cp each.".format(str(index+1),Color.get_color(sitem['itemname']),sitem['price'])+ " ```"
                    continue
                else:
                    if len(sitem['item']['slot']) == 2: # two handed weapons add their bonuses twice
                        hand = "two handed"
                        att = sitem['item']["att"]*2
                        cha = sitem['item']["cha"]*2
                    else:
                        if sitem['item']['slot'][0] == "right" or sitem['item']["slot"][0] == "left":
                            hand = sitem['item']['slot'][0] + " handed"
                        else:
                            hand = sitem['item']['slot'][0] + " slot"
                        att = sitem['item']["att"]
                        cha = sitem['item']["cha"]
                    text += "```ansi\n" + "[{}] {} ("+Color.red+"ATT"+Color.none+": {}, "+Color.blue+"DPL"+Color.none+": {} [{}]) for {} cp.".format(str(index+1),Color.get_color(sitem['itemname']),str(att),str(cha),hand,sitem['price'])+ " ```"
            else:
                text += "```ansi\n" + "[{}] {} for {} cp.".format(str(index+1),Color.get_color(sitem['itemname']),sitem['price'])+ " ```"
        text += "Do you want to buy any of these fine items? Tell me which one below:"
        channel = ctx.bot.get_channel(865203053777780766) #restrict trader to loot-spam channel on live server
        #channel = ctx.bot.get_channel(504934418289262597) #restrict trader to general channel on test server
        if channel is not None:
            msg = await channel.send(text, allowed_mentions=discord.AllowedMentions(roles=True))
        else:
            print("channel not found!")
            return
        #msg = await ctx.send(text) #old line for bug testing on beta server.
        Adventure.start_adding_reactions(msg, controls.keys(), ctx.bot.loop)
        try:
            timeout = GobCog.last_trade+1200-time.time()
            if timeout <= 0:
                timeout = 0
            Treasure.countdown(ctx, timeout, "The cart will leave in: ") #need unique countdown or else adventure countdown will overwrite the ticker...
            react, user = await ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), msg),
                timeout=timeout
            )
        except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
            try:
                await msg.delete()
            except discord.Forbidden:  # cannot remove all reactions
                for key in controls.keys():
                    await message.remove_reaction(key, ctx.bot.user)
        if react and user:
            await handle_buy(controls[react.emoji], user, stock, msg)
