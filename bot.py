# bot.py
import os
import random
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

import pymongo
from pymongo import MongoClient

import urllib.parse

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

cluster = MongoClient(os.getenv('MONGODB_URL'))
db = cluster["pokemon_bot"]
trainers = db["trainers"]
pokemon = db["pokemon"]
routes = db["routes"]
util = db["util"]

client = discord.Client()
bot = commands.Bot(command_prefix='-')

activePoke = {
    'pokeName':"",
    'level':0,
    'health':0,
    'attack':0,
    'spattack':0,
    'defense':0,
    'spdefense':0,
    'speed':0,
    '_pid':0,
    'isActive':0,
    'photoURL':""
}

# Register command for trainers
@bot.command(name='start', help='Starts your pokémon adventure')
async def start(ctx):
    if isDMChannel:
        return
    title = "Hello " + ctx.author.name
    embed = discord.Embed(
        title = title,
        description = '**Welcome to the world of pokémon!** \n To begin your adventure, choose one of these pokémon with the `-pick <pokemon>` command, like this: `-pick squirtle`',
        color = discord.Color.green()
    )

    embed.set_author(name='Professor Kitty',
    icon_url='https://cdn.discordapp.com/attachments/719996777633415240/719996801133969528/tofuKingtransparent-cropped.png')

    myquery = { "_id": ctx.author.id } # Query to see if they are registered, if not, register them
    if (trainers.count_documents(myquery) == 0):
        post = {"_id": ctx.author.id, "initiated": 0, "_title":"", "_pokemon":[], "_party":[], "pcount":0, "routes":[]}
        trainers.insert_one(post)

        embed.add_field(name='Generation I:', value='Charmander | Squirtle | Bulbasaur')
        embed.set_footer(text='Note: Trading in-game content for IRL money or using a form of automation such as macros or selfbots to gain an unfair advantage will result in a ban from the bot. Don\'t cheat!')
        await ctx.send(embed=embed)
    else:
        await ctx.send('you are already registered')


# Pick first pokemon
@bot.command(name='pick', help='Used to pick your first pokémon')
async def pick(ctx, pokeChoice):
    if isDMChannel:
        return
    pokeChoice = pokeChoice.capitalize()
    # check if they are in registering state
    query = { '_id': ctx.author.id }
    if (trainers.count_documents(query) == 0):
        await ctx.send('Please use `-start` to begin your adventure.')
        return

    trainer = trainers.find_one(query)
    if (trainer['initiated'] == 1):
        await ctx.send("You have already picked your first pokémon! Go on your adventure!")
        return

    # check vs pokemon names
    if (pokemon.count_documents({'pokeName': pokeChoice}) == 0 or (pokeChoice != 'Charmander' and pokeChoice != 'Squirtle' and pokeChoice != 'Bulbasaur')):
        await ctx.send('Please pick a valid pokemon')
        return
    
    poke = pokemon.find_one({ 'pokeName': pokeChoice})
    poke["_pid"] = util.find_one({ '_name': '_pidCount'})["_pidCount"]
    poke["level"] = 5
    poke["_ptid"] = trainer['pcount'] + 1
    # TODO: randomize pokemon stats
    util.find_one_and_update({ '_name': '_pidCount'}, { '$inc': { '_pidCount': 1}})
    trainers.update_one({'_id': ctx.author.id}, {'$set': {'initiated': 1}}, upsert=False)
    trainers.update_one({'_id': ctx.author.id}, {'$push': {'_pokemon': poke}}, upsert=True)
    trainers.update_one({'_id': ctx.author.id}, {'$inc': {'pcount': 1}}, upsert=True)

    # add new pokemon to party
    trainers.update_one({'_id': ctx.author.id}, {'$push': {'_party': {'_pid':poke['_pid']}}}, upsert=True)


    message = 'Congratulations! Your ' + pokeChoice + ' seems to like you. I hope you have many adventures together to come. Use `-info` to see more about your pokémon.'
    await ctx.send(message)

@bot.command(name='info', help='see detailed information on your active pokemon')
async def info(ctx, *ptid):
    if isDMChannel:
        return
    # Getting pokemon information
    trainer = trainers.find_one({'_id': ctx.author.id})

    # If id arg was given, get the specific pokemon info
    if (len(ptid) > 0):
        for poke in trainer['_pokemon']:
            if (str(poke['_ptid']) == str(ptid[0])):
                activePoke = poke
                break
    # if not, get the current selected pokemon info
    else:
        targetid = trainer['_party'][0]['_pid']
        for poke in trainer['_pokemon']:
            if (poke['_pid'] == targetid):
                activePoke = poke
                break


    # Setting up Embed
    title = '**Level ' + str(activePoke['level']) + ' ' + activePoke['pokeName'] + "**"
    embed = discord.Embed(
        title = title,
        description = '0/300XP\n**HP:** ' + str(activePoke['health']) + 
        "\n **Attack:** " + str(activePoke['attack']) +
        "\n **Sp. Attack:** " + str(activePoke['spattack']) +
        "\n **Defense:** " + str(activePoke['defense']) +
        "\n **Sp. Defense:** " + str(activePoke['spdefense']) +
        "\n **Speed:** " + str(activePoke['speed']),
        color = discord.Color.green()
    )
    footer = "Selected Pokémon: " + str(activePoke["_ptid"]) + "/" + str(trainer["pcount"])
    embed.set_footer(text=footer)
    embed.set_image(url=activePoke['photoURL'])
    embed.set_author(name='Professor Kitty',
    icon_url='https://cdn.discordapp.com/attachments/719996777633415240/719996801133969528/tofuKingtransparent-cropped.png')

    await ctx.send(embed=embed)

