# Small utility functions that are refactored from the main cogs

#import xml.etree.ElementTree as ET
import discord
from discord.ext import commands
import emoji
import html
import re
import modules.selfrole.find

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
    def __init__(self):
        self.pos = re.compile(r'^(enabled?)|(on)$')
        self.neg = re.compile(r'^(disabled?)|(off)$')

    async def convert(self, ctx, argument):
        if re.match(self.pos, argument.lower()):
            return 'enabled'
        if re.match(self.neg, argument.lower()):
            return 'disabled'
        raise commands.BadArgument('Accepted values are "enabled" or "disabled".')


class MaxRoleStr(commands.Converter):
    """
    Used to check whether a passed argument is a numerical value or the string "all".
    """
    async def convert(self, ctx, argument):
        arg = ''
        try:
            arg = int(argument)
        except ValueError:
            pass
        if type(arg) is int:
            if arg < 0:
                raise commands.BadArgument("Max roles must be an integer greater than or equal to 0.")
            else:
                return argument if arg > 0 else 'all'
        if argument == "all":
            return "all"
        raise commands.BadArgument('Accepted values are integers >= 0 or the string "all".')


class GroupStr(commands.Converter):
    """
    Used to convert a group in string format to an ET.Element.
    """
    async def convert(self, ctx, argument):
        selfroles = ctx.tree.find('selfroles')
        associations = selfroles.find('associations')
        groups_list = associations.findall('group')

        group = modules.selfrole.find.find_group(groups_list, argument)

        if group is None:
            raise commands.BadArgument("Group **{}** does not exist.".format(argument))

        return group


async def write_xml(ctx):
    ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))


def check_userauth_role_set(ctx):
    '''A check to see if userauth role is set'''
    role = ctx.userauth.find('role')
    return False if role.find('id').text is None else True


async def is_custom_emoji(argument):
    '''Small helper function to see if an emoji is custom or unicode'''
    if argument in emoji.UNICODE_EMOJI or argument in emoji.UNICODE_EMOJI_ALIAS:
        return False
    return True


async def make_userauth_embed(msg:str):
    '''Creates and returns the embed for useruath'''
    embed = discord.Embed(
                        title='Hallo there! Welcones to the server!',
                        description=html.unescape(msg),
                        color=0x9edbf7)

    #embed.set_author(name='Cirno', icon_url='https://i.imgur.com/sFG6Oty.png')
    embed.set_footer(text='-sarono', icon_url='https://i.imgur.com/BAj8IWu.png')
    embed.set_thumbnail(url='https://i.imgur.com/RY1IgDX.png')

    return embed


async def delete_userauth(ctx):
    try:
        message_id = int(ctx.userauth.find('message').find('id').text)
        msg = await ctx.get_message(message_id)
        await msg.delete()

    except (TypeError, discord.errors.NotFound):
        pass


async def edit_userauth(ctx, content:str):
    msg_embed = await make_userauth_embed(content)
    xml_message = ctx.userauth.find('message')

    try:
        client_message = await ctx.get_message(int(xml_message.find('id').text))
        await client_message.edit(embed=msg_embed)

    except (TypeError, discord.errors.NotFound):
        pass


async def make_simple_embed(title:str, desc:str):
    '''Creates a simple discord.embed object and returns it'''
    embed = discord.Embed(
                        title=title,
                        description=desc,
                        color=0x9edbf7)

    embed.set_footer(text='-sarono', icon_url='https://i.imgur.com/BAj8IWu.png')

    return embed


async def userauth_to_str(ctx):
    '''Given the element of userauth as root, returns indented list as a str'''
    root = ctx.userauth
    to_return = ''

    to_return += '**Status:** {sta}'.format(sta=root.find('status').text.capitalize())

    to_return += '**\nRole:** {na}'.format(na=root.find('role').find('name').text)

    xml_emoji = root.find('emoji')
    to_return += '\n**Emoji:** {emo}'.format(emo=xml_emoji.find('id').text)

    # xml_greet = root.find('greet')
    # channel_id = xml_greet.find('channel').find('id')
    # channel = await commands.TextChannelConverter().convert(ctx, channel_id) if channel_id else None
    # to_return += '\n**greet-status:** {sta}\n**greet-channel:** {ch}'.format(
    #     sta=xml_greet.find('status').text,
    #     ch=channel)

    return to_return


async def arg_to_role(ctx, r: tuple) -> discord.Role:
    s = ' '.join(r)
    return await commands.RoleConverter().convert(ctx, s)