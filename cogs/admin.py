import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from discord import PartialEmoji
from discord import Emoji

class AdminCog():

    # Static variable
    #emotes_to_define = ['cirnoWow', 'cirnoBaka', 'cirnoNoWork']

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.guild is not None and (ctx.author.guild_permissions.administrator or ctx.author.id == self.bot.owner_id)


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
    async def username(self, ctx, *, name:str):
        await self.bot.user.edit(username=name)
        await ctx.send("Username changed to {}".format(name))


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def init(self, ctx):
        if not os.path.isdir('server_data/{}'.format(ctx.guild.id)):
            os.makedirs('server_data/{}'.format(str(ctx.guild.id)))

        root = ET.Element('data')

        ET.SubElement(root, 'userauth', Status='Disabled', AuthRoleID='None', MessageID='None', Emoji='None')
        ET.SubElement(root, 'autovote', Status='Disabled')
        ET.SubElement(root, 'channelvotes')
        ET.SubElement(root, 'selfroles')
        selfroles = root.find('selfroles')
        ET.SubElement(selfroles, 'msg_id', Value='-42')
        ET.SubElement(selfroles, 'ch_id', Value='-42')

        #emotes_defined = [None for _ in
        #consider eval/exec commands
        cirnoWow = None
        cirnoBaka = None
        cirnoNoWork = None

        for emoji in self.bot.emojis:
            if emoji.name == 'cirnoWow':
                cirnoWow = emoji.id
            elif emoji.name == 'cirnoBaka':
                cirnoBaka = emoji.id
            elif emoji.name == 'cirnoNoWork':
                cirnoNoWork = emoji.id

        ET.SubElement(root, 'command_emojis', Wow=str(cirnoWow), Baka=str(cirnoBaka), NoWork=str(cirnoNoWork))

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


    @commands.group()
    async def selfrole(self, ctx):
        if ctx.invoked_subcommand is None:
            tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
            emojis = tree.find('command_emojis')
            await ctx.send('Invalid command {}'.format(self.bot.get_emoji(int(emojis.get('Baka')))))


    @selfrole.command()
    async def add(self, ctx, emoji:str, *, msg:str):
        """
        <emoji> <role>
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')
        # Requirements checking
        has_emoji = False
        if(emoji[0] == '<' and emoji[-1] == '>' and ':' in emoji):
            emoji = emoji.split(':')[1] # This is the name
        for e in ctx.guild.emojis:
            if e.name == emoji:
                has_emoji = True
                break
        if (not has_emoji):
            raise commands.CommandInvokeError("Emoji {} is not a valid emoji".format(emoji))
        has_role = False
        for r in ctx.guild.roles:
            if r.name == msg:
                has_role = True
                break
        if(not has_role):
            raise commands.CommandInvokeError("Role {} is not a valid role in the server".format(msg))

        # Functional code
        if(s_rolelist == None):
            raise commands.CommandInvokeError("Role list has not been initialized")
        else:
            # A little more checking actually
            curr_assoc = s_rolelist.find(emoji)
            if(curr_assoc != None):
                raise commands.CommandInvokeError("Error: {} is already bound to a role. Please unassign the emoji before assigning it to a different role.".format(emoji))
            role_already_bound = False
            for e in s_rolelist.iter():
                if e.get("Role") == msg:
                    role_already_bound = True
                    break
            if (role_already_bound):
                raise commands.CommandInvokeError("Error: {} is already bound to an emoji. Please unbind the emoji and the role.".format(msg))

            # (actually) functional code
            ET.SubElement(s_rolelist, emoji, Role=msg)
            tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
            await self.change_selfroles_msg(ctx, discord.utils.get(ctx.guild.emojis, name=emoji), True)
            await ctx.send("Emoji :{}: successfully registered with role {}".format(emoji, msg))


    @selfrole.command()
    async def remove(self, ctx, emoji:str):
        """
        <emoji>
        :param ctx:
        :param emoji:
        :return:
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')
        # Requirements checking
        has_emoji = False
        if (emoji[0] == '<' and emoji[-1] == '>' and ':' in emoji):
            emoji = emoji.split(':')[1]  # This is the name
        for e in ctx.guild.emojis:
            if e.name == emoji:
                has_emoji = True
                break
        if not has_emoji:
            raise commands.CommandInvokeError("Emoji {} is not a valid emoji".format(emoji))

        # Functional code (the part that does stuff)
        if (s_rolelist == None):
            raise commands.CommandInvokeError("Role list has not been initialized")
        else:
            curr_assoc = s_rolelist.find(emoji)
            if (curr_assoc == None):
                raise commands.CommandInvokeError("Error: {} is not bound to a role.".format(emoji))

            old_role = curr_assoc.get("Role")
            s_rolelist.remove(curr_assoc)
            tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
            await self.change_selfroles_msg(ctx, discord.utils.get(ctx.guild.emojis, name=emoji), False)
            await ctx.send("Emoji :{}: successfully removed; previously assigned to role {}".format(emoji, old_role))


    async def _get_list(self, ctx):
        msg = ''
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')  # Short for self_role_list
        for e in s_rolelist.iter():
            if e.tag in ('selfroles', 'msg_id', 'ch_id'):
                continue
            msg += str(discord.utils.get(ctx.guild.emojis, name=e.tag)) + ': ' + str(e.get("Role")) + '\n'
        return msg


    @selfrole.command()
    async def list(self, ctx):

        msg = "Registered emojis:\n" + await self._get_list(ctx)
        if msg == "Registered emojis:\n":
            await ctx.send("You have not registered any emojis yet! Add an emoji by typing c!selfrole add <emoji> <role>")
        else:
            await ctx.send(msg)


    @selfrole.command()
    async def create(self, ctx, new_channel_id = -21):
        '''
        [channel_id]
        :param ctx: A context object.
        :param channel_id: Integer ID of intended channel.
        :return: None.

        Moves the selfroles message to a new channel, or creates one if it doesn't exist.
        '''
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')
        ctx.selfroles_msg_id = int(s_rolelist.find('msg_id').get('Value'))
        ctx.selfroles_roles_ch = int(s_rolelist.find('ch_id').get('Value'))
        if (new_channel_id == -21):
            channel_id = ctx.channel.id
        else:
            channel_id = new_channel_id
        if (ctx.selfroles_roles_ch != -42):
            try:
                old_msg_obj = await self.bot.get_channel(ctx.selfroles_roles_ch).get_message(
                    ctx.selfroles_msg_id)
                await old_msg_obj.delete()
            except ValueError:
                raise
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')
        msg_str = "Add a reaction of whatever corresponds to the role you want." \
                  " If you want to remove the role, remove the reaction\n" + await self._get_list(ctx)
        msg_obj = await self.bot.get_channel(channel_id).send(msg_str)
        s_rolelist.find('msg_id').set('Value', str(msg_obj.id))
        s_rolelist.find('ch_id').set('Value', str(channel_id))

        for emoji_name in s_rolelist.iter():
            if emoji_name.tag in ('selfroles', 'msg_id', 'ch_id'):
                continue
            emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name.tag)
            await msg_obj.add_reaction(emoji)

        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))


    async def change_selfroles_msg(self, ctx, emoji:Emoji, to_add:bool):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        s_rolelist = tree.find('selfroles')
        ctx.selfroles_msg_id = int(s_rolelist.find('msg_id').get('Value'))
        ctx.selfroles_roles_ch = int(s_rolelist.find('ch_id').get('Value'))
        msg_obj = await self.bot.get_channel(ctx.selfroles_roles_ch).get_message(ctx.selfroles_msg_id)
        msg_str = "Add a reaction of whatever corresponds to the role you want. If you want to remove the role, remove the reaction\n" + await self._get_list(ctx)
        await msg_obj.edit(content = msg_str)
        if(to_add):
            await msg_obj.add_reaction(emoji)
        else:
            await msg_obj.remove_reaction(emoji, self.bot.user)


def setup(bot):
    bot.add_cog(AdminCog(bot))
