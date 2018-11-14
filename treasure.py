from redbot.core import commands
import asyncio
import discord
import random
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions

class Treasure:

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
            }
    rare = {"ceremonial dagger":{"slot":["right"],"att":2,"cha":2},
            "tower shield":{"slot":["left"],"att":3,"cha":1},
            "mirror shield":{"slot":["left"],"att":2,"cha":3},
            "bagpipes":{"slot":["right","left"],"att":1,"cha":2},
            "warpike":{"slot":["right"],"att":3,"cha":0},
            "panflute":{"slot":["right"],"att":0,"cha":3},
            "ring of strength":{"slot":["ring"],"att":2,"cha":0},
            "ring of charisma":{"slot":["ring"],"att":0,"cha":2},
            "ring of ambivalence":{"slot":["ring"],"att":1,"cha":1},
            "bruteforce ring":{"slot":["ring"],"att":3,"cha":-2},
            "bruteforce crescent":{"slot":["charm"],"att":3,"cha":-2},
            "silver tongued ring":{"slot":["ring"],"att":-1,"cha":3},
            "silver tongued chain":{"slot":["charm"],"att":-1,"cha":3},
            "greataxe":{"slot":["right","left"],"att":2,"cha":1},
            "spiked mace":{"slot":["right"],"att":3,"cha":-1},
            "buckler":{"slot":["left"],"att":3,"cha":0},
            "tuba":{"slot":["right","left"],"att":2,"cha":1},
            }
    unique = {"troll banhammer":{"slot":["right","left"],"att":2,"cha":2},
            "scythe of death":{"slot":["right","left"],"att":3,"cha":-2},
            "maul of efrin":{"slot":["right"],"att":5,"cha":0},
            "star of ishtar":{"slot":["charm"],"att":1,"cha":5},
            "booklet of jokes":{"slot":["charm"],"att":0,"cha":5},
            "great bulwark":{"slot":["left"],"att":5,"cha":0},
            "dragon ring":{"slot":["ring"],"att":4,"cha":3},
            "mandachord":{"slot":["right", "left"],"att":1,"cha":3},
            }

    async def open_chest(ctx, user, type):
        await ctx.send("{} is opening a treasure chest. What riches lay inside?".format(user.display_name))
        roll = random.randint(1,100)
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
        await ctx.send("{} found a {}. (Attack: {}, Charisma: {} [{}])".format(user.display_name,itemname,str(att),str(cha),hand))
        msg = await ctx.send("Do you want to equip this item?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, user)
        await ctx.bot.wait_for("reaction_add", check=pred)
        try:
            await msg.clear_reactions()
        except discord.Forbidden:  # cannot remove all reactions
            for key in ReactionPredicate.YES_OR_NO_EMOJIS:
                await msg.remove_reaction(key, ctx.bot.user)
        return {"itemname": itemname,"item":item,"equip":pred.result}
