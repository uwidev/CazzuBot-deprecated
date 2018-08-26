# Small utility functions that are refactored from the main cogs

import xml.etree.ElementTree as ET
import discord
from discord.ext import commands
import emoji
import html

def emoji_regional_update():
    '''Adds regional letters to emoji for discord-compatability checking'''
    regional_emoji = {
        u'\U0001F1E6': u':regional_indicator_a:',
        u'\U0001F1E7': u':regional_indicator_b:',
        u'\U0001F1E8': u':regional_indicator_c:',
        u'\U0001F1E9': u':regional_indicator_d:',
        u'\U0001F1EA': u':regional_indicator_e:',
        u'\U0001F1EB': u':regional_indicator_f:',
        u'\U0001F1EC': u':regional_indicator_g:',
        u'\U0001F1ED': u':regional_indicator_h:',
        u'\U0001F1EE': u':regional_indicator_i:',
        u'\U0001F1EF': u':regional_indicator_j:',
        u'\U0001F1F0': u':regional_indicator_k:',
        u'\U0001F1F1': u':regional_indicator_l:',
        u'\U0001F1F2': u':regional_indicator_m:',
        u'\U0001F1F3': u':regional_indicator_n:',
        u'\U0001F1F4': u':regional_indicator_p:',
        u'\U0001F1F5': u':regional_indicator_o:',
        u'\U0001F1F6': u':regional_indicator_r:',
        u'\U0001F1F7': u':regional_indicator_s:',
        u'\U0001F1F8': u':regional_indicator_t:',
        u'\U0001F1F9': u':regional_indicator_q:',
        u'\U0001F1FA': u':regional_indicator_u:',
        u'\U0001F1FB': u':regional_indicator_v:',
        u'\U0001F1FC': u':regional_indicator_w:',
        u'\U0001F1FD': u':regional_indicator_x:',
        u'\U0001F1FE': u':regional_indicator_y:',
        u'\U0001F1FF': u':regional_indicator_z:'
        }

    emoji.UNICODE_EMOJI.update(regional_emoji)


# Userful Converters
class AllEmoji(commands.EmojiConverter):
    '''Converts both toa custom or discord-compatable unicode emoji'''
    async def convert(self, ctx, argument):
        if await is_custom_emoji(argument):
            return await super().convert(ctx, argument)
        return argument


class StatusStr(commands.Converter):
    '''
    Mainly used to check to see if taken str is enabled or disabled.
    Also needs to be more flexible in accepted paramaters.
    '''
    async def convert(self, ctx, argument):
        accepted = ['enabled', 'disabled']  # User RE to allow present tense, conver to past
        if argument.lower() in accepted:
            return argument.lower()
        raise commands.BadArgument('Accepted values are "enabled" or "disabled".')


async def write_xml(ctx):
    ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))


def check_userauth_role_set(ctx):
    '''A check to see if userauth role is set'''
    role = ctx.userauth.find('role')
    if role.find('id').text != 'None':
        return True
    return False


async def is_custom_emoji(argument):
    '''Small helper function to see if an emoji is custom or unicode'''
    if argument in emoji.UNICODE_EMOJI or argument in emoji.UNICODE_EMOJI_ALIAS:
        return False
    return True


async def make_userauth_embed(msg:str):
    '''Creates the embed for useruath make and returns that embed'''
    embed = discord.Embed(
                        title='Hallo there! Welcones to the server!',
                        description=html.unescape(msg),
                        color=0x9edbf7)

    #embed.set_author(name='Cirno', icon_url='https://i.imgur.com/sFG6Oty.png')
    embed.set_footer(text='-sarono', icon_url='https://i.imgur.com/BAj8IWu.png')
    embed.set_thumbnail(url='https://i.imgur.com/RY1IgDX.png')

    return embed


async def make_simple_embed(title:str, desc:str):
    '''Creates a simple discord.embed object and returns it'''
    embed = discord.Embed(
                        title=title,
                        description=desc,
                        color=0x9edbf7)

    embed.set_footer(text='-sarono', icon_url='https://i.imgur.com/BAj8IWu.png')

    return embed


async def userauth_to_str(root: ET.Element):
    '''Given the element of userauth as root, returns indented list as a str'''
    to_return = ''

    to_return += '**role:** {}'.format(root.find('role').find('name').text)

    xml_emoji = root.find('emoji')
    to_return += '\n**emoji:** {}'.format(xml_emoji.find('id').text)

    return to_return
