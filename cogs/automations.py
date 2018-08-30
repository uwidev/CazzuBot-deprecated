'''
For all ongoing events that need to be monitored
'''

import xml.etree.ElementTree as ET
import html
import discord
from discord.ext import commands
from modules import utility

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot


    async def on_member_join(self, member):
        tree = await utility.load_tree_id(member.guild.id)

        # ----- Greeting Message ----- #
        xml_greet = tree.find('greet')

        if await utility.check_greet(xml_greet):
            if xml_greet.find('userauth_dependence').text == 'disabled':
                channel_id = xml_greet.find('channel').find('id').text

                channel = discord.utils.get(member.guild.text_channels,
                    id=int(channel_id))

                xml_embed = xml_greet.find('embed')

                embed = await utility.make_simple_embed(
                    xml_embed.find('title').text,
                    xml_embed.find('desc'))

                await channel.send(
                    content=xml_greet.find('message').findtext('content').format(MENTION=member.mention),
                    embed=embed)


    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return # The bot shouldn't listen to itself

        tree = await utility.load_tree_id(payload.guild_id)

        # ----- Userauth ----- #
        userauth = tree.find('userauth')
        guild = self.bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles,
                                 id=int(userauth.find('role').find('id').text))

        if role:
            if payload.message_id == int(userauth.find('embed').find('id').text):
                if str(payload.emoji) == html.unescape(userauth.find('emoji').find('id').text):
                    member = guild.get_member(payload.user_id)

                    if role not in member.roles:
                        await member.add_roles(role)

                        # ----- Greeting for Userauth ----- #
                        xml_greet = tree.find('greet')
                        if await utility.check_greet(xml_greet):
                            if xml_greet.find('userauth_dependence').text == 'enabled':
                                channel_id = xml_greet.find('channel').find('id').text

                                channel = discord.utils.get(self.bot.get_guild(payload.guild_id).text_channels,
                                    id=int(channel_id))
                                xml_message = xml_greet.find('embed')
                                embed = await utility.make_simple_embed(
                                    xml_message.find('title').text,
                                    xml_message.find('desc').text)

                                await channel.send(
                                    content=xml_greet.find('message').findtext('content').format(
                                        MENTION=self.bot.get_user(payload.user_id).mention),
                                    embed=embed)


        # Automated user self-roles
        selfrole_list = tree.find('selfroles')
        if selfrole_list.find('status').text == 'enabled':
            roles_channel_id = int(selfrole_list.find('channel').find('id').text)
            if payload.channel_id == roles_channel_id:
                selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
                if payload.message_id in selfroles_msg_ids:
                    associations = selfrole_list.find('associations')
                    guild = self.bot.get_guild(payload.guild_id)
                    author_role_names = {str(role) for role in guild.get_member(payload.user_id).roles}
                    for group in associations.findall('group'):
                        req_role = group.find('req_role').text
                        if req_role and not req_role in author_role_names:
                            continue
                        for assoc in group.findall('assoc'):
                            if str(payload.emoji) == assoc.find('emoji').text:
                                await guild.get_member(payload.user_id).add_roles(
                                    discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                                break


    async def on_raw_reaction_remove(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # automated user self-roles
        selfrole_list = tree.find('selfroles')
        if selfrole_list.find('status').text == 'enabled':
            roles_channel_id = int(selfrole_list.find('channel').find('id').text)
            if payload.channel_id == roles_channel_id:
                selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
                if payload.message_id in selfroles_msg_ids:
                    associations = selfrole_list.find('associations')
                    guild = self.bot.get_guild(payload.guild_id)
                    for assoc in associations.iter():
                        if assoc.tag != 'assoc':
                            continue
                        if str(payload.emoji) == assoc.find('emoji').text:
                            await guild.get_member(payload.user_id).remove_roles(
                                discord.utils.get(guild.roles, id=int(assoc.find('role').find('id').text)))
                            break


    def _find_role_assoc(self, role: discord.Role) -> ('tree', 'assoc', 'group'):
        """
        Finds the association corresponding to a particular
        """
        tree = ET.parse('server_data/{}/config.xml'.format(role.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        for group in associations.findall('group'):
            for assoc in group.findall('assoc'):
                if assoc.find('role').find('id').text == str(role.id):
                    return tree, assoc, group
        return tree, None, None


    async def _get_single_group_msg(self, group: ET.Element) -> discord.Embed:
        """
        It's basically the one in admin.py. This will be moved to a different module later.
        """
        title = "Group **{}**\n".format(group.find('name').text)
        req_role = group.find('req_role').text
        desc = ""
        if req_role:
            desc = "(requires {})".format(req_role)
        added_element = False
        assoc_list = group.findall('assoc')
        msg_left = ""
        msg_right = ""
        divider = len(assoc_list)/2
        for index in range(len(assoc_list)):
            assoc = assoc_list[index]
            added_element = True
            msg = "\t" + assoc.find('emoji').text + ' **:** ' + str(assoc.find('role').find('name').text) + ' ​ ​\n'
            if index < divider:
                msg_left += msg
            else:
                msg_right += msg
        embed = discord.Embed(title=title, description=desc)
        if not added_element:
            msg_left = "Empty!"
        embed.add_field(name="----------------------", value=msg_left, inline=True)
        if msg_right:
            embed.add_field(name="----------------------", value=msg_right, inline=True)
        return embed


    async def _edit_selfrole_msg(self, guild: discord.Guild, group: ET.Element, change_emoji: bool, emoji: utility.AllEmoji = None, to_add: bool = None):
        """
        Adds or removes a role from the corresponding message if it exists.

        It's basically the one in admin.py. This will be moved to a different module later.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(guild.id))
        selfrole_list = tree.find('selfroles')
        channel_id = int(selfrole_list.find('channel').find('id').text)
        if channel_id != -42:
            group_msg_id = int(group.find('message').find('id').text)
            msg_obj = await self.bot.get_channel(channel_id).get_message(group_msg_id)
            embed = await self._get_single_group_msg(group)
            await msg_obj.edit(embed=embed)
            if change_emoji:
                if to_add:
                    await msg_obj.add_reaction(emoji)
                else:
                    await msg_obj.remove_reaction(emoji, self.bot.user)


    async def on_guild_role_delete(self, before: discord.Role):
        """
        Modifies the XML in case a role is deleted.
        """
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            emoji = await utility.AllEmoji().convert(None, assoc.find('emoji').text)
            group.remove(assoc)
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await self._edit_selfrole_msg(before.guild, group, True, emoji, False)


    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        Modifies the XML in case a role is changed.
        """
        tree, assoc, group = self._find_role_assoc(before)
        if assoc:
            assoc.find('role').find('name').text = after.name
            tree.write('server_data/{}/config.xml'.format(str(before.guild.id)))
            await self._edit_selfrole_msg(before.guild, group, False)


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """
        Converts text stored in message->id to a list of message ids of type int

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))


def setup(bot):
    bot.add_cog(AutomationsCog(bot))
