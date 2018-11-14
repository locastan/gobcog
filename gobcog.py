import json
import os
import random
import discord
import asyncio
from redbot.core.utils.predicates import MessagePredicate
from redbot.core import commands, bank, checks
from .adventure import Adventure
from .treasure import Treasure

BaseCog = getattr(commands, "Cog", object)
os.chdir(r'C:\RedBot\cogs\CogManager\cogs\gobcog')

adv = Adventure()

class GobCog(BaseCog):
    """Goblins COG test"""

    @commands.command()
    @commands.guild_only()
    async def cp(self, ctx, user: discord.Member=None):
        """This shows the bank balance of you or an optionally specified member.
            !cp @locastan
            will bring up locastans balance.
            !cp without user will display your balance.
            *If you do not wish to tag the user, remove the @ after selecting
            his name from the @ mention menu. If the user has spaces in his
            username, please add " around the name so the bot knows where the
            name starts and ends.*
        """
        if user is None:
            user = ctx.author
        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            "```{} owns {} {}```".format(
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
        with open('users.json', 'r') as f:
            users = json.load(f)
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
        with open('users.json', 'w') as f:
            json.dump(users, f)


    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def give_loot(self, ctx, user: discord.Member=None, type: str="normal"):
        """[Admin] This rewards a treasure chest to a specified member.
            !give_loot @locastan
            will give locastan a normal chest.
            (Adding "rare" or "epic" to command, creates rare and epic chests.)
            *If you do not wish to tag the user, remove the @ after selecting
            his name from the @ mention menu. If the user has spaces in his
            username, please add " around the name so the bot knows where the
            name starts and ends.*
        """
        with open('users.json', 'r') as f:
            users = json.load(f)
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
        with open('users.json', 'w') as f:
            json.dump(users, f)

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def clean_stats(self, ctx, user: discord.Member=None):
        """[Admin] This recalulates each members stats based on equipped items.
            (Meant for stat cleanup after a messup error appeared.)
        """
        with open('users.json', 'r') as f:
            users = json.load(f)
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
        with open('users.json', 'w') as f:
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
        with open('users.json', 'r') as f:
            users = json.load(f)
        user = ctx.author
        if not 'treasure' in users[str(user.id)].keys():
            users[str(user.id)]['treasure'] = [0,0,0]
        treasure = users[str(user.id)]['treasure'][redux.index(1)]
        if treasure == 0:
            await ctx.send("You have no {} treasure chest to open.".format(type))
        else:
            item = await Treasure.open_chest(ctx, user, type)
            users[str(user.id)]['treasure'] = [x-y for x,y in zip(users[str(user.id)]['treasure'], redux)]
            if item['equip']:
                equip = {"itemname": item['itemname'],"item": item['item']}
                with open('users.json', 'w') as f:
                    json.dump(users, f)
                await self.equip_item(ctx, equip, False)
            else:
                users[str(user.id)]['items']['backpack'].update({item['itemname']: item['item']})
                await ctx.send("You put your {} into the backpack.".format(item['itemname']))
                with open('users.json', 'w') as f:
                    json.dump(users, f)


    @commands.command()
    @commands.guild_only()
    async def stats(self, ctx, user: discord.Member=None):
        """This draws up a charsheet of you or an optionally specified member.
            !stats @locastan
            will bring up locastans stats.
            !stats without user will open your stats.
            *If you do not wish to tag the user, remove the @ after selecting
            his name from the @ mention menu. If the user has spaces in his
            username, please add " around the name so the bot knows where the
            name starts and ends.*
        """
        if user is None:
            user = ctx.author
        if user.bot:
            return
        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)
        with open('users.json', 'r') as f:
            users = json.load(f)
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
    async def backpack(self, ctx, switch: str="None", item: str="None"):
        """This draws up the contents of your backpack.
            (It also waits for you to spell out the item
            you wish to equip in a response to the bots
            backpack listing.)
            If you want to sell an item in your backpack, use
            !backpack sell "name of item"
        """
        user = ctx.author
        if user.bot:
            return
        with open('users.json', 'r') as f:
            users = json.load(f)
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
                if not " sell " in reply.content.lower():
                    equip = {}
                    for item in users[str(user.id)]['items']['backpack']:
                        if item in reply.content.lower():
                            equip = {"itemname": item,"item": users[str(user.id)]['items']['backpack'][item]}
                            break
                    if equip != {}: #not good to change dict size during iteration so I moved this outside the for loop.
                        await self.equip_item(ctx, equip, True)
        elif switch == "sell":
            price = random.randint(1,100)*(users[str(user.id)]['items']['backpack'][item]['att']+users[str(user.id)]['items']['backpack'][item]['cha'])
            await bank.deposit_credits(user, price)
            del users[str(user.id)]['items']['backpack'][item]
            with open('users.json', 'w') as f:
                json.dump(users, f)
            await ctx.send("You sold your {} for {} copperpieces.".format(item,price))




    @commands.command()
    @commands.guild_only()
    async def give(self, ctx, amount: int=1, to: discord.Member=None):
        """This will transfer cp from you to a specified member.
            !give 10 @Elder Aramis
            will transfer 10 coins to Elder Aramis.
            *If you do not wish to tag the user, remove the @ after selecting
            his name from the @ mention menu. If the user has spaces in his
            username, please add " around the name so the bot knows where the
            name starts and ends.*
        """
        if to is None:
            await ctx.send("You need to specify who you want me to give your money to, " + ctx.author.name + ".")
        spender = ctx.author
        if bank.can_spend(spender,amount):
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
        await ctx.send("You feel adventurous, " + ctx.author.name + "?")
        Adventure.countdown(ctx, 30, "Time remaining: ")
        await asyncio.sleep(0.5)
        reward = await Adventure.simple(ctx)
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
            await ctx.send("I feel a little tired now. Ask me again in {:.0f}s".format(error.retry_after))
        else:
            pass

    async def on_message(self, message):
        with open('users.json', 'r') as f:
            users = json.load(f)
        if not message.author.bot:
            await self.update_data(users, message.author)

        with open('users.json', 'w') as f:
            json.dump(users, f)

    async def on_member_join(self, member):
        with open('users.json', 'r') as f:
            users = json.load(f)

        await self.update_data(users, member)

        with open('users.json', 'w') as f:
            json.dump(users, f)

    @staticmethod
    async def equip_item(ctx, item, from_backpack):
        with open('users.json', 'r') as f:
            users = json.load(f)
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
                users[str(user.id)]['items'][slot] = {}
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
        with open('users.json', 'w') as f:
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


    @staticmethod
    async def add_rewards(ctx, user, exp, cp, special):
        with open('users.json', 'r') as f:
            users = json.load(f)

        users[str(user.id)]['exp'] += exp
        await bank.deposit_credits(user, cp)
        await GobCog.level_up(ctx, users, user)
        if special != False:
            if not 'treasure' in users[str(user.id)].keys():
                users[str(user.id)]['treasure'] = [0,0,0]
            users[str(user.id)]['treasure'] = [sum(x) for x in zip(users[str(user.id)]['treasure'], special)]

        with open('users.json', 'w') as f:
            json.dump(users, f)

    @staticmethod
    async def level_up(ctx, users, user):
        exp = users[str(user.id)]['exp']
        lvl_start = users[str(user.id)]['lvl']
        lvl_end = int(exp ** (1/4))

        if lvl_start < lvl_end:
            await ctx.send('{} is now level {}!'.format(user.mention,lvl_end))
            users[str(user.id)]['lvl'] = lvl_end