# Pokemon Listing
@bot.command(name='checkpc', help='List all your pokemon')
async def listPokes(ctx):
    if isDMChannel:
        return

    trainer = trainers.find_one({'_id': ctx.author.id})
    pokeListStr = ""
    for poke in trainer['_pokemon']:
        pokeListStr += "**" + poke['pokeName'] + "** | Level: " + str(poke['level']) + " | ID: " + str(poke['_ptid']) + "\n"
    title = '**Your pokémon:**'
    embed = discord.Embed(
        title = title,
        description = pokeListStr,
        color = discord.Color.green()
    )
    embed.set_image(url=activePoke['photoURL'])
    embed.set_author(name='Professor Kitty',
    icon_url='https://cdn.discordapp.com/attachments/719996777633415240/719996801133969528/tofuKingtransparent-cropped.png')

    await ctx.send(embed=embed)

# Catching pokemon for testing purposes
@bot.command(name='catch')
async def catchPoke(ctx, arg):
    if isDMChannel:
        return
    pokeName = arg.capitalize()
    trainer = trainers.find_one({'_id': ctx.author.id})

    # check vs pokemon names
    if (pokemon.count_documents({'pokeName': pokeName}) == 0):
        await ctx.send('That is not a valid pokemon name D:')
        return

    poke = pokemon.find_one({ 'pokeName': pokeName})
    poke["_pid"] = util.find_one({ '_name': '_pidCount'})["_pidCount"]
    poke["level"] = 5
    poke["_ptid"] = trainer['pcount'] + 1
    util.find_one_and_update({ '_name': '_pidCount'}, { '$inc': { '_pidCount': 1}})
    trainers.update_one({'_id': ctx.author.id}, {'$push': {'_pokemon': poke}}, upsert=True)
    trainers.update_one({'_id': ctx.author.id}, {'$inc': {'pcount': 1}}, upsert=True)

    await ctx.send("You caught a " + pokeName + "!")


# Route Management
@bot.command(name='route', help='Gets info on the chosen route')
async def routeInfo(ctx, ridNo):
    if isDMChannel:
        return
    if (ridNo.isnumeric()):
        if (routes.count_documents({'ridNo': ridNo}) == 0):
            await ctx.send('The given route number is invalid. Please ask about a valid route :)')
            return
    else:
        await ctx.send('Please input a route number not a bunch letters please ;-;')
        return

    route = routes.find_one({'ridNo': ridNo})

    # Setting up Embed
    title = '**' + route['routeName'] + " info**"
    embed = discord.Embed(
        title = title,
        description = route['desc'],
        color = discord.Color.green()
    )

    # Setup route embed
    connectionEmbed = ""
    for routeName in route['connections']:
        connectionEmbed += routeName['routeName'] + "\n"
    embed.add_field(name='Connects to:', value=connectionEmbed)

    # Setup pokemon list embed
    pokemonEmbed = ""
    for poke in route['pokemon']:
        pokemonEmbed += pokemon.find_one({'idNo': poke['idNo']})['pokeName'] + "\n"
    embed.add_field(name='Pokemon Sightings:', value=pokemonEmbed)

    footer = "Selected Route: " + route['routeName']
    embed.set_footer(text=footer)
    embed.set_image(url=route['photoURL'])
    embed.set_author(name='Professor Kitty',
    icon_url='https://cdn.discordapp.com/attachments/719996777633415240/719996801133969528/tofuKingtransparent-cropped.png')

    await ctx.send(embed=embed)

@bot.command(name='explore', help='explore a route. Usage `-explore 1`')
async def exploreRoute(ctx, ridNo):

    if (ridNo.isnumeric()):
        if (routes.count_documents({'ridNo': ridNo}) == 0):
            await ctx.send('The given route number is invalid. Please ask about a valid route :)')
            return
    else:
        await ctx.send('Please input a route number not a bunch letters please ;-;')
        return

    route = routes.find_one({'ridNo': ridNo})
     # Setting up Embed
    title = '**Exploring ' + route['routeName'] + " **"
    embed = discord.Embed(
        title = title,
        description = route['desc'],
        color = discord.Color.green()
    )

    footer = "Selected Route: " + route['routeName']
    embed.set_footer(text=footer)
    embed.set_image(url=route['photoURL'])
    embed.set_author(name='Professor Kitty',
    icon_url='https://cdn.discordapp.com/attachments/719996777633415240/719996801133969528/tofuKingtransparent-cropped.png')
    await ctx.author.send(embed=embed)
    await ctx.author.send('Please type `enter` to begin your exploration.')

    timeout = time.time() + 60
    gotDM = False
    while not gotDM and time.time() < timeout:
        msg = await bot.wait_for('message', timeout=60)
        if msg:
            if isDMChannel(msg.channel) and msg.author == ctx.author:
                if msg.content == 'enter':
                    await msg.channel.send('Got your message!')
                    gotDM = True
                    break
                else:
                    await ctx.author.send('Please use `enter` to begin your exploration.')
    if not gotDM:
        ctx.author.send('Your exploration has timed out, please try again')

# Checks if the given channel is a private message or not
def isDMChannel(channel):
    return isinstance(channel, discord.channel.DMChannel)

bot.run(TOKEN)
