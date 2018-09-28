'''
This module serves as a framework to the xml data storage for each server.
Each class retains to a certain group of values
Each static function resets a setting to what would be considered default
'''

import xml.etree.ElementTree as ET
import html
import discord
from modules.utility import AllEmoji

USERAUTH_DEFAULT_TITLE = 'Hallo there! Welcones to the server!'
USERAUTH_DEFAULT_DESC = ("It says here that you need to press that "
    "button down there to gain access to the server.")
USERAUTH_DEFAULT_EMOJI = html.unescape('&#128077;')

GREET_DEFAULT_TITLE = "Oh look, a new user"
GREET_DEFAULT_DESC = ("Welcome to the server. "
                         "Have a nice time here, or something.")

def find_branch(root, arg: str):
    return root.find(arg) if root.find(arg) else ET.SubElement(root, arg)

class WorkerServer():
    def __init__(self, root):
        self.server = find_branch(root, 'server')


    async def clear(self):
        self.server.clear()


    async def create_all(self):
        await self.create_admin()
        await self.create_mod()

    async def create_admin(self):
        admin = ET.SubElement(self.server, 'admin')
        ET.SubElement(admin, 'id')

    async def create_mod(self):
        mod = ET.SubElement(self.server, 'mod')
        ET.SubElement(mod, 'id')


class WorkerUserAuth():
    title = USERAUTH_DEFAULT_TITLE
    desc = USERAUTH_DEFAULT_DESC
    emo = USERAUTH_DEFAULT_EMOJI

    def __init__(self, root):
        self.userauth = find_branch(root, 'userauth')

    async def clear(self):
        self.userauth.clear()

    async def create_all(self):
        # await self.create_feature()
        await self.create_role()
        await self.create_embed()
        await self.create_emoji()

    async def create_feature(self):
        ET.SubElement(self.userauth, 'feature').text = 'off'

    async def create_role(self):
        auth_role = ET.SubElement(self.userauth, 'role')
        ET.SubElement(auth_role, 'id')
        ET.SubElement(auth_role, 'name')

    async def create_embed(self):
        auth_embed = ET.SubElement(self.userauth, 'embed')
        ET.SubElement(auth_embed, 'id')
        ET.SubElement(auth_embed, 'title').text = self.title
        ET.SubElement(auth_embed, 'desc').text = self.desc

    async def create_emoji(self):
        auth_emoji = ET.SubElement(self.userauth, 'emoji')
        ET.SubElement(auth_emoji, 'id').text = self.emo


    async def reset_all(self):
        # await self.reset_feature()
        await self.reset_role()
        await self.reset_embed()
        await self.reset_emoji()

    async def reset_feature(self):
        self.userauth.find('feature').text = 'off'

    async def reset_role(self):
        xml_role = self.userauth.find('role')
        xml_role.find('id').text = xml_role.find('name').text = None

    async def reset_embed(self):
        xml_embed = self.userauth.find('embed')
        xml_embed.find('title').text = self.title
        xml_embed.find('desc').text = self.desc

    async def reset_emoji(self):
        self.userauth.find('emoji').find('id').text = self.emo


class WorkerGreet():
    title = GREET_DEFAULT_TITLE
    desc = GREET_DEFAULT_DESC


    def __init__(self, root):
        self.greet = find_branch(root, 'greet')


    async def clear(self):
        self.greet.clear()


    async def create_all(self):
        await self.create_feature()
        await self.create_message()
        await self.create_embed()
        await self.create_channel()
        await self.create_userauth_dependence()

    async def create_feature(self):
        ET.SubElement(self.greet, 'feature').text = 'off'

    async def create_message(self):
        xml_message = ET.SubElement(self.greet, 'message')
        ET.SubElement(xml_message, 'content')

    async def create_embed(self):
        xml_embed = ET.SubElement(self.greet, 'embed')
        ET.SubElement(xml_embed, 'title').text = self.title
        ET.SubElement(xml_embed, 'desc').text = self.desc

    async def create_channel(self):
        xml_channel = ET.SubElement(self.greet, 'channel')
        ET.SubElement(xml_channel, 'id')

    async def create_userauth_dependence(self):
        ET.SubElement(self.greet, 'userauth_dependence').text = 'disabled'


    async def reset_all(self):
        await self.reset_feature()
        await self.reset_message()
        await self.reset_embed()
        await self.reset_channel()
        await self.reset_userauth_dependence()

    async def reset_feature(self):
        self.greet.find('feature').text = 'off'

    async def reset_message(self):
        self.greet.find('message').find('content').text = None

    async def reset_embed(self):
        xml_embed = self.greet.find('embed')
        xml_embed.find('title').text = self.title
        xml_embed.find('desc').text = self.desc

    async def reset_channel(self):

        self.greet.find('channel').find('id').text = None

    async def reset_userauth_dependence(self):
        self.greet.find('userauth_dependence').text = 'disabled'


async def create_all(root):
    await WorkerServer(root).create_all()
    await WorkerUserAuth(root).create_all()
    await WorkerGreet(root).create_all()


class WorkerSelfrole:
    def __init__(self, root):
        self._root = root

    async def create_all(self):
        await self.create_associations_empty()
        await self.create_channel()
        await self.create_message()
        await self.create_status()

    async def create_associations_empty(self):
        ET.SubElement(self._root, 'associations')

    async def create_message(self):
        msg = ET.SubElement(self._root, 'message')
        msg_id = ET.SubElement(msg, 'id')
        msg_id.text = '-42'

    async def create_channel(self):
        ch = ET.SubElement(self._root, 'channel')
        ch_id = ET.SubElement(ch, 'id')
        ch_id.text = '-42'

    async def create_status(self):
        selfrole_status = ET.SubElement(self._root, 'status')
        selfrole_status.text = 'enabled'


class WorkerAddRole:

    @staticmethod
    async def create_role(group: ET.Element, emoji: AllEmoji, role: discord.Role):
        """
        Modifies the given group by adding a role to it.
        :param group:
        :param emoji:
        :param role:
        :return:
        """
        associations_in_group = group.findall('assoc')
        insert_at_end = True

        new_assoc = None
        for index in range(len(associations_in_group)):
            if role.name < associations_in_group[index].find('role').find('name').text:
                insert_at_end = False
                new_assoc = ET.Element('assoc')
                group.insert(index, new_assoc)
                break
        if insert_at_end:
            new_assoc = ET.SubElement(group, 'assoc')

        new_assoc_emoji = ET.SubElement(new_assoc, 'emoji')
        new_assoc_emoji.text = str(emoji)
        new_assoc_role = ET.SubElement(new_assoc, 'role')
        new_assoc_role_name = ET.SubElement(new_assoc_role, 'name')
        new_assoc_role_name.text = role.name
        new_assoc_role_id = ET.SubElement(new_assoc_role, 'id')
        new_assoc_role_id.text = str(role.id)