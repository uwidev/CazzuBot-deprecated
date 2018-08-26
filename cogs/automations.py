'''
For all ongoing events that need to be monitored
'''

import xml.etree.ElementTree as ET
import html
import discord
from discord.ext import commands
import modules.utility

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_raw_reaction_add(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # userauth
        try:
            userauth = tree.find('userauth')

            if userauth.find('status').text == 'enabled':
                if payload.message_id == int(userauth.find('message').find('id').text):
                    if str(payload.emoji) == html.unescape(userauth.find('emoji').find('id').text):
                        guild = self.bot.get_guild(payload.guild_id)
                        role = discord.utils.get(guild.roles,
                                                 id=int(userauth.find('role').find('id').text))
                        if role:
                            await guild.get_member(payload.user_id).add_roles(role)

        except TypeError:
            pass


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


def setup(bot):
    bot.add_cog(AutomationsCog(bot))
