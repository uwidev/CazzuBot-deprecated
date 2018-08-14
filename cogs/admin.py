import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
import emoji as emoji_module

class AdminCog():

    def __init__(self, bot):
        self.bot = bot
        self._excluded_selfroles_tags = ('selfroles', 'custom', 'unicode', 'count', 'emoji_roles', 'msg_id', 'ch_id')

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
            await ctx.send('{}'.format(error.original))
             
        elif isinstance(error, commands.BadArgument):
            await ctx.send(':x: ERROR: {}'.format(' '.join(error.args)))
             
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(':x: ERROR: {} is a required argument.'.format(error.param.name))
             
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
     
     
    async def status(self, ctx, v):
        class sta():
            def __init__(self, s):
                self.id = s
                self.name = s
        
        return sta(v) if v.lower() in ['enabled', 'disabled'] else False
        
    
    async def role(self, ctx, v):
        r = await commands.RoleConverter().convert(ctx, v)
        return r
    
        
    async def message(self, ctx, v):
        msg = await ctx.get_message(int(v))
        return msg
        
    
    async def emoji(self, ctx, v):
        e = await commands.EmojiConverter().convert(ctx, v)
        return e
        
        
    '''
    Write message and status as converters
    '''
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def init(self, ctx):
        if not os.path.isdir('server_data/{}'.format(ctx.guild.id)):
            os.makedirs('server_data/{}'.format(str(ctx.guild.id)))

        root = ET.Element('data')        
        userauth = ET.SubElement(root, 'userauth')
        
        auth_status = ET.SubElement(userauth, 'status')
        auth_status.text = 'disabled'
        
        auth_authRole = ET.SubElement(userauth, 'role')
        auth_authRole.text = 'Not yet set'
        
        auth_message = ET.SubElement(userauth, 'message')
        auth_message.text = 'Not yet set'
        
        auth_emoji = ET.SubElement(userauth, 'emoji')
        auth_emoji.text = 'Not yet set'

        selfroles = ET.SubElement(root, 'selfroles')
        ET.SubElement(selfroles, 'associations')
        msg_id = ET.SubElement(selfroles, 'msg_id')
        msg_id.text = '-42'
        ch_id = ET.SubElement(selfroles, 'ch_id')
        ch_id.text = '-42'

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


    @commands.command()
    async def configs(self, ctx):        
        root = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id)).getroot()
        msg = ''
        dis = '    {0}: {1}\n'
        
        for E in root:
            msg += '**{}**\n'.format(E.tag)
            for e in E:
                cvalue = await eval('self.{0}(ctx, "{1}")'.format(e.tag, e.text))
                if e.tag in ['role']:
                    msg += dis.format(e.tag, cvalue.name)
                elif e.tag in ['emoji']:
                    msg += dis.format(e.tag, cvalue)
                elif e.tag in ['status', 'message']:
                    msg += dis.format(e.tag, cvalue.id)                
            msg += '\n'
        await ctx.send(msg)
        
        
    @commands.group()
    async def edit(self, ctx, group, setting, *value):        
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        root = tree.getroot()
        
        if group.lower() in (element.tag for element in root):
            E = root.find(group)
            e = E.find(setting)
            
            val =  ' '.join(value)
            obj = await eval('self.{}(ctx, val)'.format(setting))
            print(type(obj), obj)
            if obj.id:
                
                e.text = str(obj.id)

            tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
    
     

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
                    await ctx.send(':thumbsup: User Authentication has been enabled')

                    
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
                await ctx.send(':thumbsup: userauth has been enabled with the following settings:\nMessageID: **{}**\nEmoji: **{}**\nRole: **{}**\n\nPlease be sure to set these configs with `userauth set <message_id> <emoji>` and `d!userauth role <role>`.'.format(ctx.userauth.get('MessageID'), self.bot.get_emoji(int(ctx.userauth.get('EmojiID'))), role))
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
            await ctx.send('Invalid command <:cirnoNoWork:469040364460834817>')


    @selfrole.group(name='role')
    async def rolesManage(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n" +
                           "Use \"c!help selfrole role\" for a list of valid commands")


    @selfrole.group(name="group")
    async def selfroleGroup(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n" +
                           "Use \"c!help selfrole group\" for a list of valid commands")


    @rolesManage.command(name='add')
    async def selfroleAdd(self, ctx, group: str, emoji: str, *, role: str):
        """
        Associates an emoji with a role for use in selfrole assignment.

        Notes: default group should be set to -- in the future. (It's not right now- don't try it)
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        if selfrole_list == None:
            raise commands.CommandInvokeError("Role list has not been initialized")
        
        associations = selfrole_list.find('associations')
        if associations == None:
            raise commands.CommandInvokeError("Please reinitialize server configs to use this command")

        groups = associations.findall('group')

        if not self._group_exists(groups, group):
            raise commands.CommandInvokeError(":x: ERROR: Group **{}** does not exist".format(group))

        # Requirements checking

        # Check emoji existence
        has_emoji = False
        custom_emoji = True

        if emoji[0] == '<' and emoji[-1] == '>' and ':' in emoji:
            emoji = emoji.split(':')[1] # This is the name in the custom emoji format used by Discord
        for e in ctx.guild.emojis:
            if e.name == emoji:
                has_emoji = True
                break
        if not has_emoji:
            custom_emoji = False
            try:
                await ctx.message.add_reaction(emoji)
                await ctx.message.remove_reaction(emoji, self.bot.user)
            except commands.CommandInvokeError:
                raise commands.CommandInvokeError("Emoji {} is not a valid emoji".format(emoji))

        # Check role existence
        has_role = False
        for r in ctx.guild.roles:
            if r.name == role:
                has_role = True
                break
        if not has_role:
            raise commands.CommandInvokeError("Role \"{}\" is not a valid role in the server".format(role))

        # Check if emoji is bound to role
        search_string = str(discord.utils.get(ctx.guild.emojis, name=emoji)) if custom_emoji else emoji
        assoc_list = self._get_all_associations(groups)
        for element in assoc_list:
            if element.find('emoji').text == search_string:
                raise commands.CommandInvokeError(
                    "Error: {} is already bound to a role. Please unassign the emoji before assigning it to a different role.".format(
                        search_string))
            if element.find('role').text == role:
                raise commands.CommandInvokeError(
                    "Error: \"{}\" is already bound to an emoji. Please unbind the emoji and the role.".format(role))

        # functional code
        group_obj = None
        for g in groups:
            if g.get('name') == group:
                group_obj = g
                break
        new_assoc = ET.SubElement(group_obj, 'assoc', {'custom': str(1 if custom_emoji else 0)})
        new_assoc_emoji = ET.SubElement(new_assoc, 'emoji')
        new_assoc_emoji.text = search_string
        new_assoc_role = ET.SubElement(new_assoc, 'role')
        new_assoc_role.text = role
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await self.change_selfroles_msg_role(ctx, group_obj, search_string, True, custom_emoji)
        await ctx.send("Emoji {} successfully registered with role \"{}\"".format(search_string, role))


    @rolesManage.command(name='del')
    async def selfroleRemove(self, ctx, *, role: str):
        """
        Removes an emoji/role association.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        if not selfrole_list:
            raise commands.CommandInvokeError("Role list has not been initialized")

        associations = selfrole_list.find('associations')
        if not associations:
            raise commands.CommandInvokeError("Please reinitialize server configs to use this command")

        # Requirements checking

        # Check role existence
        has_role = False
        for r in ctx.guild.roles:
            if r.name == role:
                has_role = True
                break
        if not has_role:
            raise commands.CommandInvokeError("Role \"{}\" is not a valid role in the server".format(role))

        # Check if emoji is bound to role
        groups_list = associations.findall('group')
        curr_assoc = None
        group_containing_role = None
        for group in groups_list:
            group_assocs = group.findall('assoc')
            for a in group_assocs:
                if a.find('role').text == role:
                    group_containing_role = group
                    curr_assoc = a
                    break
        if not group_containing_role:
            raise commands.CommandInvokeError("Error: {} is not currently bound to an emoji.".format(role))

        old_emoji = curr_assoc.find('emoji').text
        is_custom = bool(int(curr_assoc.get('custom')))
        group_containing_role.remove(curr_assoc)
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await self.change_selfroles_msg_role(ctx, group_containing_role, old_emoji, False, is_custom)
        await ctx.send("Role \"{}\" successfully removed; previously bound to emoji {}".format(role, old_emoji))

    async def change_selfroles_msg_role(self, ctx, group: "XML Element", emoji: str, to_add: bool, custom: bool):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        # ctx.selfroles_msg_id = int(s_rolelist.find('msg_id').text)
        selfroles_ch_id = int(selfrole_list.find('ch_id').text)
        # associations = selfrole_list.find('associations')
        if selfroles_ch_id != -42:

            # await self._build_message(ctx, selfroles_ch_id)
            group_msg_id = int(group.get('msg_id'))
            msg_obj = await self.bot.get_channel(selfroles_ch_id).get_message(group_msg_id)
            msg_str = await self._get_single_group_msg(group)
            await msg_obj.edit(content = msg_str)
            if custom:
                emoji = self.bot.get_emoji(int(emoji.split(':')[2][:-1]))
            if to_add:
                await msg_obj.add_reaction(emoji)
            else:
                await msg_obj.remove_reaction(emoji, self.bot.user)


    async def change_selfroles_msg_group(self, ctx, group: "XML Element", to_add: bool):
        """
        Warning: this WILL modify the group's 'msg_id' parameter
        :param ctx:
        :param group:
        :param to_add:
        :return:
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        selfroles_ch_id = int(selfrole_list.find('ch_id').text)
        if selfroles_ch_id != -42:
            if to_add:
                msg_obj = await self.bot.get_channel(selfroles_ch_id).send(await self._get_single_group_msg(group))
                group.set('msg_id', str(msg_obj.id))
            else:
                msg_id = int(group.get('msg_id'))
                msg_obj = await self.bot.get_channel(selfroles_ch_id).get_message(msg_id)
                await msg_obj.delete()
                group.set('msg_id', str(-42))



    async def _get_single_group_msg(self, group: "XML Element") -> str:
        msg = "Group **{}**:\n".format(group.get('name'))
        added_element = False
        for element in group.findall('assoc'):
            added_element = True
            msg += "\t" + str(element.find('emoji').text) + ' **:** ' + str(element.find('role').text) + '\n'
        if not added_element:
            msg += "\tEmpty!"
        return msg

    async def _get_msg_list(self, ctx):
        msg_list = []
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        for group in associations.findall('group'):
            msg_list.append(await self._get_single_group_msg(group))
        return msg_list


    @selfrole.command(name='list')
    async def selfroleList(self, ctx):
        """
        Lists all currently registered emoji/role associations.

        This command functions the same as c!selfrole role list.
        """

        # NOTE: the message below uses a static prefix. Modify later to dynamically determine the prefix
        msg_list = ["Registered emojis:\n\n"] + await self._get_msg_list(ctx)
        if msg_list == ["Registered emojis:\n\n"]:
            await ctx.send(
                "You have not registered any emojis yet! Add an emoji by typing c!selfrole add <emoji> <role>")
        else:
            for msg in msg_list:
                await ctx.send(msg)

    @rolesManage.command(name='list')
    async def selfroleRoleList(self, ctx):
        """
        Lists all currently registered emoji/role associations.

        This command functions the same as c!selfrole list.
        """

        # NOTE: the message below uses a static prefix. Modify later to dynamically determine the prefix
        msg_list = ["Registered emojis:\n\n"] + await self._get_msg_list(ctx)
        if msg_list == ["Registered emojis:\n\n"]:
            await ctx.send(
                "You have not registered any emojis yet! Add an emoji by typing c!selfrole add <emoji> <role>")
        else:
            for msg in msg_list:
                await ctx.send(msg)


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))


    def _conv_to_msg_text(self, msg_id_list: [int]) -> str:
        return ' '.join(str(i) for i in msg_id_list)


    async def _sg_del(self, ctx, suppress_output = False):
        """
        Deletes the existing selfroles message.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')

        msg_ids = self._conv_to_id_list(selfrole_list.find('msg_id').text)
        ch_id = int(selfrole_list.find('ch_id').text)
        if ch_id == -42:
            raise commands.CommandInvokeError("Error: selfroles message does not exist")

        channel = self.bot.get_channel(ch_id)
        for msg_id in msg_ids:
            message = await channel.get_message(msg_id)
            await message.delete()

        selfrole_list.find('msg_id').text = str(-42)
        selfrole_list.find('ch_id').text = str(-42)

        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))  # Writes the channel and message id
        if not suppress_output:
            await ctx.send(":bomb: Existing selfroles message has been destroyed")


    async def _build_message(self, ctx, target_channel_id: int, suppress_output = False):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        selfroles_ch_id = int(selfrole_list.find('ch_id').text)

        if target_channel_id == -21:
            channel_id = ctx.channel.id
        else:
            channel_id = target_channel_id

        if selfroles_ch_id != -42:
            await self._sg_del(ctx, suppress_output)

        new_channel = self.bot.get_channel(channel_id)
        msg_id_list = []
        msg_obj = await new_channel.send("Add a reaction of whatever corresponds to the role you want."
                                         " If you want to remove the role, remove the reaction")
        msg_id_list.append(msg_obj.id)

        for group in associations.findall('group'):
            msg_obj = await new_channel.send(await self._get_single_group_msg(group))
            msg_id_list.append(msg_obj.id)
            group.set('msg_id', str(msg_obj.id))

            # Add emoji to message
            for assoc in group.findall('assoc'):
                emoji_str = assoc.find('emoji').text
                if int(assoc.get('custom')):
                    await msg_obj.add_reaction(self.bot.get_emoji(int(emoji_str.split(':')[2][:-1])))
                else:
                    await msg_obj.add_reaction(emoji_str)

        selfrole_list.find('ch_id').text = str(channel_id)
        selfrole_list.find('msg_id').text = self._conv_to_msg_text(msg_id_list)

        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))  # Writes the channel and message id

        if not suppress_output:
            await ctx.send(":thumbsup: New selfroles message successfully created!")


    @selfrole.group(name='mkmsg')
    async def selfroleCreate(self, ctx, target_channel_name: discord.TextChannel, suppress_output = 'default'):
        """
        Creates a selfrole assignment message in the target channel if specified, or the current channel by default.

        If suppress_output is set to 'true', will not print out any confirmation messages. This is usually set to false
        by default, unless the target channel is the current channel.
        """
        '''
        if len(target_channel_name) > 0 and target_channel_name[:2] == '<#' and target_channel_name[-1] == '>':
            target_channel_id = int(target_channel_name[2:-1])
            if not discord.utils.get(ctx.guild.channels, id=target_channel_id):
                raise commands.CommandInvokeError("Error: Channel does not exist.")
        else:
            try:
                target_channel_id = -21 if target_channel_name == "" else discord.utils.get(ctx.guild.channels,
                                                                                            name=target_channel_name).id
            except AttributeError:
                raise commands.CommandInvokeError("Error: Channel does not exist.")
        '''
        if suppress_output in ['true', 'false']:
            s = suppress_output == 'true'
        else:  # Default behavior
            s = target_channel_id == -21 or ctx.message.channel.id == target_channel_id
        target_channel_id = target_channel_name.id
        await self._build_message(ctx, target_channel_id, s)


    @selfrole.command(name='delmsg')
    async def selfroleDestroy(self, ctx):
        """
        Destroys the existing selfroles message.
        """
        await self._sg_del(ctx, False)


    @selfrole.command(name="help")
    async def selfroleHelp(self, ctx):
        """
        Doesn't actually help right now
        """
        await ctx.send("This command is currently being worked on! Stay tuned for more details <:cirnoSmile:469040364045729792>")


    @selfroleGroup.command(name="add")
    async def sgCreate(self, ctx, name: str):
        """
        Creates a group that holds roles. Group names cannot contain whitespace.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        if self._group_exists(groups_list, name):
            raise commands.CommandInvokeError(":x: ERROR: group name **{}** already in use".format(name))
        group = ET.SubElement(associations, 'group', {'name': name, 'msg_id': str(-42)})

        await self.change_selfroles_msg_group(ctx, group, True)
        msg_id_list = self._conv_to_id_list(selfrole_list.find('msg_id').text) + [group.get('msg_id')]
        selfrole_list.find('msg_id').text = self._conv_to_msg_text(msg_id_list)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))
        await ctx.send("Group **{}** successfully created!".format(name))


    @selfroleGroup.command(name="del")
    async def sgDelete(self, ctx, name: str):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        targetGroup = None
        num_roles = -1
        for group in associations.findall('group'):
            if group.get('name') == name:
                targetGroup = group
                num_roles = len(group.findall('assoc'))
                break
        if num_roles == -1:
            raise commands.CommandInvokeError("Group **{}** doesn't exist.".format(name))

        def verification(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']

        await ctx.send(':exclamation: Are you sure you want to delete group **{}**? ({} role{}) [`Yes`/`No`]'.format(
            name, num_roles, '' if num_roles == 1 else 's'))
        reply = await self.bot.wait_for('message', check=verification, timeout=5)

        if reply.content.lower() == 'no':
            raise commands.CommandInvokeError(':octagonal_sign: Deletion of group **{}** cancelled.'.format(name))

        msg_id = int(targetGroup.get('msg_id'))
        await self.change_selfroles_msg_group(ctx, targetGroup, False)
        msg_id_list = [i for i in self._conv_to_id_list(selfrole_list.find('msg_id').text) if i != msg_id]
        selfrole_list.find('msg_id').text = self._conv_to_msg_text(msg_id_list)
        associations.remove(targetGroup)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))
        await ctx.send("Group **{}** successfully deleted.".format(name))


    def _group_exists(self, groups_list, name: str):
        exists = False
        for group in groups_list:
            if group.get('name') == name:
                exists = True
                break
        return exists


    def _get_all_associations(self, groups_list):
        assoc_list = []
        for group in groups_list:
            assoc_list.extend(group.findall('assoc'))

        return assoc_list


    @commands.command()
    async def isEmoji(self, ctx, *, emoji: str):
        d = emoji_module.demojize(emoji)
        await ctx.send(d)
        await ctx.send(str(d != emoji) + "!")


def setup(bot):
    bot.add_cog(AdminCog(bot))
