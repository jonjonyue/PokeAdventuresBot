# bot.py
import os
import random

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
util = db["util"]

client = discord.Client()
bot = commands.Bot(command_prefix='-')

# Register command for trainers
@bot.command(name='start', help='Starts your pokémon adventure')
async def start(ctx):
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
        post = {"_id": ctx.author.id, "initiated": 0, "_title":"", "_pokemon":[]}
        trainers.insert_one(post)

        embed.add_field(name='Generation I:', value='Charmander | Squirtle | Bulbasaur')
        embed.set_footer(text='Note: Trading in-game content for IRL money or using a form of automation such as macros or selfbots to gain an unfair advantage will result in a ban from the bot. Don\'t cheat!')
        await ctx.send(embed=embed)
    else:
        await ctx.send('you are already registered')


# Pick first pokemon
@bot.command(name='pick', help='Used to pick your first pokémon')
async def pick(ctx, pokeChoice):

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
    util.find_one_and_update({ '_name': '_pidCount'}, { '$inc': { '_pidCount': 1}})
    trainers.update_one({'_id': ctx.author.id}, {'$set': {'initiated': 1}}, upsert=False)
    trainers.update_one({'_id': ctx.author.id}, {'$push': {'_pokemon': poke}}, upsert=True)


    message = 'Congratulations! Your ' + pokeChoice + ' seems to like you. I hope you have many adventures together to come. Use `-info` to see more about your pokémon.'
    await ctx.send(message)

bot.run(TOKEN)