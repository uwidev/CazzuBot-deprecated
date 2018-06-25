import discord
from discord.ext import commands
import xml.etree.ElementTree as ET

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot 
'''
    async def on_message(self, message):
        await self.bot.process_commands(message)
        tree = ET.parse('server_data/{}/config.xml'.format(message.guild.id))

        if tree.find('channelvotes').get('Status') == 'Enabled':
            voteon = list((int(element.get('Channel_ID')) for element in tree.iter('voteon')))
            
            if message.channel.id in voteon:
                print('trueee')
                await message.add_reaction('\U0001f44d')
                await message.add_reaction('\U0001f44e')
                await message.add_reaction('\U0001f914')
'''
def setup(bot):
    bot.add_cog(AutomationsCog(bot))