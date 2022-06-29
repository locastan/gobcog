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

class Alchemy:

    # ingredients are joined to a string by "".join(sorted(ingredients)) to get the proper key for a recipe.
    # recipe output (split by upper case) for finding a random recipe could be: recipe = ''.join(" " + x if x.isupper() else x for x in random.choice(list(recipes.keys()))).strip(" ").split(" ")
    # followed by:
    #indices = [i for i, x in enumerate(recipe) if x == ""]
    #killlist = []
    #for e in indices:
    #   recipe[e-1]= recipe[e-1] + " " + recipe[e+1]
    #   killlist.append(recipe[e+1])
    #   killlist.append(recipe[e])
    #recipe[:] = (value for value in recipe if value != "")   # strip empty elements
    #for e in killlist:
    #   recipe.remove(e)   #search and destroy copied elements without iterating over a list that changes size.

    recipes = {"DaisyDaisyTongue Sprout": {"yields":".vial_of_wit", "uses": (1,6)},
                "DaisyTongue SproutTongue Sprout": {"yields":".vial_of_wit", "uses": (3,4)},
                "DaisyReedsReeds": {"yields":".vial_of_wit", "uses": (2,4)},
                "DaisyDaisyReeds": {"yields":".vial_of_wit", "uses": (1,2)},
                "DaisyMushroomOilflower": {"yields":".vial_of_aggression", "uses": (1,6)},
                "MushroomMushroomOilflower": {"yields":".vial_of_aggression", "uses": (5,10)},
                "DaisyGrufferfishTongue Sprout": {"yields":"[phenomenal phial]", "uses": (1,3)},
                "FlyleafGrufferfishTongue Sprout": {"yields":"[phenomenal phial]", "uses": (3,5)},
                "BrineappleCyanka LillyTwolip": {"yields":"[phenomenal phial]", "uses": (5,8)},
                "DaisyFlyleafTongue Sprout": {"yields":".potion_of_eloquence", "uses": (1,5)},
                "FlyleafMushroomOilflower": {"yields":".potion_of_strength", "uses": (1,5)},
                "GrufferfishMushroomOilflower": {"yields":".potion_of_strength", "uses": (5,8)},
                "DaisyTongue SproutTwolip": {"yields":".potion_of_eloquence", "uses": (4,8)},
                "Tongue SproutTongue SproutTongue Sprout": {"yields":".potion_of_eloquence", "uses": (1,5)},
                "Tongue SproutTwolipTwolip": {"yields":"[distilled charisma]", "uses": (2,3)},
                "TwolipTwolipTwolip": {"yields":"[distilled charisma]", "uses": (4,6)},
                "Cyanka LillyMushroomRaging Frills": {"yields":".potion_of_strength", "uses": (8,14)},
                "GrufferfishRaging FrillsRaging Frills": {"yields":"[brutal philtre]", "uses": (1,2)},
                "Cyanka LillyRaging FrillsRaging Frills": {"yields":"[brutal philtre]", "uses": (2,3)},
                "Raging FrillsRaging FrillsRaging Frills": {"yields":"[brutal philtre]", "uses": (4,6)},
                "MoneypennyNa-palmRaging Frills": {"yields":"[foliant of greed]", "uses": (1,2)},
                "Na-palmOozeRaging Frills": {"yields":"[foliant of greed]", "uses": (3,5)},
                "BrineappleCloverMoneypenny": {"yields":"[edible chance]", "uses": (4,6)},
                "Ancient ConchCloverOoze": {"yields":"[jacks pot]", "uses": (1,2)},
                "DaisyMoneypennyMushroom": {"yields":".dust_of_midas", "uses": (2,4)},
                "DaisyMoneypennyOilflower": {"yields":".dust_of_midas", "uses": (2,4)},
                "DaisyMushroomRose": {"yields":".scroll_of_learning", "uses": (1,2)},
                "DaisyReedsRose": {"yields":".scroll_of_learning", "uses": (3,5)},
                "ReedsRoseSageworth": {"yields":".scroll_of_learning", "uses": (8,16)},
                "DaisyRoseSageworth": {"yields":".scroll_of_learning", "uses": (10,20)},
                "FlyleafRoseSageworth": {"yields":"[foliant of wisdom]", "uses": (2,6)},
                "Mourning StarNa-palmOoze": {"yields":"[chaos egg]", "uses": (2,5)},
                "HoneytailHoneytailOilflower": {"yields":".sweet_stew", "uses": (1,2)},
                "DaisyHoneytailOilflower": {"yields":".sweet_stew", "uses": (1,2)},
                "HoneytailHoneytailHoneytail": {"yields":".sweet_stew", "uses": (2,3)},
                "ChestnutHoneytailOilflower": {"yields":"[sweetbread]", "uses": (1,2)},
                "DaisyDaisyMushroom": {"yields":"bitter stew", "uses": (2,2)},
                "DaisyMushroomMushroom": {"yields":"bitter stew", "uses": (3,4)},
                "MushroomMushroomMushroom": {"yields":"bitter stew", "uses": (5,6)},
                "DaisyDaisyRose": {"yields":".sweet_stew", "uses": (2,4)},
                "DaisyDaisyDaisy": {"yields":".sweet_stew", "uses": (1,1)},
                "ChestnutChestnutChestnut": {"yields":".hearty_stew", "uses": (3,5)},
                "ChestnutChestnutDaisy": {"yields":".hearty_stew", "uses": (1,3)},
                "BrineappleDaisyDaisy": {"yields":".salty_stew", "uses": (1,1)},
                "BrineappleDaisyOilflower": {"yields":".salty_stew", "uses": (2,2)},
                "BrineappleBrineappleDaisy": {"yields":".salty_stew", "uses": (2,4)},
                "BrineappleBrineappleBrineapple": {"yields":".salty_stew", "uses": (3,5)},
                "ChestnutDaisyDaisy": {"yields":".hearty_stew", "uses": (1,1)},
                "DaisyDaisyMaple": {"yields":".hearty_stew", "uses": (1,1)},
                "CloverCloverMoneypenny": {"yields":"four leaf clover", "uses": (6,10)},
                "CloverCloverClover": {"yields":"four leaf clover", "uses": (2,5)},
                "CloverMoneypennyMoneypenny": {"yields":"[luckworth essence]", "uses": (1,3)},
                "BrineappleMoneypennyMoneypenny": {"yields":"[luckworth essence]", "uses": (1,1)},
                "MoneypennyMoneypennyMoneypenny": {"yields":"[bottled fortune]", "uses": (2,5)},
                "MapleMapleWhipweed": {"yields":"bandaid", "uses": (1,2)},
                "MapleWhipweedWhipweed": {"yields":"bandaid", "uses": (2,4)},
                "WhipweedWhipweedWhipweed": {"yields":"bandaid", "uses": (3,6)},
                "MapleRust LeafsWhipweed": {"yields":"bandages", "uses": (2,4)},
                "Rust LeafsWhipweedWhipweed": {"yields":"bandages", "uses": (3,6)},
                "ChondrusMapleRust Leafs": {"yields":"bandages", "uses": (2,4)},
                "ChondrusChondrusRust Leafs": {"yields":"bandages", "uses": (3,7)},
                "Rust LeafsRust LeafsRust Leafs": {"yields":"bandages", "uses": (1,1)},
                "Mourning StarRoseWhipweed": {"yields":".potion_of_healing", "uses": (2,4)},
                "DaisyMourning StarRose": {"yields":".potion_of_healing", "uses": (1,2)},
                "DaisyDaisyMourning Star": {"yields":".potion_of_healing", "uses": (1,1)},
                "Mourning StarWhipweedWhipweed": {"yields":".potion_of_healing", "uses": (1,3)},
                "FleshthornMourning StarNa-palm": {"yields":"[potion of rejuvenation]", "uses": (3,5)}
                }

    raritydict = {"legendary":["Ancient Conch","Ooze","Raging Frills","Cyanka Lilly","Sageworth","Twolip","Rose","Na-palm"],
                        "epic":["Chondrus","Grufferfish","Moneypenny","Whipweed","Mourning Star","Honeytail","Clover","Chestnut","Tongue Sprout"],
                        "rare":["Brineapple","Flyleaf","Rust Leafs","Fleshthorn"],
                        "common":["Reeds","Maple","Mushroom","Oilflower","Daisy"]}

    raritylookup = ["common","rare","epic","legendary"]
    needed = {"common":50,"rare":30,"epic":20,"legendary":10}
    getting = {"rare":(10,20),"epic":(5,10),"legendary":(1,3)}

    async def brew(ctx, user):
        uses_total = 0
        inbrew = []
        for ingredient in Userdata.users[str(user.id)]['ingredients']:
            uses_total += Userdata.users[str(user.id)]['ingredients'][ingredient].get('uses', 0)
        if uses_total >= 3:
            i = 0
            introtxt = "⚗️ **{}** is starting a brew.\n".format(user.display_name)
            al_msg = await ctx.send(introtxt)
            while i < 3:
                lookup = list(Userdata.users[str(user.id)]['ingredients'])
                lookup.sort()
                text = "```css\n"
                ran_out = []
                for num, name in enumerate(lookup, start=1): #these three loops are a very crappy way of doing this...
                    act_uses = Userdata.users[str(user.id)]['ingredients'][name].get('uses', 0)
                    for ingr in inbrew: #correct list uses for stuff already in brew
                        if ingr == name:
                            act_uses -= 1
                    if act_uses == 0:
                        ran_out.append(name)
                for e in ran_out:
                    lookup.remove(e)
                for num, name in enumerate(lookup, start=1):
                    act_uses = Userdata.users[str(user.id)]['ingredients'][name].get('uses', 0)
                    for ingr in inbrew: #correct list uses for stuff already in brew
                        if ingr == name:
                            act_uses -= 1
                    text += ("[{}]: {} ({}x)\n".format(num, name, act_uses))
                text += "```"
                await al_msg.edit(content=introtxt + "You own these ingredients:\n{}Please choose ingredient {} with a number from the list. (Cancel with 0)".format(text, i+1))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    await al_msg.delete()
                    return (False,[])
                if reply.content == "0":
                    await al_msg.delete()
                    return (False,[])
                elif reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    inbrew.append(lookup[idx])
                    i += 1
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    await al_msg.delete()
                    return (False,[])
            brewing = "".join(sorted(inbrew))
            if brewing in Alchemy.recipes:
                a_name = Alchemy.recipes[brewing]['yields']
                a_uses = random.randint(Alchemy.recipes[brewing]['uses'][0],Alchemy.recipes[brewing]['uses'][1])
                if a_name in Userdata.users[str(user.id)]['consumables'].keys():
                    Userdata.users[str(user.id)]['consumables'][a_name]['uses'] = Userdata.users[str(user.id)]['consumables'][a_name].get("uses", 0) + a_uses
                else:
                    Userdata.users[str(user.id)]['consumables'].update({a_name:{"slot":["consumable"],"uses":a_uses}})
                await ctx.send("Your brew yielded {}x {}.".format(a_uses,a_name))
                await al_msg.delete()
                return (True,inbrew)
            else:
                roll = random.randint(1,20)
                if roll >= 10:
                    a_name = "bitter stew"
                    a_uses = 1
                    if a_name in Userdata.users[str(user.id)]['consumables'].keys():
                        Userdata.users[str(user.id)]['consumables'][a_name]['uses'] = Userdata.users[str(user.id)]['consumables'][a_name].get("uses", 0) + a_uses
                    else:
                        Userdata.users[str(user.id)]['consumables'].update({a_name:{"slot":["consumable"],"uses":a_uses}})
                    await ctx.send("Your brew did not quite work out right, but can at least be used as {}.".format(a_name))
                    await al_msg.delete()
                    return (True,inbrew)
                else:
                    await ctx.send("These ingredients really do not go well together. You have to toss this useless concoction.")
            await al_msg.delete()
            return (True, inbrew)
        elif uses_total < 3:
            await ctx.send("You need at least 3 ingredients to brew, try to !explore a bit more.")
            return (False,[])
        elif len(lookup) == 0:
            await ctx.send("You do not own any ingredients, try to !explore a bit.")
            return (False,[])

    async def distill(ctx, user):
        uses_total = 0
        lookup = []
        instill = None
        introtxt = "⚗️ **{}** set up the still.\n".format(user.display_name)
        di_msg = await ctx.send(introtxt + "Select category to distill:\n[1] 50x Common ({})\n[2] 30x Rare ({})\n[3] 20x Epic ({})\n[4] 10x Legendary ({})\n\n Please choose with a number from the list. (Cancel with 0)".format(", ".join(Alchemy.raritydict["common"]),", ".join(Alchemy.raritydict["rare"]),", ".join(Alchemy.raritydict["epic"]),", ".join(Alchemy.raritydict["legendary"])))
        try:
            reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("I don't have all day, you know.")
            return (False)
        if reply.content == "0":
            return (False)
        elif reply.content.isdigit() and (int(reply.content)-1) < len(Alchemy.raritylookup) and int(reply.content) > 0:
            irarity = Alchemy.raritylookup[int(reply.content)-1]
            ineed = Alchemy.needed[irarity]
        else:
            await ctx.send("Sorry, but there was something wrong with that reply.")
            return (False)
        for ingredient in Alchemy.raritydict[irarity]:
            if ingredient in Userdata.users[str(user.id)]['ingredients']:
                uses_total = Userdata.users[str(user.id)]['ingredients'][ingredient].get('uses', 0)
                if uses_total >= ineed and ingredient in Alchemy.raritydict[irarity]:
                        lookup.append(ingredient)
                        lookup.sort()
        if len(lookup) == 0:
            await ctx.send("You need at least {}x of a {} ingredient to distill, try to !explore a bit more.".format(ineed, irarity))
            return (False)
        text = "```css\n"
        for num, name in enumerate(lookup, start=1):
            text += ("[{}]: {} ({}x)\n".format(num, name, Userdata.users[str(user.id)]['ingredients'][name].get('uses', 0)))
        text += "```"
        await di_msg.edit(content=introtxt + "You own these {} ingredients:\n{}Please choose ingredient with a number from the list. (Cancel with 0)".format(irarity, text))
        try:
            reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("I don't have all day, you know.")
            return (False)
        if reply.content == "0":
            return (False)
        elif reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
            idx = int(reply.content)-1
            instill = lookup[idx]
        else:
            await ctx.send("Sorry, but there was something wrong with that reply.")
            return (False)
        if Alchemy.raritylookup.index(irarity)+1 <= 3:
            nextbest = Alchemy.raritylookup[Alchemy.raritylookup.index(irarity)+1]
        else:
            nextbest = "legendary"
        d_name = instill
        while d_name == instill:
            d_name = random.choice(Alchemy.raritydict[nextbest])
        d_uses = random.randint(Alchemy.getting[nextbest][0],Alchemy.getting[nextbest][1])
        if d_name in Userdata.users[str(user.id)]['ingredients'].keys():
            Userdata.users[str(user.id)]['ingredients'][d_name]['uses'] = Userdata.users[str(user.id)]['ingredients'][d_name].get("uses", 0) + d_uses
        else:
            Userdata.users[str(user.id)]['ingredients'].update({d_name:{"slot":['ingredients'],"uses":d_uses}})
        amount = int(Userdata.users[str(user.id)]['ingredients'][instill].get('uses'))
        if amount <= ineed:
            del Userdata.users[str(user.id)]['ingredients'][instill]
        else:
            Userdata.users[str(user.id)]['ingredients'][instill]['uses'] = Userdata.users[str(user.id)]['ingredients'][instill]['uses'] - ineed
        await ctx.send("You distilled {}x {}, which you traded in for {}x {}.".format(ineed,instill,d_uses,d_name))
        return (True)
