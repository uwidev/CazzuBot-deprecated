import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from discord import Emoji
import modules.utility
import modules.factory
import modules.exceptxml
import html


class AdminCog():

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.guild is not None and \
        (ctx.author.guild_permissions.administrator or \
        ctx.author.id == self.bot.owner_id)


    async def __error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == self.bot.owner_id and self.bot.super == True:
                #await ctx.send(':exclamation: Dev cooldown bypass.')
                await ctx.reinvoke()
            else:
                await ctx.channel.send(':hand_splayed: Command has a {} second cooldown. \
                Please try again after {} seconds.'\
                .format(str(error.cooldown.per)[0:3], str(error.retry_after)[0:3]))

        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send('{}'.format(error.original))

        elif isinstance(error, commands.BadArgument):
            await ctx.send(':x: ERROR: {}'.format(' '.join(error.args)))

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(':x: ERROR: {} is a required argument.'.format(error.param.name))

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(':x: ERROR: {} is a required argument.'.format(error))

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def init(self, ctx):
        '''Initializes the server configs based on modules.factory properties'''
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

        selfrole_status = ET.SubElement(selfroles, 'status')
        selfrole_status.text = 'enabled'

        await modules.factory.worker_userauth.create.all(userauth)

        ctx.tree = ET.ElementTree(root)

        await modules.utility.write_xml(ctx)
        await ctx.send(':thumbsup: **{}** (`{}`) server config have been initialized.'.format(ctx.guild.name, ctx.guild.id))


    @init.before_invoke
    async def init_verify(self, ctx):
        '''Asks the user before initializing server configs'''
        def verification(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']

        await ctx.send(':exclamation: Are you sure you want to initialize server configs? [`Yes`/`No`]')
        reply = await self.bot.wait_for('message', check=verification, timeout = 5)

        if reply.content.lower() == 'no':
            raise commands.CommandInvokeError(':octagonal_sign: Initialization has been cancelled.')


    @commands.group(name='userauth')
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def userauth(self, ctx):
        '''Manages user authentication.

        Admins can either set, clear, or make.
        Also makes the tree and root, which is used in subcommands.
        '''
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.userauth = ctx.tree.find('userauth')

        if ctx.invoked_subcommand is None:
            embed = await modules.utility.make_simple_embed(
                                                'Current configs for userauth',
                                                await modules.utility.userauth_to_str(ctx.userauth))
            await ctx.send(embed=embed)


    @userauth.group(name='set')
    async def userauth_set(self, ctx):
        '''Command group based userauth. Splits into below'''
        pass


    @userauth_set.command(name='role')
    async def userauth_set_role(self, ctx, *, role: discord.Role):
        '''Takes the discord.role and converts it to a str(id), write to xml'''
        xml_role = ctx.userauth.find('role')
        xml_role.find('id').text = str(role.id)
        xml_role.find('name').text = role.name

        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Role: **{}** has been saved.'\
                        .format(role.name))


    @userauth_set.command(name='emoji')
    async def userauth_set_emoji(self, ctx, *, emo: modules.utility.AllEmoji):
        '''Takes a discord.emoji and converts it to usable str, write to xml'''
        xml_emoji = ctx.userauth.find('emoji')
        if await modules.utility.is_custom_emoji(emo):
            xml_emoji.find('id').text = str(emo)
        else:
            xml_emoji.find('id').text = html.unescape(emo)

        await modules.utility.write_xml(ctx)

        xml_message = ctx.userauth.find('message')
        xml_emoji = ctx.userauth.find('emoji')
        if xml_message.find('id') != 'None':
            try:
                msg = await ctx.get_message(int(xml_message.find('id').text))
                await msg.clear_reactions()
                await msg.add_reaction(await modules.utility.AllEmoji().convert(ctx, xml_emoji.find('id').text))
            except (discord.NotFound, ValueError):
                pass

        await ctx.send(':thumbsup: Emoji: **{}** has been saved and message (if exists) has been updated.'\
                        .format(emo))


    @userauth_set.command(name='message')
    async def userauth_set_message(self, ctx, *, msg:str):
        '''Takes a message, write to xml'''
        xml_message = ctx.userauth.find('message')
        xml_message.find('content').text = msg
        await modules.utility.write_xml(ctx)

        msg_embed = await modules.utility.make_userauth_embed(xml_message.find('content').text)

        await ctx.send(content=':thumbsup: Message has been saved.',
                        embed=msg_embed)


    @userauth.command(name='make')
    @commands.check(modules.utility.check_userauth_role_set)
    async def userauth_make(self, ctx):
        '''Creates a message based from configs for userauth'''
        xml_message = ctx.userauth.find('message')
        msg_embed = await modules.utility.make_userauth_embed(xml_message.find('content').text)
        msg = await ctx.send(embed=msg_embed)

        xml_message.find('id').text = str(msg.id)

        await modules.utility.write_xml(ctx)

        xml_emoji = ctx.userauth.find('emoji')
        await msg.add_reaction(await modules.utility.AllEmoji().convert(ctx, xml_emoji.find('id').text))


    @userauth.group(name='clear')
    async def userauth_clear(self, ctx):
        '''With no subommands passed, reset all of userath's configs'''
        if ctx.subcommand_passed == 'clear':
            await modules.factory.worker_userauth.reset.all(ctx.userauth)
            await modules.utility.write_xml(ctx)

            await ctx.send(':thumbsup: Config userauth has been reset to defaults')


    @userauth_clear.command(name='role')
    async def userauth_clear_role(self, ctx):
        '''Resets userauth:role configs'''
        await modules.factory.worker_userauth.reset.role(ctx.userauth)
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Config userauth:role has been reset to defaults')


    @userauth_clear.command(name='emoji')
    async def userauth_clear_emoji(self, ctx):
        '''Resets userauth:emoji configs'''
        await modules.factory.worker_userauth.reset.emoji(ctx.userauth)
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs userauth:emoji has been reset to defaults')


    @userauth_clear.command(name='message')
    async def userauth_clear_message(self, ctx):
        '''Resets userauth:message configs'''
        await modules.factory.worker_userauth.reset.message(ctx.userauth)
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs userauth:message has been reset to defaults')


    @commands.group()
    async def selfrole(self, ctx):
        """
        Basic group command for self role assignment. Splits into below.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command <:cirnoNoWork:469040364460834817>')


    @selfrole.group(name='role')
    async def rolesManage(self, ctx):
        """
        Base command for commands which add or remove roles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n" +
                           "Use \"c!help selfrole role\" for a list of valid commands")


    @selfrole.group(name='group')
    async def selfroleGroup(self, ctx):
        """
        Base command for commands which affect groups. Groups are used to store roles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n" +
                           "Use \"c!help selfrole group\" for a list of valid commands")


    @selfrole.command(name='status')
    async def selfroleStatus(self, ctx, newStatus: str):
        if newStatus in ['enabled', 'disabled']:
            tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
            selfrole_list = tree.find('selfroles')
            selfrole_list.find('status').text = newStatus
        else:
            raise ValueError("Status is not 'enabled' or 'disabled'")


    @rolesManage.command(name='add')
    async def selfroleAdd(self, ctx, group: str, emoji: modules.utility.AllEmoji, *, role: discord.Role):
        """
        Adds a role and associates it with an emoji.
        Roles must be placed in a group. See 'c!selfrole group add' for more details.
        Will automatically update role assignment message, if one exists.
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
        Removes a role and its corresponding emoji.
        Will automatically update role assignment message, if one exists.
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

        old_emoji = await modules.utility.AllEmoji().convert(ctx, curr_assoc.find('emoji').text)
        group_containing_role.remove(curr_assoc)
        tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))
        await self.edit_selfrole_msg(ctx, group_containing_role, True, old_emoji, False)
        await ctx.send("Role \"{}\" successfully removed; previously bound to emoji {}".format(role, old_emoji))


    async def edit_selfrole_msg(self, ctx, group: ET.Element, change_emoji: bool, emoji: modules.utility.AllEmoji = None, to_add: bool = None):
        """
        Adds or removes a role from the corresponding assignment message if it exists.
        Does not modify the XML at all, only affects the role assignment message.
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


    async def add_delete_selfrole_msg(self, ctx, group: ET.Element, to_add: bool):
        """
        Adds or removes a group if necessary/possible.

        Warning: this WILL modify the group's message id parameter. When this function is called,
        the calling function will have to write the XML tree to save the changes.

        This function does not directly write anything to the XML file; the calling function is responsible for doing so
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


    async def _get_single_group_msg(self, group: ET.Element) -> discord.Embed:
        """
        Args:
            group: A role assignment message group which contains 'assoc' elements.

        Returns: An embed that displays the properties and contents of the specified group.
        """
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
        """
        Sends a series of messages displaying the properties and contents of every group.
        """
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
        Converts text stored in message->id to a list of message ids of type int

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))


    def _conv_to_msg_text(self, msg_id_list: [int]) -> str:
        """
        Converts a list of messages to text storable in message->id
        """
        return ' '.join(str(i) for i in msg_id_list)


    def _remove_item_from_list(self, item_list: list, item) -> list:
        """
        Removes an item from the specified list. Not type-sensitive.
        """
        item_list = [i for i in item_list if i != item]
        return item_list


    async def _delete_message(self, ctx, group_name: str, suppress_output = False) -> [int]:
        """
        Deletes the specified role assignment message(s).
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
        """
        Builds the specified role assignment message(s).
        Automatically avoids duplicating messages by deleting the old copy.
        This function does not permit creation of messages in multiple channels at the same time.
        """
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
                emoji = await modules.utility.AllEmoji().convert(ctx, assoc.find('emoji').text)
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
        Creates role assignment messages.

        If 'group' is specified, this command will only print the message corresponding to that group.
        If not specified or '*' is passed, all messages will be created in the target channel.

        target_channel: Default channel varies.
        If no messages exist, target_channel will be the channel the command was typed in.
        If messages exist, it will default to the channel where messages currently exist.

        If suppress_output is set to 'true', will not print out any confirmation messages.
        Default behavior: 'true' if target_channel is the channel where the command was typed, 'false' otherwise.
        """
        if target_channel:
            await self._build_message(ctx, group, suppress_output, target_channel)
        else:
            await self._build_message(ctx, group, suppress_output)


    @selfrole.command(name='delmsg')
    async def selfroleMsgDestroy(self, ctx, group: str = "*", suppress_output = 'default'):
        """
        Destroys role assignment messages.

        If 'group' is specified, this command will only delete the message corresponding to that group.
        If not specified or '*' is passed, all existing role assignment messages will be deleted.

        If suppress_output is set to 'true', will not print out any confirmation messages.
        Default behavior: 'true' if target_channel is the channel where the command was typed, 'false' otherwise.
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
        Doesn't actually help right now.
        """
        await ctx.send("This command is currently being worked on! Stay tuned for more details <:cirnoSmile:469040364045729792>")


    @selfroleGroup.command(name="add")
    async def groupCreate(self, ctx, name: str, *, requiredRole: discord.Role = "", maxSelectable: int = 'all'):
        """
        Creates a group which may contain roles. Roles must be placed in a group.

        Group names cannot contain whitespace.

        requiredRole: the role required for a user to be able to add or remove roles from this group.

        maxSelectable: the maximum number of roles a user can select from the group.
        By default, all roles from a group may be assigned at once.
        If an integer less than or equal to 0 is specified, will default to 'all'.
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
        """
        Deletes a group. Prints out a confirmation message beforehand.
        """
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
        """
        Base command for modifying groups, which are used to store roles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command usage <:cirnoBaka:469040361323364352>\n")


    @groupModify.command(name="name")
    async def group_change_name(self, ctx, oldName: str, newName: str):
        """
        Renames a group.
        When renaming groups, they will not be automatically sorted (as of right now).
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


    def _find_group(self, groups_list: list, name: str) -> ET.Element:
        """
        Finds the specified group with name 'name' in the list groups_list, if the group exists. Returns None otherwise.
        """
        for group in groups_list:
            if group.find('name').text == name:
                return group
        return None


def setup(bot):
    bot.add_cog(AdminCog(bot))
