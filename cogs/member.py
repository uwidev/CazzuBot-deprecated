import discord
from discord.ext import commands

class MemberCog():
    def __init__(self, bot):
        self.bot = bot
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
    async def repeat(self, ctx, *, msg:str):       
        await ctx.send(msg)
        
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, left: int, right: int):
        await ctx.send( left + right )
        
    @commands.command()
    async def username(self, ctx, *, name:str):
        await self.bot.user.edit(username=name)
        await ctx.send("Username changed to {}".format(name))

def setup(bot):
    bot.add_cog(MemberCog(bot))