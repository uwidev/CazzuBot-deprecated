import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep


class DevCog():
    def __init__(self, bot):
        self.bot = bot
        
    async def __local_check(self, ctx):
        return ctx.author.id == self.bot.owner_id
    
    async def on_command_error(self, ctx, error):
        ignore = (commands.CommandNotFound, commands.UserInputError)
        
        if isinstance(error, ignore):
            return
    
    @commands.command(hidden=True)
    async def super(self, ctx):
        with open('super', 'r') as readfile:
            state = readfile.read()
            with open('super', 'w') as writefile:
                if state == 'True':
                    writefile.write('False')
                    self.bot.super = False
                    await ctx.send(':clap: {}, no more super. Maybe next time.'.format(ctx.author.mention))
                else:
                    writefile.write('True')
                    self.bot.super = True
                    await ctx.send(':trumpet: {}, you have been given super. Please be careful with it.'.format(ctx.author.mention))
        

                    

def setup(bot):
    bot.add_cog(DevCog(bot))