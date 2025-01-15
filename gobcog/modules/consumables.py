import random
import asyncio
import copy
import datetime
from redbot.core.utils.predicates import MessagePredicate
from redbot.core import bank
from .userdata import Userdata
from .adventure import Adventure
from .treasure import Treasure
from .alchemy import Alchemy
from .color import Color

class Consumables:
    #Name table to assign effects to consumables. Consumable items themselfes are defined in treasure.py
    consbles = {".potion_of_strength":{'type':"buff", 'attrib':["att"], 'min':3, 'max':10, 'duration':1, 'desc':"Increases your attack bonus for one fight."},
                    ".vial_of_aggression":{'type':"buff", 'attrib':["att"], 'min':1, 'max':5, 'duration':1, 'desc':"Small increase of your attack bonus for one fight."},
                    ".malevolent_vial":{'type':"buff", 'attrib':["att"], 'min':2, 'max':3, 'duration':5, 'desc':"Small increase of your attack bonus for 5 fights."},
                    ".potion_of_eloquence":{'type':"buff", 'attrib':["cha"], 'min':3, 'max':10, 'duration':1, 'desc':"Increases your diplomacy bonus for one fight."},
                    ".vial_of_wit":{'type':"buff", 'attrib':["cha"], 'min':1, 'max':5, 'duration':1, 'desc':"Small increase of your diplomacy bonus for one fight."},
                    ".cunning_vial":{'type':"buff", 'attrib':["cha"], 'min':2, 'max':3, 'duration':5, 'desc':"Small increase of your diplomacy bonus for 5 fights."},
                    "[phenomenal phial]":{'type':"buff", 'attrib':["att","cha"], 'min':2, 'max':8, 'duration':5, 'desc':"Small increase of both attack and diplomacy bonus for 5 fights."},
                    "[jacks pot]":{'type':"buff", 'attrib':["xp","money"], 'min':20, 'max':200, 'duration':1, 'desc':"Increase of both xp and cp bonus for the next fight."},
                    "[edible chance]":{'type':"buffchance", 'attrib':["xp","money"], 'min':10, 'max':100, 'duration':1, 'desc':"Chance of either a xp or cp gain bonus next fight."},
                    "four leaf clover":{'type':"buff", 'attrib':["luck"], 'min':5, 'max':15, 'duration':1, 'desc':"This will bestow good luck during the next fight or chest opening."},
                    "[luckworth essence]":{'type':"buff", 'attrib':["luck"], 'min':15, 'max':50, 'duration':5, 'desc':"This will bestow good luck during 5 fights or opening 5 chests."},
                    "[bottled fortune]":{'type':"buff", 'attrib':["luck"], 'min':50, 'max':100, 'duration':1, 'desc':"This will bestow exceptional luck during the next fight or chest opening."},
                    ".dust_of_midas":{'type':"buff", 'attrib':["money"], 'min':10, 'max':100, 'duration':1, 'desc':"Increases amount of cp gained for one fight."},
                    "[foliant of greed]":{'type':"buff", 'attrib':["money"], 'min':50, 'max':100, 'duration':10, 'desc':"Substantially increases amount of cp gained for 10 fights."},
                    ".scroll_of_learning":{'type':"buff", 'attrib':["xp"], 'min':10, 'max':100, 'duration':1, 'desc':"Increases amount of xp gained for one fight."},
                    "[foliant of wisdom]":{'type':"buff", 'attrib':["xp"], 'min':10, 'max':100, 'duration':10, 'desc':"Increases amount of xp gained for 10 fights."},
                    "[chaos egg]":{'type':"summon", 'attrib':["monster"], 'min':10, 'max':100, 'duration':1, 'desc':"Summons a random allied monster for the next fight."},
                    "[soul essence]":{'type':"augment", 'attrib':["item"], 'min':1, 'max':5, 'duration':10, 'desc':"This can be used to improve items."},
                    "[distilled charisma]":{'type':"buff", 'attrib':["cha"], 'min':10, 'max':20, 'duration':1, 'desc':"Strong buff to your diplomacy bonus for one fight."},
                    "[brutal philtre]":{'type':"buff", 'attrib':["att"], 'min':10, 'max':20, 'duration':1, 'desc':"Strong buff to your attack bonus for one fight."},
                    "bitter stew":{'type':"buff", 'attrib':["rest"], 'min':1, 'max':2, 'duration':1, 'desc':"Nourishing gruel. Horrible taste."},
                    ".sweet_stew":{'type':"buff", 'attrib':["rest"], 'min':2, 'max':5, 'duration':1, 'desc':"A sweet meal. Dental care not included."},
                    ".hearty_stew":{'type':"buff", 'attrib':["rest"], 'min':3, 'max':4, 'duration':1, 'desc':"Nourishing and artery hardening soup."},
                    ".salty_stew":{'type':"buff", 'attrib':["rest"], 'min':3, 'max':5, 'duration':2, 'desc':"A spicy soup. Toughening your sea legs, while raising blood pressARRRe."},
                    "[sweetbread]":{'type':"buff", 'attrib':["rest"], 'min':4, 'max':6, 'duration':1, 'desc':"Delicious bread, provides a good meal."},
                    "bandaid":{'type':"medicine", 'attrib':["hp"], 'min':1, 'max':4, 'duration':1, 'desc':"Small bandaid to mend little scratches."},
                    "bandages":{'type':"medicine", 'attrib':["hp"], 'min':2, 'max':6, 'duration':1, 'desc':"Bandages to mend wounds and set broken bones."},
                    ".potion_of_healing":{'type':"medicine", 'attrib':["hp"], 'min':4, 'max':10, 'duration':1, 'desc':"Standard 2d4+2 healing potion."},
                    "[potion of rejuvenation]":{'type':"medicine", 'attrib':["hp"], 'min':50, 'max':100, 'duration':1, 'desc':"Restores a % of your HP (min 50%)."},
                    "alchemy scroll":{'type':"read", 'attrib':["recipe"], 'min':1, 'max':1, 'duration':1, 'desc':"Studying the blurred scribbles might reveal an alchemical recipe."}
                }

    async def use_con(ctx, user, con):
        cons = copy.deepcopy(Consumables.consbles.get(con)) #deepcopy needed to not modify the original dict on buffchance
        if cons['type'] == "buffchance":
            cons['attrib'] = [random.choice(cons['attrib'])]
            cons['type'] = "buff"
        if cons['type'] == "buff":
            for a in cons['attrib']:
                if a == 'att' or a == 'cha':
                    bonus = random.randint(cons['min'],cons['max'])
                    Userdata.users[str(user.id)]['buffs'].update({a:{'bonus':bonus, 'duration':cons['duration']}})
                    attb = int(Userdata.users[str(user.id)]['skill']['att'])+ int(Userdata.users[str(user.id)]['buffs'].get('att', {'bonus':0})['bonus'])
                    chab = int(Userdata.users[str(user.id)]['skill']['cha'])+ int(Userdata.users[str(user.id)]['buffs'].get('cha', {'bonus':0})['bonus'])
                    if cons['duration'] == 1:
                        await ctx.send("Your {} gives you +{} {} for the next fight.".format(con,bonus,a.upper()))
                    else:
                        await ctx.send("Your {} gives you +{} {} for the next {} fights.".format(con,bonus,a.upper(),cons['duration']))
                    await ctx.send("Your new stats: **Attack**: {} [+{}], **Diplomacy**: {} [+{}].".format(Userdata.users[str(user.id)]['att'],attb,Userdata.users[str(user.id)]['cha'],chab))
                elif a == 'luck':
                    bonus = random.randint(cons['min'],cons['max'])
                    Userdata.users[str(user.id)]['buffs'].update({a:{'bonus':bonus, 'duration':cons['duration']}})
                    if cons['duration'] == 1:
                        await ctx.send("Your {} yielded {}% increased luck during the next fight or chest opening.".format(con,bonus))
                    else:
                        await ctx.send("Your {} yielded {}% increased luck during {} fights or chest openings.".format(con,bonus,cons['duration']))
                elif a == 'rest':
                    bonus = random.randint(cons['min'],cons['max'])
                    Userdata.users[str(user.id)]['buffs'].update({a:{'bonus':bonus, 'duration':cons['duration']}})
                    if cons['duration'] == 1:
                        await ctx.send("Your {} yielded {}x faster recovery during the next rest.".format(con,bonus))
                    else:
                        await ctx.send("Your {} yielded {}x faster recovery during {} rests.".format(con,bonus,cons['duration']))
                elif a == 'xp' or a == 'money':
                    bonus = random.randint(cons['min'],cons['max'])
                    Userdata.users[str(user.id)]['buffs'].update({a:{'bonus':bonus, 'duration':cons['duration']}})
                    if cons['duration'] == 1:
                        await ctx.send("Your {} gives you {}% more {} for the next fight.".format(con,bonus,a))
                    else:
                        await ctx.send("Your {} gives you {}% more {} for the next {} fights.".format(con,bonus,a,cons['duration']))
            return True
        elif cons['type']== "augment":
            bkpk = []
            consumed = ""
            forgeables = len(Userdata.users[str(user.id)]['items']['backpack']) - sum("{.:'" in x for x in Userdata.users[str(user.id)]['items']['backpack'])- sum("[wanderring]" in x for x in Userdata.users[str(user.id)]['items']['backpack'])
            if forgeables < 1:
                await ctx.send("You need at least one augmentable item in your backpack.")
                return False
            for item in Userdata.users[str(user.id)]['items']['backpack']:
                if "{.:'" not in item and ")*" not in item and "[wanderring]" not in item:
                    if len(Userdata.users[str(user.id)]['items']['backpack'][item]['slot']) == 1:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']) + Color.none +")"+ Color.yellow + " ["+ Userdata.users[str(user.id)]['items']['backpack'][item]['slot'][0] + " slot]\n")
                    else:
                        bkpk.append(Color.get_color(item) + " (" + Color.red + "ATT " + Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['att']*2) + Color.none + " /" + Color.blue + " DPL "+ Color.green + str(Userdata.users[str(user.id)]['items']['backpack'][item]['cha']*2) + Color.none +")"+ Color.yellow + " [two handed]\n")
            pile = " " + "".join(bkpk)
            if len(pile) > 1900: #split dangerously long texts into chunks.
                chunks = []
                while pile:
                    if len(pile) <= 1900:
                        chunks.append(pile)
                        break
                    split_index = pile.rfind("\n", 0, 1900)
                    if split_index == -1:
                        # The chunk is too big, so everything until the next newline is deleted
                        try:
                            pile = pile.split("\n", 1)[1]
                        except IndexError:
                            # No "\n" in textline, i.e. the end of the input text was reached
                            break
                    else:
                        chunks.append(pile[:split_index+1])
                        pile = pile[split_index+1:]
                await ctx.send("```ansi\n"+Color.blue+"[{}´s augmentables] \n\n```".format(ctx.author.display_name))
                for chunk in chunks:
                    await ctx.send("```ansi\n" + chunk + "```")
                    await asyncio.sleep(0.3)
            else:
                await ctx.send("```ansi\n"+Color.blue+"[{}´s augmentables] \n\n".format(ctx.author.display_name) + pile + " \n\n```")
            await ctx.send("```ansi\n\n (Reply with the full or partial name of the item to select for augmenting. Try to be specific.)```")
            try:
                reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("I don't have all day, you know.")
                return False
            item1 = {}
            lookup = list(x for x in Userdata.users[str(user.id)]['items']['backpack'] if reply.content.lower() in x.lower() and "{.:'" not in x and ")*" not in x and "[wanderring]" not in x)
            if len(lookup) > 1:
                text = "```ansi\n"
                for num, name in enumerate(lookup, start=1):
                    text += ("[{}]: {}\n".format(num, Color.get_color(name)))
                text += "```"
                await ctx.send("I found these items matching that name:\n{}Please reply with a number from the list.".format(text))
                try:
                    reply = await ctx.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("I don't have all day, you know.")
                    return False
                if reply.content.isdigit() and (int(reply.content)-1) < len(lookup) and int(reply.content) > 0:
                    idx = int(reply.content)-1
                    if  "{.:'" not in lookup[idx] and ")*" not in lookup[idx] and "[wanderring]" not in lookup[idx]:
                        item1 = Userdata.users[str(user.id)]['items']['backpack'].get(lookup[idx])
                        consumed = lookup[idx]
                    else:
                        await ctx.send("This item cannot be augmented.")
                        return False
                else:
                    await ctx.send("Sorry, but there was something wrong with that reply.")
                    return False
            elif len(lookup) == 0:
                await ctx.send("I could not find that item, check your spelling.")
                return False
            else: #len(lookup) equals 1 item
                if  "{.:'" not in lookup[0] and ")*" not in lookup[0] and "[wanderring]" not in lookup[0]:
                    item1 = Userdata.users[str(user.id)]['items']['backpack'].get(lookup[0])
                    consumed = lookup[0]
                else:
                    await ctx.send("This item cannot be augmented.")
                    return False
            roll = random.randint(1,20)
            if roll == 1:
                modifier = -1
            if roll > 1 and roll <= 10:
                modifier = 1
            if roll > 10 and roll <= 17:
                modifier = 2
            if roll == 18:
                modifier = 3
            if roll == 19:
                modifier = 4
            if roll == 20:
                modifier = 5
            newatt = int(item1['att'])+modifier
            newdip = int(item1['cha'])+modifier
            prefix = "+"
            if modifier < 0:
                prefix = ""
            if len(item1['slot']) == 2:
                await ctx.send('Your augment roll was 🎲({}).\nYour {} augmented to {}{} and will have {}🗡 and {}🗨.'.format(roll,consumed,prefix,modifier,newatt*2,newdip*2))
            else:
                await ctx.send('Your augment roll was 🎲({}).\nYour {} augmented to {}{} and will have {}🗡 and {}🗨.'.format(roll,consumed,prefix,modifier,newatt,newdip))
            name = consumed + "({}{})*".format(prefix,modifier)
            newitem = {"itemname": name,"item": {"slot":item1['slot'],"att":newatt,"cha":newdip}}
            try:
                Userdata.users[str(user.id)]['items']['backpack'].pop(consumed)
            except:
                await ctx.send("Hey where did that item go now?")
            if newitem['itemname'] in Userdata.users[str(user.id)]['items']['backpack'].keys() or newitem['itemname'] in Userdata.users[str(user.id)]['lootfilter']:
                price = await Treasure.t_sell(user,newitem)
                await bank.deposit_credits(user, price)
                await ctx.send("**{}** sold {} for {} copperpieces.".format(user.display_name,newitem['itemname'],price))
            else:
                Userdata.users[str(user.id)]['items']['backpack'].update({newitem['itemname']: newitem['item']})
            await Userdata.save()
            return True
        elif cons['type'] == "summon":
            attrib = random.choice(list(Adventure.attribs.keys()))
            if int(datetime.date.today().strftime("%d")) >= 24 and int(datetime.date.today().strftime("%m")) == 10:
                flavoricon = random.choice([" 🎃"," 👻"," 🦇"," 🕸️", " 💀"])
                monster = random.choice(list(Adventure.poke_monsters.keys()))
                att = int(Adventure.poke_monsters[monster]["str"]*Adventure.attribs[attrib][0])
                cha = int(Adventure.poke_monsters[monster]["dipl"]*Adventure.attribs[attrib][1])
            else:
                flavoricon = ""
                monster = random.choice(list(Adventure.monsters.keys()))
                att = int(Adventure.monsters[monster]["str"]*Adventure.attribs[attrib][0])
                cha = int(Adventure.monsters[monster]["dipl"]*Adventure.attribs[attrib][1])
            Userdata.users[str(user.id)]['buffs'].update({cons['attrib'][0]:{'bonus':{'att':att,'cha':cha}, 'duration':cons['duration']}})
            await ctx.send("**{}** summoned a{}{} {} (🗡 {} | 🗨 {}).".format(user.display_name,flavoricon,attrib,monster,att,cha))
            return True
        elif cons['type'] == "medicine":
            bonus = random.randint(cons['min'],cons['max'])
            if "rejuvenation" in con:
                bonus = int(round(Userdata.users[str(user.id)]['base_hp']*bonus/100))
            if Userdata.users[str(user.id)]['hp'] + bonus <= Userdata.users[str(user.id)]['base_hp']:
                Userdata.users[str(user.id)]['hp'] += bonus
            else:
                Userdata.users[str(user.id)]['hp'] = int(Userdata.users[str(user.id)]['base_hp'])
            hp_pcnt = round((Userdata.users[str(user.id)]['hp']/Userdata.users[str(user.id)]['base_hp'])*100)
            await ctx.send("Your {} healed you for {} hitpoints ({}/{} {}%).".format(con,bonus,Userdata.users[str(user.id)]['hp'],Userdata.users[str(user.id)]['base_hp'],hp_pcnt))
            return True
        elif cons['type'] == "read": #maybe add chances of misreading or partial reading, obfuscate recipes, riddle form, pain to berserkers?
            if Userdata.users[str(user.id)]['class']['name']=="Berserker":
                crapfactor = random.choice([0,1,1,2,2,2,2,2,2,2])
                if crapfactor != 0:
                    await ctx.send("As a berserker you are not at home with reading stuff...")
            else:
                crapfactor = random.choice([0,1,1,1,1,2,2,2,2,2])
            result = random.choice(list(Alchemy.recipes.keys()))
            yields = Alchemy.recipes[result]['yields']
            recipe = ''.join(" " + x if x.isupper() else x for x in result).strip(" ").split(" ")
            indices = [i for i, x in enumerate(recipe) if x == ""]
            killlist = []
            for e in indices:
                recipe[e-1]= recipe[e-1] + " " + recipe[e+1]
                killlist.append(recipe[e+1])
                killlist.append(recipe[e])
            for e in killlist:
                recipe.remove(e)   #search and destroy copied elements without iterating over a list that changes size.
            recipe[:] = (value for value in recipe if value != "") #strip empty elements
            recipe = " and ".join([", ".join(recipe[:-1]),recipe[-1]])
            if crapfactor == 1:
                scr_recipe = await Consumables.scramble(recipe)
                await ctx.send("It seems to be a recipe for {}: {} ({}-{} uses).".format(yields,scr_recipe,Alchemy.recipes[result]['uses'][0],Alchemy.recipes[result]['uses'][1]))
                return True
            elif crapfactor == 2:
                scr_recipe = await Consumables.Xscramble(recipe)
                yields = await Consumables.Xscramble(yields)
                await ctx.send("A very badly damaged and smudged recipe for {}?. {}.".format(yields,scr_recipe))
                return True
            else:
                scr_recipe = recipe
                await ctx.send("You deciphered a recipe for {}: {} ({}-{} uses).".format(yields,scr_recipe,Alchemy.recipes[result]['uses'][0],Alchemy.recipes[result]['uses'][1]))
                return True


    async def Xscramble(recipe):
        wordlist = recipe.split()
        for idx, word in enumerate(wordlist):
            word = ''.join(random.sample(word + "X"*len(word), len(word)))
            charlist = list(word)
            random.shuffle(charlist)
            wordlist[idx] = ''.join(charlist)
        return ' '.join(wordlist)

    async def scramble(recipe):
        wordlist = recipe.split()
        for idx, word in enumerate(wordlist):
            charlist = list(word[1:-1])
            random.shuffle(charlist)
            wordlist[idx] = word[0] + ''.join(charlist) + word[-1]
        return ' '.join(wordlist)
