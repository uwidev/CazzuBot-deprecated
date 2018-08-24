'''
This module serves as a framework to the xml data storage for each server.
Each class retains to a certain group of values
Each static function resets a setting to what would be considered default

.create() is called when initializing the server configs
.reset() is called when from a subcommand clear
'''

import xml.etree.ElementTree as ET
import html

class worker_userauth():
    class create():
        @staticmethod
        async def all(userauth:ET.Element):
            await worker_userauth.create.role(userauth)
            await worker_userauth.create.message(userauth)
            await worker_userauth.create.emoji(userauth)

        @staticmethod
        async def role(userauth:ET.Element):
            auth_role = ET.SubElement(userauth, 'role')
            ET.SubElement(auth_role, 'id').text = 'None'
            ET.SubElement(auth_role, 'name').text = 'None'


        @staticmethod
        async def message(userauth:ET.Element):
            auth_message = ET.SubElement(userauth, 'message')
            ET.SubElement(auth_message, 'id').text = 'None'
            ET.SubElement(auth_message, 'content').text = ("It says here that you need to press that "
                                                            "button down there to gain access to the server.")


        @staticmethod
        async def emoji(userauth:ET.Element):
            auth_emoji = ET.SubElement(userauth, 'emoji')
            ET.SubElement(auth_emoji, 'id').text = html.unescape('&#128077;')


    class reset():
        @staticmethod
        async def all(userauth:ET.Element):
            await worker_userauth.reset.role(userauth)
            await worker_userauth.reset.message(userauth)
            await worker_userauth.reset.emoji(userauth)


        @staticmethod
        async def role(userauth:ET.Element):
            xml_role = userauth.find('role')
            xml_role.find('id').text = 'None'
            xml_role.find('name').text = 'None'


        @staticmethod
        async def message(userauth:ET.Element):
            xml_message = userauth.find('message')
            xml_message.find('id').text = 'None'
            xml_message.find('content').text = ("It says here that you need to press that "
                                                            "button down there to gain access to the server.")


        @staticmethod
        async def emoji(userauth:ET.Element):
            xml_emoji = userauth.find('emoji')
            xml_emoji.find('id').text = html.unescape('&#128077;')
