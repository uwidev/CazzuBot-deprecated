import traceback
import logging
import discord
from discord.ext import commands
import TOKEN_SECRET

def setup_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)


PREFIX = ['!']

# Add bot here: https://discordapp.com/oauth2/authorize?client_id=378651742239457290&scope=bot

DESC = '''Bot is in very early development for the Friends server.'''
bot = commands.Bot(
    command_prefix=PREFIX,
    description=DESC,
    self_bot=False,
    owner_id=92664421553307648,
    case_insensitive=True)

# Core -------------------
@bot.event
async def on_ready():
    '''
    Runs as soon as the bot finishes initializing itself
    '''
    print('Bot has initialized...')
    print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))
    print('-------------------------')
    print('READY!')
    print('-------------------------')

extensions = ['cogs.member', 'cogs.admin', 'cogs.dev', 'cogs.automations',
    'cogs.gowner']

if __name__ == '__main__':
    '''
    Logging, cog loading and bot owner perm override is set up here
    '''
    setup_logging()

    for ext in extensions:
        try:
            bot.load_extension(ext)
        except ImportError:
            print('Failed to load extension: {}'.format(ext))
            traceback.print_exc()

    with open('super', 'r') as readfile:
        bot.super = bool(readfile.read())


bot.run(TOKEN_SECRET.TOKEN_SECRET)
