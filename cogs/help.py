import xml.etree.ElementTree as ET
import discord
from discord.ext import commands
import emoji
import html

def emoji_regional_update():
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


def check_userauth_role_set(ctx):
    role = ctx.userauth.find('role')
    if role.find('id').text != 'None':
        return True
    return False

class AllEmoji(commands.EmojiConverter):
    async def convert(self, ctx, argument):
        if await is_custom_emoji(argument):
            return await super().convert(ctx, argument)
        return argument


async def is_custom_emoji(argument):
    if argument in emoji.UNICODE_EMOJI or argument in emoji.UNICODE_EMOJI_ALIAS:
        return False
    return True


class StatusStr(commands.Converter):
    async def convert(self, ctx, argument):
        accepted = ['enabled', 'disabled']  # User RE to allow present tense, conver to past
        if argument.lower() in accepted:
            return argument.lower()
        raise commands.BadArgument('Accepted values are "enabled" or "disabled".')


class me():
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def test(self, ctx):
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.userauth = ctx.tree.find('userauth')

        xml_emoji = ctx.userauth.find('emoji')

        emo = await AllEmoji().convert(ctx, html.unescape(xml_emoji.find('id').text))
        await ctx.send(emo)


    async def userauth_to_str(self, root: ET.Element):
        '''
        Given the element of userauth as root, returns indented list
        '''
        to_return = ''
        # to_return.append('status: {}'.format(root.find('status').text))
        to_return += '    role: {}'.format(root.find('role').find('name').text)

        xml_emoji = root.find('emoji')
        if bool(xml_emoji.find('custom').text) == 'True':
            to_return += '\n    emoji: {}'.format(str(self.bot.get_emoji(int(xml_emoji.find('id').text))))
        else:
            to_return += '\n    emoji: {}'.format(xml_emoji.find('id').text)

        return to_return



def setup(bot):
    bot.add_cog(me(bot))

emoji_regional_update()
