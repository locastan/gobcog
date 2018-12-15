import random
import asyncio
from redbot.core.utils.predicates import MessagePredicate
from .treasure import Treasure
from .adventure import Adventure

class Classes:
        #handling functions for class abilities. think of downsides if the ability fails. handling fails and crits are done in adventure.
    async def forge(ctx, item1, item2):
        newslot = random.choice([item1['slot'],item2['slot']])
        roll = random.randint(1,20)
        if roll == 1:
            modifier = 0.4
        if roll > 1 and roll <= 10:
            modifier = 0.5
        if roll > 10 and roll <= 15:
            modifier = 0.6
        if roll > 15 and roll <= 17:
            modifier = 0.7
        if roll == 18:
            modifier = 0.8
        if roll == 19:
            modifier = 1
        if roll == 20:
            modifier = 1.2
        newatt = round((int(item1['att'])+int(item2['att']))*modifier)
        newdip = round((int(item1['cha'])+int(item2['cha']))*modifier)
        newslot = random.choice([item1['slot'],item2['slot']])
        if len(newslot) == 2: # two handed weapons add their bonuses twice
            hand = "two handed"
        else:
            if newslot[0] == "right" or newslot[0] == "left":
                hand = newslot[0] + " handed"
            else:
                hand = newslot[0] + " slot"
        if len(newslot) == 2:
            await ctx.send('Your forging roll was 🎲({}).\nThe device you tinkered will have {}🗡 and {}🗨 and be {}.'.format(roll,newatt*2,newdip*2,hand))
        else:
            await ctx.send('Your forging roll was 🎲({}).\nThe device you tinkered will have {}🗡 and {}🗨 and be {}.'.format(roll,newatt,newdip,hand))
        await ctx.send('Please respond with a name for your creation within 30s.\n(You will not be able to change it afterwards. 40 characters maximum.)')
        reply = None
        try:
            reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
        except asyncio.TimeoutError:
            reply = "Unnamed Artifact"
        if reply == None:
            name = "{.:'Unnamed Artifact':.}"
        else:
            if hasattr(reply, 'content'):
                if len(reply.content) > 40:
                    name = "{.:'Long-winded Artifact':.}"
                else:
                    name = "{.:'" + reply.content + "':.}"
            else:
                name = "{.:'" + reply + "':.}"
        item = {"itemname": name,"item": {"slot":newslot,"att":newatt,"cha":newdip}}
        return item


    async def rage(ctx, users):
        user = ctx.author.id
        if users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            Adventure.users = users
            return users
        users[str(user)]['class']['ability'] = True
        await ctx.send('**{}** is starting to froth at the mouth...🗯️'.format(ctx.author.display_name))
        Adventure.users = users
        return users

    async def bless(ctx,users):
        user = ctx.author.id
        if users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            Adventure.users = users
            return users
        users[str(user)]['class']['ability'] = True
        await ctx.send('**{}** is starting an inspiring sermon. 📜'.format(ctx.author.display_name))
        Adventure.users = users
        return users

    async def sing(ctx,users):
        user = ctx.author.id
        if users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            Adventure.users = users
            return users
        users[str(user)]['class']['ability'] = True
        await ctx.send('♪♫♬ **{}** is whipping up a performance. ♬♫♪'.format(ctx.author.display_name))
        Adventure.users = users
        return users

    pets = {"flitterwisp": {'name': "flitterwisp", 'bonus': 1.05, 'cha': 10},
            "hufflepuff": {'name': "hufflepuff", 'bonus': 1.1, 'cha': 12},
            "sylvan wolf": {'name': "silvan wolf", 'bonus': 1.2, 'cha': 16},
            "zephyr cat": {'name': "zephyr cat", 'bonus': 1.2, 'cha': 16},
            "giggling imp": {'name': "giggling imp", 'bonus': 1.4, 'cha': 20},
            "pocket dragon": {'name': "pocket dragon", 'bonus': 1.5, 'cha': 30},
            }

    async def pet(ctx,users,flag):
        user = ctx.author.id
        if flag == "free":
            if users[str(user)]['class']['ability'] != False:
                users[str(user)]['class']['ability'] = False
                ctx.command.reset_cooldown(ctx)
                await ctx.send('**{}** relased his pet into the wild again.'.format(ctx.author.display_name))
            else:
                return None
        elif flag == "forage":
            return await Treasure.open_chest(ctx,users[str(user)]['class']['ability']['pet']['name'],'pet')
        else:
            if users[str(user)]['class']['ability'] == False:
                await ctx.send('**{}** is trying to tame a pet.'.format(ctx.author.display_name))
                await asyncio.sleep(2)
                pet = random.choice(list(Classes.pets.keys()))
                roll = random.randint(1,20)
                await ctx.send('You are tracking a wild **{}** with a roll of 🎲({}).'.format(Classes.pets[pet]['name'], roll))
                await asyncio.sleep(1)
                dipl_value = roll + users[str(user)]['cha'] + users[str(user)]['skill']['cha']
                if roll == 1:
                    return await ctx.send('But you stepped on a twig and scared it away.')

                elif roll == 20:
                    await ctx.send('You happen to have its favorite food.')
                    dipl_value += 25
                if dipl_value > Classes.pets[pet]['cha']:
                    await ctx.send('You successfully tamed the {}.'.format(Classes.pets[pet]['name']))
                    return Classes.pets[pet]
                else:
                    return await ctx.send('The {} escaped.'.format(Classes.pets[pet]['name']))

            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send('You already have a pet. Try foraging.')
                return None
