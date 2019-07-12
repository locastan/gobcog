import random
import asyncio
import discord
import contextlib
from typing import Union, Iterable, Optional
from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate
from .treasure import Treasure
from .custompredicate import CustomPredicate
from .userdata import Userdata

_ReactableEmoji = Union[str, discord.Emoji]

class Explore:

    #This class provides a simple emoji based 2D game engine for discord.

    tiles = {"Ooze":{"tile": " 🦠 ", "desc":"Some kind of goo. It seems forever changing in color and shapes."},
            "Moneypenny":{"tile": "🌸", "desc":"A delicate pink flower, supposed to bring good fortune."},
            "Raging Frills":{"tile": "💮", "desc":"A white flower with red rimmed petals, likened to resemble the blooshot eyes of raging warriors."},
            "Cyanka Lilly":{"tile": "🏵", "desc":"A poisonous blue flowered weed. Experimental ingredient used in small doses."},
            "Rose":{"tile": "🌹", "desc":"A beautiful red rose. Charms the senses and lightens the mood."},
            "Mourning Star":{"tile": "🥀", "desc":"A peculiar flower as it always appears to be wilting."},
            "Sageworth":{"tile": "🌺", "desc":"Said to improve the powers of the mind and promote clear thinking."},
            "Oilflower":{"tile": "🌻", "desc":"Generally used for its emulsifying oils."},
            "Daisy":{"tile": "🌼", "desc":"Common ingredient in various stews and potions."},
            "Twolip":{"tile": "🌷", "desc":"Said to improve speech and performance activities."},
            "Tongue Sprout":{"tile": "🌱", "desc":"Creates a beautiful singing voice if prepared properly."},
            "Conifer":{"tile": "🌲", "desc":"A big evergreen tree."},
            "Oak":{"tile": "🌳", "desc":"A huge oak."},
            "Na-Palm":{"tile": "🌴", "desc":"This weird tree is known to spontaneously combust. Better stay away from it."},
            "Fleshthorn":{"tile": "🌵", "desc":"The resin is supposed to harden skin, although it could also be from the callouses induced when being covered in spikes."},
            "Honeytail":{"tile": "🌾", "desc":"A sweet grass with marvelous taste."},
            "Whipweed":{"tile": "🌿", "desc":"Lashing, long, whiplike shrubbery. Useful bark."},
            "Clover":{"tile": "🍀", "desc":"A four leaf clover."},
            "Maple":{"tile": "🍁", "desc":"Maple leafs."},
            "Rust Leafs":{"tile": "🍂", "desc":"Even fresh, these leafs have the color of dried old ones."},
            "Flyleaf":{"tile": "🍃", "desc":"Very light and aromatic leafs. Good booster to alchemy."},
            "Mushroom":{"tile": "🍄", "desc":"Redcap mushrooms have powerful potency."},
            "Chestnut":{"tile": "🌰", "desc":"Some chestnuts. Good for eating and brewing."},
            "Fog":{"tile": "⬜", "desc":"Step in to find out."},
            "Rock":{"tile": "🌑", "desc":"A big rock. You cannot move here."},
            #"Grass":{"tile": "<:Grassland:593422372468686859>", "desc":"Just grassland."}, #use this for beta server
            "Grass":{"tile": "<:Grassland:593755278328201226>", "desc":"Just grassland."}, #use this for Goblinscomic Discord
            "Player":{"tile": "🗿", "desc":"Player"}
            }

    tile_lookup = {" 🦠 ":"Ooze",
            "🌸":"Moneypenny",
            "💮":"Raging Frills",
            "🏵": "Cyanka Lilly",
            "🌹": "Rose",
            "🥀": "Mourning Star",
            "🌺": "Sageworth",
            "🌻": "Oilflower",
            "🌼": "Daisy",
            "🌷": "Twolip",
            "🌱": "Tongue Sprout",
            "🌲": "Conifer",
            "🌳": "Oak",
            "🌴": "Na-Palm",
            "🌵": "Fleshthorn",
            "🌾": "Honeytail",
            "🌿": "Whipweed",
            "🍀": "Clover",
            "🍁": "Maple",
            "🍂": "Rust Leafs",
            "🍃": "Flyleaf",
            "🍄": "Mushroom",
            "🌰": "Chestnut",
            "⬜": "Fog",
            "🌑": "Rock",
            #"<:Grassland:593422372468686859>": "Grass", #use this on testserver
            "<:Grassland:593755278328201226>": "Grass", #use this on Goblins Discord server
            "🗿": "Player"
            }

    #biomes carry rarities and what can be found in the tileset.
    biomes = {"forest": {"legendary":["Ooze","Sageworth","Whipweed","Conifer","Cyanka Lilly","Flyleaf"],"epic":["Mushroom","Whipweed","Maple","Oak"],"rare":["Rock"],"common":["Oak","Oak","Grass"]},
            "grassland": {"legendary":["Twolip","Moneypenny","Raging Frills","Rose","Oak"],"epic":["Mourning Star","Honeytail","Clover","Rock"],"rare":["Oilflower"],"common":["Daisy","Grass","Grass"]},
            "drygrass":{"legendary":["Na-Palm","Fleshthorn","Rock"],"epic":["Tongue Sprout","Rock"],"rare":["Rust Leafs"],"common":["Rock","Grass","Grass"]}
            }

    mapsize = [13,13]
    timeout = 300
    player_pos = [6,6]
    lodrange = 2 #rendersize; max 6 as a 13x13 visible tilegrid is the max number of big emojis discord can put in one message.
    statusmsg = None
    mapmsg = None
    intro = None
    loot = {}
    moves = 0
    movesmsg = None

    async def explore(ctx,user):
        Explore.intro = await ctx.send("{} is exploring:".format(user.display_name))
        Explore.statusmsg = None
        Explore.loot = {}
        Explore.mapmsg = None
        Explore.player_pos = [6,6]
        Explore.moves = 10 + int(Userdata.users[str(user.id)]['lvl']/2)
        Explore.movesmsg = await ctx.send("{} moves remaining.".format(Explore.moves))
        Explore.map, Explore.fowmap = await Explore.generate(random.choice(list(Explore.biomes.keys())),Explore.mapsize)
        await Explore.update_fow()
        output = await Explore.mapdrawer(list(Explore.fowmap)) #passing just a copy of the original tile list so original does not get changed.
        Explore.mapmsg = await ctx.send(output)
        await Explore.menu(ctx, ["Move with these controls:"], {"\U00002B05": Explore.left, "\U00002B06" : Explore.up, "\U00002B07" : Explore.down, "\U000027A1" : Explore.right, "\U00002139": Explore.inspect, "\U0001F44A" : Explore.pick, "\U000023CF": Explore.exit}, Explore.statusmsg)
        return Explore.loot

    async def mapdrawer(map):
        # calculating render ranges
        if Explore.player_pos[0]-Explore.lodrange <= 0:
            compensator = abs(Explore.player_pos[0]-Explore.lodrange)
            visible_x = range(0,Explore.player_pos[0]+Explore.lodrange+1+compensator)
        elif Explore.player_pos[0]+Explore.lodrange+1 >= Explore.mapsize[0]:
            compensator = (Explore.player_pos[0]+Explore.lodrange+1)-Explore.mapsize[0]
            visible_x = range(Explore.player_pos[0]-Explore.lodrange-compensator,Explore.mapsize[0])
        else:
            visible_x = range(Explore.player_pos[0]-Explore.lodrange,Explore.player_pos[0]+Explore.lodrange+1)
        if Explore.player_pos[1]-Explore.lodrange <= 0:
            compensator = abs(Explore.player_pos[1]-Explore.lodrange)
            visible_y = range(0,Explore.player_pos[1]+Explore.lodrange+1+compensator)
        elif Explore.player_pos[1]+Explore.lodrange+1 >= Explore.mapsize[1]:
            compensator = (Explore.player_pos[1]+Explore.lodrange+1)-Explore.mapsize[1]
            visible_y = range(Explore.player_pos[1]-Explore.lodrange-compensator,Explore.mapsize[1])
        else:
            visible_y = range(Explore.player_pos[1]-Explore.lodrange,Explore.player_pos[1]+Explore.lodrange+1)
        '''  Use this for calculating viewrange for FoW removal
        if Explore.player_pos[0]-Explore.lodrange <= 0:
            visible_x = range(0,Explore.player_pos[0]+Explore.lodrange+1)
        elif Explore.player_pos[0]+Explore.lodrange+1 >= Explore.mapsize[0]:
            visible_x = range(Explore.player_pos[0]-Explore.lodrange,Explore.mapsize[0])
        else:
            visible_x = range(Explore.player_pos[0]-Explore.lodrange,Explore.player_pos[0]+Explore.lodrange+1)
        print(visible_x)
        if Explore.player_pos[1]-Explore.lodrange <= 0:
            visible_y = range(0,Explore.player_pos[1]+Explore.lodrange+1)
        elif Explore.player_pos[1]+Explore.lodrange+1 >= Explore.mapsize[1]:
            visible_y = range(Explore.player_pos[1]-Explore.lodrange,Explore.mapsize[1])
        else:
            visible_y = range(Explore.player_pos[1]-Explore.lodrange,Explore.player_pos[1]+Explore.lodrange+1)
        print(visible_y)
        '''
        text = ""
        for r in visible_x:
            for t in visible_y:
                if r == Explore.player_pos[0] and t == Explore.player_pos[1]:
                    text += Explore.tiles["Player"]["tile"] + " "
                else:
                    text += map[r][t] + " "
            text += "\n"
        return text

    async def generate(biome,size):
        map = [[0] * size[0] for i in range(size[1])]
        fowmap = [[Explore.tiles["Fog"]["tile"]] * size[0] for i in range(size[1])]
        for r in range(len(map)):
            for t in range(len(map[r])):
                roll = random.randint(1,100)
                if roll <= 1:
                    map[r][t] = Explore.tiles[random.choice(Explore.biomes[biome].get("legendary"))]["tile"]
                elif roll <= 5:
                    map[r][t] = Explore.tiles[random.choice(Explore.biomes[biome].get("epic"))]["tile"]
                elif roll <= 15:
                    map[r][t] = Explore.tiles[random.choice(Explore.biomes[biome].get("rare"))]["tile"]
                elif roll <= 100:
                    map[r][t] = Explore.tiles[random.choice(Explore.biomes[biome].get("common"))]["tile"]
        return map, fowmap

    async def update_fow(): #this unveils the Fog of war in directly adjacient tiles.
        adjacient = [(0,-1),(1,0),(-1,0),(0,1)]
        for x in adjacient:
            pos_x = Explore.player_pos[0]+x[0]
            pos_y = Explore.player_pos[1]+x[1]
            if 0 <= pos_x < Explore.mapsize[0] and 0 <= pos_y < Explore.mapsize[1]:
                Explore.fowmap[pos_x][pos_y] = Explore.map[pos_x][pos_y]
            else:
                continue


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

        if not Explore.statusmsg:
            if isinstance(current_page, discord.Embed):
                Explore.statusmsg = await ctx.send(embed=current_page)
            else:
                Explore.statusmsg = await ctx.send(current_page)
            # Don't wait for reactions to be added (GH-1797)
            # noinspection PyAsyncCall
            Explore.start_adding_reactions(Explore.statusmsg, controls.keys(), ctx.bot.loop)
        else:
            if isinstance(current_page, discord.Embed):
                await Explore.statusmsg.edit(embed=current_page)
            else:
                await Explore.statusmsg.edit(content=current_page)

        try:
            done, pending = await asyncio.wait([ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), Explore.statusmsg, [ctx.author.id]),
                timeout=Explore.timeout
            ),
            ctx.bot.wait_for(
                "reaction_remove",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), Explore.statusmsg, [ctx.author.id]),
                timeout=Explore.timeout
            )], return_when=asyncio.FIRST_COMPLETED, timeout=Explore.timeout)
            for task in done:
                react, user = task.result()
        except asyncio.TimeoutError:  #the timeout only applies if no reactions are made!
            try:
                await Explore.statusmsg.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in controls.keys():
                    await Explore.statusmsg.remove_reaction(key, ctx.bot.user)
            pages = ["but nobody did anything. You failed."]
            await Explore.statusmsg.edit(content=pages[0])
            for future in pending:
                future.cancel()
            return
        for future in pending:
            future.cancel()
        await controls[react.emoji](ctx, pages, controls, Explore.statusmsg, page, Explore.timeout, react.emoji, user)

    async def left(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        if int(Explore.player_pos[1]) - 1 >= 0 and Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]][Explore.player_pos[1]-1]) != "Rock":
            Explore.player_pos[1] = int(Explore.player_pos[1]) - 1
            await Explore.update_fow()
            Explore.moves -= 1
            await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
            output = await Explore.mapdrawer(list(Explore.fowmap))
            await Explore.mapmsg.edit(content=output)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)
        else:
            text = "** You cannot move there. **"
            await Explore.statusmsg.edit(content=text)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)


    async def up(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        if int(Explore.player_pos[0]) - 1 >= 0 and Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]-1][Explore.player_pos[1]]) != "Rock":
            Explore.player_pos[0] = int(Explore.player_pos[0]) - 1
            await Explore.update_fow()
            Explore.moves -= 1
            await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
            output = await Explore.mapdrawer(list(Explore.fowmap))
            await Explore.mapmsg.edit(content=output)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)
        else:
            text = "** You cannot move there. **"
            await Explore.statusmsg.edit(content=text)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)

    async def down(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        if int(Explore.player_pos[0]) + 1 < Explore.mapsize[0] and Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]+1][Explore.player_pos[1]]) != "Rock":
            Explore.player_pos[0] = int(Explore.player_pos[0]) + 1
            await Explore.update_fow()
            Explore.moves -= 1
            await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
            output = await Explore.mapdrawer(list(Explore.fowmap))
            await Explore.mapmsg.edit(content=output)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)
        else:
            text = "** You cannot move there. **"
            await Explore.statusmsg.edit(content=text)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)

    async def right(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        if int(Explore.player_pos[1]) + 1 < Explore.mapsize[1] and Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]][Explore.player_pos[1]+1]) != "Rock":
            Explore.player_pos[1] = int(Explore.player_pos[1]) + 1
            await Explore.update_fow()
            Explore.moves -= 1
            await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
            output = await Explore.mapdrawer(list(Explore.fowmap))
            await Explore.mapmsg.edit(content=output)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)
        else:
            text = "** You cannot move there. **"
            await Explore.statusmsg.edit(content=text)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)

    async def inspect(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        tilename = Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]][Explore.player_pos[1]])
        text = "**" + tilename + ": " + Explore.tiles[tilename].get("desc") + "**"
        Explore.moves -= 1
        await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
        await Explore.statusmsg.edit(content=text)
        await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)

    async def pick(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        unpickable = ["Fog","Rock","Oak","Conifer","Grass"]
        tilename = Explore.tile_lookup.get(Explore.map[Explore.player_pos[0]][Explore.player_pos[1]])
        if tilename not in unpickable:
            text = "** You picked up: " + tilename + "**"
            Explore.moves -= 1
            await Explore.movesmsg.edit(content="{} moves remaining.".format(Explore.moves))
            await Explore.statusmsg.edit(content=text)
            Explore.loot.update({tilename:(Explore.loot.get(tilename,0)+1)})
            Explore.map[Explore.player_pos[0]][Explore.player_pos[1]] = Explore.tiles["Grass"]["tile"]
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)
        else:
            text = "** This cannot be picked. " + tilename + "**"
            await Explore.statusmsg.edit(content=text)
            await Explore.check(ctx, pages, controls, message, page, Explore.timeout, emoji, user)

    async def check(ctx, pages, controls, message, page, timeout, emoji, user):
        if Explore.moves <= 0:
            return await Explore.result(ctx, pages, controls, message, page, Explore.timeout, user)
        try:
            done, pending = await asyncio.wait([ctx.bot.wait_for(
                "reaction_add",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message, [user.id]),
                timeout=Explore.timeout
            ),
            ctx.bot.wait_for(
                "reaction_remove",
                check=CustomPredicate.with_emojis(tuple(controls.keys()), message, [user.id]),
                timeout=Explore.timeout
            )], return_when=asyncio.FIRST_COMPLETED, timeout=Explore.timeout)
            for task in done:
                react, user = task.result()
        except asyncio.TimeoutError:
            for future in pending:
                future.cancel()
            return await Explore.result(ctx, pages, controls, message, page, Explore.timeout, user)
        for future in pending:
            future.cancel()
        return await controls[react.emoji](ctx, pages, controls, message, page, Explore.timeout, react.emoji, user)


    async def exit(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        emoji: str,
        user: discord.User,
    ):
        if Explore.mapmsg:
            await Explore.mapmsg.delete()
        if Explore.statusmsg:
            await Explore.statusmsg.delete()
        if Explore.movesmsg:
            await Explore.movesmsg.delete()
        if Explore.intro:
            text = "{} went exploring here and found:\n".format(user.display_name)
            for key in Explore.loot.keys():
                text += "{}x {} \n".format(Explore.loot.get(key),key)
            await Explore.intro.edit(content=text)
        return None

    async def result(
        ctx: commands.Context,
        pages: list,
        controls: dict,
        message: discord.Message,
        page: int,
        timeout: float,
        user: discord.User,
    ):
        if Explore.mapmsg:
            await Explore.mapmsg.delete()
        if Explore.statusmsg:
            await Explore.statusmsg.delete()
        if Explore.movesmsg:
            await Explore.movesmsg.delete()
        if Explore.intro:
            text = "{} went exploring here and found:\n".format(user.display_name)
            for key in Explore.loot.keys():
                text += "{}x {} \n".format(Explore.loot.get(key),key)
            await Explore.intro.edit(content=text)
        return None

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
