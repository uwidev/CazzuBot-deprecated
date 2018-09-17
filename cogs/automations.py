'''
For all ongoing events that need to be monitored
'''

import xml.etree.ElementTree as ET
import html
import discord
from discord.ext import commands
import modules.utility
import modules.selfrole as sr
import modules.selfrole.message

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return # The bot shouldn't listen to itself

        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # Userauth
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

        # Automated user self-roles
        selfrole_list = tree.find('selfroles')
        if selfrole_list.find('status').text == 'enabled':
            roles_channel_id = int(selfrole_list.find('channel').find('id').text)
            if payload.channel_id == roles_channel_id:
                selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
                if payload.message_id in selfroles_msg_ids:
                    associations = selfrole_list.find('associations')
                    guild = self.bot.get_guild(payload.guild_id)
                    author_roles = guild.get_member(payload.user_id).roles
                    author_role_names = {str(role) for role in author_roles}
                    user_added_role = False
                    for group in associations.findall('group'):
                        req_role = group.find('req_role').text
                        if not int(group.find('message').find('id').text) == payload.message_id or \
                                (req_role and not req_role in author_role_names):
                            continue

                        assoc_list = group.findall('assoc')

                        # Check max roles
                        max_text = group.find('max').text
                        if max_text != 'all':
                            s = {int(a.find('role').find('id').text) for a in assoc_list}
                            t = {r.id for r in author_roles}
                            num_from_group = len(s.intersection(t))
                            if num_from_group >= int(max_text):
                                continue

                        for assoc in assoc_list:
                            if str(payload.emoji) == assoc.find('emoji').text:
                                user_added_role = True
                                await guild.get_member(payload.user_id).add_roles(
                                    discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                                break
                    if not user_added_role:
                        msg = await self.bot.get_channel(payload.channel_id).get_message(payload.message_id)
                        await msg.remove_reaction(payload.emoji, guild.get_member(payload.user_id))


    async def on_raw_reaction_remove(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # Automated user self-roles
        selfrole_list = tree.find('selfroles')
        if selfrole_list.find('status').text == 'enabled':
            roles_channel_id = int(selfrole_list.find('channel').find('id').text)
            if payload.channel_id == roles_channel_id:
                associations = selfrole_list.find('associations')
                guild = self.bot.get_guild(payload.guild_id)
                author_roles = guild.get_member(payload.user_id).roles
                author_role_names = {str(role) for role in author_roles}
                for group in associations.findall('group'):
                    req_role = group.find('req_role').text
                    if not int(group.find('message').find('id').text) == payload.message_id or \
                            (req_role and not req_role in author_role_names):
                        continue
                    guild = self.bot.get_guild(payload.guild_id)
                    for assoc in group.findall('assoc'):
                        if str(payload.emoji) == assoc.find('emoji').text:
                            await guild.get_member(payload.user_id).remove_roles(
                                discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                            break


    def _find_role_assoc(self, role: discord.Role) -> ('tree', 'assoc', 'group'):
        """
        Finds the association corresponding to a particular role.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(role.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        for group in associations.findall('group'):
            for assoc in group.findall('assoc'):
                if assoc.find('role').find('id').text == str(role.id):
                    return tree, assoc, group
        return tree, None, None


    async def on_guild_role_delete(self, before: discord.Role):
        """
        Modifies the XML in case a role is deleted.
        """
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            emoji = await modules.utility.AllEmoji().convert(None, assoc.find('emoji').text)
            group.remove(assoc)
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await sr.message.edit_selfrole_msg(self, before.guild, group, True, emoji, False)


    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        Modifies the XML in case a role is changed.
        """
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            assoc.find('role').find('name').text = after.name
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await sr.message.edit_selfrole_msg(self, before.guild, group, False)


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """
        Converts text stored in message->id to a list of message ids of type int

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))

    '''
    async def on_message(self, message):
        await self.bot.process_commands(message)
        tree = ET.parse('server_data/{}/config.xml'.format(message.guild.id))
    '''


def setup(bot):
    bot.add_cog(AutomationsCog(bot))
