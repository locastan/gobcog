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
import logging

_ReactableEmoji = Union[str, discord.Emoji]

class Quest:

    log = logging.getLogger("red")

    attribs = {" terrifying":[1,1.2],
                " hideous":[1,1],
                " lumbering":[1,1],
                " weak":[0.5,1],
                " sick":[0.3,0.9],
                " stupid":[1,0.5],
                " cunning":[1.2,1.2],
                " furious":[1.1,0.9],
                " fairly intelligent":[1,1.2],
                " dumb":[1,0.8],
                "n old":[0.8,1.5],
                "n ancient":[0.8,2],
                " colossal":[2,1.1],
                " miniature":[0.7,0.9],
                " feral":[1.8,0.9],
                " careless":[0.5,0.8],
                " breathtaking":[1,1.9],
                " brutal":[2,0.8],
                "n overpowered":[3,3]}
    wood_monsters = {"Ogre":{"str":28,"dipl":18, "pronoun": "its"},
                "Gnoll":{"str":20,"dipl":15, "pronoun": "its"},
                "Cave Spider":{"str":60,"dipl":50, "pronoun": "its"},
                "Wood Troll":{"str":35,"dipl":10, "pronoun": "its"},
                "Band of Troggels":{"str":25,"dipl":28, "pronoun": "its"},
                "Orc":{"str":26,"dipl":20, "pronoun": "his"},
                "Swarm of Jabberflies":{"str":30,"dipl":30, "pronoun": "its"},
                "Witch":{"str":30,"dipl":30, "pronoun": "her"},
                "Owlbear":{"str":40,"dipl":35, "pronoun": "its"},
                "Pack of Wolves":{"str":29,"dipl":45, "pronoun": "it"},
                "Toadward and 3 Ogres":{"str":50,"dipl":50, "pronoun": "their"},
                "Bandit":{"str":20,"dipl":20, "pronoun": "him"},
                "Giant":{"str":45,"dipl":30, "pronoun": "its"},
                "Archmage":{"str":28,"dipl":30, "pronoun": "him"}}
    wood_bosses = {"Lady Bane":{"str":90,"dipl":115, "pronoun": ""},
                "Green Dragon":{"str":95,"dipl":105, "pronoun": "The "},
                "Duke Igthorn":{"str":130,"dipl":120, "pronoun": ""}}
    tomb_monsters = {"Beholder Zombie":{"str":30,"dipl":35, "pronoun": "it"},
                "Bunch of Ghouls":{"str":60,"dipl":60, "pronoun": "it"},
                "Wizard":{"str":20,"dipl":25, "pronoun": "he"},
                "Trap":{"str":65,"dipl":50, "pronoun": "it"},
                "Diamond Troll":{"str":50,"dipl":50, "pronoun": "he"}}
    tomb_bosses = {"Grz'al Brömpf":{"str":120,"dipl":120, "pronoun": "he"}}
    arena_monsters = {"Brassmoon Guard":{"str":4,"dipl":6, "pronoun": "He is"},
                "Warforged Golem":{"str":10,"dipl":8, "pronoun": "It is"},
                "Hammerhead Dwarf":{"str":5,"dipl":9, "pronoun": "He is"},
                "Drunk Bard":{"str":8,"dipl":10, "pronoun": "He is"},
                "Darkelf Mage":{"str":9,"dipl":12, "pronoun": "He is"},
                "Bone Dragon":{"str":18,"dipl":20, "pronoun": "It is"},
                "Black Aliss":{"str":20,"dipl":19, "pronoun": "She is"},
                "Gnome Warlord":{"str":10,"dipl":12, "pronoun": "He is"},
                "Pictsie":{"str":9,"dipl":6, "pronoun": "He is"},
                "Ice Giantess":{"str":12,"dipl":15, "pronoun": "She is"},
                "Hellspectre":{"str":17,"dipl":18, "pronoun": "It is"},
                "Switchbeast":{"str":22,"dipl":18, "pronoun": "It is"},
                "Can of Purpleworms":{"str":20,"dipl":15, "pronoun": "It is"},
                "Wraith":{"str":20,"dipl":20, "pronoun": "It is"},
                "Xorza\'cuatl":{"str":14,"dipl":16, "pronoun": "Whatever this is, it\'s"},
                "Westershire Pirate":{"str":9,"dipl":10, "pronoun": "He is"}}
    arena_bosses = {"Destroyer":{"str":25,"dipl":23, "pronoun": "He is"},
                "Bonesmasher":{"str":26,"dipl":20, "pronoun": "He is"},
                "Kyra Dragonqueen":{"str":27,"dipl":30, "pronoun": "She is"},
                "Black Aliss":{"str":20,"dipl":19, "pronoun": "She is"},}
    effects = {"Weakness":["str",0.5,0.8],
                "Sleep":["dipl",0,0],
                "Blind":["str",0.2,0.9],
                "Entangle":["str",0.3,1],
                "Fumble":["dipl",0,0],
                "Silence":["dipl",1,0.1],
                "Magic Missile":["dmg",1,4],
                "Fireball":["dmg",5,12]}

                    # structure of quest entries: text, challenge attrib, challenge, effect, effect text, chance to cause effect
    tomb = [["**The tomb of Grz'al Brömpf** is beckoning. {} mighty heroes are brave and mad enough to attempt loot the vast riches deep in the mountain.", None, None, None, None, 0],
            ["The entrance is guarded by **a{0} {1}**. The {1} warns you not to enter this dungeon, claiming all the treasure inside to be rightfully his.", None, "Wizard", "Any", "```css\n The affronted {} casts {}.```", 40],
            ["With the selfproclaimed guardian out of the way, you venture inside. Narrow passages were hewn into the bare rock making it uncomfortable to move along. A small chamber finally allows for some space, but **a{0} {1}** heard you enter and is now waking up.", None, "Beholder Zombie", "Weakness", "```css\n The {} is making a flatulent sound and a foul odour is making an assault on your senses.```", 100],
            ["That decaying Beholder was no match for this party! Onwards and downwards you venture into perilous darkness. You descend into a large cave, where luminous fungi and sharp crystals decorating every surface create a breathtaking display of wonder. Then the crystals start to move and the floor shakes as **a{} {}** unfolds.", " lumbering", "Diamond Troll", "Blind", "```css\n A bright flash of light comes off the {}, blinding you.```", 100],
            ["You made a bit of profit on that one if you manage to get out of this tomb alive. As you venture on, it gets quite a bit warmer and the air smells of brimstone. It's probably just some geothermal vent or volcanic activity you reassure yourselfes moving on. From behind a boulder in a darker corner, two gleaming eyes gleefully watch you trigger **a{} {}**.","n ancient","Trap","Entangle","```css\n Creepy black tendrils whip around blindly searching for anything to grab.```", 100],
            ["That wasn't easy. On top of things, **a{} {}** got attracted by the trap to prey on its victims.",None,"Bunch of Ghouls",None,None,0],
            ["Finally this seems to be the end of this tomb. You found an ornate coffin amidst several tall bookcases filled with magic folios. Some stacks of books are piled on a sturdy desk, where an oil lamp is burning. Doesn't it seem strange how this resembles more an active workplace than a grave? This question is answered with a sombre \"YES\" as the archlich **{1}** manifests himself out of the very dust this room is covered in."," hideous","Grz'al Brömpf","Sleep","```css\n \"GOOD NIGHT, MIGHTY HERO\" {} booms maniacally.```",50]]
    wood = [["**The dark and brooding shadow forests of Dunwyn** lie in front of you. {} heroes be crossing. How far will they make it?", None, None, None, None, 0],
            ["A clearing opens up and allows for some scarce sunlight in this gloomy woods. Apparently **a{0} {1}** is enjoying the sun as well, startled by your sudden appearance.", None, None, None, None, 0],
            ["Further back in some overgrown thicket, you spot a small cottage...made of gingerbread? **A{0} {1}** is beckoning you closer. The fact that {2} skin is green and {2} faces\' warts are nearly covered by the big hooked nose does not bode well.", "n old", "Witch", "Any", "```css\n The wicked old {} casts {}.```", 80],
            ["A cave tunnel was mentioned in a travellers guide as a shortcut. As you joyfully enter, you start wondering after a few meters if this spidersilk clad tunnel with bones on the floor is the right way. **A{0} {1}** however is grateful for such a big snack walking in willingly.", None, "Cave Spider", None, None, 0],
            ["As you return from the cave, you tear up that wretched travellers guide into shreds. **A{0} {1}** is not happy about your littering the forest it calls {2} home.", " colossal", "Owlbear", None, None, 0],
            ["Swatting your partymember to keep that infernal buzzing noise down, you realize it is coming from all around you. **A{0} {1}** has surrounded you.", None, "Swarm of Jabberflies", "Blind", "```css\n The {} is like a black cloud obscuring your vision.```", 100],
            ["Now this seems to be the cave tunnel shortcut the guide was talking about. No spidersilk anywhere and smooth walls! But this time it is guarded by **a{0} {1}**", None, "Toadward and 3 Ogres", None, None, 0],
            ["The end of that tunnel led you up into the middle of Drekmore Castle! **{2} {1}** watched you emerge from the small grate in the courtyard and is now launching an attack.", None, None, "Any", "```css\n {2}{0} is casting {1}.```", 80]]
    arena = [["Our {} adventurers are bravely entering the **Arena of endless horrible Deaths**. Then suddenly all hell breaks loose.", None, None, None, None, 0],
            ["The announcer summons **a{0} {1}** into the arena.", None, None, None, None, 0],
            ["Next up on the list of contestants is **a{0} {1}**. {2} rudely gesturing what {3} going to do to your slain corpses.", None, None, None, None, 0],
            ["Time for some crowd pleasing! **A{0} {1}** is whipping up some dark magic.", None, None, "Any", "```css\n The {} casts {}.```", 100],
            ["Her heart is as black as her soul. Meet **a{0} {1}**. A melange of blackclad witchdom and halitosis.", None, "Black Aliss", "Any", "```css\n {} giggles maniacally and casts {}.```", 90],
            ["Here comes **a{0} {1}**. {2} as colorful as a bruise.", None, None, None, None, 0],
            ["Some like **a{0} {1}** to the salt of the earth. Probably meaning {3} square, rough and bad for your health.", None, None, None, None, 0],
            ["Order up! Here comes **a{0} {1}**. No refunds!", None, None, "Any", "```css\n To your surprise, the {} cast {}.```", 50],
            ["Now **a{0} {1}** is raging and screaming towards you.", None, None, None, None, 0],
            ["**A{0} {1}** is making quite a pompous entrance. Let's see if you can cut this challenge down to size.", None, None, None, None, 0],
            ["Gather round to see **a{0} {1}** make a move in the arena.", None, None, None, None, 0],
            ["A round of applause heralds the coming of **a{0} {1}**. {2} an all time audience favourite.", None, None, None, None, 0]]

    challenge = ""
    attrib = ""
    userslist = {}
    emoji_lookup = {"fight": "🗡", "talk" : "🗨", "pray" : "🛐", "run" : "❌"}
    finish = 0
    timeout = 0
    started = 0

    async def queste(ctx, party): # party is a list of user.display_name of partymembers.
        if Quest.timeout != 0:
            Quest.log.exception("Quest.timeout != 0: There is already a Quest in session.")
            return None
        Quest.rewards = {}
        Quest.effect = None
        Quest.affected = []
        Quest.dead = []
        Quest.participants = party
        Quest.partyIDs = []
        Quest.idx = 0
        Quest.depth = 0 #only used for endless dungeons
        Quest.running = True
        Quest.failed = False
        Quest.sumxp = 0
        Quest.sumcp = 0
        Quest.dmgred = 1
        Quest.sumtreasure = [0,0,0,0]
        for user in party:
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member == None:
                await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (Namechange during quest)")
                continue
            Quest.partyIDs.append(member.id)
        Quest.name = random.choice(["tomb", "wood", "arena"])
        Quest.endless = (Quest.name == "arena")
        Quest.quest = getattr(Quest, Quest.name)
        Quest.monsters = getattr(Quest, Quest.name + "_monsters")
        Quest.bosses = getattr(Quest, Quest.name + "_bosses")

        if Quest.endless:
            await ctx.send(Quest.quest.pop(Quest.idx)[0].format(len(Quest.participants)))
        else:
            await ctx.send(Quest.quest[Quest.idx][0].format(len(Quest.participants)))
        await Quest.narrate(ctx)
        if Quest.failed:
            for ID in Quest.partyIDs:
                member = discord.utils.find(lambda m: m.id == ID, ctx.guild.members)
                Quest.dead.append(member.display_name)
                if member.display_name in Quest.rewards:
                    Quest.rewards.pop(member.display_name)
        return (Quest.rewards, party, Quest.dead)

    async def narrate(ctx):
        while Quest.running:
            Quest.userslist = {"fight":[],"pray":[],"talk":[],"run":[]}
            Quest.dmgred = 1
            if Quest.endless:
                Quest.idx = random.randint(0,int(len(Quest.quest)-1)) #randomized pick from list of stages
                Quest.depth += 1 #this keeps track of how far/deep we are now.
            else:
                Quest.idx += 1
            Quest.affected = []
            if Quest.quest[Quest.idx][1] == None:
                Quest.attrib = random.choice(list(Quest.attribs.keys()))
            else:
                Quest.attrib = Quest.quest[Quest.idx][1]
            if Quest.quest[Quest.idx][2] == None:
                if Quest.endless:
                    if Quest.depth % 5 == 0:
                        Quest.challenge = random.choice(list(Quest.bosses.keys()))
                    else:
                        Quest.challenge = random.choice(list(Quest.monsters.keys()))
                else:
                    if Quest.idx < (len(Quest.quest)-1):
                        Quest.challenge = random.choice(list(Quest.monsters.keys()))
                    elif Quest.idx >= (len(Quest.quest)-1):
                        Quest.challenge = random.choice(list(Quest.bosses.keys()))
            else:
                Quest.challenge = Quest.quest[Quest.idx][2]
            Quest.effect = Quest.quest[Quest.idx][3] # Intended for special ability or effect of a room or enemy or trap.
            if Quest.endless:
                if Quest.depth % 5 == 0:
                    Quest.str = Quest.bosses[Quest.challenge]["str"]*Quest.attribs[Quest.attrib][0] * Quest.depth
                    Quest.dipl = Quest.bosses[Quest.challenge]["dipl"]*Quest.attribs[Quest.attrib][1] * Quest.depth
                else:
                    Quest.str = Quest.monsters[Quest.challenge]["str"]*Quest.attribs[Quest.attrib][0] * Quest.depth
                    Quest.dipl = Quest.monsters[Quest.challenge]["dipl"]*Quest.attribs[Quest.attrib][1] * Quest.depth
            else:
                if Quest.idx < (len(Quest.quest)-1):
                    Quest.str = Quest.monsters[Quest.challenge]["str"]*Quest.attribs[Quest.attrib][0]
                    Quest.dipl = Quest.monsters[Quest.challenge]["dipl"]*Quest.attribs[Quest.attrib][1]
                elif Quest.idx >= (len(Quest.quest)-1):
                    Quest.str = Quest.bosses[Quest.challenge]["str"]*Quest.attribs[Quest.attrib][0]
                    Quest.dipl = Quest.bosses[Quest.challenge]["dipl"]*Quest.attribs[Quest.attrib][1]
            Quest.started = time.time()
            if "Dragon" in Quest.challenge:
                Quest.timeout = 90
            elif (Quest.str + Quest.dipl) > 100:
                Quest.timeout = 60
            else:
                Quest.timeout = 45
            if Quest.endless:
                await ctx.send("🏟️ **Round {}**".format(Quest.depth))
            else:
                await ctx.send("📖 **Chapter {}**".format(Quest.idx))
            Quest.countdown(ctx, None, "Time remaining: ")
            await asyncio.sleep(0.2)
            if Quest.endless:
                if Quest.depth % 5 == 0: #Quest.idx is randomized.
                    await Quest.menu(ctx, [(Quest.quest[Quest.idx][0]).format(Quest.attrib,Quest.challenge,Quest.bosses[Quest.challenge]["pronoun"],Quest.bosses[Quest.challenge]["pronoun"].lower())], {"🗡": Quest.fight, "🗨": Quest.talk, "🛐": Quest.pray, "❌": Quest.run})
                else:
                    await Quest.menu(ctx, [(Quest.quest[Quest.idx][0]).format(Quest.attrib,Quest.challenge,Quest.monsters[Quest.challenge]["pronoun"],Quest.monsters[Quest.challenge]["pronoun"].lower())], {"🗡": Quest.fight, "🗨": Quest.talk, "🛐": Quest.pray, "❌": Quest.run})
            else:
                if Quest.idx < (len(Quest.quest)-1):
                    await Quest.menu(ctx, [(Quest.quest[Quest.idx][0]).format(Quest.attrib,Quest.challenge,Quest.monsters[Quest.challenge]["pronoun"],Quest.monsters[Quest.challenge]["pronoun"].lower())], {"🗡": Quest.fight, "🗨": Quest.talk, "🛐": Quest.pray, "❌": Quest.run})
                else:
                    await Quest.menu(ctx, [(Quest.quest[Quest.idx][0]).format(Quest.attrib,Quest.challenge,Quest.bosses[Quest.challenge]["pronoun"],Quest.bosses[Quest.challenge]["pronoun"].lower())], {"🗡": Quest.fight, "🗨": Quest.talk, "🛐": Quest.pray, "❌": Quest.run})

    async def handle_breakup(user):
        equipped = {}
        for slot in Userdata.users[str(user.id)]['items']:
            if Userdata.users[str(user.id)]['items'][slot] and slot != "backpack":
                equipped.update(Userdata.users[str(user.id)]['items'][slot])
        item = random.choice(list(equipped.keys()))
        for slot in equipped[item].get('slot'):
            Userdata.users[str(user.id)]['items'][slot] = {}
            Userdata.users[str(user.id)]['att'] -= int(equipped[item].get('att'))     # keep in mind that double handed items grant their bonus twice so they remove twice
            Userdata.users[str(user.id)]['cha'] -= int(equipped[item].get('cha'))
            await Userdata.save()
            await ctx.send("**{}** broke his **{}** during the fumble.".format(user.display_name,item))

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
            Quest.start_adding_reactions(message, controls.keys(), ctx.bot.loop)
        else:
            if isinstance(current_page, discord.Embed):
                await message.edit(embed=current_page)
            else:
                await message.edit(content=current_page)

        try:
            react, user = await ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message, Quest.partyIDs),
                timeout=Quest.timeout
            )
        except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
            try:
                await message.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in controls.keys():
                    await message.remove_reaction(key, ctx.bot.user)
            pages = ["Nobody did anything. You all died."]
            await message.edit(content=pages[0])
            Quest.running = False
            Quest.Failed = True
            return
        await controls[react.emoji](ctx, pages, controls, message, page, Quest.timeout, react.emoji, user)

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
        await Quest.check(check_other,"fight", ctx, pages, controls, message, page, Quest.timeout, emoji, user)

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
        await Quest.check(check_other,"run", ctx, pages, controls, message, page, Quest.timeout, emoji, user)

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
        await Quest.check(check_other,"pray", ctx, pages, controls, message, page, Quest.timeout, emoji, user)

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
        await Quest.check(check_other,"talk", ctx, pages, controls, message, page, Quest.timeout, emoji, user)

    async def check(check_lists,call_from, ctx, pages, controls, message, page, timeout, emoji, user):
        for x in check_lists:
            if user.display_name in Quest.userslist[x]:
                symbol = Quest.emoji_lookup[x]
                Quest.userslist[x].remove(user.display_name)
                await message.remove_reaction(symbol, user)
        if user.display_name not in Quest.userslist[call_from] and user.id in Quest.partyIDs:
            Quest.userslist[call_from].append(user.display_name)
        try:
            react, user = await ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message, Quest.partyIDs),
                timeout=Quest.timeout
            )
        except asyncio.TimeoutError:
            return await Quest.result(ctx, pages, controls, message, page, Quest.timeout)
        return await controls[react.emoji](ctx, pages, controls, message, page, Quest.timeout, react.emoji, user)


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
        att_mod = 1
        dipl_mod = 1
        fumblelist = []
        critlist = []
        people = len(Quest.userslist["fight"])+len(Quest.userslist["talk"])+len(Quest.userslist["pray"])

        async def handle_effect():
            if Quest.effect != None:
                roll = random.randint(1,100) #if effect chance is not met return silently.
                saving_throw = 10 #initializte here with a default value if something goes wrong later with the if else.
                if roll > Quest.quest[Quest.idx][5]:
                    return
                if Quest.effect == "Any":
                    Quest.effect = random.choice(list(Quest.effects.keys()))
                if Quest.endless:
                    if Quest.depth % 5 == 0:
                        await ctx.send((Quest.quest[Quest.idx][4]).format(Quest.challenge,Quest.effect,Quest.bosses[Quest.challenge]["pronoun"]))
                    else:
                        await ctx.send((Quest.quest[Quest.idx][4]).format(Quest.challenge,Quest.effect,Quest.monsters[Quest.challenge]["pronoun"]))
                elif Quest.idx < (len(Quest.quest)-1):
                    await ctx.send((Quest.quest[Quest.idx][4]).format(Quest.challenge,Quest.effect,Quest.monsters[Quest.challenge]["pronoun"]))
                else:
                    await ctx.send((Quest.quest[Quest.idx][4]).format(Quest.challenge,Quest.effect,Quest.bosses[Quest.challenge]["pronoun"]))
                await asyncio.sleep(1.5)
                if Quest.effect == "Sleep":
                    all = Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]
                    sleepyhead = random.choice(all)
                    if sleepyhead in Quest.userslist["fight"]:
                        Quest.userslist["fight"].remove(sleepyhead)
                    elif sleepyhead in Quest.userslist["talk"]:
                        Quest.userslist["talk"].remove(sleepyhead)
                    else:
                        Quest.userslist["pray"].remove(sleepyhead)
                    fumblelist.append(sleepyhead)
                    await ctx.send("**" + sleepyhead + "**" + " fell asleep.")
                elif Quest.effects[Quest.effect][0] == "dmg":
                    for ID in Quest.partyIDs:
                        roll = random.randint(1,20) #50% chance to get hit.
                        if roll <= 10:
                            member = discord.utils.find(lambda m: m.id == ID, ctx.guild.members)
                            Quest.affected.append(member.display_name)
                    if len(Quest.affected) > 0:
                        s_damage = random.randint(Quest.effects[Quest.effect][1],Quest.effects[Quest.effect][2])
                        affected = " and ".join([", ".join(Quest.affected[:-1]),Quest.affected[-1]] if len(Quest.affected) > 2 else Quest.affected)
                        await Quest.damage(ctx,Quest.affected,s_damage*20)
                    else:
                        await ctx.send("Everyone dodged.")
                else:
                    fails = []
                    if Quest.endless:
                        if Quest.depth % 5 == 0:
                            saving_throw = round(Quest.bosses[Quest.challenge][Quest.effects[Quest.effect][0]]*0.2 + Quest.depth*2)
                        else:
                            if Quest.depth < 3:
                                saving_throw = round(Quest.monsters[Quest.challenge][Quest.effects[Quest.effect][0]]*0.8 + Quest.depth*2)
                            elif Quest.depth < 5:
                                saving_throw = round(Quest.monsters[Quest.challenge][Quest.effects[Quest.effect][0]]*0.4 + Quest.depth*2)
                    elif Quest.idx < (len(Quest.quest)-1):
                        if Quest.idx < 3:
                            saving_throw = round(Quest.monsters[Quest.challenge][Quest.effects[Quest.effect][0]]*0.8 + Quest.idx*2)
                        elif Quest.idx < 5:
                            saving_throw = round(Quest.monsters[Quest.challenge][Quest.effects[Quest.effect][0]]*0.4 + Quest.idx*2)
                    else:
                        saving_throw = round(Quest.bosses[Quest.challenge][Quest.effects[Quest.effect][0]]*0.2 + Quest.idx*2)
                    saving_stat = Quest.effects[Quest.effect][0]
                    stat_txt = ""
                    for ID in Quest.partyIDs:
                        roll = random.randint(1,20)
                        att_value = Userdata.users[str(ID)]['att'] + Userdata.users[str(ID)]['skill']['att'] + roll
                        dipl_value = Userdata.users[str(ID)]['cha'] + Userdata.users[str(ID)]['skill']['cha'] + roll
                        member = discord.utils.find(lambda m: m.id == ID, ctx.guild.members)
                        if saving_stat == "str":
                            stat_txt = "ATT"
                            if att_value < saving_throw:
                                Quest.affected.append(member.display_name)
                        elif saving_stat == "dipl":
                            stat_txt = "DIPL"
                            if dipl_value < saving_throw:
                                Quest.affected.append(member.display_name)
                    if len(Quest.affected) > 0:
                        affected = " and ".join([", ".join(Quest.affected[:-1]),Quest.affected[-1]] if len(Quest.affected) > 2 else Quest.affected)
                        await ctx.send("**" + affected + "**" + " missed the {} saving throw of {}.".format(stat_txt,saving_throw))
                    else:
                        await ctx.send("Everyone resisted the effect.")
                    people = len(Quest.userslist["fight"])+len(Quest.userslist["talk"])+len(Quest.userslist["pray"])

        async def handle_run(attack, diplomacy):
            if len(list(Quest.userslist["run"])) != 0:
                for user in Quest.userslist["run"]:
                    member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                    if member == None:
                        await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (Namechange during quest)")
                        Quest.partyIDs.remove(member.id)
                    Quest.partyIDs.remove(member.id) #user left party and can no longer participate with reactions
                runners = " and ".join([", ".join(Quest.userslist["run"][:-1]),Quest.userslist["run"][-1]] if len(Quest.userslist["run"]) > 2 else Quest.userslist["run"])
                await ctx.send("**" + runners + "**" + " left the party, keeping rewards earned so far.")
            return (attack,diplomacy)

        async def handle_fight(fumblelist, critlist, attack):
            if len(Quest.userslist["fight"]) == 0:
                return (fumblelist, critlist, attack)
            report = "Attack Party: |"
            for user in Quest.userslist["fight"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (Namechange during quest)")
                    return (fumblelist, critlist, attack)
                att_effect = 1
                effect = ""
                if user in Quest.affected and Quest.effect != "Fumble" and Quest.effects[Quest.effect][0] != "dmg":
                    att_effect = Quest.effects[Quest.effect][1]
                    effect = " *" + Quest.effect + "*"
                att_value = round((Userdata.users[str(member.id)]['att'] + Userdata.users[str(member.id)]['skill']['att'] + Userdata.users[str(member.id)]['buffs'].get('att', {'bonus':0})['bonus'])*att_effect)
                monster_string = ""
                bow_bonus = ""
                monster_value = 0
                if "monster" in Userdata.users[str(member.id)]['buffs']:
                    monster_value = Userdata.users[str(member.id)]['buffs'].get('monster', {'bonus':{'att':0}})['bonus']['att']
                    monster_string = " + 🦖{}".format(monster_value)
                if roll == 1:
                    await ctx.send("**" + user + "**" + " fumbled the attack.")
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                        attack += -roll - bonus - att_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({}) -".format(roll) + "💥{} + ".format(bonus) + "- 🗡" + str(att_value) + monster_string + " |"
                elif user in Quest.affected and Quest.effect == "Fumble" and 1 < roll <= 5:
                    await ctx.send("**" + user + "**" + " has been fumbled.")
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                        attack += -roll - bonus - att_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({}) -".format(roll) + " 💥{} - ".format(bonus) + "🗡" + str(att_value) + effect + monster_string + " |"
                elif roll == 20 or (Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']):
                    ability = ""
                    bonus = 0
                    if roll == 20:
                        await ctx.send("**" + user + "**" + " landed a critical hit.")
                        critlist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and Userdata.users[str(member.id)]['class']['ability']:
                        ability = "🗯️"
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                    elif Userdata.users[str(member.id)]['class']['name']=="Ranger" and any("bow" in k for k in Userdata.users[str(member.id)]['items']['right'].keys()):
                        ability = "🏹"
                        bonus = random.randint(max(5,int(Userdata.users[str(member.id)]['lvl']/2)),max(15,int(Userdata.users[str(member.id)]['lvl'])))
                    else:
                        bonus = random.randint(5,15)
                    attack += roll + bonus + att_value + monster_value
                    bonus_str = str(bonus)+ ability
                    if Userdata.users[str(member.id)]['class']['name']=="Berserker" and len(Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["slot"]) == 2 and "bow" not in list(Userdata.users[str(member.id)]['items']['right'].keys())[0]:
                        barb_bonus = Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["att"]*2
                        attack += barb_bonus
                        barb_bonus_str = " + {}🀄 ".format(barb_bonus)
                        bonus_str += barb_bonus_str
                    report += "**" + user + "**: " +  "🎲({}) +".format(roll) + " {} + ".format(bonus_str) + "🗡" + str(att_value) + effect + monster_string + " |"
                else:
                    bonus = 0
                    if Userdata.users[str(member.id)]['class']['name']=="Ranger" and any("bow" in k for k in Userdata.users[str(member.id)]['items']['right'].keys()):
                        bonus = int(Userdata.users[str(member.id)]['lvl']/10)*2
                        bow_bonus = " {}🏹 + ".format(bonus)
                    elif Userdata.users[str(member.id)]['class']['name']=="Berserker" and len(Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["slot"]) == 2 and "bow" not in list(Userdata.users[str(member.id)]['items']['right'].keys())[0]:
                        bonus = Userdata.users[str(member.id)]['items']['right'][list(Userdata.users[str(member.id)]['items']['right'].keys())[0]]["att"]*2
                        bow_bonus = " {}🀄 + ".format(bonus)
                    attack += roll + bonus + att_value + monster_value
                    report += "**" + user + "**: " +  "🎲({}) +".format(roll) + bow_bonus + "🗡" + str(att_value) + monster_string + " |"
            for user in fumblelist:
                if user in Quest.userslist["fight"]:
                    Quest.userslist["fight"].remove(user)
                    fumble = random.randint(1,100)
                    if fumble <= 5:
                        await Quest.handle_breakup(member)
            if len(Quest.userslist["fight"]) > 0:
                await ctx.send(report)
            return (fumblelist, critlist, attack)

        async def handle_pray(fumblelist, attack, diplomacy):
            for user in Quest.userslist["pray"]:
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (Namechange during quest)")
                    return (fumblelist, critlist, attack)
                if Userdata.users[str(member.id)]['class']['name']=="Cleric" and Userdata.users[str(member.id)]['class']['ability']:
                    roll = random.randint(1,20)
                    if len(Quest.userslist["fight"]+Quest.userslist["talk"]) == 0:
                        await ctx.send("**" + user + "**" + " blessed like a madman but nobody was there to receive it.")
                        return (fumblelist, attack, diplomacy)
                    if roll == 1:
                        attack -= 5 * len(Quest.userslist["fight"])
                        diplomacy -= 5 * len(Quest.userslist["talk"])
                        Quest.dmgred = 1
                        fumblelist.append(user)
                        await ctx.send("**" + user + "**" + "'s sermon offended the mighty Herbert. (🎲({}) -{}🗡/-{}🗨)".format(roll, 5 * len(Quest.userslist["fight"]),5 * len(Quest.userslist["talk"])))
                    elif roll > 1 and roll <= 10:
                        attack += 2 * len(Quest.userslist["fight"])
                        diplomacy += 2 * len(Quest.userslist["talk"])
                        Quest.dmgred = 2
                        await ctx.send("**" + user + "**" + "'s blessed you all in Herberts name. (🎲({}) +{}🗡/+{}🗨)".format(roll, 2 * len(Quest.userslist["fight"]),2 * len(Quest.userslist["talk"])))
                    elif roll > 10 and roll <= 19:
                        attack += 5 * len(Quest.userslist["fight"])
                        diplomacy += 5 * len(Quest.userslist["talk"])
                        Quest.dmgred = 4
                        await ctx.send("**" + user + "**" + "'s blessed you all in Herberts name. (🎲({}) +{}🗡/+{}🗨)".format(roll, 5 * len(Quest.userslist["fight"]),5 * len(Quest.userslist["talk"])))
                    else:
                        attack += 20 * len(Quest.userslist["fight"])
                        diplomacy += 20 * len(Quest.userslist["talk"])
                        Quest.dmgred = 100
                        await ctx.send("**" + user + "**" + " turned into an avatar of mighty Herbert. (🎲({}) +{}🗡/+{}🗨)".format(roll, 20 * len(Quest.userslist["fight"]),20 * len(Quest.userslist["talk"])))
                else:
                    roll = random.randint(1,4)
                    if len(Quest.userslist["fight"]+Quest.userslist["talk"]) == 0:
                        await ctx.send("**" + user + "**" + " prayed like a madman but nobody else helped him.")
                        return (fumblelist, attack, diplomacy)
                    if roll == 4:
                        attack += 10 * len(Quest.userslist["fight"])
                        diplomacy += 10 * len(Quest.userslist["talk"])
                        await ctx.send("**" + user + "**" + "'s prayer called upon the mighty Herbert to help you. (+{}🗡/+{}🗨)".format(10 * len(Quest.userslist["fight"]),10 * len(Quest.userslist["talk"])))
                    else:
                        fumblelist.append(user)
                        await ctx.send("**" + user + "**" + "'s prayers went unanswered.")
            for user in fumblelist:
                if user in Quest.userslist["pray"]:
                    Quest.userslist["pray"].remove(user)
            return (fumblelist, attack, diplomacy)

        async def handle_talk(fumblelist, critlist, diplomacy):
            if len(Quest.userslist["talk"]) == 0:
                return (fumblelist, critlist, diplomacy)
            report = "Talking Party: |"
            for user in Quest.userslist["talk"]:
                roll = random.randint(1,20)
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
                    await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird. (Namechange during quest)")
                    return (fumblelist, critlist, attack)
                dipl_effect = 1
                effect = ""
                if user in Quest.affected and Quest.effect != "Fumble" and Quest.effects[Quest.effect][0] != "dmg":
                    dipl_effect = Quest.effects[Quest.effect][2]
                    effect = " *" + Quest.effect + "*"
                dipl_value = round((Userdata.users[str(member.id)]['cha'] + Userdata.users[str(member.id)]['skill']['cha'] + Userdata.users[str(member.id)]['buffs'].get('cha', {'bonus':0})['bonus'])*dipl_effect)
                songbonus = 0
                if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                    songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                monster_string = ""
                monster_value = 0
                if "monster" in Userdata.users[str(member.id)]['buffs']:
                    monster_value = Userdata.users[str(member.id)]['buffs'].get('monster', {'bonus':{'cha':0}})['bonus']['cha']
                    monster_string = " + 🦖{}".format(monster_value)
                if roll == 1:
                    await ctx.send("**" + user + "**" + (" accidentally offended the {}.").format(Quest.challenge))
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(5,15)
                        if songbonus != 0: #recalc if song is sung
                            low = max(5,int(Userdata.users[str(member.id)]['lvl']/4))
                            bonus = random.randint(low, max(low, songbonus))
                        diplomacy += -roll - bonus - dipl_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({})-".format(roll) + " 💥{} - ".format(bonus) + "🗨" + str(dipl_value) + effect + monster_string + " |"
                elif user in Quest.affected and Quest.effect == "Fumble" and 1 < roll <= 5:
                    await ctx.send("**" + user + "**" + (" got fumbled by the {}.").format(Quest.challenge))
                    fumblelist.append(user)
                    if Userdata.users[str(member.id)]['class']['name']=="Bard" and Userdata.users[str(member.id)]['class']['ability']:
                        bonus = random.randint(5,15)
                        if songbonus != 0: #recalc if song is sung
                            low = max(5,int(Userdata.users[str(member.id)]['lvl']/4))
                            bonus = random.randint(low, max(low, songbonus))
                        diplomacy += -roll - bonus - dipl_value + monster_value
                        report += "**" + user + "**: " +  "- 🎲({})-".format(roll) + " 💥{} - ".format(bonus) + "🗨" + str(dipl_value) + effect + monster_string + " |"
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
                    diplomacy += roll + bonus + dipl_value + monster_value
                    bonus_str = ability + str(bonus+critbonus)
                    report += "**" + user + "**: " +  "🎲({})+".format(roll) + " {} + ".format(bonus_str) + "🗨" +str(dipl_value) + effect + monster_string + " |"
                else:
                    diplomacy += roll + dipl_value + monster_value
                    report += "**" + user + "**: " +  "🎲({})+".format(roll) + "🗨" + str(dipl_value) + effect + monster_string + " |"
            for user in fumblelist:
                if user in Quest.userslist["talk"]:
                    Quest.userslist["talk"].remove(user)
            if len(Quest.userslist["talk"]) > 0:
                await ctx.send(report)
            return (fumblelist, critlist, diplomacy)

        async def handle_basilisk(failed):
            if Quest.challenge == "Basilisk" or Quest.challenge == "Medusa":
                failed = True
                for user in Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]: #check if any fighter has an equipped mirror shield to give them a chance.
                    member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                    if member == None:
                        continue
                    if next(iter(Userdata.users[str(member.id)]['items']['left']))[0:14] == '.mirror_shield':
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

        attack,diplomacy = await handle_run(attack, diplomacy)
        if people == 0:
            await ctx.send("Everyone withdrew from the Quest.")
            Quest.participants = Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]+Quest.userslist["run"]+fumblelist
            Quest.running = False
            return

        await handle_effect()
        if people == 0:
            await ctx.send("Everyone was incapacitated.")
            Quest.participants = Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]+Quest.userslist["run"]+fumblelist
            Quest.running = False
            Quest.failed = True
            return

        fumblelist, attack, diplomacy = await handle_pray(fumblelist, attack, diplomacy)
        fumblelist, critlist, diplomacy= await handle_talk(fumblelist, critlist, diplomacy)
        Quest.failed = await handle_basilisk(Quest.failed)
        fumblelist, critlist, attack = await handle_fight(fumblelist, critlist, attack)

        slain = attack >= Quest.str
        persuaded = diplomacy >= Quest.dipl
        CR = Quest.str + Quest.dipl

        fighters = " and ".join([", ".join(Quest.userslist["fight"][:-1]),Quest.userslist["fight"][-1]] if len(Quest.userslist["fight"]) > 2 else Quest.userslist["fight"])
        talkers = " and ".join([", ".join(Quest.userslist["talk"][:-1]),Quest.userslist["talk"][-1]] if len(Quest.userslist["talk"]) > 2 else Quest.userslist["talk"])
        preachermen = " and ".join([", ".join(Quest.userslist["pray"][:-1]),Quest.userslist["pray"][-1]] if len(Quest.userslist["pray"]) > 2 else Quest.userslist["pray"])
        text = ""

        if slain or persuaded and not Quest.failed:
            treasure = [0,0,0,0]
            if CR >= 80 or Quest.challenge == "Basilisk" or Quest.challenge == "Medusa": #rewards 50:50 rare:normal chest for killing something like the basilisk
                treasure = random.choice([[0,1,0,0],[1,0,0,0]])
            elif CR >= 180: #rewards 50:50 epic:rare chest for killing hard stuff.
                treasure = random.choice([[0,0,1,0],[0,1,0,0]])
            if "Dragon" in Quest.challenge: #always rewards an epic chest.
                treasure[2] += 1
            if len(critlist) != 0:
                treasure[0] += len(critlist)
            checklist = Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]
            for user in checklist:
                member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
                if member == None:
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
                        await ctx.send("**{}** was lucky to dig up an extra chest for the party!".format(user))
                    elif roll >= 120:
                        await ctx.send("**{}** was lucky to dig up several extra chests for the party!".format(user))
            if treasure == [0,0,0,0]:
                treasure = False
        if (Quest.challenge == "Basilisk" or Quest.challenge == "Medusa") and Quest.failed:
            Quest.participants= Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]+Quest.userslist["run"]+fumblelist
            await ctx.send("The {}s gaze turned everyone to stone.".format(Quest.challenge))
            await Quest.damage(ctx,[item for item in Quest.participants if item not in Quest.userslist["run"]],CR*2)
            Quest.running = False
            Quest.failed = True
            return
        if (Quest.challenge == "Basilisk" or Quest.challenge == "Medusa") and not slain and not persuaded:
            Quest.participants= Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]+Quest.userslist["run"]+fumblelist
            await ctx.send("The mirror shield reflected the {}s gaze, but it still managed to kill you.".format(Quest.challenge))
            await Quest.damage(ctx,[item for item in Quest.participants if item not in Quest.userslist["run"]],CR*2)
            Quest.running = False
            Quest.failed = True
            return
        amount = ((Quest.str+Quest.dipl)*people)
        Quest.participants = Quest.userslist["fight"]+Quest.userslist["talk"]+Quest.userslist["pray"]+Quest.userslist["run"]+fumblelist
        if people == 1:
            if slain:
                text= ("**{}** has slain the {} in epic battle!").format(fighters,Quest.challenge)
                text += await Quest.reward(ctx, Quest.participants,amount,(attack/Quest.str),treasure)

            if  persuaded:
                text= ("**{}** almost died in battle,").format(talkers) + (" but confounded the {} in the last second.").format(Quest.challenge)
                text += await Quest.reward(ctx, Quest.participants,amount,(diplomacy/Quest.dipl),treasure)

            if not slain and not persuaded:
                options = ["No amount of diplomacy or valiant fighting could save you. You died.", "This challenge was too much for one hero.", "You tried your best, but couldn't succeed alone."]
                text= random.choice(options)
                Quest.running = False
                Quest.failed = True
        else:
            if slain and persuaded:
                if len(Quest.userslist["pray"]) > 0:
                    text= ("**{}** slayed the {} in battle,").format(fighters,Quest.challenge) + ("while **{}** distracted with flattery and **{}** aided in Herberts name.").format(talkers, preachermen)
                else:
                    text= ("**{}** slayed the {} in battle,").format(fighters,Quest.challenge) + ("while **{}** distracted with insults.").format(talkers)
                text += await Quest.reward(ctx, Quest.participants,amount,(attack/Quest.str+diplomacy/Quest.dipl),treasure)

            if  not slain and persuaded:
                if len(Quest.userslist["pray"]) > 0:
                    text= ("**{}** talked the {} down with **{}'s** blessing'.").format(talkers,Quest.challenge, preachermen)
                else:
                    text= ("**{}** talked the {} down.").format(talkers,Quest.challenge)
                text += await Quest.reward(ctx, Quest.participants,amount,(diplomacy/Quest.dipl),treasure)

            if slain and not persuaded:
                if len(Quest.userslist["pray"]) > 0:
                    text= ("**{}** killed the {} in a most heroic battle with a little help from **{}**.").format(fighters,Quest.challenge, preachermen)
                else:
                    text= ("**{}** killed the {} in an epic fight.").format(fighters,Quest.challenge)
                text += await Quest.reward(ctx, Quest.participants,amount,(attack/Quest.str),treasure)

            if not slain and not persuaded:
                options = ["No amount of diplomacy or valiant fighting could save you. Everyone died.", "This challenge was too much for this group.", "You tried your best, but succumbed to overwhelming forces in the end."]
                text= random.choice(options)
                Quest.running = False
                Quest.failed = True

        await ctx.send(text)
        if not slain and not persuaded:
            await Quest.damage(ctx,[item for item in Quest.participants if item not in Quest.userslist["run"]],CR)

        for user in Quest.participants: #reset activated abilities
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member == None:
                continue
            if 'name' in Userdata.users[str(member.id)]['class']:
                if Userdata.users[str(member.id)]['class']['name'] != "Ranger" and Userdata.users[str(member.id)]['class']['ability']:
                    Userdata.users[str(member.id)]['class']['ability'] = False
                songbonus = Userdata.users[str(member.id)]['class'].get("basebonus", 0)
                if Userdata.users[str(member.id)]['class']['name'] == "Bard" and songbonus != 0:
                    Userdata.users[str(member.id)]['class'].pop('basebonus')
            expired = []
            for buff in Userdata.users[str(member.id)]['buffs'].keys(): #reduce duration of active buffs
                if buff != "rest":
                    if Userdata.users[str(member.id)]['buffs'][buff]['duration'] <= 1:
                        expired.append(buff)
                    else:
                        Userdata.users[str(member.id)]['buffs'][buff]['duration'] = Userdata.users[str(member.id)]['buffs'][buff]['duration'] - 1
            for buff in expired: #remove buffs outside loop not to change size during iteration
                Userdata.users[str(member.id)]['buffs'].pop(buff)
        Quest.timeout = 0
        if Quest.idx >= (len(Quest.quest)-1) and not Quest.endless:
            Quest.running = False
        await asyncio.sleep(1)

    async def reward(ctx, list, xamount, modif, special):
        if Quest.endless:
            depthbonus = float("1.3" + str(Quest.depth))
        else:
            depthbonus = float("1.3" + str(Quest.idx))
        xamount = xamount * depthbonus
        xp = max(1,round(xamount))
        Quest.sumxp += xp
        cp = max(1,round(xamount * modif))
        Quest.sumcp += cp
        phrase = ""
        if Quest.endless and (Quest.depth % 5 == 0):
            phrase += "You defeated the champion and were rewarded a quest chest for your victory!"
            special[3] += 1
        elif not Quest.endless and Quest.idx >= (len(Quest.quest)-1):
            phrase += "You defeated the questboss and earned a quest chest for your troubles!"
            special[3] += 1
        for user in list:
            if user not in Quest.rewards:
                Quest.rewards[user] = {"xp":0,"cp":0,"special":[0,0,0,0]}
            bxp = 0
            bcp = 0
            member = discord.utils.find(lambda m: m.display_name == user, ctx.guild.members)
            if member == None:
                await ctx.send("**" + user + "**" + " wandered off to look at a particular interesting bird before getting rewards. (Namechange during quest)")
                continue
            if "xp" in Userdata.users[str(member.id)]['buffs'].keys():
                bxp = int(xp * (Userdata.users[str(member.id)]['buffs']['xp']['bonus']/100))
                phrase += "\n**{}** received **+{}** bonus xp.".format(member.display_name, bxp)
            if "money" in Userdata.users[str(member.id)]['buffs'].keys():
                bcp = int(cp * (Userdata.users[str(member.id)]['buffs']['money']['bonus']/100))
                phrase += "\n**{}** received **+{}** bonus cp.".format(member.display_name, bcp)
            roll = random.randint(1,5)
            if roll == 5 and Userdata.users[str(member.id)]['class']['name']=="Ranger" and not isinstance(Userdata.users[str(member.id)]['class']['ability'], bool):
                Quest.rewards[user]["xp"] += int((xp+bxp) * Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'])
                Quest.rewards[user]["cp"] += int((cp+bxp) * Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'])
                percent = round((Userdata.users[str(member.id)]['class']['ability']['pet']['bonus'] - 1.0) * 100)
                phrase += "\n**{}** received a **{}%** reward bonus ({}).".format(member.display_name, percent, Userdata.users[str(member.id)]['class']['ability']['pet']['name'])
            else:
                Quest.rewards[user]["xp"] += xp + bxp
                Quest.rewards[user]["cp"] += cp + bcp
            if special != False:
                    Quest.rewards[user]["special"] = [sum(x) for x in zip(Quest.rewards[user]["special"], special)]
        if special != False:
            Quest.sumtreasure = [sum(x) for x in zip(Quest.sumtreasure, special)]
        if Quest.sumtreasure != [0,0,0,0] and sum(Quest.sumtreasure) == 1:
            types = [" normal"," rare","n epic", "quest"]
            ctype = types[Quest.sumtreasure.index(1)]
            phrase += "\nYou have {} xp and found {} copperpieces so far. You also secured **a{} treasure chest**!".format(Quest.sumxp,Quest.sumcp,ctype)
        elif Quest.sumtreasure != [0,0,0,0] and sum(Quest.sumtreasure) > 1:
            chesttext = []
            ctypes = ["{} normal","{} rare","{} epic", "{} quest"]
            for i,c in enumerate(Quest.sumtreasure):
                if c >= 1:
                    chesttext.append(ctypes[i].format(c))
            phrase += "\nBase rewards: {} xp and {} copperpieces. You also secured **{} treasure chests**!".format(xp,cp, " and ".join([", ".join(chesttext[:-1]),chesttext[-1]] if len(chesttext) > 2 else chesttext))
        else:
            phrase += "\nYou have {} xp and found {} copperpieces so far.".format(Quest.sumxp,Quest.sumcp)
        if len(Userdata.sleepers) != 0:
            slept = " and ".join([", ".join(Userdata.sleepers[:-1]),Userdata.sleepers[-1]] if len(Userdata.sleepers) > 2 else Userdata.sleepers)
            phrase += "\n**{}** slept through the whole encounter.".format(slept)
            for name in Userdata.sleepers:
                member = discord.utils.find(lambda m: m.display_name == name, ctx.guild.members)
                phrase += " " + member.mention
            Userdata.sleepers.clear()
        return phrase

    async def damage(ctx,injured,CR):
        if "Dragon" in Quest.challenge or Quest.challenge in Quest.bosses.keys():
            org_dmg = max(1,round(CR/10))
        else:
            org_dmg = max(1,round(CR/20))
        base_dmg = round(org_dmg/Quest.dmgred)
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
                Quest.dead.append(user)
                Quest.partyIDs.remove(member.id) #user is dead and can no longer participate with reactions
                if user in Quest.rewards:
                    Quest.rewards.pop(user)
        await Userdata.save()
        incapacitated = " and ".join([", ".join(incap[:-1]),incap[-1]] if len(incap) > 2 else incap)
        inj_txt = " and ".join([", ".join(injured[:-1]),injured[-1]] if len(injured) > 2 else injured)
        preachermen = " and ".join([", ".join(Quest.userslist["pray"][:-1]),Quest.userslist["pray"][-1]] if len(Quest.userslist["pray"]) > 2 else Quest.userslist["pray"])
        if base_dmg == 0:
            d_txt += "**{}** mitigated all damage. ".format(preachermen)
        elif dmg_red > 0:
            d_txt += "**{}** reduced damage taken by {}. \n**{}** took {} damage. ".format(preachermen,dmg_red,inj_txt,base_dmg)
        else:
            d_txt += "**{}** took {} damage. ".format(inj_txt,base_dmg)
        if len(incap) > 0:
            d_txt += "**{}** died and will not receive any rewards from this quest.".format(incapacitated)
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
                    secondint = int(Quest.timeout)
                    Quest.finish = await getEpoch()
                    if secondint < 0:
                        await ctx.send("I dont think im allowed to do negatives \U0001f914")
                        return
                    rem, done = await remaining(Quest.finish, True)
                    message = await ctx.send(title + " " + str(rem))
                    while True:
                        timer, done = await remaining(Quest.finish, True)
                        if done:
                            Quest.timeout = 0
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
                Quest.timeout = remaining
            if h == 0 and m == 0:
                out = "{:02d}".format(s)
            elif h == 0:
                out = "{:02d}:{:02d}".format(m, s)
            else:
                out = "{:01d}:{:02d}:{:02d}".format(h, m, s)
            return out, finish

        async def getEpoch():
            #epoch = time.time()
            epoch = Quest.started
            epoch += Quest.timeout
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



    DEFAULT_CONTROLS = {"🗡": fight, "🗨": talk, "🛐": pray, "❌": close_menu}
