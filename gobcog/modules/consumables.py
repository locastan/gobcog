import random
import asyncio
from redbot.core.utils.predicates import MessagePredicate
from .userdata import Userdata
from .adventure import Adventure

class Consumables:
    #Name table to assign effects to consumables. Consumable items themselfes are defined in treasure.py
    # need to figure out durations, if only for number of fights or opened chests for example.
    #soul essence is a special consumable only available to tinkerers. Chance to get one when dismantling a device.
    consbles = {".potion_of_strength":{'type':"buff", 'attrib':"att", 'min':1, 'max':4, 'duration':1, 'desc':"Increases your attack bonus for one fight."},
                    ".vial_of_strength":{'type':"buff", 'attrib':"att", 'min':1, 'max':2, 'duration':1, 'desc':"Small increase of your attack bonus for one fight."},
                    ".potion_of_eloquence":{'type':"buff", 'attrib':"cha", 'min':1, 'max':4, 'duration':1, 'desc':"Increases your diplomacy bonus for one fight."},
                    ".vial_of_eloquence":{'type':"buff", 'attrib':"cha", 'min':1, 'max':2, 'duration':1, 'desc':"Small increase of your diplomanc bonus for one fight."},
                    "four leaf clover":{'type':"buff", 'attrib':"luck", 'min':5, 'max':15, 'duration':1, 'desc':"This will bestow good luck during the next fight or chest opening."},
                    "[luckworth essence]":{'type':"buff", 'attrib':"luck", 'min':15, 'max':50, 'duration':5, 'desc':"This will bestow good luck during 5 fights or opening 5 chests."},
                    ".dust_of_midas":{'type':"buff", 'attrib':"money", 'min':10, 'max':100, 'duration':1, 'desc':"Increases amount of cp gained for one fight."},
                    ".scroll_of_learning":{'type':"buff", 'attrib':"xp", 'min':10, 'max':100, 'duration':1, 'desc':"Increases amount of xp gained for one fight."},
                    "[foliant of wisdom]":{'type':"buff", 'attrib':"xp", 'min':10, 'max':100, 'duration':10, 'desc':"Increases amount of xp gained for 10 fights."},
                    "[chaos egg]":{'type':"summon", 'attrib':"monster", 'min':10, 'max':100, 'duration':1, 'desc':"Summons a random allied monster for the next fight."},
                    "[soul essence]":{'type':"augment", 'attrib':"item", 'min':1, 'max':5, 'duration':10, 'desc':"This can be used to improve items."}
                }

    async def use_con(ctx, user, con):
        cons = Consumables.consbles.get(con)
        if cons['type'] == "buff":
            if cons['attrib'] == 'att' or cons['attrib'] == 'cha':
                bonus = random.randint(cons['min'],cons['max'])
                Userdata.users[str(user.id)]['buffs'].update({cons['attrib']:{'bonus':bonus, 'duration':cons['duration']}})
                attb = int(Userdata.users[str(user.id)]['skill']['att'])+ int(Userdata.users[str(user.id)]['buffs'].get('att', {'bonus':0})['bonus'])
                chab = int(Userdata.users[str(user.id)]['skill']['cha'])+ int(Userdata.users[str(user.id)]['buffs'].get('cha', {'bonus':0})['bonus'])
                await ctx.send("Your new stats: **Attack**: {} [+{}], **Diplomacy**: {} [+{}].".format(Userdata.users[str(user.id)]['att'],attb,Userdata.users[str(user.id)]['cha'],chab))
                return True
            elif cons['attrib'] == 'luck':
                bonus = random.randint(cons['min'],cons['max'])
                Userdata.users[str(user.id)]['buffs'].update({cons['attrib']:{'bonus':bonus, 'duration':cons['duration']}})
                if cons['duration'] == 1:
                    await ctx.send("Your {} yielded {}% increased luck during the next fight or chest opening.".format(con,bonus,cons['duration']))
                else:
                    await ctx.send("Your {} yielded {}% increased luck during {} fights or chest openings.".format(con,bonus,cons['duration']))
                return True
            elif cons['attrib'] == 'xp' or cons['attrib'] == 'money':
                bonus = random.randint(cons['min'],cons['max'])
                Userdata.users[str(user.id)]['buffs'].update({cons['attrib']:{'bonus':bonus, 'duration':cons['duration']}})
                if cons['duration'] == 1:
                    await ctx.send("Your {} gives you {}% more {} for the next fight.".format(con,bonus,cons['attrib']))
                else:
                    await ctx.send("Your {} gives you {}% more {} for the next {} fights.".format(con,bonus,cons['attrib'],cons['duration']))
                return True
        elif cons['type']== "augment":
            bkpk = ""
            consumed = ""
            forgeables = len(Userdata.users[str(user.id)]['items']['backpack']) - sum("{.:'" in x for x in Userdata.users[str(user.id)]['items']['backpack'])
            if forgeables < 1:
                await ctx.send("You need at least one augmentable item in your backpack.")
                return False
            for item in Userdata.users[str(user.id)]['items']['backpack']:
                if "{.:'" not in item:
                    if len(Userdata.users[str(user.id)]['items']['backpack'][item]['slot']) == 1:
                        bkpk += " - " + item + " - (ATT: "+ str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']) + " | DPL: "+ str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']) +" ["+ Userdata.users[str(user.id)]['items']['backpack'][item]['slot'][0] + " slot])\n"
                    else:
                        bkpk += " - " + item + " -(ATT: "+ str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']*2) + " | DPL: "+ str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']*2) +" [two handed])\n"
            await ctx.send(
                "```css\n[{}'s augmentables] \n\n```".format(
                    ctx.author.display_name
                ) + "```css\n" + bkpk + "\n (Reply with the full or partial name of the item for augmentation. Try to be specific.)```"
            )
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("I don't have all day, you know.")
                return False
            item1 = {}
            for item in Userdata.users[str(user.id)]['items']['backpack']:
                if reply.content.lower() in item:
                    if  "{.:'" not in item and ")*" not in item:
                        item1 = Userdata.users[str(user.id)]['items']['backpack'].get(item)
                        consumed = item
                        break
                    else:
                        await ctx.send("Devices and already augmented items cannot be augmented.")
                        return False
            if item1 == {}:
                await ctx.send("I could not find that item, check your spelling.")
                return False
            roll = random.randint(1,20)
            if roll == 1:
                modifier = -1
            if roll > 1 and roll <= 10:
                modifier = 1
            if roll > 10 and roll <= 16:
                modifier = 2
            if roll == 17:
                modifier = 3
            if roll >= 18 and roll <= 19:
                modifier = 4
            if roll == 20:
                modifier = 5
            newatt = int(item1['att'])+modifier
            newdip = int(item1['cha'])+modifier
            prefix = "+"
            if modifier < 0:
                prefix = ""
            if len(item1['slot']) == 2:
                await ctx.send('Your forging roll was 🎲({}).\nYour weapon is now a {}{} item and will have {}🗡 and {}🗨.'.format(roll,prefix,modifier,newatt*2,newdip*2))
            else:
                await ctx.send('Your forging roll was 🎲({}).\nYour weapon is now a {}{} item and will have {}🗡 and {}🗨.'.format(roll,prefix,modifier,newatt,newdip))
            name = consumed + ":({}{})*".format(prefix,modifier)
            newitem = {"itemname": name,"item": {"slot":item1['slot'],"att":newatt,"cha":newdip}}
            Userdata.users[str(user.id)]['items']['backpack'].pop(consumed)
            Userdata.users[str(user.id)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
            await Userdata.save()
            return True
        elif cons['type'] == "summon":
            attrib = random.choice(list(Adventure.attribs.keys()))
            monster = random.choice(list(Adventure.monsters.keys()))
            att = int(Adventure.monsters[monster]["str"]*Adventure.attribs[attrib][0])
            cha = int(Adventure.monsters[monster]["dipl"]*Adventure.attribs[attrib][1])
            Userdata.users[str(user.id)]['buffs'].update({cons['attrib']:{'bonus':{'att':att,'cha':cha}, 'duration':cons['duration']}})
            await ctx.send("**{}** summoned a{} {} (🗡 {} | 🗨 {}).".format(user.display_name,attrib,monster,att,cha))
            return True
