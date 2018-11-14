import json
import os
from redbot.core import commands
import asyncio
import contextlib
from typing import Union, Iterable, Optional
import discord
import random
import calendar
import time
from .custompredicate import CustomPredicate

os.chdir(r'C:\RedBot\cogs\CogManager\cogs\gobcog')

_ReactableEmoji = Union[str, discord.Emoji]

class Adventure:

    attribs = {" terrifying":[1,1.2]," hideous":[1,1]," weak":[0.5,1]," sick":[0.3,0.9]," stupid":[1,0.5]," cunning":[1.2,1.2]," fat":[1.1,0.9]," fairly intelligent":[1,1.2]," dumb":[1,0.8],"n old":[0.8,1.5],"n ancient":[0.8,2]}
    monsters = {"Ogre":{"str":18,"dipl":10},"Gnoll":{"str":12,"dipl":8},"Wizard":{"str":8,"dipl":15},"Demon":{"str":30,"dipl":17},"Cave Rat":{"str":5,"dipl":99},"Fire Elemental":{"str":13,"dipl":13},"Bandit":{"str":10,"dipl":10},"Basilisk":{"str":50,"dipl":50},"Red Dragon":{"str":95,"dipl":95}}
    challenge = ""
    attrib = ""
    userslist = {}
    emoji_lookup = {"fight": "🗡", "talk" : "🗨", "pray" : "🛐", "run" : "❌"}
    finish = 0

    async def simple(ctx):
        locations = ["There is telling of a dangerous cave nearby, holding immense riches. ", "You found a small clearing. ", "A bridge crosses over a deep gorge. ", "This towns inn looks very inviting. "]
        raisins = [" is going to investigate, but ", " is curious to have a peek, but ", " would like to have a look, but ", " wants to go there, but "]
        await ctx.send(random.choice(locations) + ctx.author.name + random.choice(raisins))
        await Adventure.choice(ctx)
        return Adventure.rewards

    async def choice(ctx):
        Adventure.challenge = random.choice(list(Adventure.monsters.keys())) #if you want the dict with accompanying subkeys use: Adventure.monsters[random.choice(list(Adventure.monsters.keys()))]
        Adventure.attrib = random.choice(list(Adventure.attribs.keys()))
        Adventure.str = Adventure.monsters[Adventure.challenge]["str"]*Adventure.attribs[Adventure.attrib][0]
        Adventure.dipl = Adventure.monsters[Adventure.challenge]["dipl"]*Adventure.attribs[Adventure.attrib][1]
        Adventure.userslist = {"fight":[],"pray":[],"talk":[],"run":[]}
        Adventure.rewards = {}
        if Adventure.challenge == "Red Dragon":
            await Adventure.menu(ctx, [("a{} {} just landed in front of you glaring! \n\nWhat will you do and will other heroes be brave enough to help you? (Str: {}, Dipl: {}) \nHeroes have 30s to participate via reaction:").format(Adventure.attrib,Adventure.challenge,str(int(Adventure.str)),str(int(Adventure.dipl)))], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})
        elif Adventure.challenge == "Basilisk":
            await Adventure.menu(ctx, [("a{} {} stepped out looking around. \n\nWhat will you do and will other heroes help your cause? (Str: {}, Dipl: {}) \nHeroes have 30s to participate via reaction:").format(Adventure.attrib,Adventure.challenge,str(int(Adventure.str)),str(int(Adventure.dipl)))], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})
        else:
            await Adventure.menu(ctx, [("a{} {} is guarding it with menace. \n\nWhat will you do and will other heroes help your cause? (Str: {}, Dipl: {}) \nHeroes have 30s to participate via reaction:").format(Adventure.attrib,Adventure.challenge,str(int(Adventure.str)),str(int(Adventure.dipl)))], {"🗡": Adventure.fight, "🗨": Adventure.talk, "🛐": Adventure.pray, "❌": Adventure.run})


    async def menu(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message = None,
        page: int = 0,
        timeout: float = 30.0,
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
                timeout=timeout,
            )
        except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
            try:
                await message.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in controls.keys():
                    await message.remove_reaction(key, ctx.bot.user)
            pages = ["nobody did anything. You failed."]
            return await Adventure.menu(ctx, pages, controls, message=message, page=page, timeout=timeout)
        await controls[react.emoji](ctx, pages, controls, message, page, timeout, react.emoji, user)

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
        Adventure.finish = time.time() + 15
        await Adventure.check(check_other,"fight", ctx, pages, controls, message, page, timeout, emoji, user)

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
        Adventure.finish = time.time() + 15
        await Adventure.check(check_other,"run", ctx, pages, controls, message, page, timeout, emoji, user)

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
        Adventure.finish = time.time() + 15
        await Adventure.check(check_other,"pray", ctx, pages, controls, message, page, timeout, emoji, user)

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
        Adventure.finish = time.time() + 15
        await Adventure.check(check_other,"talk", ctx, pages, controls, message, page, timeout, emoji, user)

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
                timeout=15,
            )
        except asyncio.TimeoutError:
            return await Adventure.result(ctx, pages, controls, message, page, timeout)
        return await controls[react.emoji](ctx, pages, controls, message, page, timeout, react.emoji, user)


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
            for user in Adventure.userslist["fight"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if roll== 1:
                    await ctx.send("**" + user + "**" + " fumbled his attack.")
                    fumblelist.append(user)
                elif roll == 20:
                    await ctx.send("**" + user + "**" + " landed a critical hit.")
                    critlist.append(user)
                    attack += roll + random.randint(5,10) + users[str(member.id)]['att']
                else:
                    attack += roll + users[str(member.id)]['att']
            return (fumblelist, critlist, attack)

        async def handle_pray(attack, diplomacy):
            for user in Adventure.userslist["pray"]:
                roll = random.randint(1,20)
                if roll == 20:
                    attack += 20
                    diplomacy += 20
                    await ctx.send("**" + user + "**" + "'s prayer called upon the mighty Herbert to help you.")
                else:
                    Adventure.userslist["pray"].remove(user)
                    await ctx.send("**" + user + "**" + "'s prayers went unanswered.")
            return (attack, diplomacy)

        async def handle_talk(fumblelist, critlist, diplomacy):
            for user in Adventure.userslist["talk"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if roll== 1:
                    await ctx.send("**" + user + "**" + (" accidentally offended the {}.").format(Adventure.challenge))
                    fumblelist.append(user)
                elif roll == 20:
                    await ctx.send("**" + user + "**" + " made a compelling argument.")
                    critlist.append(user)
                    diplomacy += roll + random.randint(5,10) + users[str(member.id)]['cha']
                else:
                    diplomacy += roll + users[str(member.id)]['cha']
            return (fumblelist, critlist, diplomacy)

        async def handle_basilisk(failed):
            if Adventure.challenge == "Basilisk":
                failed = True
                for user in Adventure.userslist["fight"]: #check if any fighter has an equipped mirror shield to give them a chance.
                    member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                    if 'mirror_shield' in users[str(member.id)]['items']['left']:
                        failed = False
                        break
            else:
                failed = False
            return failed

        with open('users.json', 'r') as f:
            users = json.load(f)
        try:
            await message.clear_reactions()
        except discord.Forbidden:  # cannot remove all reactions
            for key in controls.keys():
                await message.remove_reaction(key, ctx.bot.user)
        pages = [w.replace('\nHeroes have 30s to participate via reaction:', '') for w in pages]
        current_page = pages[page]
        if isinstance(current_page, discord.Embed):
            await message.edit(embed=current_page)
        else:
            await message.edit(content=current_page)
        if people == 0:
            pages = ["everyone ran away. You failed."]
            return await Adventure.menu(ctx, pages, controls, message=message, page=page, timeout=timeout)

        attack,diplomacy = await handle_run(attack, diplomacy)
        attack, diplomacy = await handle_pray(attack, diplomacy)
        fumblelist, critlist, diplomacy= await handle_talk(fumblelist, critlist, diplomacy)
        failed = await handle_basilisk(failed)
        fumblelist, critlist, attack = await handle_fight(fumblelist, critlist, attack)

        slain = attack >= Adventure.str
        persuaded = diplomacy >= Adventure.dipl

        fighters = " and ".join([", ".join(Adventure.userslist["fight"][:-1]),Adventure.userslist["fight"][-1]] if len(Adventure.userslist["fight"]) > 2 else Adventure.userslist["fight"])
        talkers = " and ".join([", ".join(Adventure.userslist["talk"][:-1]),Adventure.userslist["talk"][-1]] if len(Adventure.userslist["talk"]) > 2 else Adventure.userslist["talk"])
        text = ""

        if slain or persuaded and not failed:
            if Adventure.challenge == "Basilisk": #rewards 50:50 epic:normal chest for killing the basilisk
                treasure = random.choice([[0,1,0],[1,0,0]])
            elif Adventure.challenge == "Dragon": #always rewards an epic chest.
                treasure = [0,0,1]
            else:
                if len(critlist) != 0:
                    treasure = [1,0,0]
                else:
                    treasure = False
        if Adventure.challenge == "Basilisk" and failed:
            await ctx.send("The Basilisk's gaze turned everyone to stone.")
            return
        if Adventure.challenge == "Basilisk" and not slain and not persuaded:
            await ctx.send("The mirror shield reflected the Basilisks gaze, but he still managed to kill you.")
            return
        if people == 1:
            if slain:
                text= ("{} has slain the {} in epic battle!").format(fighters,Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["pray"],((Adventure.str+Adventure.dipl)//people),(attack/Adventure.str),treasure)

            if  persuaded:
                text= ("{} almost died in battle,").format(talkers) + (" but confounded the {} in the last second.").format(Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["talk"]+Adventure.userslist["pray"],((Adventure.str+Adventure.dipl)//people),(diplomacy/Adventure.dipl),treasure)

            if not slain and not persuaded:
                options = ["No amount of diplomacy or valiant fighting could save you. You died.", "This challenge was too much for one hero.", "You tried your best, but couldn't succeed alone."]
                text= random.choice(options)
        else:
            if slain and persuaded:
                text= ("{} slayed the {} in battle,").format(fighters,Adventure.challenge) + ("while {} distracted with insults.").format(talkers)
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["talk"]+Adventure.userslist["pray"],((Adventure.str+Adventure.dipl)//people),(attack/Adventure.str+diplomacy/Adventure.dipl),treasure)

            if  not slain and persuaded:
                text= ("{} talked the {} down.").format(talkers,Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["talk"]+Adventure.userslist["pray"],((Adventure.str+Adventure.dipl)//people),(diplomacy/Adventure.dipl),treasure)

            if slain and not persuaded:
                text= ("{} killed the {} in a most heroic battle.").format(fighters,Adventure.challenge)
                text += await Adventure.reward(ctx, Adventure.userslist["fight"]+Adventure.userslist["pray"],((Adventure.str+Adventure.dipl)//people),(attack/Adventure.str),treasure)

            if not slain and not persuaded:
                options = ["No amount of diplomacy or valiant fighting could save you. Everyone died.", "This challenge was too much for this group.", "You tried your best, but succumbed to overwhelming forces in the end."]
                text= random.choice(options)

        await ctx.send(text)

    async def reward(ctx, list, amount, modif, special):
        xp = max(1,round(amount / modif))
        cp = max(1,round(amount * modif))
        for user in list:
            Adventure.rewards[user] = {}
            Adventure.rewards[user]["xp"] = xp
            Adventure.rewards[user]["cp"] = cp
            if special != False:
                Adventure.rewards[user]["special"] = special
            else:
                Adventure.rewards[user]["special"] = False
        if special != False:
            types = [" normal"," rare","n epic"]
            type = types[special.index(1)]
            return "\nYou have been awarded {} xp and found {} copperpieces. You also secured a{} treasure chest!".format(xp,cp,type)
        else:
            return "\nYou have been awarded {} xp and found {} copperpieces.".format(xp,cp)

    def countdown(ctx, seconds, title, loop: Optional[asyncio.AbstractEventLoop] = None,) -> asyncio.Task:

        async def countdown():
            counter = 0
            try:
                secondint = int(seconds)
                Adventure.finish = getEpoch(secondint)
                if secondint < 0 or secondint == 0:
                    await ctx.send("I dont think im allowed to do negatives \U0001f914")
                    raise BaseException

                message = await ctx.send("[" + title +"] " + remaining(Adventure.finish)[0])
                while True:
                    timer, done = remaining(Adventure.finish)
                    if done:
                        await message.delete()
                        break
                    await message.edit(content=("[" + title + "] {0}s".format(timer)))
                    await asyncio.sleep(1)
            except ValueError:
                await ctx.send("Must be a number!")

        def remaining(epoch):
            remaining = epoch - time.time()
            finish = (remaining < 0)
            m, s = divmod(remaining, 60)
            h, m = divmod(m, 60)
            s = int(s)
            m = int(m)
            h = int(h)
            out = "{:02d}".format(s)
            return out, finish

        def getEpoch(seconds : int):
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



    DEFAULT_CONTROLS = {"🗡": fight, "🗨": talk, "🛐": pray, "❌": close_menu}
