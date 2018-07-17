import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep


class AdminCog():
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.guild is not None and ctx.author.guild_permissions.administrator
    
    
    async def __error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == self.bot.owner_id and self.bot.super == True:
                #await ctx.send(':exclamation: Dev cooldown bypass.')
                await ctx.reinvoke()
            else:
                await ctx.channel.send(':hand_splayed: Command has a {} second cooldown. Please try again after {} seconds.'.format(str(error.cooldown.per)[0:3], str(error.retry_after)[0:3]))
         
        elif isinstance(error, commands.CommandInvokeError):
            return await ctx.send('{}'.format(error.original))
             
        elif isinstance(error, commands.BadArgument):
            return await ctx.send(':x: ERROR: {}'.format(' '.join(error.args)))
             
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(':x: ERROR: {} is a required argument.'.format(error.param.name))
             
             
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
     
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def init(self, ctx):
        if not os.path.isdir('server_data/{}'.format(ctx.guild.id)):
            os.makedirs('server_data/{}'.format(str(ctx.guild.id)))
  
        root = ET.Element('data')
        
        ET.SubElement(root, 'userauth', Status='Disabled', AuthRoleID='None', MessageID='None', Emoji='None')
        ET.SubElement(root, 'autovote', Status='Disabled')
        ET.SubElement(root, 'channelvotes')
        
        ctx.tree = ET.ElementTree(root)
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        
        await ctx.send(':thumbsup: **{}** (`{}`) server config have been initialized.'.format(ctx.guild.name, ctx.guild.id))


    @init.before_invoke
    async def initVerify(self, ctx):
        
        def verification(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']
        
        await ctx.send(':exclamation: Are you sure you want to initialize server configs? [`Yes`/`No`]')
        reply = await self.bot.wait_for('message', check=verification, timeout = 5)
        
        if reply.content.lower() == 'no':
            raise commands.CommandInvokeError(':octagonal_sign: Initialization has been cancelled.')


    @commands.group()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def userAuth(self, ctx):
        # When no arguments are given, default into showing the status of userauth
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.userauth = ctx.tree.find('userauth')
                
        if ctx.subcommand_passed == None:
            if ctx.userauth.get('Status') == 'Disabled':
                await ctx.send(':x: Userauth is currently **disabled.**')
            
            elif ctx.userauth.get('Status') == 'Enabled':
                try:
                    role = discord.utils.get(ctx.guild.roles, id=int(ctx.userauth.get('AuthRoleID')))
                except:
                    role = 'None'
                finally:
                    await ctx.send(':thumbsup: userauth has been enabled with the following settings:\nMessageID: **{}**\nEmoji: **{}**\nRole: **{}**\n\nPlease be sure to set these configs with `d!userauth set <message_id> <emoji>` and `d!userauth role <role>`.'.format(ctx.userauth.get('MessageID'), self.bot.get_emoji(int(ctx.userauth.get('Emoji'))), role))
    
    @userAuth.command(name='status')
    async def userAuthStatus(self, ctx, status: str):
        if status.lower() == 'enable':
            ctx.userauth.set('Status', 'Enabled')
            ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
            try:
                role = discord.utils.get(ctx.guild.roles, id=int(ctx.userauth.get('AuthRoleID')))
            except:
                role = 'None'
            finally:
                await ctx.send(':thumbsup: userauth has been enabled with the following settings:\nMessageID: **{}**\nEmoji: **{}**\nRole: **{}**\n\nPlease be sure to set these configs with `userauth set <message_id> <emoji>` and `d!userauth role <role>`.'.format(ctx.userauth.get('MessageID'), self.bot.get_emoji(int(ctx.userauth.get('Emoji'))), role))
        
        elif status.lower() == "disable":
            ctx.userauth.set('Status', 'Disabled')
            
            ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
            await ctx.send(':octagonal_sign: userauth has been disabled.')
            
        else:
            await ctx.send(':octagonal_sign: Must be enable or disable.')
        
        
    @userAuth.command(name='role')
    async def userAuthRole(self, ctx, role: discord.Role):
        ctx.userauth.set('AuthRoleID', str(role.id))
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        
        await ctx.send(':thumbsup: Role: **{}** has been saved.'.format(discord.utils.get(ctx.guild.roles, id=int(ctx.userauth.get('AuthRoleID')))))


    @userAuth.command(name='set')
    async def userAuthSet(self, ctx, msg_id, emote: discord.Emoji):
        ctx.userauth.set('MessageID', msg_id)
        ctx.userauth.set('Emoji', str(emote.id))
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        
        await ctx.send(':thumbsup: Message **({})** and emoji id **({})** has been saved.'.format(ctx.userauth.get('MessageID'), ctx.userauth.get('Emoji')))


    @commands.group()
    async def channelVotes(self, ctx):
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.channelvotes = ctx.tree.find('channelvotes')
        
        if ctx.subcommand_passed == None:
            message = ''
            if ctx.channelvotes.get('Status') == 'Enabled':
                message += ':thumbsup: Automated Channel Votings are currently enabled.'
                
            else:
                message += ':octagonal_sign: Automated Channel Votings are currently disabled.'
            
            query = list(discord.utils.get(ctx.guild.channels, id=int(voteon.get('Channel_ID'))).mention for voteon in ctx.channelvotes.findall('voteon'))
            if len(query) == 0:
                message += '\n\nNo channels are currently set up for automated voting.'
            else:
                message += '\n\nChannels set for automated voting are:\n**' + '\n'.join(query)+'**'
            
            await ctx.send(message)
    
    
    @channelVotes.command(name='status')
    async def channelVotesStatus(self, ctx, status=''):
        if status.lower() == 'enable':
            ctx.channelvotes.set('Status', 'Enabled')
            ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
                
            query = list(discord.utils.get(ctx.guild.channels, id=int(voteon.get('Channel_ID'))).mention for voteon in ctx.channelvotes.findall('voteon'))
            if len(query) == 0:
                await ctx.send(':thumbsup: Userauth is currently **enabled**.\nNo channels are currently set up for automated voting.')
            else:
                await ctx.send(':thumbsup: Userauth is currently **enabled**.\nChannels set for automated voting are:\n**' + '\n'.join(query)+'**')
            
        elif status.lower() == "disable":
            ctx.channelvotes.set('Status', 'Disabled')
            
            ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
            await ctx.send(':octagonal_sign: Automated channel votings has been disabled.')
    
        else:
            message = ''
            if ctx.channelvotes.get('Status') == 'Enabled':
                message += ':thumbsup: Automated Channel Votings are currently enabled.'
                
            else:
                message += ':octagonal_sign: Automated Channel Votings are currently disabled.'
            
            query = list(discord.utils.get(ctx.guild.channels, id=int(voteon.get('Channel_ID'))).mention for voteon in ctx.channelvotes.findall('voteon'))
            if len(query) == 0:
                message += '\n\nNo channels are currently set up for automated voting.'
            elif status == '':
                message += '\n\nChannels set for automated voting are:\n**' + '\n'.join(query)+'**'
            
            await ctx.send(message)
            
    
    @channelVotes.command(name='add')
    async def channelVotesAdd(self, ctx, channel: discord.TextChannel):
        if str(channel.id) in list(element.get('Channel_ID') for element in ctx.channelvotes.iter('voteon')):
            query = list(discord.utils.get(ctx.guild.channels, id=int(voteon.get('Channel_ID'))).mention for voteon in ctx.channelvotes.findall('voteon'))
            raise commands.BadArgument('{} already exists in the channel lists.\n\n'.format(channel.mention) + 'Channels set for automated voting are:\n**' + '\n'.join(query)+'**')
        
        ET.SubElement(ctx.channelvotes, 'voteon', Channel_ID='{}'.format(channel.id))
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await ctx.send(':trumpet: Channel {} has been added to the automated votings list.'.format(channel.mention))

        
    @channelVotes.command(name='remove', aliases= ['rm', 'delete', 'del'])
    async def channelVotesRemove(self, ctx, channel: discord.TextChannel):
        for element in ctx.channelvotes.iter('voteon'):
            if discord.utils.get(ctx.guild.channels, id=int(element.get('Channel_ID'))) == channel:
                ctx.channelvotes.remove(element)
                ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
                await ctx.send(':trumpet: Channel {} has been removed from the automated votings list.'.format(channel.mention))
                return
        await ctx.send(':exclamation: Channel {} is already not on the current automated votings.'.format(channel))

        
def setup(bot):
    bot.add_cog(AdminCog(bot))