import discord
from discord.ext import commands
import xml.etree.ElementTree as ET
#import main

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
    async def repeat(self, ctx, *, msg = "Empty message :cirnoBaka:"):
        await ctx.send(msg)
    
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def repeatd(self, ctx, *, msg = "Empty message :cirnoBaka:"):       
        await ctx.message.delete()
        await ctx.send(msg)
    
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, left: int, right: int):
        await ctx.send( left + right )


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def hashiresoriyo(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=rkWk0Nq5GjI")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tableflip(self, ctx):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        emojis = tree.find('command_emojis')
        await ctx.send("{} ︵ ┻━┻".format(self.bot.get_emoji(int(emojis.get('NoWork')))))


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def noot(self, ctx):
        await ctx.send("NOOT NOOT")
    

def setup(bot):
    bot.add_cog(MemberCog(bot))
