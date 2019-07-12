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
                "MushroomMushroomOilflower": {"yields":".vial_of_aggression", "uses": (1,10)},
                "DaisyFlyleafTongue Sprout": {"yields":".potion_of_eloquence", "uses": (1,5)},
                "FlyleafMushroomOilflower" {"yields":".potion_of_strength", "uses": (1,5)},
                }

    async def brew(ctx, user, ingredients):
        await ctx.send("")#do sth.
