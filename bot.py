import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

import twitter
import json

import datetime

import urllib.request
import uuid

from twitter_monitor import add_user, remove_user

from subprocess import call

load_dotenv()

api = twitter.Api(consumer_key=os.getenv('TWTR_CONSUMER_KEY'),
                  consumer_secret=os.getenv('TWTR_CONSUMER_SECRET'),
                  access_token_key=os.getenv('TWTR_ACCESS_KEY'),
                  access_token_secret=os.getenv('TWTR_ACCESS_SECRET'))

TOKEN = os.getenv('DISCORD_TOKEN')

monitoring_loc = os.getenv('MONITORING_JSON_PATH')
profile_cache_dir = os.getenv('PROFILE_PIC_CACHE_DIR')

bot = commands.Bot(command_prefix='!')

def strip_trailing_at(username):
    if username[0] == '@':
        return username[1:]

    return username

@bot.command(name='monitor', help='Adds user to monitor')
async def add_user(ctx, username : str):
    username = strip_trailing_at(username)

    file = None

    try:
        # Get user id by username
        user = api.GetUser(screen_name=username)
        user_id = user.id_str
        user_profile_url = user.profile_image_url_https

        # Open monitoring.json and add user
        with open(monitoring_loc) as json_file:
            json_decoded = json.load(json_file)

        if user_id not in json_decoded:
            json_decoded[user_id] = []

            with open(monitoring_loc, 'w') as json_file:
                json.dump(json_decoded, json_file)

            # Download to cache
            filename = profile_cache_dir + '/' + str(uuid.uuid4()) + '.jpg'
            urllib.request.urlretrieve(user_profile_url, filename)

            # Create file handle
            file = discord.File(filename)

            add_user(username, user_profile_url)

            # Run monitoring script
            call(["python", "twitter_monitor.py"])

            response = "```yaml\n@{0}\n```Account **added** successfully.\nToday at {1}".format(username, datetime.datetime.now().strftime("%I:%M %p"))
        else:
            response = "```yaml\n@{0}\n```\nAccount already added.".format(username)
    except:
        response = "```yaml\n@{0}\n```\nCould not add account. Please try again.".format(username)
        
    if file:
        await ctx.send(response, file=file)
    else:
        await ctx.send(response)

@bot.command(name='remove', help='Remove user from being monitored')
async def remove_user(ctx, username : str):
    username = strip_trailing_at(username)

    file = None

    try:
        # Get user id by username
        user = api.GetUser(screen_name=username)
        user_id = user.id_str
        user_profile_url = user.profile_image_url_https
        
        with open(monitoring_loc) as json_file:
            json_decoded = json.load(json_file)

        if user_id in json_decoded:
            # Remove user from monitoring.json
            del json_decoded[user_id]

            # Resave
            with open(monitoring_loc, 'w') as json_file:
                json.dump(json_decoded, json_file)

            # Download to cache
            filename = profile_cache_dir + '/' + str(uuid.uuid4()) + '.jpg'
            urllib.request.urlretrieve(user_profile_url, filename)

            # Create file handle
            file = discord.File(filename)

            remove_user(username, user_profile_url)

            # Run monitoring script
            call(["python", "twitter_monitor.py"])

            response = "```yaml\n@{0}\n```Account **removed** successfully.\nToday at {1}".format(username, datetime.datetime.now().strftime("%I:%M %p"))
        else:
            response = "```yaml\n@{0}\n```\nAccount has not been added yet.".format(username)
    except:
        response = "```yaml\n@{0}\n```\nCould not remove account. Please try again.".format(username)
        
    if file:
        await ctx.send(response, file=file)
    else:
        await ctx.send(response)

bot.run(TOKEN)
