from redbot.core import commands
import asyncio
import discord
import random
import time
from typing import Union, Iterable, Optional
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions

class Treasure:

    finish = 0

    controls = {"✅": "equip", "❎": "backpack", "💰": "sell"}
    #attribs= {"old":{"att":{0},"cha":{-1}}} not sure if I want to use these or hardcode the prefixes...
    common = {"rusty sword":{"slot":["right"],"att":1,"cha":-1},
            "shiny sword":{"slot":["right"],"att":1,"cha":1},
            "wooden club":{"slot":["right"],"att":1,"cha":0},
            "hornpipe":{"slot":["right"],"att":0,"cha":3},
            "moldy old shield":{"slot":["left"],"att":1,"cha":-1},
            "longsword":{"slot":["right"],"att":2,"cha":0},
            "dagger":{"slot":["right"],"att":1,"cha":0},
            "quarterstaff":{"slot":["right","left"],"att":1,"cha":1},
            "greatsword":{"slot":["right","left"],"att":1,"cha":1},
            "wooden shield":{"slot":["left"],"att":1,"cha":0},
            "steel shield":{"slot":["left"],"att":2,"cha":0},
            "ringlet of strength":{"slot":["ring"],"att":1,"cha":0},
            "ringlet of charisma":{"slot":["ring"],"att":0,"cha":1},
            "amulet of strength":{"slot":["charm"],"att":1,"cha":0},
            "simple axe":{"slot":["right"],"att":2,"cha":0},
            "peg leg":{"slot":["left"],"att":2,"cha":-1},
            "tambourine":{"slot":["left"],"att":0,"cha":2},
            "twig bow":{"slot":["right"],"att":1,"cha":-1},
            "short bow":{"slot":["right","left"],"att":1,"cha":0}
            }
    rare = {".ceremonial_dagger":{"slot":["right"],"att":2,"cha":2},
            ".tower_shield":{"slot":["left"],"att":3,"cha":1},
            ".mirror_shield":{"slot":["left"],"att":2,"cha":3},
            ".bagpipes":{"slot":["right","left"],"att":1,"cha":2},
            ".warpike":{"slot":["right"],"att":3,"cha":0},
            ".panflute":{"slot":["right"],"att":0,"cha":3},
            ".ring_of_strength":{"slot":["ring"],"att":2,"cha":0},
            ".ring_of_charisma":{"slot":["ring"],"att":0,"cha":2},
            ".ring_of_ambivalence":{"slot":["ring"],"att":1,"cha":1},
            ".bruteforce_ring":{"slot":["ring"],"att":3,"cha":-2},
            ".bruteforce_crescent":{"slot":["charm"],"att":3,"cha":-2},
            ".silver_tongued_ring":{"slot":["ring"],"att":-1,"cha":3},
            ".silver_tongued_chain":{"slot":["charm"],"att":-1,"cha":3},
            ".greataxe":{"slot":["right","left"],"att":2,"cha":1},
            ".spiked_mace":{"slot":["right"],"att":3,"cha":-1},
            ".buckler":{"slot":["left"],"att":3,"cha":0},
            ".tuba":{"slot":["right","left"],"att":2,"cha":1},
            ".pistol_crossbow":{"slot":["right"],"att":2,"cha":1}
            }
    unique = {"[troll banhammer]":{"slot":["right","left"],"att":2,"cha":2},
            "[scythe of death]":{"slot":["right","left"],"att":3,"cha":-2},
            "[maul of efrin]":{"slot":["right"],"att":5,"cha":0},
            "[star of ishtar]":{"slot":["charm"],"att":1,"cha":5},
            "[booklet of jokes]":{"slot":["charm"],"att":0,"cha":5},
            "[chain of command]":{"slot":["charm"],"att":4,"cha":2},
            "[balance scales]":{"slot":["charm"],"att":3,"cha":3},
            "[great bulwark]":{"slot":["left"],"att":5,"cha":0},
            "[dragon ring]":{"slot":["ring"],"att":4,"cha":3},
            "[mandachord]":{"slot":["right", "left"],"att":1,"cha":4},
            "[repeater crossbow]":{"slot":["right","left"],"att":3,"cha":1}
            }

    async def open_chest(ctx, user, type):
        if hasattr(user, "display_name"):
            await ctx.send("{} is opening a treasure chest. What riches lay inside?".format(user.display_name))
        else:
            await ctx.send("{} is foraging for treasure. What will it find?".format(user[:1].upper() + user[1:]))
            await asyncio.sleep(2)
        roll = random.randint(1,100)
        if type == "pet":
            if roll <= 5:
                chance = Treasure.unique
            elif roll > 5 and roll <= 25:
                chance = Treasure.rare
            elif roll > 25 and roll <= 75:
                chance = Treasure.common
            else:
                await ctx.send("{} found nothing of value.".format(user[:1].upper() + user[1:]))
                return None
        if type == "normal":
            if roll <= 5:
                chance = Treasure.unique
            elif roll > 5 and roll <= 25:
                chance = Treasure.rare
            else:
                chance = Treasure.common
        if type == "rare":
            if roll <= 15:
                chance = Treasure.unique
            elif roll > 15 and roll <= 45:
                chance = Treasure.rare
            else:
                chance = Treasure.common
        if type == "epic":
            if roll <= 25:
                chance = Treasure.unique
            else:
                chance = Treasure.rare
        itemname = random.choice(list(chance.keys()))
        item = chance[itemname]
        if len(item["slot"]) == 2: # two handed weapons add their bonuses twice
            hand = "two handed"
            att = item["att"]*2
            cha = item["cha"]*2
        else:
            if item["slot"][0] == "right" or item["slot"][0] == "left":
                hand = item["slot"][0] + " handed"
            else:
                hand = item["slot"][0] + " slot"
            att = item["att"]
            cha = item["cha"]
        if hasattr(user, "display_name"):
            await ctx.send("{} found a {}. (Attack: {}, Charisma: {} [{}])".format(user.display_name,itemname,str(att),str(cha),hand))
        else:
            await ctx.send("Your {} found a {}. (Attack: {}, Charisma: {} [{}])".format(user,itemname,str(att),str(cha),hand))
        msg = await ctx.send("Do you want to equip, put in backpack or sell this item?")
        start_adding_reactions(msg, Treasure.controls.keys())
        if hasattr(user, "id"):
            pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, user)
        else:
            pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, ctx.author)
        react, user = await ctx.bot.wait_for("reaction_add", check=pred)
        try:
            await msg.clear_reactions()
        except discord.Forbidden:  # cannot remove all reactions
            for key in Treasure.controls.keys():
                await msg.remove_reaction(key, ctx.bot.user)
        return {"itemname": itemname,"item":item,"equip":Treasure.controls[react.emoji]}


    async def trader_get_items():
        items = {}
        output = {}
        type = random.randint(1,100)
        while len(items) < 4:
            chance = None
            roll = random.randint(1,100)
            if type <= 60:
                if roll <= 5:
                    chance = Treasure.unique
                elif roll > 5 and roll <= 25:
                    chance = Treasure.rare
                elif roll >= 90:
                    chest = [1,0,0]
                    if "normal chest" not in items:
                        items.update({"normal chest": {"itemname": "normal chest","item":chest, "price": 2000}})
                else:
                    chance = Treasure.common
            elif type <= 75:
                if roll <= 15:
                    chance = Treasure.unique
                elif roll > 15 and roll <= 45:
                    chance = Treasure.rare
                elif roll >= 90:
                    treasure = random.choice([[0,1,0],[1,0,0]])
                    types = ["normal chest",".rare_chest","[epic chest]"]
                    prices = [2000,5000,10000]
                    chesttext = types[treasure.index(1)]
                    price = prices[treasure.index(1)]
                    if chesttext not in items:
                        items.update({chesttext: {"itemname": "{}".format(chesttext),"item":treasure, "price": price}})
                else:
                    chance = Treasure.common
            elif type <= 90:
                if roll <= 25:
                    chance = Treasure.unique
                elif roll >= 90:
                    treasure = random.choice([[0,1,0],[0,0,1]])
                    types = ["normal chest",".rare_chest","[epic chest]"]
                    prices = [2000,5000,10000]
                    chesttext = types[treasure.index(1)]
                    price = prices[treasure.index(1)]
                    if chesttext not in items:
                        items.update({chesttext: {"itemname": "{}".format(chesttext),"item":treasure, "price": price}})
                else:
                    chance = Treasure.rare
            if chance != None:
                itemname = random.choice(list(chance.keys()))
                item = chance[itemname]
                if len(item["slot"]) == 2: # two handed weapons add their bonuses twice
                    hand = "two handed"
                    att = item["att"]*2
                    cha = item["cha"]*2
                else:
                    att = item["att"]
                    cha = item["cha"]
                if "[" in itemname:
                    price = random.randint(1000,2000)*max(att+cha, 1)
                elif "." in itemname:
                    price = random.randint(200,1000)*max(att+cha, 1)
                else:
                    price = random.randint(10,200)*max(att+cha, 1)
                if itemname not in items:
                    items.update({itemname: {"itemname": itemname,"item":item, "price": price}})
        for index, item in enumerate(items):
            output.update({index: items[item]})
        return output

    def countdown(ctx, seconds, title, loop: Optional[asyncio.AbstractEventLoop] = None,) -> asyncio.Task:
            # unique countdown for the trader, so it won't be overwritten by starting adventures.
        async def countdown():
            counter = 0
            try:
                secondint = int(seconds)
                Treasure.finish = getEpoch(secondint)
                if secondint < 0 or secondint == 0:
                    await ctx.send("I dont think im allowed to do negatives \U0001f914")
                    return

                message = await ctx.send("[" + title +"] " + remaining(Treasure.finish)[0])
                while True:
                    timer, done = remaining(Treasure.finish)
                    if done:
                        await message.delete()
                        break
                    await message.edit(content=("⏳ [" + title + "] {0}s".format(timer)))
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
            if h == 0 and m == 0:
                out = "{:02d}".format(s)
            elif h == 0:
                out = "{:02d}:{:02d}".format(m, s)
            else:
                out = "{:01d}:{:02d}:{:02d}".format(h, m, s)
            return out, finish

        def getEpoch(seconds : int):
            epoch = time.time()
            epoch += seconds
            return epoch

        if loop is None:
            loop = asyncio.get_event_loop()

        return loop.create_task(countdown())
