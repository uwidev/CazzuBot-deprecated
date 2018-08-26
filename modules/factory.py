'''
This module serves as a framework to the xml data storage for each server.
Each class retains to a certain group of values
Each static function resets a setting to what would be considered default
'''

import xml.etree.ElementTree as ET
import html

USERAUTH_DEFAULT_MESSAGE = ("It says here that you need to press that "
    "button down there to gain access to the server.")
USERAUTH_DEFAULT_EMOJI = html.unescape('&#128077;')

class WorkerUserAuth():
    msg = USERAUTH_DEFAULT_MESSAGE
    emo = USERAUTH_DEFAULT_EMOJI
    # default_greet_message = ("Oh look, a new user\nWelcome to the server {MENTION}. "
    #                          "Hope you have a nice time on here, or something.")

    def __init__(self, root):
        self.root = root

    async def create_all(self):
        await self.create_status()
        await self.create_role()
        await self.create_message()
        await self.create_emoji()

    async def create_status(self):
        ET.SubElement(self.root, 'status').text = 'disabled'

    async def create_role(self):
        auth_role = ET.SubElement(self.root, 'role')
        ET.SubElement(auth_role, 'id')
        ET.SubElement(auth_role, 'name')

    async def create_message(self):
        auth_message = ET.SubElement(self.root, 'message')
        ET.SubElement(auth_message, 'id')
        ET.SubElement(auth_message, 'content').text = self.msg

    async def create_emoji(self):
        auth_emoji = ET.SubElement(self.root, 'emoji')
        ET.SubElement(auth_emoji, 'id').text = self.emo

    # async def create_greet(self):
    #     auth_greet = ET.SubElement(self.root, 'greet')
    #     ET.SubElement(auth_greet, 'status').text = 'disabled'
    #
    #     auth_greet_message = ET.SubElement(auth_greet, 'message')
    #     ET.SubElement(auth_greet_message, 'content').text = workon_userauth.default_greet_message
    #
    #     auth_greet_channel = ET.SubElement(auth_greet, 'channel')
    #     ET.SubElement(auth_greet_channel, 'id')
    #     ET.SubElement(auth_greet_channel, 'name')

    # Reset

    async def reset_all(self):
        await self.reset_status()
        await self.reset_role()
        await self.reset_message()
        await self.reset_emoji()

    async def reset_status(self):
        self.root.find('status').text = 'disabled'

    async def reset_role(self):
        xml_role = self.root.find('role')
        xml_role.find('id').text = xml_role.find('name').text = None

    async def reset_message(self):
        xml_message = self.root.find('message')
        xml_message.find('content').text = self.msg

    async def reset_emoji(self):
        self.root.find('emoji').find('id').text = self.emo
    #
    # async def greet(self):
    #     xml_greet = userauth.find('greet')
    #     xml_greet.find('status').text = 'disabled'
    #     xml_greet.find('message').find('content').text = workon_userauth.default_greet_message
    #
    #     xml_greet_channel = xml_greet.find('channel')
    #     xml_greet_channel.find('id').text = None
    #     xml_greet_channel.find('name').text = None

class WorkerGreet():
    default_message = ("Oh look, a new user\nWelcome to the server {MENTION}. "
                             "Hope you have a nice time on here, or something.")

    async def create_all(self):
        self.create_message()
        self.create_channel()


    async def create_message(self):
        pass


    async def create_channel(self):
        pass

    async def reset_all(self):
        self.reset_message()
        self.reset_channel()


    async def reset_message(self):
        pass


    async def reset_channel(self):
        pass
