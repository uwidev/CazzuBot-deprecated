import discord
from discord.ext import commands
import TOKEN_SECRET
import traceback
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


PREFIX = ['d!']
# Add bot here: https://discordapp.com/oauth2/authorize?client_id=427583823912501248&scope=bot

def get_prefix(bot, msg):
    pre = PREFIX
    return pre

description = '''Bot is in very early development for the Friends server.'''
bot = commands.Bot(command_prefix=get_prefix, description=description, self_bot = False, owner_id = 212797661412065281, case_insensitive=True)

# Core -------------------
@bot.event
async def on_ready():
    print('Bot has initialized...')
    print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))
    print('-------------------------')    
    print('READY!')
    print('-------------------------')
    
extensions = ['cogs.member', 'cogs.admin', 'cogs.dev', 'cogs.automations', 'cogs.helper']

if __name__ == '__main__':
    for ext in extensions:
        try:
            bot.load_extension(ext)
        except:
            print('Failed to load extension: {}'.format(ext))
            traceback.print_exc()
            
    with open('super', 'r') as readfile:
        state = readfile.read()
        if state == 'True':
            bot.super = True
        else:
            bot.super = False
    

bot.run(TOKEN_SECRET.TOKEN_SECRET)
