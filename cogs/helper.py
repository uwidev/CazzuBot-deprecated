import discord
from discord.ext import commands
import emoji
import re

class HelperCog():
    def __init__(self, bot):
        self.bot = bot
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
  
    class AllEmoji(commands.EmojiConverter):
        async def convert(self, ctx, argument):
            if argument in emoji.UNICODE_EMOJI or argument in emoji.UNICODE_EMOJI_ALIAS:
                return argument
            return await super().convert(ctx, argument)

    @commands.command()
    async def test(self, ctx, *, arg: AllEmoji):
        print(arg)
        
        await ctx.send(arg)

       
def setup(bot):
    bot.add_cog(HelperCog(bot))