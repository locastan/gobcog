import json
from redbot.core.data_manager import cog_data_path
from redbot.core import commands
import asyncio
import contextlib
from typing import Union, Iterable, Optional
import discord
import random
import calendar
import time
from .custompredicate import CustomPredicate
from .userdata import Userdata
from .classes import Classes

_ReactableEmoji = Union[str, discord.Emoji]

class Adventure:

    attribs = {" terrifying":[1,1.2],
                " hideous":[1,1],
                " weak":[0.5,1],
                " sick":[0.3,0.9],
                " stupid":[1,0.5],
                " cunning":[1.2,1.2],
                " furious":[1.1,0.9],
                " fairly intelligent":[1,1.2],
                " dumb":[1,0.8],
                "n old":[0.8,1.5],
                "n ancient":[0.8,2],
                " sly":[1.5,1.4],
                " colossal":[2,1.1],
                " miniature":[0.7,0.9],
                " feral":[1.8,0.9],
                " battered":[0.5,0.5],
                " mesmerizing":[0.9,2.5],
                " menacing":[2.5,0.9],
                " palatine":[2,2],
                "n overpowered":[3,3]}
    monsters = {"Ogre":{"str":18,"dipl":10},
                "Gnoll":{"str":12,"dipl":8},
                "Wood Spider":{"str":20,"dipl":20},
                "Yuan-ti":{"str":20,"dipl":30},
                "Mountain Troll":{"str":25,"dipl":10},
                "Kobold":{"str":15,"dipl":18},
                "Orc":{"str":16,"dipl":10},
                "Ghoul":{"str":10,"dipl":10},
                "Shrieker":{"str":11,"dipl":12},
                "Zombie":{"str":15,"dipl":12},
                "Skeleton":{"str":13,"dipl":16},
                "Sahuagin":{"str":15,"dipl":15},
                "Swarm of Quipper":{"str":25,"dipl":12},
                "Slaad":{"str":12,"dipl":15},
                "Gelatinous Cube":{"str":12,"dipl":30},
                "Green Ooze":{"str":10,"dipl":30},
                "Black Ooze":{"str":30,"dipl":40},
                "Marid":{"str":32,"dipl":48},
                "Golem":{"str":40,"dipl":20},
                "Wizard":{"str":8,"dipl":15},
                "Demon":{"str":30,"dipl":17},
                "Owlbear":{"str":30,"dipl":25},
                "Umber Hulk":{"str":35,"dipl":50},
                "Cave Rat":{"str":5,"dipl":30},
                "Pack of Wolves":{"str":19,"dipl":35},
                "Fire Elemental":{"str":20,"dipl":20},
                "Bandit":{"str":10,"dipl":10},
                "Vigilante":{"str":15,"dipl":18},
                "Thief":{"str":15,"dipl":18},
                "Giant":{"str":35,"dipl":20},
                "Archmage":{"str":28,"dipl":30},
                "Basilisk":{"str":50,"dipl":50},
                "Displacer Beast":{"str":45,"dipl":80},
                "Fire Giant":{"str":55,"dipl":45},
                "Ice Giant":{"str":60,"dipl":55},
                "Medusa":{"str":65,"dipl":65},
                "Wyvern":{"str":70,"dipl":60},
                "Hydra":{"str":75,"dipl":65},
                "Purpleworm":{"str":80,"dipl":55},
                "Brainbug":{"str":100,"dipl":155},
                "Bulette":{"str":120,"dipl":55},
                "Mind-Flayer":{"str":55,"dipl":85},
                "Warforged Golem":{"str":90,"dipl":100},
                "Red Dragon":{"str":95,"dipl":95},
                "Blue Dragon":{"str":110,"dipl":100},
                "Black Dragon":{"str":130,"dipl":120},
                "White Dragon":{"str":200,"dipl":220},
                "Leviathan":{"str":320,"dipl":320},
                "Tarrasque":{"str":400,"dipl":400}}

    challenge = ""
    attrib = ""
    userslist = {}
    emoji_lookup = {"fight": "🗡", "talk" : "🗨", "pray" : "🛐", "run" : "❌"}
    finish = 0
    timeout = 0
    started = 0

    async def simple(ctx):
        text = ""
        if Adventure.timeout != 0:
            return None
        Adventure.challenge = random.choice(list(Adventure.monsters.keys())) #if you want the dict with accompanying subkeys use: Adventure.monsters[random.choice(list(Adventure.monsters.keys()))]
        Adventure.attrib = random.choice(list(Adventure.attribs.keys()))
        Adventure.str = Adventure.monsters[Adventure.challenge]["str"]*Adventure.attribs[Adventure.attrib][0]
        Adventure.dipl = Adventure.monsters[Adventure.challenge]["dipl"]*Adventure.attribs[Adventure.attrib][1]
        Adventure.userslist = {"fight":[],"pray":[],"talk":[],"run":[]}
        Adventure.rewards = {}
        Adventure.dmgred = 1
        Adventure.participants = []
        Adventure.started = time.time()
        if "Dragon" in Adventure.challenge or "Tarrasque" in Adventure.challenge or "Leviathan" in Adventure.challenge:
            Adventure.timeout = 120
            modRole = discord.utils.get(ctx.guild.roles, name='Goblin Adventurer!')
            if modRole is not None:
                if len(Adventure.attrib.split(" ")) <= 2:
                    namedesc = Adventure.attrib.split(" ")[1].capitalize()
                else:
                    namedesc = Adventure.attrib.split(" ")[1].capitalize() + " " + Adventure.attrib.split(" ")[2].capitalize()
                text = modRole.mention + "\n" + "```ansi\n [2;31m[{} {} Alarm!][0m```".format(namedesc,Adventure.challenge)
        elif (Adventure.str + Adventure.dipl) > 100:
            Adventure.timeout = 60
        else:
            Adventure.timeout = 30
        Adventure.countdown(ctx, None, "Time remaining: ")
        await asyncio.sleep(0.2)
        locations = ["There is telling of a dangerous cave nearby, holding immense riches. ", "You found a small clearing. ", "A bridge crosses over a deep gorge. ", "This towns inn looks very inviting. "]
        raisins = [" is going to investigate,", " is curious to have a peek,", " would like to have a look,", " wants to go there,"]
        advmsg = await ctx.send(text + random.choice(locations)+ "\n" + "**" + ctx.author.display_name + "**" + random.choice(raisins), allowed_mentions=discord.AllowedMentions(roles=True))
        await Adventure.choice(ctx)
        advmsg.mentions.clear()
        text = advmsg.content.replace("@Goblin Adventurer!", "")
        await advmsg.edit(content=text)
        return (Adventure.rewards, Adventure.participants)

    async def choice(ctx):
        if "Dragon" in Adventure.challenge:
            await Adventure.menu(ctx, [("but **a{} {}** just landed in front of you glaring! \n\nWhat will you do and will other heroes be brave enough to help you?\nHeroes participate via reaction:").format(Adventure.attrib,Adventure.challenge)], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})
        elif "Tarrasque" in Adventure.challenge:
            await Adventure.menu(ctx, [("but **a{} {}** just reared its ugly head! \n\nDo you feel lucky today?\nHeroes participate via reaction:").format(Adventure.attrib,Adventure.challenge)], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})
        elif Adventure.challenge == "Basilisk" or Adventure.challenge == "Medusa":
            await Adventure.menu(ctx, [("but **a{} {}** stepped out looking around. \n\nWhat will you do and will other heroes help your cause?\nHeroes participate via reaction:").format(Adventure.attrib,Adventure.challenge)], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})
        else:
            threatee = [" menace", " glee", " malice", " all means necessary", " a couple of friends", " a crosseyed squint", " steady pace"]
            await Adventure.menu(ctx, [("but **a{} {}** is guarding it with{}. \n\nWhat will you do and will other heroes help your cause?\nHeroes participate via reaction:").format(Adventure.attrib,Adventure.challenge,random.choice(threatee))], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})

    async def menu(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message = None,
        page: int = 0,
    ):
        """
        An emoji-based menu

        .. note:: All pages should be of the same type

        .. note:: All functions for handling what a particular emoji does
                  should be coroutines (i.e. :code:`async def`). Additionally,
                  they must take all of the parameters of this function, in
                  addition to a string representing the emoji reacted with.
                  This parameter should be the last one, and none of the
                  parameters in the handling functions are optional

        Parameters
        ----------
        ctx: commands.Context
            The command context
        pages: `list` of `str` or `discord.Embed`
            The pages of the menu.
        controls: dict
            A mapping of emoji to the function which handles the action for the
            emoji.
        message: discord.Message
            The message representing the menu. Usually :code:`None` when first opening
            the menu
        page: int
            The current page number of the menu
        timeout: float
            The time (in seconds) to wait for a reaction

        Raises
        ------
        RuntimeError
            If either of the notes above are violated
        """

        if not all(isinstance(x, discord.Embed) for x in pages) and not all(
            isinstance(x, str) for x in pages
        ):
            raise RuntimeError("All pages must be of the same type")
        for key, value in controls.items():
            if not asyncio.iscoroutinefunction(value):
                raise RuntimeError("Function must be a coroutine")
        current_page = pages[page]

        if not message:
            if isinstance(current_page, discord.Embed):
                message = await ctx.send(embed=current_page)
            else:
                message = await ctx.send(current_page)
            # Don't wait for reactions to be added (GH-1797)
            # noinspection PyAsyncCall
            Adventure.start_adding_reactions(message, controls.keys(), ctx.bot.loop)
        else:
            if isinstance(current_page, discord.Embed):
                await message.edit(embed=current_page)
            else:
                await message.edit(content=current_page)

        try:
            react, user = await ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message),
                timeout=Adventure.timeout
            )
        except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
            try:
                await message.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in controls.keys():
                    await message.remove_reaction(key, ctx.bot.user)
            pages = ["but nobody did anything. You failed."]
            await message.edit(content=pages[0])
            return
        await controls[react.emoji](ctx, pages, controls, message, page, Adventure.timeout, react.emoji, user)

    async def fight(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        check_other = ["talk","pray","run"]
        await Adventure.check(check_other,"fight", ctx, pages, controls, message, page, Adventure.timeout, emoji, user)

    async def run(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        check_other = ["talk","pray","fight"]
        await Adventure.check(check_other,"run", ctx, pages, controls, message, page, Adventure.timeout, emoji, user)

    async def pray(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        check_other = ["talk","fight","run"]
        await Adventure.check(check_other,"pray", ctx, pages, controls, message, page, Adventure.timeout, emoji, user)

    async def talk(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        check_other = ["fight","pray","run"]
        await Adventure.check(check_other,"talk", ctx, pages, controls, message, page, Adventure.timeout, emoji, user)

    async def check(check_lists,call_from, ctx, pages, controls, message, page, timeout, emoji, user):
        for x in check_lists:
            if user.display_name in Adventure.userslist[x]:
                symbol = Adventure.emoji_lookup[x]
                Adventure.userslist[x].remove(user.display_name)
                await message.remove_reaction(symbol, user)
        if user.display_name not in Adventure.userslist[call_from]:
            Adventure.userslist[call_from].append(user.display_name)
        try:
            react, user = await ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message),
                timeout=Adventure.timeout)
        except asyncio.TimeoutError:
            return await Adventure.result(ctx, pages, controls, message, page, Adventure.timeout)
        return await controls[react.emoji](ctx, pages, controls, message, page, Adventure.timeout, react.emoji, user)


    async def close_menu(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
    ):
        if message:
            await message.delete()
        return None

    async def result(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
    ):
        attack = 0
        diplomacy = 0
        fumblelist = []
        critlist = []
        failed = False
        people = len(Adventure.userslist["fight"])+len(Adventure.userslist["talk"])+len(Adventure.userslist["pray"])

        async def handle_run(attack, diplomacy):
            if len(list(Adventure.userslist["run"])) != 0:
                for user in Adventure.userslist["run"]:
                    attack -= 1
                    diplomacy -= 1
                runners = ','.join(map(str, Adventure.userslist["run"]))
                await ctx.send("**" + runners + "**" + " just ran away.")
            return (attack,diplomacy)

        async def handle_fight(fumblelist, critlist, attack):
            if len(Adventure.userslist["fight"]) == 0:
                return (fumblelist, critlist, attack)
            report = "Attack Party: | "
            for user in Adventure.userslist["fight"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (1)")
                    return (fumblelist, critlist, attack)
                att_value = Userdata.users[str(member.id)]['att'] + Userdata.users[str(member.id)]['skill']['att'] + Userdata.users[str(member.id)]['buffs'].get('att', {'bonus':0})['bonus']
                monster_string = ""
                bow_bonus = ""
                monster_value = 0
                if "monster" in Userdata.users[str(member.id)]['buffs']:
                    monster_value = Userdata.users[str(member.id)]['buffs'].get('monster', {'bonus':{'att':0}})['bonus']['att']
                    monster_string = " + 🦖{}".format(monster_value)
                if roll == 1 and not (Userdata.users[str(member.id)]['class']['name']=="Monk" and Userdata.users[str(member.id)]['class']['ability']):
                    await ctx.send("**" + user + "**" + " fumbled the attack.")
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                        r_penalty = random.randint(5,max(6,int(bonus/2)))
                        duration = int(max(2,bonus/10))
                        attack += -roll -bonus -att_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({}) -".format(roll) + " 💥{} ".format(bonus) + "- 🗡" + str(att_value) + monster_string + " | "
                        await Userdata.debuff(ctx,str(member.id),"Your Rage",r_penalty,duration,'att')
                elif roll == 20 or (Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']):
                    ability = ""
                    bonus = 0
                    if roll == 20:
                        await ctx.send("**" + user + "**" + " landed a critical hit.")
                        critlist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']:
                        ability = "🗯️"
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                        r_penalty = random.randint(5,max(6,int(bonus/2)))
                        duration = int(max(2,bonus/10))
                        await Userdata.debuff(ctx,str(member.id),"Your Rage",r_penalty,duration,'att')
                    elif Userdata.users[str(member.id)]['class']['name']=="Ranger" and any("bow" in k for k in Userdata.users[str(member.id)]['items']['right'].keys()):
                        bowbonus = int(Userdata.users[str(member.id)]['lvl']/10)*2
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl']))) + bowbonus
                        bow_bonus = "🏹{} + ".format(bowbonus)
                    else:
                        bonus = random.randint(5,15)
                    attack += roll + bonus + att_value + monster_value
                    bonus_str = ability + str(bonus)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['items']['right'] != {}:
                        if len(Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["slot"]) == 2 and "bow" not in list(Userdata.users[str(member.id)]['items']['right'].keys())[0]:
                            barb_bonus = Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["att"]*2
                            attack += barb_bonus
                            barb_bonus_str = " 🀄{} ".format(barb_bonus)
                            bonus_str += barb_bonus_str
                    elif Userdata.users[str(member.id)]['class']['name']=="Monk":
                        monkbonus = await Classes.calc_monkbonus(ctx, member.id)
                        bonus_roll = random.randrange(min(1,monkbonus[0]),max(1,monkbonus[0]))
                        attack += bonus_roll
                        monk_bonus_str = " ⚖️{} + ".format(bonus_roll)
                        bonus_str += monk_bonus_str
                    report += "**" + user + "**: " +  "🎲({}) +".format(roll) + " {} + ".format(bonus_str) + "🗡" + str(att_value) + monster_string + " | "
                else:
                    bonus = 0
                    if Userdata.users[str(member.id)]['class']['name']=="Ranger" and any("bow" in k for k in Userdata.users[str(member.id)]['items']['right'].keys()):
                        bonus = int(Userdata.users[str(member.id)]['lvl']/10)*2
                        bow_bonus = " 🏹{} + ".format(bonus)
                    elif Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['items']['right'] != {}:
                        if len(Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["slot"]) == 2 and "bow" not in list(Userdata.users[str(member.id)]['items']['right'].keys())[0]:
                            bonus = Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["att"]*2
                            bow_bonus = " 🀄{} + ".format(bonus)
                    elif Userdata.users[str(member.id)]['class']['name']=="Monk":
                        if roll == 1 and Userdata.users[str(member.id)]['class']['ability']:
                            await ctx.send("A steady resolve prevented **" + user + "**" + "from a fumble.")
                        monkbonus = await Classes.calc_monkbonus(ctx, member.id)
                        bonus_roll = random.randrange(min(1,monkbonus[0]),max(1,monkbonus[0]))
                        attack += bonus_roll
                        bow_bonus = " ⚖️{} + ".format(bonus_roll)
                    attack += roll + bonus + att_value + monster_value
                    report += "**" + user + "**: " +  "🎲({}) +".format(roll) + bow_bonus + "🗡" + str(att_value) + monster_string + " | "
            for user in fumblelist:
                if user in Adventure.userslist["fight"]:
                    Adventure.userslist["fight"].remove(user)
            if len(Adventure.userslist["fight"]) > 0:
                await ctx.send(report)
            return (fumblelist, critlist, attack)

        async def handle_pray(fumblelist, attack, diplomacy):
            for user in Adventure.userslist["pray"]:
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (2)")
                    return (fumblelist, attack, diplomacy)
                if Userdata.users[str(member.id)]['class']['name']=="Cleric" and Userdata.users[str(member.id)]['class']['ability']:
                    roll = random.randint(1,20)
                    if len(Adventure.userslist["fight"]+Adventure.userslist["talk"]) == 0:
                        await ctx.send("**" + user + "**" + " blessed like mad but nobody was there to receive it.")
                        return (fumblelist, attack, diplomacy)
                    if roll == 1:
                        attack -= 5 * len(Adventure.userslist["fight"])
                        diplomacy -= 5 * len(Adventure.userslist["talk"])
                        Adventure.dmgred = 1
                        fumblelist.append(user)
                        await ctx.send("**" + user + "**" + "'s sermon offended the mighty Herbert. (🎲({}) -{}🗡/-{}🗨)".format(roll,5 * len(Adventure.userslist["fight"]),5 * len(Adventure.userslist["talk"])))
                    elif roll > 1 and roll <= 10:
                        attack += 2 * len(Adventure.userslist["fight"])
                        diplomacy += 2 * len(Adventure.userslist["talk"])
                        Adventure.dmgred = 2
                        await ctx.send("**" + user + "**" + "'s blessed you all in Herberts name. (🎲({}) +{}🗡/+{}🗨)".format(roll,2 * len(Adventure.userslist["fight"]),2 * len(Adventure.userslist["talk"])))
                    elif roll > 10 and roll <= 19:
                        attack += 5 * len(Adventure.userslist["fight"])
                        diplomacy += 5 * len(Adventure.userslist["talk"])
                        Adventure.dmgred = 4
                        await ctx.send("**" + user + "**" + "'s blessed you all in Herberts name. (🎲({}) +{}🗡/+{}🗨)".format(roll,5 * len(Adventure.userslist["fight"]),5 * len(Adventure.userslist["talk"])))
                    else:
                        attack += 20 * len(Adventure.userslist["fight"])
                        diplomacy += 20 * len(Adventure.userslist["talk"])
                        Adventure.dmgred = 100
                        await ctx.send("**" + user + "**" + " turned into an avatar of mighty Herbert. (🎲({}) +{}🗡/+{}🗨)".format(roll,20 * len(Adventure.userslist["fight"]),20 * len(Adventure.userslist["talk"])))
                else:
                    roll = random.randint(1,4)
                    if len(Adventure.userslist["fight"]+Adventure.userslist["talk"]) == 0:
                        await ctx.send("**" + user + "**" + " prayed like mad but nobody else was there to help.")
                        return (fumblelist, attack, diplomacy)
                    if roll == 4:
                        attack += 10 * len(Adventure.userslist["fight"])
                        diplomacy += 10 * len(Adventure.userslist["talk"])
                        await ctx.send("**" + user + "**" + "'s prayer called upon the mighty Herbert to help you. (+{}🗡/+{}🗨)".format(10 * len(Adventure.userslist["fight"]),10 * len(Adventure.userslist["talk"])))
                    else:
                        fumblelist.append(user)
                        await ctx.send("**" + user + "**" + "'s prayers went unanswered.")
            for user in fumblelist:
                if user in Adventure.userslist["pray"]:
                    Adventure.userslist["pray"].remove(user)
            return (fumblelist, attack, diplomacy)

        async def handle_talk(fumblelist, critlist, diplomacy):
            if len(Adventure.userslist["talk"]) == 0:
                return (fumblelist, critlist, diplomacy)
            report = "Talking Party: | "
            for user in Adventure.userslist["talk"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (3)")
                    return (fumblelist, critlist, diplomacy)
                dipl_value = Userdata.users[str(member.id)]['cha'] + Userdata.users[str(member.id)]['skill']['cha'] + Userdata.users[str(member.id)]['buffs'].get('cha', {'bonus':0})['bonus']
                songbonus = 0
                if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                    songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                monster_string = ""
                monster_value = 0
                if "monster" in Userdata.users[str(member.id)]['buffs']:
                    monster_value = Userdata.users[str(member.id)]['buffs'].get('monster', {'bonus':{'cha':0}})['bonus']['cha']
                    monster_string = " + 🦖{}".format(monster_value)
                if roll== 1 and not (Userdata.users[str(member.id)]['class']['name']=="Monk" and Userdata.users[str(member.id)]['class']['ability']):
                    await ctx.send("**" + user + "**" + (" accidentally offended the {}.").format(Adventure.challenge))
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(5,15)
                        if songbonus != 0: #recalc if song is sung
                            low = max(5,int(Userdata.users[str(member.id)]['lvl']/4))
                            bonus = random.randint(low, max(low, songbonus))
                        diplomacy += -roll - bonus - dipl_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({}) -".format(roll) + " 💥{} - ".format(bonus) + "🗨" + str(dipl_value) + monster_string + " | "
                elif roll == 20 or (Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']):
                    ability = ""
                    bonus = 0
                    critbonus = 0
                    if roll == 20:
                        await ctx.send("**" + user + "**" + " made a compelling argument.")
                        critbonus = random.randint(5,15)
                        critlist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                        ability = "🎵"
                    if songbonus != 0: #recalc if song is sung
                        low = max(5,int(Userdata.users[str(member.id)]['lvl']/4))
                        bonus = random.randint(low, max(low, songbonus))
                    diplomacy += roll + bonus + critbonus + dipl_value + monster_value
                    bonus_str = ability + str(bonus+critbonus)
                    report += "**" + user + "**: " +  "🎲({}) + ".format(roll) + "{} + ".format(bonus_str) + "🗨" +str(dipl_value) + monster_string + " | "
                elif Userdata.users[str(member.id)]['class']['name']=="Monk":
                    if roll == 1 and Userdata.users[str(member.id)]['class']['ability']:
                        await ctx.send("A steady resolve prevented **" + user + "**" + "from a fumble.")
                    monkbonus = await Classes.calc_monkbonus(ctx, member.id)
                    bonus_roll = random.randrange(min(1,monkbonus[1]),max(1,monkbonus[1]))
                    diplomacy += bonus_roll
                    monk_bonus_str = " ⚖️{} + ".format(bonus_roll)
                    bonus_str = monk_bonus_str
                    report += "**" + user + "**: " +  "🎲({}) + ".format(roll) + "{} + ".format(bonus_str) + "🗨" +str(dipl_value) + monster_string + " | "
                else:
                    diplomacy += roll + dipl_value + monster_value
                    report += "**" + user + "**: " +  "🎲({}) + ".format(roll) + "🗨" + str(dipl_value) + monster_string + " | "
            for user in fumblelist:
                if user in Adventure.userslist["talk"]:
                    Adventure.userslist["talk"].remove(user)
            if len(Adventure.userslist["talk"]) > 0:
                await ctx.send(report)
            return (fumblelist, critlist, diplomacy)

        async def handle_basilisk(failed):
            if Adventure.challenge == "Basilisk" or Adventure.challenge == "Medusa":
                failed = True
                for user in Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]: #check if any fighter has an equipped mirror shield to give them a chance.
                    member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                    if member == None:
                        await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (4)")
                        continue
                    if next((iter(Userdata.users[str(member.id)]['items']['left'])), "Empty_slot")[0:14] == '.mirror_shield':
                        failed = False
                        break
            else:
                failed = False
            return failed
        try:
            await message.clear_reactions()
        except discord.Forbidden:  # cannot remove all reactions
            for key in controls.keys():
                await message.remove_reaction(key, ctx.bot.user)
        pages = [w.replace('\nHeroes participate via reaction:', '') for w in pages]
        current_page = pages[page]
        if isinstance(current_page, discord.Embed):
            await message.edit(embed=current_page)
        else:
            await message.edit(content=current_page)
        if people == 0:
            pages = ["everyone ran away. You failed."]
            Adventure.participants = Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]+Adventure.userslist["run"]+fumblelist
            await message.edit(content=pages[0])
            return

        attack,diplomacy = await handle_run(attack, diplomacy)
        fumblelist, attack, diplomacy = await handle_pray(fumblelist, attack, diplomacy)
        fumblelist, critlist, diplomacy= await handle_talk(fumblelist, critlist, diplomacy)
        failed = await handle_basilisk(failed)
        fumblelist, critlist, attack = await handle_fight(fumblelist, critlist, attack)

        slain = attack >= Adventure.str
        persuaded = diplomacy >= Adventure.dipl
        CR = Adventure.str + Adventure.dipl

        fighters = " and ".join([", ".join(Adventure.userslist["fight"][:-1]),Adventure.userslist["fight"][-1]] if len(Adventure.userslist["fight"]) > 2 else Adventure.userslist["fight"])
        talkers = " and ".join([", ".join(Adventure.userslist["talk"][:-1]),Adventure.userslist["talk"][-1]] if len(Adventure.userslist["talk"]) > 2 else Adventure.userslist["talk"])
        preachermen = " and ".join([", ".join(Adventure.userslist["pray"][:-1]),Adventure.userslist["pray"][-1]] if len(Adventure.userslist["pray"]) > 2 else Adventure.userslist["pray"])
        text = ""

        if slain or persuaded and not failed:
            treasure = [0,0,0,0]
            if CR >= 400:
                treasure = random.choice([[1,2,3,0],[1,3,2,0],[4,2,1,0],[0,3,3,0],[0,0,4,0],[0,0,0,1]])
            elif CR >= 250:
                treasure = random.choice([[0,1,2,0],[0,2,1,0],[3,1,0,0],[0,2,2,0],[0,0,3,0]])
            elif CR >= 180: #rewards 50:50 epic:rare chest for killing hard stuff.
                treasure = random.choice([[0,0,1,0],[0,1,0,0]])
            elif CR >= 80 or Adventure.challenge == "Basilisk" or Adventure.challenge == "Medusa": #rewards 50:50 rare:normal chest for killing something like the basilisk
                treasure = random.choice([[0,1,0,0],[1,0,0,0]])
            if "Dragon" in Adventure.challenge: #always rewards an epic chest.
                treasure[2] += 1
            elif "Tarrasque" in Adventure.challenge: #rewards up to 10 rare, 5 epic and 3 quest chests
                treasure[1] += random.randint(3,10)
                treasure[2] += random.randint(2,5)
                treasure[3] += random.randint(1,3)
            if len(critlist) != 0:
                treasure[0] += len(critlist)
            checklist = Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]
            for user in checklist:
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (5)")
                    continue
                lucky = Userdata.users[str(member.id)]['buffs'].get('luck')
                if lucky != None:
                    roll = random.randint(1,50+Userdata.users[str(member.id)]['buffs']['luck']['bonus'])
                    if roll <= 50:
                        continue
                    elif roll <= 75: #25% normal
                        treasure[0] += 1
                    elif roll <= 90: #15% rare
                        treasure[1] += 1
                    elif roll <= 95: #5% epic
                        treasure[2] += 1
                    elif roll >= 100: #1% quest
                        treasure[3] += 1
                    elif roll >= 120: # quest and an epic
                        treasure[3] += 1
                        treasure[2] += 1
                    elif roll >= 140: #2 quest
                        treasure[3] += 2
                    if roll >= 51:
                        await ctx.send("**{}** was lucky to dig up an extra chest for the group!".format(user))
                    elif roll >= 120:
                        await ctx.send("**{}** was lucky to dig up several extra chests for the group!".format(user))
            if treasure == [0,0,0,0]:
                treasure = False
        if (Adventure.challenge == "Basilisk" or Adventure.challenge == "Medusa") and failed:
            Adventure.participants= Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]+Adventure.userslist["run"]+fumblelist
            await ctx.send("The {}s gaze turned everyone to stone.".format(Adventure.challenge))
            await Adventure.damage(ctx,[item for item in Adventure.participants if item not in Adventure.userslist["run"]],CR*2)
            return
        if (Adventure.challenge == "Basilisk" or Adventure.challenge == "Medusa") and not slain and not persuaded:
            Adventure.participants= Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]+Adventure.userslist["run"]+fumblelist
            await ctx.send("The mirror shield reflected the {}s gaze, but it still managed to defeat you.".format(Adventure.challenge))
            await Adventure.damage(ctx,[item for item in Adventure.participants if item not in Adventure.userslist["run"]],CR)
            return
        amount = ((Adventure.str+Adventure.dipl)*people)
        if people == 1:
            if slain:
                scale = attack-Adventure.str
                if scale == 0:
                    text= ("**{}** bested the {} by a hair\'s breadth.").format(fighters,Adventure.challenge)
                elif scale <= 5:
                    text= ("**{}** barely managed to defeat the {}.").format(fighters,Adventure.challenge)
                elif scale <= 10:
                    text= ("**{}** defeated the {} with a skillful blow.").format(fighters,Adventure.challenge)
                elif scale <= 25:
                    text= ("That {} was no match for **{}s** fighting skills.").format(Adventure.challenge,fighters)
                else:
                    text= ("**{}** dispatched the {} effortlessly like swatting a fly.").format(fighters,Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["pray"],amount,(attack/Adventure.str),treasure)

            if persuaded:
                scale = diplomacy-Adventure.dipl
                if scale == 0:
                    text= ("**{}** almost died in battle,").format(talkers) + (" but confounded the {} in the last second.").format(Adventure.challenge)
                elif scale <= 5:
                    text= ("The {} resisted a bit,").format(Adventure.challenge) + (" but **{}** had the last word.").format(talkers)
                elif scale <= 10:
                    text= ("**{}** stumped the {} with eloquent skill.").format(talkers,Adventure.challenge)
                elif scale <= 25:
                    text= ("That {} was all ears for **{}**.").format(Adventure.challenge,talkers)
                else:
                    text= ("**{}** skillfully charmed the {}. There was no resistance.").format(talkers,Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["talk"]+Adventure.userslist["pray"],amount,(diplomacy/Adventure.dipl),treasure)

            if not slain and not persuaded:
                if attack == 0:
                    scale = Adventure.dipl-diplomacy
                else:
                    scale = Adventure.str-attack
                if scale <= 5:
                    options = ["That was slightly too difficult. Better luck next time.", "You could almost taste the glory of victory, now all you taste is blood.", "You almost won this."]
                elif scale <= 25:
                    options = ["No amount of diplomacy or valiant fighting could save you.", "This challenge was too much for one hero.", "You tried your best, but couldn't succeed alone."]
                else:
                    options = ["You never really had a chance.", "That one really mopped the floor with you.", "That could not have gone worse...", "You were beaten into a little gooey pulp."]
                text= random.choice(options)
        else:
            if slain and persuaded:
                ascale = attack-Adventure.str
                if ascale <= 5:
                    atxt = ("**{}** barely beat the {} in battle,").format(fighters,Adventure.challenge)
                elif ascale <= 10:
                    atxt = ("**{}** slayed the {} in battle,").format(fighters,Adventure.challenge)
                elif ascale <= 25:
                    atxt = ("**{}** skillfully defeated the {},").format(fighters,Adventure.challenge)
                else:
                    atxt = ("**{}** annihilated the {},").format(fighters,Adventure.challenge)
                dscale = diplomacy-Adventure.dipl
                if dscale <= 5:
                    dtxt = (" while **{}** desperately kept talking").format(talkers)
                elif dscale <= 10:
                    dtxt = (" during which **{}** distracted with flattery").format(talkers)
                elif dscale <= 25:
                    dtxt = (" as **{}** provided a charming distraction").format(talkers)
                else:
                    dtxt = (" but compared to the diplomacy of **{}**, there was no contest").format(talkers)
                if len(Adventure.userslist["pray"]) > 0:
                    text=  atxt + dtxt + (" and **{}** aided in Herberts name.").format(preachermen)
                else:
                    text= atxt + dtxt + "."
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"],amount,(attack/Adventure.str+diplomacy/Adventure.dipl),treasure)

            if not slain and persuaded:
                scale = diplomacy-Adventure.dipl
                if scale == 0:
                    text= ("**{}** almost died in battle,").format(talkers) + (" but survived solely on wit against the {} in the end").format(Adventure.challenge)
                elif scale <= 5:
                    text= ("The {} resisted a bit,").format(Adventure.challenge) + (" but **{}** had better arguments").format(talkers)
                elif scale <= 10:
                    text= ("**{}** dumbfounded the {} cunningly").format(talkers,Adventure.challenge)
                elif scale <= 25:
                    text= ("The {} has quite taken to **{}**").format(Adventure.challenge,talkers)
                else:
                    text= ("**{}** slyly mesmerized the {}. There never was a chance").format(talkers,Adventure.challenge)
                if len(Adventure.userslist["pray"]) > 0:
                    text += (", with **{}'s** blessing'.").format(preachermen)
                else:
                    text += "."
                text += await Adventure.reward(ctx, Adventure.userslist["talk"]+Adventure.userslist["pray"],amount,(diplomacy/Adventure.dipl),treasure)

            if slain and not persuaded:
                scale = attack-Adventure.str
                if scale == 0:
                    text= ("**{}** almost died to the {} but got the upper hand in the end").format(fighters,Adventure.challenge)
                elif scale <= 5:
                    text= ("**{}** slew the {} in a tough fight").format(fighters,Adventure.challenge)
                elif scale <= 10:
                    text= ("**{}** ended the {} with some cunning blows").format(fighters,Adventure.challenge)
                elif scale <= 25:
                    text= ("The {} had a really bad day meeting **{}**").format(Adventure.challenge,fighters)
                else:
                    text= ("**{}** just casually destroyed the {}").format(fighters,Adventure.challenge)
                if len(Adventure.userslist["pray"]) > 0:
                    text += (", with a little help from **{}**.").format(preachermen)
                else:
                    text += "."
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["pray"],amount,(attack/Adventure.str),treasure)

            if not slain and not persuaded:
                if attack == 0:
                    scale = Adventure.dipl-diplomacy
                elif diplomacy == 0:
                    scale = Adventure.str-attack
                else:
                    scale = (Adventure.dipl+Adventure.str)-(attack+diplomacy)
                if scale <= 5:
                    options = ["That was slightly too difficult. Better luck next time.", "The group could almost taste the glory of victory, now all you taste is blood.", "You almost had this. What a pity."]
                elif scale <= 25:
                    options = ["No amount of diplomacy or valiant fighting could save you.", "This challenge was too much for this group.", "You tried your best, but succumbed to overwhelming forces in the end."]
                else:
                    options = ["The party never really had a chance.", "That one really mopped the floor with the entire group.", "Not. Even. Close.", "All that remains of the valiant party are some greasy smears on the floor..."]
                text= random.choice(options)

        Adventure.timeout = 0
        await ctx.send(text)
        Adventure.participants= Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"]+Adventure.userslist["run"]+fumblelist
        if not slain and not persuaded:
            await Adventure.damage(ctx,[item for item in Adventure.participants if item not in Adventure.userslist["run"]],CR)

    async def reward(ctx, list, amount, modif, special):
        xp = max(1,round(amount))
        cp = max(1,round(amount * modif))
        phrase = ""
        for user in list:
            Adventure.rewards[user] = {}
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member == None:
                await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (6)")
                continue
            bxp = 0
            bcp = 0
            rroll = random.randint(1,50)
            if rroll == 50:
                await ctx.send("\n**{}** found an old scroll of parchment".format(member.display_name))
                if 'alchemy scroll' in Userdata.users[str(member.id)]['consumables'].keys():
                    Userdata.users[str(member.id)]['consumables']['alchemy scroll']['uses'] = Userdata.users[str(member.id)]['consumables']['alchemy scroll'].get("uses", 0) + 1
                else:
                    Userdata.users[str(member.id)]['consumables'].update({'alchemy scroll':{"slot":["consumable"],"uses":1}})
            if "xp" in Userdata.users[str(member.id)]['buffs'].keys():
                bxp = int(xp * (Userdata.users[str(member.id)]['buffs']['xp']['bonus']/100))
                phrase += "\n**{}** received **+{}** bonus xp.".format(member.display_name, bxp)
            if "money" in Userdata.users[str(member.id)]['buffs'].keys():
                bcp = int(cp * (Userdata.users[str(member.id)]['buffs']['money']['bonus']/100))
                phrase += "\n**{}** received **+{}** bonus cp.".format(member.display_name, bcp)
            roll = random.randint(1,5)
            if roll == 5 and Userdata.users[str(member.id)]['class']['name']=="Ranger" and not isinstance(Userdata.users[str(member.id)]['class']['ability'], bool):
                Adventure.rewards[user]["xp"] = int((xp+bxp) * Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'])
                Adventure.rewards[user]["cp"] = int((cp+bcp) * Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'])
                percent = round((Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'] - 1.0) * 100)
                phrase += "\n**{}** received a **{}%** reward bonus ({}).".format(member.display_name, percent, Userdata.users[str(member.id)]['class']['ability']['pet']['name'])
            else:
                Adventure.rewards[user]["xp"] = xp + bxp
                Adventure.rewards[user]["cp"] = cp + bcp
            if special != False:
                Adventure.rewards[user]["special"] = special
            else:
                Adventure.rewards[user]["special"] = False
        if special != False and sum(special) == 1:
            types = [" normal"," rare","n epic", "quest"]
            type = types[special.index(1)]
            phrase += "\nBase rewards: {} xp and {} copperpieces. You also secured **a{} treasure chest**!".format(xp,cp,type)
        elif special != False and sum(special) > 1:
            chesttext = []
            ctypes = ["{} normal","{} rare","{} epic", "{} quest"]
            for i,c in enumerate(special):
                if c >= 1:
                    chesttext.append(ctypes[i].format(c))
            phrase += "\nBase rewards: {} xp and {} copperpieces. You also secured **{} treasure chests**!".format(xp,cp, " and ".join([", ".join(chesttext[:-1]),chesttext[-1]] if len(chesttext) > 2 else chesttext))
        else:
            phrase += "\nBase rewards: {} xp and {} copperpieces.".format(xp,cp)
        if len(Userdata.sleepers) != 0:
            slept = " and ".join([", ".join(Userdata.sleepers[:-1]),Userdata.sleepers[-1]] if len(Userdata.sleepers) > 2 else Userdata.sleepers)
            phrase += "\n**{}** slept through the whole encounter.".format(slept)
            for name in Userdata.sleepers:
                member = discord.utils.find(lambda m: m.display_name == name, ctx.guild.members)
                if member != None:
                    phrase += " " + member.mention
            Userdata.sleepers.clear()
        return phrase

    async def damage(ctx,injured,CR):
        if "Dragon" in Adventure.challenge:
            org_dmg = max(1,round(CR/10))
        else:
            org_dmg = max(1,round(CR/20))
        base_dmg = round(org_dmg/Adventure.dmgred)
        dmg_red = org_dmg - base_dmg
        incap = []
        d_txt = ""
        for user in injured:
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member == None:
                continue
            if Userdata.users[str(member.id)]['hp'] > base_dmg:
                Userdata.users[str(member.id)]['hp'] -= base_dmg
            else:
                Userdata.users[str(member.id)]['hp'] = 0
                incap.append(user)
        await Userdata.save()
        incapacitated = " and ".join([", ".join(incap[:-1]),incap[-1]] if len(incap) > 2 else incap)
        inj_txt = " and ".join([", ".join(injured[:-1]),injured[-1]] if len(injured) > 2 else injured)
        preachermen = " and ".join([", ".join(Adventure.userslist["pray"][:-1]),Adventure.userslist["pray"][-1]] if len(Adventure.userslist["pray"]) > 2 else Adventure.userslist["pray"])
        if base_dmg == 0:
            d_txt += "**{}** mitigated all damage during this encounter. ".format(preachermen)
        elif dmg_red > 0:
            d_txt += "**{}** reduced damage taken by {}. \n**{}** took {} damage during this encounter. ".format(preachermen,dmg_red,inj_txt,base_dmg)
        else:
            d_txt += "**{}** took {} damage during this encounter. ".format(inj_txt,base_dmg)
        if len(incap) > 0:
            d_txt += "Time to rest for **{}** in order to recover some health.".format(incapacitated)
        await ctx.send(d_txt)


    def countdown(ctx, seconds = None, title = "Remaining: ", loop: Optional[asyncio.AbstractEventLoop] = None,) -> asyncio.Task:

        async def countdown():
            if seconds != None:
                counter = 0
                try:
                    secondint = int(seconds)
                    finish = await getEpochS(secondint)
                    if secondint < 0:
                        await ctx.send("I dont think im allowed to do negatives \U0001f914")
                        return
                    rem, done = await remaining(finish, False)
                    message = await ctx.send(title +" " + str(rem))
                    while True:
                        timer, done = await remaining(finish, False)
                        if done:
                            await message.delete()
                            break
                        await message.edit(content=("⏳ " + title + " {0}s".format(timer)))
                        await asyncio.sleep(1)
                except ValueError:
                    await ctx.send("Must be a number!")
            else:
                counter = 0
                try:
                    secondint = int(Adventure.timeout)
                    Adventure.finish = await getEpoch()
                    if secondint < 0:
                        await ctx.send("I dont think im allowed to do negatives \U0001f914")
                        return
                    rem, done = await remaining(Adventure.finish, True)
                    message = await ctx.send(title + " " + str(rem))
                    while True:
                        timer, done = await remaining(Adventure.finish, True)
                        if done:
                            Adventure.timeout = 0
                            await message.delete()
                            break
                        await message.edit(content=("⏳ " + title + " {0}s".format(timer)))
                        await asyncio.sleep(1)
                except ValueError:
                    await ctx.send("Must be a number!")

        async def remaining(epoch, fromAdv):
            remaining = epoch - time.time()
            finish = (remaining < 0)
            m, s = divmod(remaining, 60)
            h, m = divmod(m, 60)
            s = int(s)
            m = int(m)
            h = int(h)
            if fromAdv:
                Adventure.timeout = remaining
            if h == 0 and m == 0:
                out = "{:02d}".format(s)
            elif h == 0:
                out = "{:02d}:{:02d}".format(m, s)
            else:
                out = "{:01d}:{:02d}:{:02d}".format(h, m, s)
            return out, finish

        async def getEpoch():
            #epoch = time.time()
            epoch = Adventure.started
            epoch += Adventure.timeout
            return epoch

        async def getEpochS(seconds : int):
            epoch = time.time()
            epoch += seconds
            return epoch

        if loop is None:
            loop = asyncio.get_event_loop()

        return loop.create_task(countdown())


    def start_adding_reactions(
        message: discord.Message,
        emojis: Iterable[_ReactableEmoji],
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> asyncio.Task:
        """Start adding reactions to a message.

        This is a non-blocking operation - calling this will schedule the
        reactions being added, but will the calling code will continue to
        execute asynchronously. There is no need to await this function.

        This is particularly useful if you wish to start waiting for a
        reaction whilst the reactions are still being added - in fact,
        this is exactly what `menu` uses to do that.

        This spawns a `asyncio.Task` object and schedules it on ``loop``.
        If ``loop`` omitted, the loop will be retreived with
        `asyncio.get_event_loop`.

        Parameters
        ----------
        message: discord.Message
            The message to add reactions to.
        emojis : Iterable[Union[str, discord.Emoji]]
            The emojis to react to the message with.
        loop : Optional[asyncio.AbstractEventLoop]
            The event loop.

        Returns
        -------
        asyncio.Task
            The task for the coroutine adding the reactions.

        """

        async def task():
            # The task should exit silently if the message is deleted
            with contextlib.suppress(discord.NotFound):
                for emoji in emojis:
                    await message.add_reaction(emoji)

        if loop is None:
            loop = asyncio.get_event_loop()

        return loop.create_task(task())
