# bot.py
import os
import re 

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MONITOR_CHANNEL_ID = os.getenv('MONITOR_CHANNEL_ID')
LEADERBOARD_CHANNEL_ID = os.getenv('LEADERBOARD_CHANNEL_ID')
WORDLE_ROLE_NAME = os.getenv('WORDLE_ROLE_NAME')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # filter messages by the channel we are monitoring, then ensure it starts with the proper substring
    if message.channel.id == MONITOR_CHANNEL_ID and message.content.startswith('Wordle '):
        # check if user has appropriate role to post wordle scores
        verified_role = discord.utils.find(lambda r: r.name == WORDLE_ROLE_NAME, message.guild.roles)
        if verified_role in message.author.roles:
            # parse wordle result
            user_result = message.content.split('\n')[0].split(' ')
            user_series = int(user_result[1])
            user_score = user_result[2].split('/')[0]
            
            # calculate score
            if user_score == 'X':
                user_score = 0
            else:
                user_score = 7 - int(user_score)
                if user_score > 6 or user_score < 0:
                    await message.channel.send(f'Please don\'t cheat :)')
                    return
            
            # now we look for the right series message to update/send new one
            channel = client.get_channel(LEADERBOARD_CHANNEL_ID)
            records = [m async for m in channel.history(limit=2)]
            
            series_found = False
            for r in records:
                if not series_found and r.content.startswith(f'**{user_series}**'):
                    # check if user score is already submitted for that particular series
                    scores = r.content.split('\n')[1:]
                    
                    for s in scores:
                        user_id = int(s.split(' ')[0][2:-1])
                        if message.author.id == user_id:
                            await message.channel.send(f'You already submitted a score for {user_series}. Sorry :(')
                            return
                    
                    # at this point, assume the user has a score for the past series but didn't submit it
                    await r.edit(content=f'{r.content}\n{message.author.mention} `+{user_score}`')
                    await message.channel.send(f'Your score of {user_score} has been recorded!')
                    return
            
            # catch-all for when wordle reinitializes for some reason
            if len(records) > 1:
                latest_series = int(records[0].content[2:5]) + 1
            else:
                latest_series = 1
            
            # make sure users can only post score for today's wordle puzzle, if the series was not found in the last few messages
            if user_series == latest_series:
                await channel.send(f'**{latest_series}**\n{message.author.mention} `+{user_score}`')
                await message.channel.send(f'Your score of {user_score} has been recorded!')
                return
            
            # catch-all for when score is not posted for whatever reason
            await message.channel.send(f'Your score is invalid. Sorry :(')
            return

client.run(TOKEN)