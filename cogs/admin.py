import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from cogs.helper import HelperCog
AllEmoji = HelperCog.AllEmoji


class AdminCog():

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
        msg = ET.SubElement(selfroles, 'message')
        msg_id = ET.SubElement(msg, 'id')
        msg_id.text = '-42'
        ch = ET.SubElement(selfroles, 'channel')
        ch_id = ET.SubElement(ch, 'id')
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


    @selfrole.group(name='group')
    async def selfroleGroup(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n" +
                           "Use \"c!help selfrole group\" for a list of valid commands")


    @rolesManage.command(name='add')
    async def selfroleAdd(self, ctx, group: str, emoji: AllEmoji, *, role: discord.Role):
        """
        Associates an emoji with a role for use in selfrole assignment.
        """
        group_str = group   # Rename to avoid confusion in code

        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        if selfrole_list is None:
            raise commands.CommandInvokeError("Role list has not been initialized")
        associations = selfrole_list.find('associations')
        groups = associations.findall('group')
        group_obj = self._find_group(groups, group_str)
        if group_obj is None:
            raise ValueError("Group **{}** does not exist".format(group_str))

        # Check if emoji is bound to role
        for g in groups:
            for assoc in g.findall('assoc'):
                if assoc.find('emoji').text == str(emoji):
                    raise commands.CommandInvokeError(
                        "Error: {} is already bound to a role. Please unassign the emoji before assigning it to a different role.".format(
                            emoji))
                if assoc.find('role').find('id').text == str(role.id):
                    raise commands.CommandInvokeError(
                        "Error: \"{}\" is already bound to an emoji. Please unbind the emoji and the role.".format(role.name))

        # functional code
        associations_in_group = group_obj.findall('assoc')
        insert_at_end = True
        new_assoc = None
        for index in range(len(associations_in_group)):
            if role.name < associations_in_group[index].find('role').find('name').text:
                insert_at_end = False
                new_assoc = ET.Element('assoc')
                group_obj.insert(index, new_assoc)
                break
        if insert_at_end:
            new_assoc = ET.SubElement(group_obj, 'assoc')
        new_assoc_emoji = ET.SubElement(new_assoc, 'emoji')
        new_assoc_emoji.text = str(emoji)
        new_assoc_role = ET.SubElement(new_assoc, 'role')
        new_assoc_role_name = ET.SubElement(new_assoc_role, 'name')
        new_assoc_role_name.text = role.name
        new_assoc_role_id = ET.SubElement(new_assoc_role, 'id')
        new_assoc_role_id.text = str(role.id)
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await self.edit_selfrole_msg(ctx, group_obj, True, emoji, True)
        await ctx.send("Emoji {} successfully registered with role \"{}\"".format(emoji, role.name))


    @rolesManage.command(name='del')
    async def selfroleRemove(self, ctx, *, role: discord.Role):
        """
        Removes an emoji/role association.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        if not selfrole_list:
            raise commands.CommandInvokeError("Role list has not been initialized")
        associations = selfrole_list.find('associations')

        # Check if emoji is bound to role
        groups_list = associations.findall('group')
        curr_assoc = None
        group_containing_role = None
        for group in groups_list:
            group_assocs = group.findall('assoc')
            for a in group_assocs:
                if a.find('role').find('id').text == str(role.id):
                    group_containing_role = group
                    curr_assoc = a
                    break
        if not group_containing_role:
            raise commands.CommandInvokeError("Error: {} is not currently bound to an emoji.".format(role))

        old_emoji = await AllEmoji().convert(ctx, curr_assoc.find('emoji').text)
        group_containing_role.remove(curr_assoc)
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await self.edit_selfrole_msg(ctx, group_containing_role, True, old_emoji, False)
        await ctx.send("Role \"{}\" successfully removed; previously bound to emoji {}".format(role, old_emoji))


    async def edit_selfrole_msg(self, ctx, group: "XML Element", change_emoji: bool, emoji: AllEmoji = None, to_add: bool = None):
        """
        Adds or removes a role from the corresponding message if it exists.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        channel_id = int(selfrole_list.find('channel').find('id').text)
        if channel_id != -42:
            group_msg_id = int(group.find('message').find('id').text)
            msg_obj = await self.bot.get_channel(channel_id).get_message(group_msg_id)
            embed = await self._get_single_group_msg(group)
            await msg_obj.edit(embed=embed)
            if change_emoji:
                if to_add:
                    await msg_obj.add_reaction(emoji)
                else:
                    await msg_obj.remove_reaction(emoji, self.bot.user)


    async def add_delete_selfrole_msg(self, ctx, group: "XML Element", to_add: bool):
        """
        Adds or removes a group if necessary/possible.

        Warning: this WILL modify the group's message id parameter.
        (See RoleChStat at the top of this file for details on what 'single' mode is)
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        selfroles_ch_id = int(selfrole_list.find('channel').find('id').text)
        if selfroles_ch_id != -42:
            if to_add:
                msg_obj = await self.bot.get_channel(selfroles_ch_id).send(
                    embed=await self._get_single_group_msg(group))
                group.find('message').find('id').text = str(msg_obj.id)
            else:
                msg_id = int(group.find('message').find('id').text)
                msg_obj = await self.bot.get_channel(selfroles_ch_id).get_message(msg_id)
                await msg_obj.delete()
                group.find('message').find('id').text = str(-42)


    async def _get_single_group_msg(self, group: "XML Element") -> discord.Embed:
        title = "Group **{}**\n".format(group.find('name').text)
        req_role = group.find('req_role').text
        desc = ""
        if req_role:
            desc = "(requires {})".format(req_role)
        added_element = False
        assoc_list = group.findall('assoc')
        msg_left = ""
        msg_right = ""
        divider = len(assoc_list)/2
        for index in range(len(assoc_list)):
            assoc = assoc_list[index]
            added_element = True
            msg = "\t" + assoc.find('emoji').text + ' **:** ' + str(assoc.find('role').find('name').text) + ' ​ ​\n'
            if index < divider:
                msg_left += msg
            else:
                msg_right += msg
        embed = discord.Embed(title=title, description=desc)
        if not added_element:
            msg_left = "Empty!"
        embed.add_field(name="----------------------", value=msg_left, inline=True)
        if msg_right:
            embed.add_field(name="----------------------", value=msg_right, inline=True)
        return embed


    async def _listing_command(self, ctx):
        # NOTE: the message below uses a static prefix. Modify later to dynamically determine the prefix
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        if not groups_list:
            await ctx.send(
                "You have not registered any groups yet! Add an group by typing c!selfrole group add <group>")
        else:
            await ctx.send("Registered emojis:\n\n")
            for group in groups_list:
                await ctx.send(embed=await self._get_single_group_msg(group))


    @selfrole.command(name='list')
    async def selfroleList(self, ctx):
        """
        Lists all currently registered emoji/role associations.

        This command functions the same as c!selfrole role list.
        """
        await self._listing_command(ctx)


    @rolesManage.command(name='list')
    async def selfroleRoleList(self, ctx):
        """
        Lists all currently registered emoji/role associations.

        This command functions the same as c!selfrole list.
        """
        await self._listing_command(ctx)


    def _conv_to_id_list(self, msg_id_text: str) -> [int]:
        """

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))


    def _conv_to_msg_text(self, msg_id_list: [int]) -> str:
        return ' '.join(str(i) for i in msg_id_list)


    def _remove_item_from_list(self, item_list: list, item) -> list:
        item_list = [i for i in item_list if i != item]
        return item_list


    async def _delete_message(self, ctx, group_name: str, suppress_output = False) -> [int]:
        """
        Deletes the existing selfroles message.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')

        msg_id_list = self._conv_to_id_list(selfrole_list.find('message').find('id').text)
        ch_id = int(selfrole_list.find('channel').find('id').text)
        if ch_id == -42:
            raise commands.CommandInvokeError("Error: no selfrole assignment messages currently exist.")

        channel = self.bot.get_channel(ch_id)
        groups_list = associations.findall('group')
        if group_name == '*':
            delmsg = ":bomb: All existing role assignment messages have been destroyed"
            for msg_id in msg_id_list:
                message = await channel.get_message(msg_id)
                await message.delete()
                for group in groups_list:
                    if int(group.find('message').find('id').text) == msg_id:
                        group.find('message').find('id').text = str(-42)
                        break
            msg_id_list = []

            selfrole_list.find('message').find('id').text = str(-42)
            selfrole_list.find('channel').find('id').text = str(-42)
        else:
            delmsg = ":x: Target message does not exist"
            for group in groups_list:
                if group.find('name').text != group_name:
                    continue
                msg_id = int(group.find('message').find('id').text)
                if msg_id != -42:
                    message = await channel.get_message(msg_id)
                    await message.delete()
                    group.find('message').find('id').text = str(-42)
                    msg_id_list = self._remove_item_from_list(msg_id_list, msg_id)
                    selfrole_list.find('message').find('id').text = self._conv_to_msg_text(msg_id_list)
                    delmsg = ":bomb: Target message has been destroyed"
                break
            if len(msg_id_list) == 1:
                message = await channel.get_message(msg_id_list[0])
                await message.delete()
                selfrole_list.find('message').find('id').text = str(-42)
                selfrole_list.find('channel').find('id').text = str(-42)
                msg_id_list = []

        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))  # Writes the channel and message id
        if not suppress_output:
            await ctx.send(delmsg)

        return msg_id_list


    async def _build_message(self, ctx, group_name: str, suppress_output_str: str, channel: discord.TextChannel = None):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        curr_channel_id = int(selfrole_list.find('channel').find('id').text)

        if group_name != '*':
            target_group = self._find_group(associations.findall('group'), group_name)
            if not target_group:
                raise ValueError("Group **{}** does not exist".format(group_name))

        if suppress_output_str in ['true', 'false']:
            suppress_output = suppress_output_str == 'true'
        else:  # Default behavior
            suppress_output = channel is None

        if channel is None:  # No channel specified by user
            if curr_channel_id != -42:
                destination_channel = self.bot.get_channel(curr_channel_id)
                suppress_output = curr_channel_id == ctx.message.channel.id
            else:
                destination_channel = ctx.message.channel
        elif curr_channel_id != channel.id and group_name != '*':
            raise commands.CommandInvokeError(":x: Error: Cannot create role assignment messages in multiple channels")
        else:
            destination_channel = channel

        if curr_channel_id == -42:
            msg_id_list = []
        else:
            msg_id_list = await self._delete_message(ctx, group_name, suppress_output)  # Receives updated message list

        if len(msg_id_list) == 0:
            msg_obj = await destination_channel.send("Add a reaction of whatever corresponds to the role you want."
                                                     " If you want to remove the role, remove the reaction")
            msg_id_list.append(msg_obj.id)

        for group in associations.findall('group'):
            if group_name != '*' and group.find('name').text != group_name:
                continue
            msg_obj = await destination_channel.send(embed=await self._get_single_group_msg(group))
            msg_id_list.append(msg_obj.id)
            group.find('message').find('id').text = str(msg_obj.id)

            # Add emoji to message
            for assoc in group.findall('assoc'):
                emoji = await AllEmoji().convert(ctx, assoc.find('emoji').text)
                await msg_obj.add_reaction(emoji)
            if group_name != '*':
                break

        selfrole_list.find('channel').find('id').text = str(destination_channel.id)
        selfrole_list.find('message').find('id').text = self._conv_to_msg_text(msg_id_list)
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))  # Writes the channel and message id

        if not suppress_output:
            await ctx.send(":thumbsup: New selfroles message successfully created!")


    @selfrole.group(name='mkmsg')
    async def selfroleMsgCreate(self, ctx, group: str = "*", target_channel: discord.TextChannel = None, suppress_output = 'default'):
        """
        Creates a selfrole assignment message in the target channel if specified.

        Default channel varies. If no messages exist, target_channel will be the channel the command was typed in.
        If messages exist, it will default to the channel where messages currently exist.

        If group is specified, this command will only print the message corresponding to that group.

        If suppress_output is set to 'true', will not print out any confirmation messages. This is usually set to false
        by default, unless the target channel is the current channel.
        """
        if target_channel:
            await self._build_message(ctx, group, suppress_output, target_channel)
        else:
            await self._build_message(ctx, group, suppress_output)


    @selfrole.command(name='delmsg')
    async def selfroleMsgDestroy(self, ctx, group: str = "*", suppress_output = 'default'):
        """
        Destroys the selfrole assignment message for the specified group, or all messages if not specified.

        If suppress_output is set to 'true', will not print out any confirmation messages. This is usually set to false
        by default, unless the target channel is the current channel.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        ch_id = int(selfrole_list.find('channel').find('id').text)

        if suppress_output in ['true', 'false']:
            s = suppress_output == 'true'
        else:  # Default behavior
            s = ctx.message.channel.id == ch_id
        await self._delete_message(ctx, group, s)


    @selfrole.command(name="help")
    async def selfroleHelp(self, ctx):
        """
        Doesn't actually help right now
        """
        await ctx.send("This command is currently being worked on! Stay tuned for more details <:cirnoSmile:469040364045729792>")


    @selfroleGroup.command(name="add")
    async def groupCreate(self, ctx, name: str, *, requiredRole: discord.Role = "", maxSelectable: int = 'all'):
        """
        Creates a group that holds roles. Group names cannot contain whitespace.

        maxSelectable represents the maximum number of roles a user can select from the group. By default, all roles
        from a group may be assigned at once. Setting this number to 0 will have the same effect.
        """
        if name == '*':
            raise commands.CommandInvokeError(":x: ERROR: Name ***** is reserved.")
        if type(maxSelectable) == int and maxSelectable <= 0:
            maxSelectable = 'all'
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        if not (self._find_group(groups_list, name) is None):
            raise commands.CommandInvokeError(":x: ERROR: group name **{}** already in use".format(name))

        # Insert the element in the correct location
        insert_at_end = True
        group = None
        for index in range(len(groups_list)):
            if name < groups_list[index].find('name').text:
                insert_at_end = False
                group = ET.Element('group')
                associations.insert(index, group)
                break
        if insert_at_end:
            group = ET.SubElement(associations, 'group')
        group_name = ET.SubElement(group, 'name')
        group_name.text = name
        msg = ET.SubElement(group, 'message')
        msg_id = ET.SubElement(msg, 'id')
        group_role = ET.SubElement(group, 'req_role')
        group_max_select = ET.SubElement(group, 'max_select')
        [msg_id.text, group_role.text, group_max_select.text] = ['-42', str(requiredRole), str(maxSelectable)]

        await self.add_delete_selfrole_msg(ctx, group, True)
        msg_id_list = self._conv_to_id_list(selfrole_list.find('message').find('id').text) + [group.find('message').find('id').text]
        selfrole_list.find('message').find('id').text = self._conv_to_msg_text(msg_id_list)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))
        await ctx.send("Group **{}** successfully created!".format(name))


    @selfroleGroup.command(name="del")
    async def groupDelete(self, ctx, name: str):
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        targetGroup = None
        num_roles = -1
        for group in associations.findall('group'):
            if group.find('name').text == name:
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

        msg_id = int(targetGroup.find('message').find('id').text)
        await self.add_delete_selfrole_msg(ctx, targetGroup, False)
        msg_id_list = self._remove_item_from_list(self._conv_to_id_list(selfrole_list.find('message').find('id').text), msg_id)
        selfrole_list.find('message').find('id').text = self._conv_to_msg_text(msg_id_list)
        associations.remove(targetGroup)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))
        await ctx.send("Group **{}** successfully deleted.".format(name))


    @selfroleGroup.group(name="mod")
    async def groupModify(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n")


    @groupModify.command(name="name")
    async def group_change_name(self, ctx, oldName: str, newName: str):
        """
        Renames a group.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        group = self._find_group(groups_list, oldName)
        if group:
            group.find('name').text = newName
            await self.edit_selfrole_msg(ctx, group, False)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))


    @groupModify.command(name="role")
    async def group_change_role(self, ctx, groupName: str, *, newRole: discord.Role = ""):
        """
        Changes the role requirement for the specified group to newRole.
        """
        tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        selfrole_list = tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        group = self._find_group(groups_list, groupName)
        if group:
            group.find('req_role').text = str(newRole)
            await self.edit_selfrole_msg(ctx, group, False)
        tree.write('server_data/{}/config.xml'.format(ctx.guild.id))


    def _find_group(self, groups_list: list, name: str) -> "XML Element":
        for group in groups_list:
            if group.find('name').text == name:
                return group
        return None


def setup(bot):
    bot.add_cog(AdminCog(bot))
