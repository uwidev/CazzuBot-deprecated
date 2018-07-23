import discord
from discord.ext import commands
import xml.etree.ElementTree as ET

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot 

    async def on_raw_reaction_add(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))
        userauth = tree.find('userauth')
        guild = self.bot.get_guild(payload.guild_id)
        
        if payload.message_id == int(userauth.get('MessageID')) and payload.emoji.id == int(userauth.get('Emoji')) and userauth.get('Status') == 'Enabled':
            #await self.bot.get_channel(payload.channel_id).send('Success!')
            await guild.get_member(payload.user_id).add_roles(discord.utils.get(guild.roles, id = int(userauth.get('AuthRoleID'))))
            
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