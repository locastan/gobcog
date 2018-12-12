import json
from redbot.core.data_manager import cog_data_path
import random
import discord
import asyncio
import time
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from .custompredicate import CustomPredicate
from redbot.core.commands.context import Context
from redbot.core import commands, bank, checks
from .adventure import Adventure
from .treasure import Treasure
from .classes import Classes

BaseCog = getattr(commands, "Cog", object)
users = {}

class GobCog(BaseCog):

    fp = cog_data_path(None, "gobcog") / 'users.json'  # this looks for users.json inside your RedBot/cogs/gobcog folder. Needs to be setup once: create the folder, make a users.json with just an empty {} inside.
    global users
    with fp.open('r') as f:
        users = json.load(f)
    last_trade = 0
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
        for slot in users[str(user.id)]['items']:
            if users[str(user.id)]['items'][slot] and slot != "backpack":
                equipped.update(users[str(user.id)]['items'][slot])
        if item == "None" or not any([x for x in equipped if item in x.lower()]):
            if item == "{.:'":
                return
            else:
                return await ctx.send("You do not have an item matching {} equipped.".format(item))
        else:
            lookup = list(x for x in equipped if item in x.lower())
            for olditem in lookup:
                for slot in equipped[olditem].get('slot'):
                    users[str(user.id)]['items'][slot] = {}
                    users[str(user.id)]['att'] -= int(equipped[olditem].get('att'))     # keep in mind that double handed items grant their bonus twice so they remove twice
                    users[str(user.id)]['cha'] -= int(equipped[olditem].get('cha'))
                users[str(user.id)]['items']['backpack'].update({olditem: equipped[olditem]}) # TODO: Change data structure of items dict so you can have duplicate items because of key duplicate overwrite in dicts.
                await ctx.send("You removed {} and put it into your backpack.".format(olditem))
            await ctx.send("Your new stats: **Attack**: {} [+{}], **Diplomacy**: {} [+{}].".format(users[str(user.id)]['att'],users[str(user.id)]['skill']['att'],users[str(user.id)]['cha'],users[str(user.id)]['skill']['cha']))


    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def give_loot(self, ctx, type: str="normal", user: discord.Member=None):
        """[Admin] This rewards a treasure chest to a specified member.
            !give_loot normal @locastan
            will give locastan a normal chest.
            (Adding "rare" or "epic" to command, creates rare and epic chests.)
        """
        global users
        if user is None:
            user = ctx.author
        if not 'treasure' in users[str(user.id)].keys():
            users[str(user.id)]['treasure'] = [0,0,0]
        if type == "rare":
            users[str(user.id)]['treasure'][1] += 1
        elif type == "epic":
            users[str(user.id)]['treasure'][2] += 1
        else:
            users[str(user.id)]['treasure'][0] += 1
        await ctx.send(
            "```{} now owns {} normal, {} rare and {} epic chests.```".format(
                user.display_name, str(users[str(user.id)]['treasure'][0]),str(users[str(user.id)]['treasure'][1]),str(users[str(user.id)]['treasure'][2])))
        with GobCog.fp.open('w') as f:
            json.dump(users, f)

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
            i = iter(users[str(user)]['items'])
            attack = 0
            diplomacy = 0
            for slot in i:
                if users[str(user)]['items'][slot] and slot != "backpack":
                    item = list(users[str(user)]['items'][slot].keys())[0]
                    attack += users[str(user)]['items'][slot][item]['att']
                    diplomacy += users[str(user)]['items'][slot][item]['cha']
            users[str(user)]['att'] = attack
            users[str(user)]['cha'] = diplomacy
            users[str(user)]['name'] = {}
            users[str(user)]['name'] = member.display_name
            if 'class' not in users[str(user)]:
                users[str(user)]['class'] = {}
            if users[str(user)]['class'] == {}:
                users[str(user)]['class'] = {'name': "Hero", 'ability': False, 'desc': "Your basic adventuring hero."}
            if 'skill' not in users[str(user)]:
                users[str(user)]['skill'] = {}
                users[str(user)]['skill'] = {'pool': 0, 'att': 0, 'cha': 0}
            print(users[str(user)]['name']+": "+str(int(users[str(user)]['lvl'] / 5)) + "-" + str(users[str(user)]['skill']['att']+users[str(user)]['skill']['cha']))
            users[str(user)]['skill']['pool'] = int(users[str(user)]['lvl'] / 5) - (users[str(user)]['skill']['att']+users[str(user)]['skill']['cha'])
        for userID in deadsies:
            users.pop(userID)
        with GobCog.fp.open('w') as f:
            json.dump(users, f)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=43200, type=commands.BucketType.user)
    async def pet(self,ctx, switch:str=None):
        """This allows a Ranger to tame or set free a pet or send it foraging (once per day).
            !pet
            !pet forage
            !pet free
        """
        global users
        user = ctx.author.id
        if 'name' in users[str(user)]['class'] and users[str(user)]['class']['name'] != "Ranger":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Ranger to do this.")
        else:
            if switch == None or users[str(user)]['class']['ability'] == False:
                pet = await Classes.pet(ctx, users, None)
                if pet != None:
                    ctx.command.reset_cooldown(ctx) #reset cooldown so ppl can forage right after taming a new pet.
                    users[str(user)]['class']['ability'] = {'active': True, 'pet': pet}
                    with GobCog.fp.open('w') as f:
                        json.dump(users, f)
            elif switch == 'forage':
                item = await Classes.pet(ctx, users, switch)
                if item != None:
                    if item['equip'] == "sell":
                        price = await GobCog.sell(ctx.author,item)
                        await ctx.send("{} sold the {} for {} copperpieces.".format(ctx.author.display_name,item['itemname'],price))
                    elif item['equip'] == "equip":
                        equip = {"itemname": item['itemname'],"item": item['item']}
                        await self.equip_item(ctx, equip, False)
                    else:
                        users[str(user)]['items']['backpack'].update({item['itemname']: item['item']})
                        await ctx.send("{} put the {} into the backpack.".format(ctx.author.display_name,item['itemname']))
                        with GobCog.fp.open('w') as f:
                            json.dump(users, f)
            elif switch == 'free':
                await Classes.pet(ctx, users, switch)
                with GobCog.fp.open('w') as f:
                    json.dump(users, f)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def rage(self,ctx):
        """This allows a Berserker to add substantial attack bonuses for one battle.
        """
        global users
        user = ctx.author.id
        if 'name' in users[str(user)]['class'] and users[str(user)]['class']['name'] != "Berserker":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Berserker to do this.")
        else:
            users = await Classes.rage(ctx, users)


    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def bless(self,ctx):
        """This allows a praying Cleric to add substantial bonuses for heroes fighting the battle.
        """
        global users
        user = ctx.author.id
        if 'name' in users[str(user)]['class'] and users[str(user)]['class']['name'] != "Cleric":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Cleric to do this.")
        else:
            users = await Classes.bless(ctx, users)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def sing(self,ctx):
        """This allows a Bard to add substantial diplomacy bonuses for one battle.
        """
        global users
        user = ctx.author.id
        if 'name' in users[str(user)]['class'] and users[str(user)]['class']['name'] != "Bard":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Bard to do this.")
        else:
            users = await Classes.sing(ctx, users)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=43200, type=commands.BucketType.user)
    async def forge(self,ctx):
        """This allows a Tinkerer to forge two items into a device.
        """
        global users
        user = ctx.author.id
        if 'name' in users[str(user)]['class'] and users[str(user)]['class']['name'] != "Tinkerer":
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to be a Tinkerer to do this.")
        else:
            bkpk = ""
            consumed = []
            forgeables = len(users[str(user)]['items']['backpack']) - sum("{.:'" in x for x in users[str(user)]['items']['backpack'])
            if forgeables <= 1:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("You need at least two forgeable items in your backpack to forge.")
            for item in users[str(user)]['items']['backpack']:
                if "{.:'" not in item:
                    if len(users[str(user)]['items']['backpack'][item]['slot']) == 1:
                        bkpk += " - " + item + " - (ATT: "+ str(users[str(user)]['items']['backpack'][item]['att']) + " | DPL: "+ str(users[str(user)]['items']['backpack'][item]['cha']) +" ["+ users[str(user)]['items']['backpack'][item]['slot'][0] + " slot])\n"
                    else:
                        bkpk += " - " + item + " -(ATT: "+ str(users[str(user)]['items']['backpack'][item]['att']*2) + " | DPL: "+ str(users[str(user)]['items']['backpack'][item]['cha']*2) +" [two handed])\n"
            await ctx.send(
                "```css\n[{}'s forgeables] \n\n```".format(
                    ctx.author.display_name
                ) + "```css\n" + bkpk + "\n (Reply with the full or partial name of item 1 to select for forging. Try to be specific.)```"
            )
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("I don't have all day, you know.")
            item1 = {}
            for item in users[str(user)]['items']['backpack']:
                if reply.content.lower() in item:
                    if  "{.:'" not in item:
                        item1 = users[str(user)]['items']['backpack'].get(item)
                        consumed.append(item)
                        break
                    else:
                        ctx.command.reset_cooldown(ctx)
                        return await ctx.send("Tinkered devices cannot be reforged.")
            if item1 == {}:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("I could not find that item, check your spelling.")
            bkpk = ""
            for item in users[str(user)]['items']['backpack']:
                if item not in consumed and "{.:'" not in item:
                    if len(users[str(user)]['items']['backpack'][item]['slot']) == 1:
                        bkpk += " - " + item + " - (ATT: "+ str(users[str(user)]['items']['backpack'][item]['att']) + " | DPL: "+ str(users[str(user)]['items']['backpack'][item]['cha']) +" ["+ users[str(user)]['items']['backpack'][item]['slot'][0] + " slot])\n"
                    else:
                        bkpk += " - " + item + " -(ATT: "+ str(users[str(user)]['items']['backpack'][item]['att']*2) + " | DPL: "+ str(users[str(user)]['items']['backpack'][item]['cha']*2) +" [two handed])\n"
            await ctx.send(
                "```css\n[{}'s forgeables] \n\n```".format(
                    ctx.author.display_name
                ) + "```css\n" + bkpk + "\n (Reply with the full or partial name of item 2 to select for forging. Try to be specific.)```"
            )
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("I don't have all day, you know.")
            item2 = {}
            for item in users[str(user)]['items']['backpack']:
                if reply.content.lower() in item and reply.content.lower() not in consumed:
                    if  "{.:'" not in item:
                        item2 = users[str(user)]['items']['backpack'].get(item)
                        consumed.append(item)
                        break
                    else:
                        ctx.command.reset_cooldown(ctx)
                        return await ctx.send("Tinkered devices cannot be reforged.")
            if item2 == {}:
                    ctx.command.reset_cooldown(ctx)
                    return await ctx.send("I could not find that item, check your spelling.")
            newitem = await Classes.forge(ctx, item1, item2)
            for item in consumed:
                users[str(user)]['items']['backpack'].pop(item)
            await GobCog.sub_unequip(ctx,"{.:'")
            lookup = list(x for x in users[str(user)]['items']['backpack'] if "{.:'" in x.lower())
            if len(lookup) > 0:
                msg = await ctx.send("```css\n You already have a device. Do you want to replace {}? ```".format(', '.join(lookup)))
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                await ctx.bot.wait_for("reaction_add", check=pred)
                try:
                    await msg.delete()
                except discord.Forbidden:  # cannot remove message try remove emojis
                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                        await msg.remove_reaction(key, ctx.bot.user)
                if pred.result: #user reacted with Yes.
                    for item in lookup:
                        del users[str(user)]['items']['backpack'][item]
                        users[str(user)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
                        await ctx.send('```css\n Your new {} consumed {} and is now lurking in your backpack. ```'.format(newitem['itemname'], ', '.join(lookup)))
                else:
                    with GobCog.fp.open('w') as f:
                        json.dump(users, f)
                    return await ctx.send('```css\n {} got mad at your rejection and blew itself up. ```'.format(newitem['itemname']))
            else:
                users[str(user)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
                await ctx.send('```css\n Your new {} is lurking in your backpack. ```'.format(newitem['itemname']))
                with GobCog.fp.open('w') as f:
                    json.dump(users, f)


    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def heroclass(self, ctx, clz:str=None, action:str=None):
        """This allows you to select a class.
            You need to be level 10 to select one.
            For information on class use: !heroclass "classname" info
        """
        global users
        classes = {'Tinkerer': {'name': "Tinkerer", 'ability': False, 'desc': "Tinkerers can forge two different items into a device bound to their very soul.\n Use !forge."},
                    'Berserker':{'name': "Berserker", 'ability': False, 'desc': "Berserker have the option to rage and add big bonuses to attacks, but fumbles hurt.\n Use !rage when attacking in an adventure."},
                    'Cleric': {'name': "Cleric", 'ability': False, 'desc': "Clerics can bless the entire group when praying.\n Use !bless when fighting in an adventure."},
                    'Ranger': {'name': "Ranger", 'ability': False, 'desc': "Rangers can gain a special pet, which can find items and give reward bonuses.\n Use !pet."},
                    'Bard': {'name': "Bard", 'ability': False, 'desc': "Bards can perform to aid their comrades in diplomacy.\n Use !sing when being diplomatic in an adventure."}}
        user = ctx.author
        if clz == None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("So you feel like taking on a class, **{}**?\nAvailable classes are: Tinkerer, Berserker, Cleric, Ranger and Bard.\n Use !heroclass \"name-of-class\" to choose one.".format(user.display_name))
        else:
            clz = clz[:1].upper() + clz[1:]
            if clz in classes and action == None:
                if users[str(user.id)]['lvl'] >= 10:
                    if 'name' in users[str(user.id)]['class']:
                        if users[str(user.id)]['class']['name'] == 'Tinkerer' or users[str(user.id)]['class']['name'] == 'Ranger':
                            curclass = users[str(user.id)]['class']['name']
                            if curclass == 'Tinkerer':
                                msg = await ctx.send("```css\n You will loose your forged device if you change your class.\nShall I proceed? ```")
                            else:
                                msg = await ctx.send("```css\n You will loose your pet if you change your class.\nShall I proceed? ```")
                            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                            await ctx.bot.wait_for("reaction_add", check=pred)
                            try:
                                await msg.delete()
                            except discord.Forbidden:  # cannot remove message try remove emojis
                                for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                                    await msg.remove_reaction(key, ctx.bot.user)
                            if pred.result: #user reacted with Yes.
                                if curclass == 'Tinkerer':
                                    await GobCog.sub_unequip(ctx,"{.:'")
                                    if any([x for x in users[str(user.id)]['items']['backpack'] if "{.:'" in x.lower()]):
                                        lookup = list(x for x in users[str(user.id)]['items']['backpack'] if "{.:'" in x.lower())
                                        for item in lookup:
                                            del users[str(user.id)]['items']['backpack'][item]
                                            await ctx.send('```css\n {} has run off to find a new master. ```'.format(', '.join(lookup)))
                            else:
                                ctx.command.reset_cooldown(ctx)
                                return
                    users[str(user.id)]['class'] = {}
                    users[str(user.id)]['class'] = classes[clz]
                    await ctx.send("Congratulations. You are now a {}.".format(classes[clz]['name']))
                    with GobCog.fp.open('w') as f:
                        json.dump(users, f)
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
    async def skill(self, ctx, spend:str=None):
        """This allows you to spend skillpoints.
            !skill attack/diplomacy
        """
        global users
        user = ctx.author
        if users[str(user.id)]['skill']['pool'] == 0:
            return await ctx.send("You do not have unspent skillpoints.")
        if spend == None:
            await ctx.send("You currently have **{}** unspent skillpoints.\nIf you want to put them towards a permanent attack or diplomacy bonus,\nuse !skill attack or !skill diplomacy".format(str(users[str(user.id)]['skill']['pool'])))
        else:
            if spend not in ['attack','diplomacy']:
                return await ctx.send("Don't try to fool me! There is no such thing as {}.".format(spend))
            elif spend == "attack":
                users[str(user.id)]['skill']['pool'] -= 1
                users[str(user.id)]['skill']['att'] += 1
            elif spend == "diplomacy":
                users[str(user.id)]['skill']['pool'] -= 1
                users[str(user.id)]['skill']['cha'] += 1
            await ctx.send("You permanently raised your {} value by one.".format(spend))
            with GobCog.fp.open('w') as f:
                json.dump(users, f)


    @commands.command()
    @commands.guild_only()
    async def loot(self, ctx, type: str="normal"):
        """This opens one of your precious treasure chests.
            (If you have rare or epic chests, type "rare" or
            "epic" after the command to open those.)
        """
        if type == "normal":
            redux = [1,0,0]
        elif type == "rare":
            redux = [0,1,0]
        elif type == "epic":
            redux = [0,0,1]
        else:
            await ctx.send("There is talk of a {} treasure chest but nobody ever saw one.".format(type))
            return
        global users
        user = ctx.author
        if not 'treasure' in users[str(user.id)].keys():
            users[str(user.id)]['treasure'] = [0,0,0]
        treasure = users[str(user.id)]['treasure'][redux.index(1)]
        if treasure == 0:
            await ctx.send("You have no {} treasure chest to open.".format(type))
        else:
            item = await Treasure.open_chest(ctx, user, type)
            users[str(user.id)]['treasure'] = [x-y for x,y in zip(users[str(user.id)]['treasure'], redux)]
            if item['equip'] == "sell":
                price = await GobCog.sell(user,item)
                await ctx.send("{} sold the {} for {} copperpieces.".format(user.display_name,item['itemname'],price))
            elif item['equip'] == "equip":
                equip = {"itemname": item['itemname'],"item": item['item']}
                await self.equip_item(ctx, equip, False)
            else:
                users[str(user.id)]['items']['backpack'].update({item['itemname']: item['item']})
                await ctx.send("{} put the {} into the backpack.".format(user.display_name,item['itemname']))


    @commands.command()
    @commands.guild_only()
    async def stats(self, ctx, user: discord.Member=None):
        """This draws up a charsheet of you or an optionally specified member.
            !stats @locastan
            will bring up locastans stats.
            !stats without user will open your stats.
        """
        if user is None:
            user = ctx.author
        if user.bot:
            return
        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)
        global users
        xp = round(users[str(user.id)]['exp'])
        lvl = users[str(user.id)]['lvl']
        att = users[str(user.id)]['att']
        satt = users[str(user.id)]['skill']['att']
        cha = users[str(user.id)]['cha']
        scha = users[str(user.id)]['skill']['cha']
        pool = users[str(user.id)]['skill']['pool']
        equip = "Equipped Items: \n"
        i = iter(users[str(user.id)]['items'])
        for slot in i:
            if users[str(user.id)]['items'][slot] and slot != "backpack":
                item = list(users[str(user.id)]['items'][slot].keys())[0]
                if len(users[str(user.id)]['items'][slot][item]['slot']) == 1:
                    equip += " - " + item + " - (ATT: "+ str(users[str(user.id)]['items'][slot][item]['att']) + " | CHA: "+ str(users[str(user.id)]['items'][slot][item]['cha']) +" ["+ users[str(user.id)]['items'][slot][item]['slot'][0] + " slot])\n"
                else:
                    equip += " - " + item + " -(ATT: "+ str(users[str(user.id)]['items'][slot][item]['att']*2) + " | CHA: "+ str(users[str(user.id)]['items'][slot][item]['cha']*2) +" [two handed])\n"
                    next(i, None)
        next_lvl = int((lvl+1) ** 4)
        if users[str(user.id)]['class'] != {} and 'name' in users[str(user.id)]['class']:
            clazz = users[str(user.id)]['class']['name'] + "\n" + users[str(user.id)]['class']['desc']
        else:
            clazz = "Hero."
        await ctx.send(
            "```css\n[{}'s Character Sheet] \n\n```".format(user.display_name) + "```css\nA level {} {} \n\n- ATTACK: {} [+{}] - DIPLOMACY: {} [+{}] -\n\n- Credits: {} {} \n- Experience: {}/{} \n- Unspent skillpoints: {} \n```".format(
                lvl, clazz, att, satt, cha, scha, bal, currency, xp, next_lvl, pool
            ) + "```css\n" + equip + "```" +
            "```css\n" + "You own {} normal, {} rare and {} epic chests.```".format(
                str(users[str(user.id)]['treasure'][0]),str(users[str(user.id)]['treasure'][1]),str(users[str(user.id)]['treasure'][2]))
        )

    @commands.command(name="backpack", aliases=['b'])
    @commands.guild_only()
    async def _backpack(self, ctx, switch: str="None", item: str="None", asking: int=10, buyer: discord.Member=None):
        """This draws up the contents of your backpack.
            Selling: !backpack sell "(partial) name of item"
            Trading: !backpack trade "name of item" cp @buyer
            Equip:   !backpack equip "(partial) name of item"
            or respond with "name of item" to backpack.
        """
        user = ctx.author
        if user.bot:
            return
        global users
        bkpk = "Items in Backpack: \n"
        if switch == "None":
            for item in users[str(user.id)]['items']['backpack']: # added second if level for two handed weapons so their slots show properly.
                if len(users[str(user.id)]['items']['backpack'][item]['slot']) == 1:
                    bkpk += " - " + item + " - (ATT: "+ str(users[str(user.id)]['items']['backpack'][item]['att']) + " | DPL: "+ str(users[str(user.id)]['items']['backpack'][item]['cha']) +" ["+ users[str(user.id)]['items']['backpack'][item]['slot'][0] + " slot])\n"
                else:
                    bkpk += " - " + item + " -(ATT: "+ str(users[str(user.id)]['items']['backpack'][item]['att']*2) + " | DPL: "+ str(users[str(user.id)]['items']['backpack'][item]['cha']*2) +" [two handed])\n"
            await ctx.send(
                "```css\n[{}'s baggage] \n\n```".format(
                    user.display_name
                ) + "```css\n" + bkpk + "\n (Reply with the name of an item or use !backpack equip \"name of item\" to equip it.)```"
            )
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                return
            if not reply:
                return
            else:
                if not " sell " in reply.content.lower() and not " trade " in reply.content.lower():
                    equip = {}
                    for item in users[str(user.id)]['items']['backpack']:
                        if reply.content.lower() in item:
                            equip = {"itemname": item,"item": users[str(user.id)]['items']['backpack'][item]}
                            break
                    if equip != {}: #not good to change dict size during iteration so I moved this outside the for loop.
                        await self.equip_item(ctx, equip, True)
        elif switch == "equip":
            if item == "None" or not any([x for x in users[str(user.id)]['items']['backpack'] if item in x.lower()]):
                await ctx.send("You have to specify an item from your backpack to equip.")
                return
            lookup = list(x for x in users[str(user.id)]['items']['backpack'] if item in x.lower())
            if len(lookup) > 1:
                await ctx.send("I found multiple items ({}) matching that name in your backpack.\nPlease be more specific.".format(" and ".join([", ".join(lookup[:-1]),lookup[-1]] if len(lookup) > 2 else lookup)))
                return
            else:
                item = lookup[0]
                equip = {"itemname": item,"item": users[str(user.id)]['items']['backpack'][item]}
                await self.equip_item(ctx, equip, True)
        elif switch == "sell": #new logic allows for bulk sales. It also always confirms the sale by yes/no query to avoid accidents.
            if item == "None" or not any([x for x in users[str(user.id)]['items']['backpack'] if item in x.lower()]):
                await ctx.send("You have to specify an item (or partial name) from your backpack to sell.")
                return
            lookup = list(x for x in users[str(user.id)]['items']['backpack'] if item in x.lower())
            if any([x for x in lookup if "{.:'" in x.lower()]):
                device = [x for x in lookup if "{.:'" in x.lower()]
                await ctx.send("```css\n Your {} is refusing to be sold and bit your finger for trying. ```".format(device))
                return
            msg = await ctx.send("Do you want to sell these items {}?".format(str(lookup)))
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, buyer)
            await ctx.bot.wait_for("reaction_add", check=pred)
            try:
                await msg.delete()
            except discord.Forbidden:  # cannot remove message try remove emojis
                for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                    await msg.remove_reaction(key, ctx.bot.user)
            if pred.result: #user reacted with Yes.
                for item in lookup:
                    queryitem = {'itemname': item,'item': users[str(user.id)]['items']['backpack'].get(item)}
                    price = await GobCog.sell(user,item)
                    del users[str(user.id)]['items']['backpack'][item]
                    await ctx.send("You sold your {} for {} copperpieces.".format(item,price))
                    with GobCog.fp.open('w') as f:
                        json.dump(users, f)
        elif switch == "trade":
            if item == "None" or not any([x for x in users[str(user.id)]['items']['backpack'] if item in x.lower()]):
                await ctx.send("You have to specify an item from your backpack to trade.")
                return
            lookup = list(x for x in users[str(user.id)]['items']['backpack'] if item in x.lower())
            if len(lookup) > 1:
                await ctx.send("I found multiple items ({}) matching that name in your backpack.\nPlease be more specific.".format(" and ".join([", ".join(lookup[:-1]),lookup[-1]] if len(lookup) > 2 else lookup)))
                return
            if any([x for x in lookup if "{.:'" in x.lower()]):
                device = [x for x in lookup if "{.:'" in x.lower()]
                await ctx.send("```css\n Your {} does not want to leave you. ```".format(device))
                return
            else:
                item = lookup[0]
                if len(users[str(user.id)]['items']['backpack'][item]["slot"]) == 2: # two handed weapons add their bonuses twice
                    hand = "two handed"
                    att = users[str(user.id)]['items']['backpack'][item]["att"]*2
                    cha = users[str(user.id)]['items']['backpack'][item]["cha"]*2
                else:
                    if users[str(user.id)]['items']['backpack'][item]["slot"][0] == "right" or users[str(user.id)]['items']['backpack'][item]["slot"][0] == "left":
                        hand = users[str(user.id)]['items']['backpack'][item]["slot"][0] + " handed"
                    else:
                        hand = users[str(user.id)]['items']['backpack'][item]["slot"][0] + " slot"
                    att = users[str(user.id)]['items']['backpack'][item]["att"]
                    cha = users[str(user.id)]['items']['backpack'][item]["cha"]
                await ctx.send("{} wants to sell his {}. (Attack: {}, Charisma: {} [{}])".format(user.display_name,item,str(att),str(cha),hand))
                msg = await ctx.send("Do you want to buy this item for {} cp?".format(str(asking)))
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, buyer)
                await ctx.bot.wait_for("reaction_add", check=pred)
                try:
                    await msg.delete()
                except discord.Forbidden:  # cannot remove message try remove emojis
                    for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                        await msg.remove_reaction(key, ctx.bot.user)
                if pred.result: #buyer reacted with Yes.
                    spender = buyer
                    to = user
                    if await bank.can_spend(spender,asking):
                        bal = await bank.transfer_credits(spender, to, asking)
                        currency = await bank.get_currency_name(ctx.guild)
                        tradeitem = users[str(user.id)]['items']['backpack'].pop(item)
                        users[str(buyer.id)]['items']['backpack'].update({item: tradeitem})
                        with GobCog.fp.open('w') as f:
                            json.dump(users, f)
                        await ctx.send(
                            "```css\n" + "{} traded to {} for {} {}```".format(
                                item, buyer.display_name, asking, currency
                            ))
                    else:
                        await ctx.send("You do not have enough copperpieces.")

    @commands.command()
    @commands.guild_only()
    async def give(self, ctx, amount: int=1, to: discord.Member=None):
        """This will transfer cp from you to a specified member.
            !give 10 @Elder Aramis
            will transfer 10 cp to Elder Aramis.
        """
        if to is None:
            await ctx.send("You need to specify who you want me to give your money to, " + ctx.author.name + ".")
        spender = ctx.author
        if await bank.can_spend(spender,amount):
            bal = await bank.transfer_credits(spender, to, amount)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```You transferred {3} {2}. {0} now has {1} {2}```".format(
                to.display_name, bal, currency, amount
            )
        )

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def fund(self, ctx, amount: int=1, to: discord.Member=None):
        """This will create cp for a specified member.
            !fund 10 @Elder Aramis
            will create 10 cp and add to Elder Aramis.
        """
        if to is None:
            return await ctx.send("You need to specify a receiving member, " + ctx.author.name + ".")
        member = discord.utils.find(lambda m: m.name == to, ctx.guild.members)
        if member == None:
            return await ctx.send("I could not find that user, " + ctx.author.name + ".")
        bal = await bank.deposit_credits(to, amount)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```You funded {3} {2}. {0} now has {1} {2}```".format(
                to.display_name, bal, currency, amount
            )
        )

    @commands.command(name="adventure", aliases=['a'])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=120, type=commands.BucketType.guild)
    async def _adventure(self, ctx):
        """This will send you on an adventure!
            You play by reacting with the offered emojis.
        """
        global users
        await ctx.send("You feel adventurous, " + ctx.author.display_name + "?")
        reward, participants = await Adventure.simple(ctx, users) #Adventure class doesn't change any user info, so no need to return the users object in rewards.
        if reward is not None:
            print(reward, participants)
            for user in reward.keys():
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                await self.add_rewards(ctx, member, reward[user]["xp"], reward[user]["cp"], reward[user]["special"])
            for user in participants: #reset activated abilities
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if 'name' in users[str(member.id)]['class']:
                    if users[str(member.id)]['class']['name'] != "Ranger" and users[str(member.id)]['class']['ability']:
                        users[str(member.id)]['class']['ability'] = False
            with GobCog.fp.open('w') as f:
                json.dump(users, f)


    @commands.command(name="negaverse", aliases=['nv'])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    async def _negaverse(self, ctx, amount: int = None):
        """This will send you to fight a nega-member!
            !nv amount_of_cp
        """
        spender = ctx.message.author
        if amount == None:
            return await ctx.send("You need to specify some cp to convert into energy before entering.")
        if await bank.can_spend(spender,amount):
            await bank.withdraw_credits(spender, amount)
        else:
            return await ctx.send("You don't have enough copperpieces.")
        negachar = "**Nega-" + random.choice(ctx.message.guild.members).name + "**"
        await ctx.send("You enter the negaverse and meet " + negachar + ".")
        roll = random.randint(1,20)
        versus = random.randint(1,20)
        if roll== 1:
            await ctx.send("**" + ctx.author.name + "**" + " fumbled and died to " + negachar + "'s savagery.")
        elif roll == 20:
            await ctx.send("**" + ctx.author.name + "**" + " decapitated " + negachar + ". You gain {} xp and {} cp.".format(amount*2, amount))
            await self.add_rewards(ctx, ctx.message.author, amount*2, amount, False)
        elif roll > versus:
            await ctx.send("**" + ctx.author.name + "** 🎲({})".format(roll) + " bravely defeated " + negachar + " 🎲({}). You gain {} xp.".format(versus, amount))
            await self.add_rewards(ctx, ctx.message.author, amount, 0, False)
        elif roll == versus:
            await ctx.send("**" + ctx.author.name + "** 🎲({})".format(roll) + " almost killed " + negachar + " 🎲({}).".format(versus))
        else:
            await ctx.send("**" + ctx.author.name + "** 🎲({})".format(roll) + " was killed by " + negachar + " 🎲({}).".format(versus))

    async def __error(self, ctx: commands.Context, error):
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
            if h == 0 and m < 3:
                await Adventure.countdown(ctx, error.retry_after, "I feel a little tired now. !{} is available again in: ".format(ctx.command.qualified_name))
            else:
                await ctx.send("⏳ " + "Don't be hasty, {}. You can use !{} again in: ".format(ctx.author.display_name, ctx.command.qualified_name) + out)
        else:
            pass

    async def on_message(self, message):
        global users
        if not message.author.bot:
            await self.update_data(users, message.author)
            if GobCog.last_trade == 0: #this shuts hawls bro up for 3 hours after a cog reload
                GobCog.last_trade = time.time()
            roll = random.randint(1,20)
            if roll == 20:
                ctx = await self.bot.get_context(message)
                await self.trader(ctx)


    async def on_member_join(self, member):
        global users
        await self.update_data(users, member)

        with GobCog.fp.open('w') as f:
            json.dump(users, f)

    @staticmethod
    async def equip_item(ctx, item, from_backpack):
        global users
        user = ctx.author
        if not 'items' in users[str(user.id)].keys(): # if the user has an older account or something went wrong, create empty items slot.
            users[str(user.id)]['items'] = {"left":{},"right":{},"ring":{},"charm":{},"backpack": {}}
        for slot in item['item']["slot"]:
            if users[str(user.id)]['items'][slot] == {}:
                users[str(user.id)]['items'][slot][item['itemname']] = item['item']
                users[str(user.id)]['att'] += item['item']['att']
                users[str(user.id)]['cha'] += item['item']['cha']
                await ctx.send("You equipped {}.".format(item['itemname']))
            else:
                olditem = users[str(user.id)]['items'][slot]
                for oslot in olditem[list(olditem.keys())[0]]['slot']:
                    users[str(user.id)]['items'][oslot] = {}
                    users[str(user.id)]['att'] -= olditem[list(olditem.keys())[0]]['att']     # keep in mind that double handed items grant their bonus twice so they remove twice
                    users[str(user.id)]['cha'] -= olditem[list(olditem.keys())[0]]['cha']
                users[str(user.id)]['items']['backpack'].update(olditem)
                users[str(user.id)]['items'][slot][item['itemname']] = item['item']
                users[str(user.id)]['att'] += item['item']['att']
                users[str(user.id)]['cha'] += item['item']['cha']
                await ctx.send("You equipped {} and put {} into your backpack.".format(item['itemname'],list(olditem.keys())[0]))
        if from_backpack:
            del users[str(user.id)]['items']['backpack'][item['itemname']]
        await ctx.send("Your new stats: **Attack**: {} [+{}], **Diplomacy**: {} [+{}].".format(users[str(user.id)]['att'],users[str(user.id)]['skill']['att'],users[str(user.id)]['cha'],users[str(user.id)]['skill']['cha']))
        with GobCog.fp.open('w') as f:
            json.dump(users, f)

    @staticmethod
    async def update_data(users, user):
        if str(user.id) not in users:
            print('Setting up account for', user.display_name + '.')
            users[str(user.id)] = {}
            users[str(user.id)]['exp'] = 0
            users[str(user.id)]['lvl'] = 1
            users[str(user.id)]['att'] = 0
            users[str(user.id)]['cha'] = 0
            users[str(user.id)]['treasure'] = [0,0,0]
            users[str(user.id)]['items'] = {"left":{},"right":{},"ring":{},"charm":{},"backpack": {}}
            users[str(user.id)]['name'] = {}
            users[str(user.id)]['name'] = user.display_name
            users[str(user.id)]['class'] = {}
            users[str(user.id)]['class'] = {'name': "Hero", 'ability': False, 'desc': "Your basic adventuring hero."}
            users[str(user.id)]['skill'] = {}
            users[str(user.id)]['skill'] = {'pool': 0, 'att': 0, 'cha': 0}
            with GobCog.fp.open('w') as f:
                json.dump(users, f)


    @staticmethod
    async def add_rewards(ctx, user, exp, cp, special):
        global users
        users[str(user.id)]['exp'] += exp
        await bank.deposit_credits(user, cp)
        await GobCog.level_up(ctx, users, user)
        if special != False:
            if not 'treasure' in users[str(user.id)].keys():
                users[str(user.id)]['treasure'] = [0,0,0]
            users[str(user.id)]['treasure'] = [sum(x) for x in zip(users[str(user.id)]['treasure'], special)]

        with GobCog.fp.open('w') as f:
            json.dump(users, f)

    @staticmethod
    async def level_up(ctx, users, user):
        exp = users[str(user.id)]['exp']
        lvl_start = users[str(user.id)]['lvl']
        lvl_end = int(exp ** (1/4))

        if lvl_start < lvl_end: #recalculate free skillpoint pool based on new level and already spent points.
            await ctx.send('{} is now level {}!'.format(user.mention,lvl_end))
            users[str(user.id)]['lvl'] = lvl_end
            users[str(user.id)]['skill']['pool'] = int(lvl_end / 5) - (users[str(user.id)]['skill']['att']+users[str(user.id)]['skill']['cha'])
            if users[str(user.id)]['skill']['pool'] > 0:
                await ctx.send('You have skillpoints available.')

    @staticmethod
    async def sell(user,item):
        if "[" in item['itemname']:
            base = (500,1000)
        elif "." in item['itemname']:
            base = (100,500)
        else :
            base = (10,200)
        price = random.randint(base[0],base[1])*max(item['item']['att']+item['item']['cha'],1)
        await bank.deposit_credits(user, price)
        return(price)

    @staticmethod
    async def trader(ctx):

        async def handle_buy(itemindex, user, stock, msg):
            global users
            item = stock[itemindex]
            spender = user
            react = None
            if await bank.can_spend(spender,int(item['price'])):
                await bank.withdraw_credits(spender, int(item['price']))
                if 'chest' in item['itemname']:
                    if item['itemname'] == ".rare_chest":
                        users[str(user.id)]['treasure'][1] += 1
                    elif item['itemname'] == "[epic chest]":
                        users[str(user.id)]['treasure'][2] += 1
                    else:
                        users[str(user.id)]['treasure'][0] += 1
                else:
                    users[str(user.id)]['items']['backpack'].update({item['itemname']: item['item']})
                with GobCog.fp.open('w') as f:
                    json.dump(users, f)
                await ctx.send("{} bought the {} for {} cp and put it into the backpack.".format(user.display_name,item['itemname'],str(item['price'])))
            else:
                await ctx.send("You do not have enough copperpieces.")
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
                await handle_buy(controls[react.emoji], user, stock, msg)

        em_list = ReactionPredicate.NUMBER_EMOJIS[:5]
        react = False
        controls = {em_list[1]: 0, em_list[2]: 1, em_list[3]: 2, em_list[4]: 3}
        modRole = discord.utils.get(ctx.guild.roles, name='Goblin Adventurer!')
        if modRole is not None:
            text = modRole.mention + "\n" + "```css\n [Hawls brother is bringing the cart around!]```"
        else:
            text = "```css\n [Hawls brother is bringing the cart around!]```"
        if GobCog.last_trade == 0:
            GobCog.last_trade = time.time()
        elif GobCog.last_trade >= time.time()-10800: #trader can return after 3 hours have passed since last visit.
            print("Last Trade Visit: {}, current time: {}".format(str(GobCog.last_trade), str(time.time())))
            return #silent return.
        GobCog.last_trade = time.time()
        stock = await Treasure.trader_get_items()
        for index, item in enumerate(stock):
            item = stock[index]
            if "chest" not in item['itemname']:
                if len(item['item']["slot"]) == 2: # two handed weapons add their bonuses twice
                    hand = "two handed"
                    att = item['item']["att"]*2
                    cha = item['item']["cha"]*2
                else:
                    if item['item']["slot"][0] == "right" or item['item']["slot"][0] == "left":
                        hand = item['item']["slot"][0] + " handed"
                    else:
                        hand = item['item']["slot"][0] + " slot"
                    att = item['item']["att"]
                    cha = item['item']["cha"]
                text += "```css\n" + "[{}] {} (Attack: {}, Charisma: {} [{}]) for {} cp.".format(str(index+1),item['itemname'],str(att),str(cha),hand,item['price'])+ " ```"
            else:
                text += "```css\n" + "[{}] {} for {} cp.".format(str(index+1),item['itemname'],item['price'])+ " ```"
        text += "Do you want to buy any of these fine items? Tell me which one below:"
        msg = await ctx.send(text)
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
