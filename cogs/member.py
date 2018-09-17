import discord
from discord.ext import commands
import xml.etree.ElementTree as ET
#import main


class MemberCog():

    def __init__(self, bot):
        self.bot = bot
        self.default_repeat_msg = "You tried to send an empty message <:cirnoBaka:489185059732193298>"
        
    '''
    async def __error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == self.bot.owner_id and self.bot.super == True:
                #await ctx.send(':exclamation: Dev cooldown bypass.')
                await ctx.reinvoke()
            else:
                await ctx.channel.send(':hand_splayed: Please try again after {} seconds.'.format(str(error.retry_after)[0:3]))
    '''

    

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send(':ping_pong: Pong! {}ms'.format(str(self.bot.latency * 1000)[0:6]))
    
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def repeat(self, ctx, *, msg = None):
        """
        The bot will repeat whatever you say!
        """
        if msg is None:
            msg = self.default_repeat_msg
        await ctx.send(msg)
    
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def repeatd(self, ctx, *, msg = None):
        """
        Repeats your message while deleting it. Super incognito mode activated
        """
        if msg is None:
            msg = self.default_repeat_msg
        else:
            await ctx.message.delete()
        await ctx.send(msg)
    
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, left: int, right: int):
        await ctx.send( left + right )


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def hashire(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=efdN69QscAg")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tableflip(self, ctx):
        """
        Flips a table.
        """
        await ctx.send("<:cirnoNoWork:489185064844787712> ︵ ┻━┻")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tableflipd(self, ctx):
        """
        Flips a table. The table lands on your message, causing it to vanish instantly.
        """
        await ctx.message.delete()
        await ctx.send("<:cirnoNoWork:489185064844787712> ︵ ┻━┻")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unflip(self, ctx):
        await ctx.send("┬─┬ <:cirnoBaka:489185059732193298>")


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def noot(self, ctx):
        await ctx.send("NOOT NOOT")


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def rads(self, ctx):
        await ctx.send("uwi nuked the dev server")


    @commands.command(name="f")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def payRespects(self, ctx, *, something = None):
        if not something:
            await ctx.send("{} has paid their respects!".format(str(ctx.author.mention)))
        else:
            if something == self.bot.user.mention:
                await ctx.send("{} has paid their respects for... me apparently <:cirnoSaddest:477396508832956417>".format(str(ctx.author.mention)))
            else:
                await ctx.send("{} has paid their respects for {}!".format(str(ctx.author.mention), something))


    @commands.command()
    async def woop(self, ctx):
        embed = discord.Embed()
        embed.set_image(url="https://i.imgur.com/VKxwEzx.gif")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MemberCog(bot))
