import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from discord import Emoji
import modules.utility as utility
import modules.factory as factory
import modules.exceptxml
import html
import modules.selfrole as sr
import modules.selfrole.group
import modules.selfrole.list
import modules.selfrole.message

group_modify_cmd = """
print('starting test')
@gp.selfrole.command(name=name, hidden=True)
async def test2(ctx):
    '''
    Does stuff.
    '''
    await ctx.send('some shit')
    
print('ending test')

"""


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
            await ctx.send(':x: ERROR: {}'.format(error))

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
        await factory.WorkerUserAuth(userauth).create_all()

        selfroles = ET.SubElement(root, 'selfroles')
        await factory.WorkerSelfrole(selfroles).create_all()

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

        Admins can either set, reset, or make.
        Also makes the tree and root, which is used in subcommands.
        '''
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.userauth = ctx.tree.find('userauth')

        if ctx.invoked_subcommand is None:
            base_embed = await modules.utility.make_simple_embed(
                                                'Current configs for userauth',
                                                await modules.utility.userauth_to_str(ctx))


            xml_message_content = ctx.userauth.find('message').find('content').text
            # msg_embed = await modules.utility.make_userauth_embed(xml_message_content)

            await ctx.send(embed=base_embed)
            # await ctx.send(content='Below is what your current userauth looks like to users', embed=msg_embed)


    @userauth.group(name='set')
    async def userauth_set(self, ctx):
        '''Command group based userauth. Splits into below'''
        pass


    @userauth_set.command(name='status')
    async def userauth_set_status(self, ctx, status:utility.StatusStr):
        ctx.userauth.find('status').text = status

        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: User Authentication is now {sta}.'.format(sta=status))


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
        xml_emoji_id = ctx.userauth.find('emoji').find('id')
        xml_emoji_id.text = html.unescape(str(emo))

        await modules.utility.write_xml(ctx)

        xml_message_id = ctx.userauth.find('message').find('id').text
        if xml_message_id is not None:
            try:
                msg = await ctx.get_message(int(xml_message_id))
                await msg.clear_reactions()
                await msg.add_reaction(await modules.utility.AllEmoji().convert(ctx, xml_emoji_id))
            except (discord.NotFound, TypeError):
                pass

        await ctx.send(':thumbsup: Emoji: **{}** has been saved and message (if exists) has been updated.'\
                        .format(emo))


    @userauth_set.command(name='message')
    async def userauth_set_message(self, ctx, *, msg:str):
        '''Takes a message, edits existing, write to xml'''
        xml_message = ctx.userauth.find('message')
        xml_message_content = xml_message.find('content').text = msg

        await modules.utility.write_xml(ctx)

        await utility.edit_userauth(ctx, msg)

        await ctx.send(content=':thumbsup: Message has been saved and message (if exists) has been updated.')


    # @userauth_set.group(name='greet')
    # async def userauth_set_greet(self, ctx, status:modules.utility.StatusStr):
    #     '''Takes a StatusStr, writes to xml'''
    #     ctx.userauth.find('greet').find('status').text = status
    #
    #     await modules.utility.write_xml(ctx)
    #
    #     await ctx.send(content=(':thumbsup: userauth is now {0}.'.format(status)))


    @userauth.command(name='make')
    @commands.check(modules.utility.check_userauth_role_set)
    async def userauth_make(self, ctx):
        '''Deletes old userauth and creates a message based from configs for userauth'''
        await utility.delete_userauth(ctx)
        xml_message = ctx.userauth.find('message')
        msg_embed = await modules.utility.make_userauth_embed(xml_message.find('content').text)
        msg = await ctx.send(embed=msg_embed)

        xml_message.find('id').text = str(msg.id)

        await modules.utility.write_xml(ctx)

        xml_emoji = ctx.userauth.find('emoji')
        await msg.add_reaction(await modules.utility.AllEmoji().convert(ctx, xml_emoji.find('id').text))


    @userauth.group(name='reset')
    async def userauth_reset(self, ctx):
        '''With no subommands passed, reset all of userath's configs, deletes old userauth'''
        if ctx.subcommand_passed == 'reset':
            await utility.delete_userauth(ctx)
            await factory.WorkerUserAuth(ctx.userauth).reset_all()
            await modules.utility.write_xml(ctx)

            await ctx.send(':thumbsup: userauth has been reset to defaults.')


    @userauth_reset.command(name='role')
    async def userauth_reset_role(self, ctx):
        '''Resets userauth:role configs'''
        await factory.WorkerUserAuth(ctx.userauth).reset_role()
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Config userauth:role has been reset to defaults')


    @userauth_reset.command(name='emoji')
    async def userauth_reset_emoji(self, ctx):
        '''Resets userauth:emoji configs'''
        await factory.WorkerUserAuth(ctx.userauth).reset_emoji()
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs userauth:emoji has been reset to defaults')


    @userauth_reset.command(name='message')
    async def userauth_reset_message(self, ctx):
        '''Resets userauth:message configs, edits existing userauth'''
        await utility.edit_userauth(ctx, factory.USERAUTH_DEFAULT_MESSAGE)

        await factory.WorkerUserAuth(ctx.userauth).reset_message()
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs userauth:message has been reset to defaults')


    @commands.group(name="selfrole", aliases=['sr'])
    async def selfrole(self, ctx):
        """
        Basic group command for self role assignment. Splits into below.
        """
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command <:cirnoNoWork:489185064844787712>')

    @selfrole.command(name='status')
    async def selfrole_status(self, ctx, newStatus: utility.StatusStr):
        selfrole_list = ctx.tree.find('selfroles')
        selfrole_list.find('status').text = newStatus
        await modules.utility.write_xml(ctx)
        await ctx.send('Selfroles have been {sta}'.format(sta=newStatus))

    @selfrole.command(name='list')
    async def selfrole_list(self, ctx):
        """
        Lists all currently registered emoji/role associations.

        This command functions the same as c!selfrole role list.
        """
        # NOTE: the message below uses a static prefix. Modify later to dynamically determine the prefix
        selfrole_list = ctx.tree.find('selfroles')
        associations = selfrole_list.find('associations')
        groups_list = associations.findall('group')
        if not groups_list:
            await ctx.send(
                "You have not registered any groups yet! Add an group by typing c!selfrole group add <group>")
        else:
            await ctx.send("Registered emojis:\n\n")
            for group in groups_list:
                await ctx.send(embed=await sr.message.get_single_group_msg(group))

    def conv_to_id_list(self, msg_id_text: str) -> [int]:
        """
        Converts text stored in message->id to a list of message ids of type int

        :param msg_id_text: the msg_id element's text in a server_data document
        :return: The list of ids of messages
        """
        return list(map(int, msg_id_text.strip().split()))

    def conv_to_msg_text(self, msg_id_list: [int]) -> str:
        """
        Converts a list of messages to text storable in message->id
        """
        return ' '.join(str(i) for i in msg_id_list)


    def remove_item_from_list(self, item_list: list, item) -> list:
        """
        Removes an item from the specified list. Not type-sensitive.
        """
        item_list = [i for i in item_list if i != item]
        return item_list

    @selfrole.group(name='message', invoke_without_command=True)
    async def selfrole_message_manage(self, ctx):
        """
        Base command for modifications to the role assignment message.
        """
        await ctx.send("Invalid command usage <:cirnoBaka:489185059732193298>\n" +
                       "Use \"c!help selfrole role\" for a list of valid commands")

    @selfrole_message_manage.command(name='make', aliases=['m', 'c'])
    async def selfrole_msg_create(self, ctx, group: str = "*", target_channel: discord.TextChannel = None, suppress_output = 'default'):
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
            await sr.message.build_message(self, ctx, group, suppress_output, target_channel)
        else:
            await sr.message.build_message(self, ctx, group, suppress_output)

    @selfrole_message_manage.command(name='destroy', aliases=['d'])
    async def selfrole_msg_destroy(self, ctx, group: str = "*", suppress_output = 'default'):
        """
        Destroys role assignment messages.

        If 'group' is specified, this command will only delete the message corresponding to that group.
        If not specified or '*' is passed, all existing role assignment messages will be deleted.

        If suppress_output is set to 'true', will not print out any confirmation messages.
        Default behavior: 'true' if target_channel is the channel where the command was typed, 'false' otherwise.
        """
        selfrole_list = ctx.tree.find('selfroles')
        ch_id = int(selfrole_list.find('channel').find('id').text)

        if suppress_output in ['true', 'false']:
            s = suppress_output == 'true'
        else:  # Default behavior
            s = ctx.message.channel.id == ch_id
        await sr.message.delete_message(self, ctx, group, s)

    @selfrole.command(name="help")
    async def selfrole_help(self, ctx):
        """
        Doesn't actually help right now.
        """
        await ctx.send("This command is currently being worked on! Stay tuned for more details <:cirnoSmile:469040364045729792>")

    @selfrole.group(name="group", invoke_without_command=True)
    async def srGroup(self, ctx):
        """
        Base command for the create/delete group commands. Groups are used to store roles.
        """
        await ctx.send("Invalid command usage <:cirnoBaka:489185059732193298>\n" +
                       "Use \"c!help selfrole group\" for a list of valid commands")

    @srGroup.command(name="create", aliases=['c'])
    async def groupCreate(self, ctx, *, name: str):
        """
        Creates a group which may contain roles. Roles must be placed in a group.

        Group names can contain whitespace, but the group name must be surrounded in quotes.

        requiredRole: the role required for a user to be able to add or remove roles from this group.

        maxSelectable: the maximum number of roles a user can select from the group.
        By default, all roles from a group may be assigned at once.
        If an integer less than or equal to 0 is specified, will default to 'all'.
        """
        await sr.group.groupCreate(self, ctx, name)

    @srGroup.command(name="delete", aliases=['d'])
    async def groupDelete(self, ctx, *, name: str):
        """
        Deletes a group. Prints out a confirmation message beforehand.
        """
        await sr.group.groupDelete(self, ctx, name)

    @selfrole.group(name="roles", invoke_without_command=True)
    async def srRoles(self, ctx):
        """
        Base command for the create/delete role commands.
        """
        await ctx.send("Invalid command usage <:cirnoBaka:489185059732193298>\n" +
                       "Use \"c!help selfrole roles\" for a list of valid commands")

    @srRoles.command(name="add")
    async def srAdd(self, ctx, group: modules.utility.GroupStr, emoji: modules.utility.AllEmoji, role: discord.Role):
        """
        Adds a role and associates it with an emoji.
        Roles must be placed in a group. See 'c!selfrole group add' for more details.
        Will automatically update role assignment message, if one exists.
        """
        await sr.group.role_add(self, ctx, group, emoji, role)

    @srRoles.command(name="del")
    async def srDel(self, ctx, group: modules.utility.GroupStr, role: discord.Role):
        """
        Removes a role and its corresponding emoji.
        Will automatically update role assignment message, if one exists.
        """
        await sr.group.role_del(self, ctx, group, role)

    @selfrole.command(name="rename")
    async def srRename(self, ctx, group: modules.utility.GroupStr, new_name: str):
        """
        Renames a group.
        When renaming groups, they will not be automatically sorted (as of right now).
        """
        await sr.group.group_change_name(self, ctx, group, new_name)

    @selfrole.command(name="req")
    async def srReq(self, ctx, group: modules.utility.GroupStr, role: str = None):
        """
        Changes the role requirement for the specified group to newRole.
        The role requirement can be reset to None by typing 'reset' instead of a role name.
        """
        await sr.group.group_change_role_req(self, ctx, group, role)

    @selfrole.command(name="max")
    async def srMax(self, ctx, group: modules.utility.GroupStr, new_max: modules.utility.MaxRoleStr = None):
        """
        Limits the number of roles a user can select from this group.
        Limit can be removed by setting new_max to 'all', 'reset', or the number 0.
        """
        await sr.group.group_change_max(self, ctx, group, new_max)

    @selfrole.command(name="reset")
    async def srReset(self, ctx, group: modules.utility.GroupStr):
        """
        Resets the group to default values.
        (No roles, no role requirement, unlimited max, doesn't change role name)
        """
        await sr.group.group_reset(self, ctx, group)


def setup(bot):
    bot.add_cog(AdminCog(bot))
