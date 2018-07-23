import discord
from discord.ext import commands
import xml.etree.ElementTree as ET

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot 

    async def on_raw_reaction_add(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # userauth
        try:
            userauth = tree.find('userauth')
            guild = self.bot.get_guild(payload.guild_id)

            if payload.message_id == int(userauth.get('MessageID')) and payload.emoji.id == int(userauth.get('Emoji')) and userauth.get('Status') == 'Enabled':
                #await self.bot.get_channel(payload.channel_id).send('Success!')
                await guild.get_member(payload.user_id).add_roles(discord.utils.get(guild.roles, id = int(userauth.get('AuthRoleID'))))
        except ValueError:
            print("userauth settings not properly defined")

        # automated user self-roles
        s_rolelist = tree.find('selfroles')
        selfroles_msg_id = int(s_rolelist.find('msg_id').get('Value'))
        selfroles_roles_ch = int(s_rolelist.find('ch_id').get('Value'))
        guild = self.bot.get_guild(payload.guild_id)
        if payload.message_id == selfroles_msg_id and payload.channel_id == selfroles_roles_ch:  # and s_rolelist.get('Status') == 'Enabled':
            for e in s_rolelist.iter():
                if(payload.emoji.name == e.tag):
                    await guild.get_member(payload.user_id).add_roles(
                        discord.utils.get(guild.roles, name=e.get("Role")))
                    break

    async def on_raw_reaction_remove(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # automated user self-roles
        s_rolelist = tree.find('selfroles')
        selfroles_msg_id = int(s_rolelist.find('msg_id').get('Value'))
        selfroles_roles_ch = int(s_rolelist.find('ch_id').get('Value'))
        guild = self.bot.get_guild(payload.guild_id)
        if payload.message_id == selfroles_msg_id and payload.channel_id == selfroles_roles_ch:  # and s_rolelist.get('Status') == 'Enabled':
            for e in s_rolelist.iter():
                if (payload.emoji.name == e.tag):
                    await guild.get_member(payload.user_id).remove_roles(
                        discord.utils.get(guild.roles, name=e.get("Role")))
                    break
    
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