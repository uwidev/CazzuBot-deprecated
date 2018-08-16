import discord
from discord.ext import commands
import xml.etree.ElementTree as ET

class AutomationsCog():
    def __init__(self, bot):
        self.bot = bot 

    async def on_raw_reaction_add(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # Userauth
        try:
            userauth = tree.find('userauth')
            guild = self.bot.get_guild(payload.guild_id)

            if payload.message_id == int(userauth.get('MessageID')) and payload.emoji.id == int(
                    userauth.get('Emoji')) and userauth.get('Status') == 'Enabled':
                # await self.bot.get_channel(payload.channel_id).send('Success!')
                await guild.get_member(payload.user_id).add_roles(
                    discord.utils.get(guild.roles, id=int(userauth.get('AuthRoleID'))))
        except ValueError:
            print("Error: userauth settings not properly defined")
            print("Check automations.py if you were expecting a detailed error message")
        except TypeError:
            print("Error: userauth settings not properly defined")
            print("Check automations.py if you were expecting a detailed error message")

        if payload.user_id == self.bot.user.id:
            return # The bot shouldn't listen to itself


        # Automated user self-roles
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('msg_id').text)
        selfroles_roles_ch = int(selfrole_list.find('ch_id').text)
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id in selfroles_msg_ids and payload.channel_id == selfroles_roles_ch:  # and selfrole_list.get('Status') == 'Enabled':
            for e in associations.iter():
                if e.tag != 'assoc':
                    continue
                if str(payload.emoji.id if int(e.get('custom')) else payload.emoji) == e.find('emoji').text:
                    await guild.get_member(payload.user_id).add_roles(
                        discord.utils.get(guild.roles, name=e.find('role').text))
                    break


    async def on_raw_reaction_remove(self, payload):
        tree = ET.parse('server_data/{}/config.xml'.format(payload.guild_id))

        # automated user self-roles
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        selfroles_msg_ids = self._conv_to_id_list(selfrole_list.find('msg_id').text)
        selfroles_roles_ch = int(selfrole_list.find('ch_id').text)
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id in selfroles_msg_ids and payload.channel_id == selfroles_roles_ch:  # and selfrole_list.get('Status') == 'Enabled':
            for e in associations.iter():
                if e.tag != 'assoc':
                    continue
                if str(payload.emoji.id if int(e.get('custom')) else payload.emoji) == e.find('emoji').text:
                    await guild.get_member(payload.user_id).remove_roles(
                        discord.utils.get(guild.roles, name=e.find('role').text))
                    break


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))
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