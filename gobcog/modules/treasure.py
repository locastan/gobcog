from redbot.core import commands
import asyncio
import discord
import random
import time
from redbot.core import bank
from typing import Union, Iterable, Optional
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions
from .userdata import Userdata

class Treasure:

    finish = 0

    controls = {"✅": "equip", "❎": "backpack", "💰": "sell", "❌": "cancel"}
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
            "short bow":{"slot":["right","left"],"att":1,"cha":0},
            "amulet of ambivalence":{"slot":["charm"],"att":1,"cha":1},
            "four leaf clover":{"slot":["consumable"],"uses":3},
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
            ".pistol_crossbow":{"slot":["right"],"att":2,"cha":1},
            ".ring_of_balance":{"slot":["ring"],"att":2,"cha":2},
            ".potion_of_strength":{"slot":["consumable"],"uses":3},
            ".vial_of_aggression":{"slot":["consumable"],"uses":5},
            ".potion_of_eloquence":{"slot":["consumable"],"uses":3},
            ".vial_of_wit":{"slot":["consumable"],"uses":5},
            ".dust_of_midas":{"slot":["consumable"],"uses":5},
            ".scroll_of_learning":{"slot":["consumable"],"uses":3}
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
            "[repeater crossbow]":{"slot":["right","left"],"att":3,"cha":1},
            "[elvish longbow]":{"slot":["right","left"],"att":4,"cha":2},
            "[gauntlet of balance]":{"slot":["ring"],"att":3,"cha":3},
            "[paci-fist]":{"slot":["ring"],"att":1,"cha":5},
            "[luckworth essence]":{"slot":["consumable"],"uses":2},
            "[foliant of wisdom]":{"slot":["consumable"],"uses":2},
            "[chaos egg]":{"slot":["consumable"],"uses":3},
            "[soul essence]":{"slot":["consumable"],"uses":1}
            }
    quest = {"[lichtooth]":{"slot":["charm"],"att":2,"cha":6},
            "[occam\'s razor]":{"slot":["right","left"],"att":5,"cha":1},
            "[compound longbow]":{"slot":["right","left"],"att":5,"cha":3},
            "[cape of shadows]":{"slot":["charm"],"att":4,"cha":4},
            "[very pointy stick]":{"slot":["right"],"att":7,"cha":-1},
            "[chattering shield]":{"slot":["left"],"att":6,"cha":2},
            "[isildur\'s bane]":{"slot":["ring"],"att":6,"cha":3},
            "[dragon scales]":{"slot":["charm"],"att":4,"cha":5},
            "[mace of many]":{"slot":["right"],"att":6,"cha":1},
            "[mesmer ring]":{"slot":["ring"],"att":1,"cha":6},
            "[crumhorn]":{"slot":["right", "left"],"att":3,"cha":5}
            }

    async def open_chest(ctx, user, type):
        if hasattr(user, "display_name"):
            await ctx.send("{} is opening a treasure chest. What riches lay inside?".format(user.display_name))
        else: #this is when a pet is foraging.
            await ctx.send("{} is foraging for treasure. What will it find?".format(user[:1].upper() + user[1:]))
            await asyncio.sleep(2)
        if hasattr(user, "display_name"):
            luckbonus = Userdata.users[str(user.id)]['buffs'].get('luck', {'bonus':0})['bonus']
            roll = random.randint(1,100)-luckbonus
        else:
            luckbonus = 0
            roll = random.randint(1,100)
        if type == "pet":
            if roll <= 1:
                await ctx.send("{} found something precious!".format(user[:1].upper() + user[1:]))
                chance = Treasure.quest
            elif roll <= 11:
                chance = Treasure.unique
            elif roll > 11 and roll <= 50:
                chance = Treasure.rare
            elif roll > 50 and roll <= 75:
                chance = Treasure.common
            else:
                await ctx.send("{} found nothing of value.".format(user[:1].upper() + user[1:]))
                return None
        elif type == "normal":
            if roll <= 5:
                chance = Treasure.unique
            elif roll > 5 and roll <= 25:
                chance = Treasure.rare
            else:
                chance = Treasure.common
        elif type == "rare":
            if roll <= 15:
                chance = Treasure.unique
            elif roll > 15 and roll <= 45:
                chance = Treasure.rare
            else:
                chance = Treasure.common
        elif type == "epic":
            if roll <= 1:
                await ctx.send("This was no ordinary epic chest!")
                chance = Treasure.quest
            elif roll <= 25:
                chance = Treasure.unique
            else:
                chance = Treasure.rare
        elif type == "quest":
            if roll <= 10:
                chance = Treasure.quest
            else:
                chance = Treasure.unique
        itemname = random.choice(list(chance.keys()))
        item = chance[itemname]
        if item['slot'] == ['consumable']:
            item['uses'] = random.randint(1,item['uses'])
            if hasattr(user, "display_name"):
                await ctx.send("```css\n{} found {} ({}x).```".format(user.display_name,itemname,item['uses']))
            else:
                await ctx.send("```css\nYour {} found {} ({}x)```.".format(user,itemname,item['uses']))
            msg = await ctx.send("Do you want to use, put in backpack or sell this item?")
            start_adding_reactions(msg, Treasure.controls.keys())
            if hasattr(user, "id"):
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, user)
            else:
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, ctx.author)
            react = None
            try:
                react, user = await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Item claim timed out after one minute. Selling...")
                react.emoji = "💰"
            try:
                await msg.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in Treasure.controls.keys():
                    await msg.remove_reaction(key, ctx.bot.user)
            return {"itemname": itemname,"item":item,"equip":Treasure.controls[react.emoji]}
        else:
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
                await ctx.send("```css\n{} found a {}. (Attack: {}, Charisma: {} [{}])```".format(user.display_name,itemname,str(att),str(cha),hand))
            else:
                await ctx.send("```css\nYour {} found a {}. (Attack: {}, Charisma: {} [{}])```".format(user,itemname,str(att),str(cha),hand))
            msg = await ctx.send("Do you want to equip, put in backpack or sell this item?")
            start_adding_reactions(msg, Treasure.controls.keys())
            if hasattr(user, "id"):
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, user)
            else:
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, ctx.author)
            react = None
            try:
                react, user = await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Item claim timed out after one minute. Selling...")
                react.emoji = "💰"
            try:
                await msg.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in Treasure.controls.keys():
                    await msg.remove_reaction(key, ctx.bot.user)
            if luckbonus != 0:
                if Userdata.users[str(user.id)]['buffs']['luck']['duration'] <= 1:
                    Userdata.users[str(user.id)]['buffs'].pop('luck')
                else:
                    Userdata.users[str(user.id)]['buffs']['luck']['duration'] = Userdata.users[str(user.id)]['buffs']['luck']['duration'] - 1
            await Userdata.save()
            return {"itemname": itemname,"item":item,"equip":Treasure.controls[react.emoji]}

    async def autoopen_chest(ctx, user, type, many):
        lootpile = {}
        moneypile = 0
        if hasattr(user, "display_name"):
            await ctx.send("{} is opening {} treasure chests. What riches hide inside those?".format(user.display_name, many))
        #enter for range many loop.
        for x in range(0, many):
            if hasattr(user, "display_name"):
                luckbonus = Userdata.users[str(user.id)]['buffs'].get('luck', {'bonus':0})['bonus']
                roll = random.randint(1,100)-luckbonus
            else:
                luckbonus = 0
                roll = random.randint(1,100)
            if type == "normal":
                if roll <= 5:
                    chance = Treasure.unique
                elif roll > 5 and roll <= 25:
                    chance = Treasure.rare
                else:
                    chance = Treasure.common
            elif type == "rare":
                if roll <= 15:
                    chance = Treasure.unique
                elif roll > 15 and roll <= 45:
                    chance = Treasure.rare
                else:
                    chance = Treasure.common
            elif type == "epic":
                if roll <= 1:
                    await ctx.send("This one was no ordinary epic chest!")
                    chance = Treasure.quest
                elif roll <= 25:
                    chance = Treasure.unique
                else:
                    chance = Treasure.rare
            elif type == "quest":
                if roll <= 10:
                    chance = Treasure.quest
                else:
                    chance = Treasure.unique
            itemname = random.choice(list(chance.keys()))
            item = chance[itemname]
            if item['slot'] == ['consumable']:
                item['uses'] = random.randint(1,item['uses'])
                if luckbonus != 0 and hasattr(Userdata.users[str(user.id)]['buffs'], "luck"):
                    if Userdata.users[str(user.id)]['buffs']['luck']['duration'] <= 1:
                        Userdata.users[str(user.id)]['buffs'].pop('luck')
                    else:
                        Userdata.users[str(user.id)]['buffs']['luck']['duration'] = Userdata.users[str(user.id)]['buffs']['luck']['duration'] - 1
                await Userdata.save()
                if itemname in lootpile.keys():
                    lootpile[itemname]['item']['uses'] = lootpile[itemname]['item'].get("uses", 0) + item['uses']
                else:
                    lootpile.update({itemname: {"itemname": itemname,"item":item}})
            else:
                if luckbonus != 0:
                    if Userdata.users[str(user.id)]['buffs']['luck']['duration'] <= 1:
                        Userdata.users[str(user.id)]['buffs'].pop('luck')
                    else:
                        Userdata.users[str(user.id)]['buffs']['luck']['duration'] = Userdata.users[str(user.id)]['buffs']['luck']['duration'] - 1
                await Userdata.save()
                if itemname in lootpile.keys() or itemname in Userdata.users[str(user.id)]['items']['backpack'].keys():
                    moneypile += await Treasure.t_sell(user, {"itemname": itemname,"item":item})
                else:
                    lootpile.update({itemname: {"itemname": itemname,"item":item}})
        itempile = []
        conspile = []
        for thing in lootpile:
            itemname = lootpile[thing]['itemname']
            item = lootpile[thing]['item']
            if item['slot'] == ['consumable']:
                item['uses'] = random.randint(1,item['uses'])
                if hasattr(user, "display_name"):
                    conspile.append("{} ({}x)".format(itemname,item['uses']))
            else:
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
                itempile.append("{} (Attack: {}, Charisma: {} [{}])".format(itemname,str(att),str(cha),hand))
        conspile.sort()
        itempile.sort()
        consreport = " - " + "\n - ".join(conspile) + "```"
        pilereport = " - " + "\n - ".join(itempile)
        if len(pilereport) > 1900: #split dangerously long texts into chunks.
            chunks = [pilereport[i:i+1900] for i in range(0, len(pilereport), 1900)]
            await ctx.send("```css\n The following items were added to your backpack:\n```")
            for chunk in chunks:
                await ctx.send("```css\n" + chunk + "```")
                await asyncio.sleep(0.3)
        else:
            await ctx.send("```css\n The following items were added to your backpack:\n" + pilereport + "```")
        await ctx.send("```css\n Added consumables:\n" + consreport)
        await ctx.send("```css\n You also received {} copperpieces from selling duplicate items.```".format(moneypile))
        return lootpile

    async def one_from(ctx,user,list): #user needs to be a discord.member object. list is a namestring of a droplist of items here.
        chance = getattr(Treasure, list)
        itemname = random.choice(list(chance.keys()))
        item = chance[itemname]
        if item['slot'] == ['consumable']:
            item['uses'] = random.randint(1,item['uses'])
            await ctx.send("```css\n{} found {} ({}x).```".format(user.display_name,itemname,item['uses']))
            msg = await ctx.send("Do you want to use, put in backpack or sell this item?")
            start_adding_reactions(msg, Treasure.controls.keys())
            if hasattr(user, "id"):
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, user)
            else:
                pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, ctx.author)
            react = None
            try:
                react, user = await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Item claim timed out after one minute. Selling...")
                react.emoji = "💰"
            try:
                await msg.clear_reactions()
            except discord.Forbidden:  # cannot remove all reactions
                for key in Treasure.controls.keys():
                    await msg.remove_reaction(key, ctx.bot.user)
            return {"itemname": itemname,"item":item,"equip":Treasure.controls[react.emoji]}
        else:
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
            await ctx.send("```css\n{} found a {}. (Attack: {}, Charisma: {} [{}])```".format(user.display_name,itemname,str(att),str(cha),hand))
            msg = await ctx.send("Do you want to equip, put in backpack or sell this item?")
            start_adding_reactions(msg, Treasure.controls.keys())
            pred = ReactionPredicate.with_emojis(tuple(Treasure.controls.keys()), msg, user)
            react = None
            try:
                react, user = await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Item claim timed out after one minute. Selling...")
                react.emoji = "💰"
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
                    treasure = random.choice([[0,1,0,0],[1,0,0,0]])
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
                    treasure = random.choice([[0,1,0,0],[0,0,1,0]])
                    types = ["normal chest",".rare_chest","[epic chest]"]
                    prices = [2000,5000,10000]
                    chesttext = types[treasure.index(1)]
                    price = prices[treasure.index(1)]
                    if chesttext not in items:
                        items.update({chesttext: {"itemname": "{}".format(chesttext),"item":treasure, "price": price}})
                else:
                    chance = Treasure.rare
            if chance != None: #item is selected from a droplist, not a manually created chest
                itemname = random.choice(list(chance.keys()))
                item = chance[itemname]
                if item['slot'] == ['consumable']:
                    if "[" in itemname:
                        base = (3000,10000)
                    elif "." in itemname:
                        base = (500,3000)
                    else :
                        base = (100,500)
                    price = random.randint(base[0],base[1])*max(item['uses'],1)
                else:
                    if "[" in itemname:
                        base = (1000,2000)
                    elif "." in itemname:
                        base = (200,1000)
                    else :
                        base = (10,200)
                    if len(item["slot"]) == 2: # two handed weapons add their bonuses twice
                        hand = "two handed"
                        att = item["att"]*2
                        cha = item["cha"]*2
                    else:
                        att = item["att"]
                        cha = item["cha"]
                    price = random.randint(base[0],base[1])*max(item['att']+item['cha'],1)
                if itemname not in items and item['slot'] == ['consumable']:
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
                Treasure.finish = await getEpoch(secondint)
                if secondint < 0 or secondint == 0:
                    await ctx.send("I dont think im allowed to do negatives \U0001f914")
                    return
                rem, done = await remaining(Treasure.finish)
                message = await ctx.send("[" + title +"] " + rem)
                while True:
                    timer, done = await remaining(Treasure.finish)
                    if done:
                        await message.delete()
                        break
                    await message.edit(content=("⏳ [" + title + "] {0}s".format(timer)))
                    await asyncio.sleep(1)
            except ValueError:
                await ctx.send("Must be a number!")

        async def remaining(epoch):
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

        async def getEpoch(seconds : int):
            epoch = time.time()
            epoch += seconds
            return epoch

        if loop is None:
            loop = asyncio.get_event_loop()

        return loop.create_task(countdown())

    async def t_sell(user,item):
        if "[" in item['itemname']:
            base = (500,1000)
        elif "." in item['itemname']:
            base = (100,500)
        else :
            base = (10,200)
        if item['item']['slot'] == ['consumable']:
            price = random.randint(base[0],base[1])*max(item['item']['uses'],1)
        else:
            price = random.randint(base[0],base[1])*max(item['item']['att']+item['item']['cha'],1)
        await bank.deposit_credits(user, price)
        return(price)
