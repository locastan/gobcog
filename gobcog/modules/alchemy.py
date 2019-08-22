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
from .consumables import Consumables

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
                "DaisyMushroomOilflower": {"yields":".vial_of_aggression", "uses": (1,6)},
                "MushroomMushroomOilflower": {"yields":".vial_of_aggression", "uses": (5,10)},
                "DaisyFlyleafTongue Sprout": {"yields":".potion_of_eloquence", "uses": (1,5)},
                "FlyleafMushroomOilflower": {"yields":".potion_of_strength", "uses": (1,5)},
                "DaisyTongue SproutTwolip": {"yields":".potion_of_eloquence", "uses": (2,5)},
                "Tongue SproutTwolipTwolip": {"yields":"[distilled charisma]", "uses": (1,2)},
                "TwolipTwolipTwolip": {"yields":"[distilled charisma]", "uses": (3,5)},
                "Cyanka LillyMushroomRaging Frills": {"yields":".potion_of_strength", "uses": (2,5)},
                "Cyanka LillyRaging FrillsRaging Frills": {"yields":"[brutal philtre]", "uses": (1,2)},
                "Raging FrillsRaging FrillsRaging Frills": {"yields":"[brutal philtre]", "uses": (3,5)},
                "DaisyMoneypennyMushroom": {"yields":".dust_of_midas", "uses": (2,4)},
                "DaisyMoneypennyOilflower": {"yields":".dust_of_midas", "uses": (2,4)},
                "DaisyRoseSageworth": {"yields":".scroll_of_learning", "uses": (2,4)},
                "FlyleafRoseSageworth": {"yields":"[foliant of wisdom]", "uses": (1,2)},
                "Mourning StarNa-PalmOoze": {"yields":"[chaos egg]", "uses": (1,1)},
                "HoneytailHoneytailOilflower": {"yields":".sweet_stew", "uses": (1,2)},
                "DaisyHoneytailOilflower": {"yields":".sweet_stew", "uses": (1,2)},
                "HoneytailHoneytailHoneytail": {"yields":".sweet_stew", "uses": (2,3)},
                "ChestnutHoneytailOilflower": {"yields":"[sweetbread]", "uses": (1,2)},
                "DaisyDaisyMushroom": {"yields":"bitter stew", "uses": (1,2)},
                "DaisyMushroomMushroom": {"yields":"bitter stew", "uses": (2,3)},
                "MushroomMushroomMushroom": {"yields":"bitter stew", "uses": (3,4)},
                "DaisyDaisyRose": {"yields":".sweet_stew", "uses": (2,4)},
                "DaisyDaisyDaisy": {"yields":".sweet_stew", "uses": (1,1)},
                "ChestnutChestnutChestnut": {"yields":".hearty_stew", "uses": (3,5)},
                "DaisyChestnutChestnut": {"yields":".hearty_stew", "uses": (1,3)},
                "DaisyDaisyChestnut": {"yields":".hearty_stew", "uses": (1,1)},
                "CloverCloverMoneypenny": {"yields":"four leaf clover", "uses": (6,10)},
                "CloverCloverClover": {"yields":"four leaf clover", "uses": (2,5)},
                "CloverMoneypennyMoneypenny": {"yields":"[luckworth essence]", "uses": (1,3)},
                "MoneypennyMoneypennyMoneypenny": {"yields":"[luckworth essence]", "uses": (3,5)},
                }

    async def brew(ctx, user, ingredients):
        await ctx.send("")#do sth.
