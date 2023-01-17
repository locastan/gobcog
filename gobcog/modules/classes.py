import random
import asyncio
import hashlib
import math
from redbot.core.utils.predicates import MessagePredicate
from .treasure import Treasure
from .userdata import Userdata

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

    async def meditate(ctx):
        user = ctx.author.id
        if Userdata.users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            return
        Userdata.users[str(user)]['class']['ability'] = True
        await ctx.send('**{}** is becoming one with the situation at hand...🖖'.format(ctx.author.display_name))
        return

    async def calc_monkbonus(ctx, id):
        mbonus=[0,0]
        balancing = 0.5
        lvl = Userdata.users[str(id)]['lvl']
        if Userdata.users[str(id)]['items']['left'] == {} and Userdata.users[str(id)]['items']['right'] == {}:
            att1 = att2 = dipl1 = dipl2 = 0
            balancing = 0.3
        if Userdata.users[str(id)]['items']['right'] != {}:
            if len(Userdata.users[str(id)]['items']['right'][list(Userdata.users[str(id)]['items']['right'].keys())[0]]["slot"]) == 2:
                att1 = att2 = dipl1 = dipl2 = 0
                balancing = 0.3
        try:
            weapon1 = list(Userdata.users[str(id)]['items']['left'].keys())[0]
        except IndexError:
            #fill with non-existing name, so the default value will be returned by the following .get(weapon...)
            weapon1 = "empty"
        try:
            weapon2 = list(Userdata.users[str(id)]['items']['right'].keys())[0]
        except IndexError:
            weapon2 = "empty"
        att1 = Userdata.users[str(id)]['items']['left'].get(weapon1, {'att':0})['att']
        dipl1 = Userdata.users[str(id)]['items']['left'].get(weapon1, {'cha':0})['cha']
        att2 = Userdata.users[str(id)]['items']['right'].get(weapon2, {'att':0})['att']
        dipl2 = Userdata.users[str(id)]['items']['right'].get(weapon2, {'cha':0})['cha']
        overall_balance = (1/math.cosh((att1+dipl1)-(att2+dipl2)))*1.2
        mbonus[0] = int(round(balancing*lvl*(-math.sinh((float(att1+att2)/10))+overall_balance)))
        mbonus[1] = int(round(balancing*lvl*(-math.sinh((float(dipl1+dipl2)/10))+overall_balance)))
        #print(att1,dipl1,att2,dipl2,overall_balance,-math.sinh((float(att1+att2)/10)),-math.sinh((float(dipl1+dipl2)/10)))
        return mbonus

    async def rage(ctx):
        user = ctx.author.id
        if Userdata.users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            return
        Userdata.users[str(user)]['class']['ability'] = True
        await ctx.send('**{}** is starting to froth at the mouth...🗯️'.format(ctx.author.display_name))
        return

    async def bless(ctx):
        user = ctx.author.id
        if Userdata.users[str(user)]['class']['ability'] == True:
            await ctx.send("Ability already in use.")
            return
        Userdata.users[str(user)]['class']['ability'] = True
        await ctx.send('**{}** is starting an inspiring sermon. 📜'.format(ctx.author.display_name))
        return

    async def heal(ctx,healer,user):
        d8 = random.randint(1,8)
        bonus = d8 + int(round(Userdata.users[str(healer.id)]['lvl']/5))
        if Userdata.users[str(user.id)]['hp'] + bonus <= Userdata.users[str(user.id)]['base_hp']:
            Userdata.users[str(user.id)]['hp'] += bonus
        else:
            Userdata.users[str(user.id)]['hp'] = int(Userdata.users[str(user.id)]['base_hp'])
        hp_pcnt = round((Userdata.users[str(user.id)]['hp']/Userdata.users[str(user.id)]['base_hp'])*100)
        if healer == user:
            await ctx.send("**{}** selfhealed for {} hitpoints ({}/{} {}%).".format(healer.display_name,bonus,Userdata.users[str(user.id)]['hp'],Userdata.users[str(user.id)]['base_hp'],hp_pcnt))
        else:
            healxp = bonus * int(round(Userdata.users[str(healer.id)]['lvl']/4))
            Userdata.users[str(healer.id)]['exp'] += healxp
            await ctx.send("**{}** healed **{}** for {} hitpoints ({}/{} {}%) and gained {}xp.".format(healer.display_name,user.display_name,bonus,Userdata.users[str(user.id)]['hp'],Userdata.users[str(user.id)]['base_hp'],hp_pcnt,healxp))
        return

    async def sing(ctx, *args):
        user = ctx.author.id
        #counting instruments Equipped and calculating instrument bonus
        i_count = 0
        if list(Userdata.users[str(user)]['items'].get('left', "Empty_slot")) in Treasure.instrument:
            i_count += 1
        if list(Userdata.users[str(user)]['items'].get('right', "Empty_slot")) == list(Userdata.users[str(user)]['items'].get('left', "Empty_slot")):
            pass
        elif list(Userdata.users[str(user)]['items'].get('right', "Empty_slot")) in Treasure.instrument:
            i_count += 1
        bonus_list = []
        if i_count == 1:
            bonus_list = [1.5,2]
        elif i_count == 2:
            bonus_list = [1.5,2,2.5,3]
        else:
            bonus_list = [1]
        bonus_modifier = random.choice(bonus_list)
        if bonus_modifier > 1:
            bonus_percent = "(+" + str((bonus_modifier-1)*100) + "% intrument bonus.)"
        else:
            bonus_modifier = ""
        if len(args) == 0: #user did not pass a song
            Userdata.users[str(user)]['class']['ability'] = True
            basebonus = random.randint(1,(Userdata.users[str(user)]['lvl']//2))*bonus_modifier
            Userdata.users[str(user)]['class'].update({"basebonus": basebonus})
            await ctx.send('♪♫♬ **{}** is whipping up a random performance. {} ♬♫♪'.format(ctx.author.display_name, bonus_modifier))
            return
        else:
            argstring = ''.join(map(str, args))
            level = Userdata.users[str(user)]['lvl']
            #n = int(hashlib.sha1(argstring.encode()).hexdigest(),16)
            n = abs(int(hashlib.sha1(argstring.encode()).hexdigest(),16)) % 10000000 #take last 7 digits to get first iteration between 0 and 63?
            basebonus, optimal = await Classes.calc_song(n, level, 0)
            Userdata.users[str(user)]['class']['ability'] = True
            Userdata.users[str(user)]['class'].update({"basebonus": basebonus})
            rating = round(basebonus/Userdata.users[str(user)]['lvl']*10)
            basebonus = basebonus*bonus_modifier #apply instrument bonus after song rating
            stars = ""
            for i in range(1, rating+1):
                stars += "★"
            for i in range(1, 10-rating+1):
                stars += "☆"
            #await ctx.send('♪♫♬ **{}** is singing \"{}\" [{}]. ♬♫♪ (Hash:{}; Bonus:{}; Optimum: {})'.format(ctx.author.display_name, " ".join(args), stars, n, basebonus, optimal))
            await ctx.send('♪♫♬ **{}** is singing \"{}\" [{}]. {} ♬♫♪'.format(ctx.author.display_name, " ".join(args), stars, bonus_modifier))
            if optimal == 0:
                return
            elif optimal-level <= 5:
                await ctx.send("This needs just a little more practice.")
            elif optimal-level <= 10:
                await ctx.send("This will get better with considerable time and effort.")
            elif optimal-level <= 20:
                await ctx.send("You can get there with a LOT of training.")
            else:
                await ctx.send("This is far beyond your current skill.")
            return

    pets = {"flitterwisp": {'name': "flitterwisp", 'bonus': 1.05, 'cha': 10},
            "hufflepuff": {'name': "hufflepuff", 'bonus': 1.1, 'cha': 12},
            "sylvan wolf": {'name': "sylvan wolf", 'bonus': 1.2, 'cha': 16},
            "zephyr cat": {'name': "zephyr cat", 'bonus': 1.2, 'cha': 16},
            "giggling imp": {'name': "giggling imp", 'bonus': 1.4, 'cha': 20},
            "pocket dragon": {'name': "pocket dragon", 'bonus': 1.5, 'cha': 30},
            }

    async def pet(ctx, flag):
        user = ctx.author.id
        if flag == "free":
            if Userdata.users[str(user)]['class']['ability'] != False:
                Userdata.users[str(user)]['class']['ability'] = False
                await ctx.send('**{}** relased his pet into the wild again.'.format(ctx.author.display_name))
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send('You have no pet to release.')
        elif flag == "forage":
            return await Treasure.open_chest(ctx,Userdata.users[str(user)]['class']['ability']['pet']['name'],'pet')
        else:
            if Userdata.users[str(user)]['class']['ability'] == False:
                await ctx.send('**{}** is trying to tame a pet.'.format(ctx.author.display_name))
                await asyncio.sleep(2)
                pet = random.choice(list(Classes.pets.keys()))
                roll = random.randint(1,20)
                await ctx.send('You are tracking a wild **{}** with a roll of 🎲({}).'.format(Classes.pets[pet]['name'], roll))
                await asyncio.sleep(1)
                dipl_value = roll + Userdata.users[str(user)]['cha'] + Userdata.users[str(user)]['skill']['cha']
                if roll == 1:
                    await ctx.send('But you stepped on a twig and scared it away.')
                    return None
                elif roll == 20:
                    await ctx.send('You happen to have its favorite food.')
                    dipl_value += 25
                if dipl_value > Classes.pets[pet]['cha']:
                    await ctx.send('You successfully tamed the {}.'.format(Classes.pets[pet]['name']))
                    return Classes.pets[pet]
                else:
                    await ctx.send('The {} escaped.'.format(Classes.pets[pet]['name']))
                    return None
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send('You already have a pet. Try foraging.')
                return None

    async def calc_song(n,lvl,prev):
        x = sum(int(digit) for digit in str(n))
        if x <= lvl:
            return x, prev
        else:
            return await Classes.calc_song(x,lvl,x)
