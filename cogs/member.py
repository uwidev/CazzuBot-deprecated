import discord
from discord.ext import commands
#import main

class MemberCog():

    def __init__(self, bot):
        self.bot = bot
        something = bot
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

    # Potential idea: repeatd command
        
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, left: int, right: int):
        await ctx.send( left + right )
        
    @commands.command()
    async def username(self, ctx, *, name:str):
        await self.bot.user.edit(username=name)
        await ctx.send("Username changed to {}".format(name))
    
    ''' MOVE THIS TO ADMIN LATER '''
    
    @commands.group()
    async def selfrole(self, ctx, msg):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command :cirnoBaka:')
    
    @selfrole.command()
    async def add(self, ctx, msg):
        await ctx.send('You tried to add a role :cirnoWow:')
    
    @selfrole.command()
    async def delete(self, ctx, msg):
        await ctx.send('You tried to remove a role :cirnoWow:')
    
    ''' SNIPPY SNIP '''

def setup(bot):
    bot.add_cog(MemberCog(bot))
