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
        global users
        user = ctx.author
        if item == "None":
            return await ctx.send("You need to name the item you want to put in your backpack.")
        else:
            for slot in users[str(user.id)]['items']:
                if users[str(user.id)]['items'][slot] and slot != "backpack":
                    if item == list(users[str(user.id)]['items'][slot].keys())[0]:
                        olditem = users[str(user.id)]['items'][slot]
                        for slot in olditem[list(olditem.keys())[0]]['slot']:
                            users[str(user.id)]['items'][slot] = {}
                            users[str(user.id)]['att'] -= olditem[list(olditem.keys())[0]]['att']     # keep in mind that double handed items grant their bonus twice so they remove twice
                            users[str(user.id)]['cha'] -= olditem[list(olditem.keys())[0]]['cha']
                        users[str(user.id)]['items']['backpack'].update(olditem) # TODO: Change data structure of items dict so you can have duplicate items because of key duplicate overwrite in dicts.
                        await ctx.send("You removed {} and put it into your backpack.".format(list(olditem.keys())[0]))
                        await ctx.send("Your new stats: **Attack**: {}, **Diplomacy**: {}.".format(users[str(user.id)]['att'],users[str(user.id)]['cha']))


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
    async def clean_stats(self, ctx, user: discord.Member=None):
        """[Admin] This recalulates each members stats based on equipped items.
            (Meant for stat cleanup after a messup error appeared.)
        """
        global users
        if user is None:
            user = ctx.author
        for user in users:
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
            if type(users[str(user)]['treasure']) == int:
                normal = users[str(user)]['treasure']
                users[str(user)]['treasure'] = [0,0,0]
                users[str(user)]['treasure'][0] = normal
            member = discord.utils.get(ctx.guild.members, id=int(user))
            if member:
                users[str(user)]['name'] = {}
                users[str(user)]['name'] = member.name
        with GobCog.fp.open('w') as f:
            json.dump(users, f)

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def hawl(self, ctx):
        """[Admin] This manually summons the trader.
        """
        await self.trader(ctx)

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
                price = random.randint(10,1000)*max(item['item']['att']+item['item']['cha'],1)
                await bank.deposit_credits(user, price)
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
        cha = users[str(user.id)]['cha']
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
        await ctx.send(
            "```css\n[{}'s Character Sheet] \n\n```".format(user.display_name) + "```css\nA level {} Hero. \n\n- ATTACK: {} - DIPLOMACY: {} -\n\n- Credits: {} {} \n- Experience: {}/{} \n```".format(
                lvl, att, cha, bal, currency, xp, next_lvl
            ) + "```css\n" + equip + "```" +
            "```css\n" + "You own {} normal, {} rare and {} epic chests.```".format(
                str(users[str(user.id)]['treasure'][0]),str(users[str(user.id)]['treasure'][1]),str(users[str(user.id)]['treasure'][2]))
        )

    @commands.command()
    @commands.guild_only()
    async def backpack(self, ctx, switch: str="None", item: str="None", asking: int=10, buyer: discord.Member=None):
        """This draws up the contents of your backpack.
            Selling: !backpack sell "name of item"
            Trading: !backpack trade "name of item" cp @buyer
            Equip:   !backpack equip "name of item"
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
                ) + "```css\n" + bkpk + "\n (Reply with the name of an item to equip it.)```"
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
                        if item in reply.content.lower():
                            equip = {"itemname": item,"item": users[str(user.id)]['items']['backpack'][item]}
                            break
                    if equip != {}: #not good to change dict size during iteration so I moved this outside the for loop.
                        await self.equip_item(ctx, equip, True)
        elif switch == "equip":
            if item == "None" or item not in users[str(user.id)]['items']['backpack']:
                await ctx.send("You have to specify an item from your backpack to equip.")
                return
            else:
                equip = {"itemname": item,"item": users[str(user.id)]['items']['backpack'][item]}
                await self.equip_item(ctx, equip, True)
        elif switch == "sell":
            if item == "None" or item not in users[str(user.id)]['items']['backpack']:
                await ctx.send("You have to specify an item from your backpack to sell.")
                return
            price = random.randint(10,1000)*max(users[str(user.id)]['items']['backpack'][item]['att']+users[str(user.id)]['items']['backpack'][item]['cha'],1)
            await bank.deposit_credits(user, price)
            del users[str(user.id)]['items']['backpack'][item]
            await ctx.send("You sold your {} for {} copperpieces.".format(item,price))
        elif switch == "trade":
            if item == "None" or item not in users[str(user.id)]['items']['backpack']:
                await ctx.send("You have to specify an item from your backpack to trade.")
                return
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
            *If you do not wish to tag the user, remove the @ after selecting
            his name from the @ mention menu. If the user has spaces in his
            username, please add " around the name so the bot knows where the
            name starts and ends.*
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

    @commands.command(name="adventure", aliases=['a'])
    @commands.cooldown(rate=1, per=120, type=commands.BucketType.guild)
    async def _adventure(self, ctx):
        """This will send you on an adventure!
            You play by reacting with the offered emojis.
        """
        global users
        await ctx.send("You feel adventurous, " + ctx.author.display_name + "?")
        Adventure.countdown(ctx, 30, "Time remaining: ")
        await asyncio.sleep(0.5)
        reward = await Adventure.simple(ctx, users) #Adventure class doesn't change any user info, so no need to return the users object in rewards.
        print(reward)
        for user in reward.keys():
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            await self.add_rewards(ctx, member, reward[user]["xp"], reward[user]["cp"], reward[user]["special"])


    @commands.command()
    @commands.cooldown(rate=1, per=120, type=commands.BucketType.user)
    async def negaverse(self, ctx):
        """This will send you to fight a nega-member!
        """
        negachar = "**Nega-" + random.choice(ctx.message.guild.members).name + "**"
        await ctx.send("You enter the negaverse and meet " + negachar + ".")
        roll = random.randint(1,20)
        if roll== 1:
            await ctx.send("**" + ctx.author.name + "**" + " fumbled and died to " + negachar + "'s savagery.")
        elif roll == 20:
            await ctx.send("**" + ctx.author.name + "**" + " decapitated " + negachar + ".")
            await self.add_rewards(ctx, ctx.message.author, 20, 0, False)
        elif roll >=10:
            await ctx.send("**" + ctx.author.name + "**" + " bravely defeated " + negachar + ". You gain 5 xp.")
            await self.add_rewards(ctx, ctx.message.author, 5, 0, False)
        else:
            await ctx.send("**" + ctx.author.name + "**" + " was killed by " + negachar + ".")

    async def __error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await Adventure.countdown(ctx, error.retry_after, "I feel a little tired now. Ask me again in: ")
        else:
            pass

    async def on_message(self, message):
        global users
        if not message.author.bot:
            await self.update_data(users, message.author)
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
        await ctx.send("Your new stats: **Attack**: {}, **Diplomacy**: {}.".format(users[str(user.id)]['att'],users[str(user.id)]['cha']))
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

        if lvl_start < lvl_end:
            await ctx.send('{} is now level {}!'.format(user.mention,lvl_end))
            users[str(user.id)]['lvl'] = lvl_end

    @staticmethod
    async def trader(ctx):

        async def handle_buy(itemindex, user, stock, msg):
            global users
            item = stock[itemindex]
            spender = user
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
            if react and user:
                await handle_buy(controls[react.emoji], user, stock, msg)

        em_list = ReactionPredicate.NUMBER_EMOJIS[:5]
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
        print(str(stock))
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
