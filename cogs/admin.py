import discord, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from discord import Emoji
from modules import factory, utility
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
        tree = await utility.load_tree(ctx)

        if ctx.author == ctx.guild.owner:
            return True

        if ctx.guild is not None:
            try:
                admin = await commands.RoleConverter().convert(
                    ctx, tree.find('server').find('admin').find('id').text)
                if admin in ctx.author.roles:
                    return True

            except TypeError:
                pass

            if ctx.author.id == self.bot.owner_id:
                return True

        return False


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


    @commands.group(name='userauth')
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def userauth(self, ctx):
        '''Manages user authentication.'''
        ctx.tree = await utility.load_tree(ctx)
        ctx.userauth = ctx.tree.find('userauth')

        if ctx.invoked_subcommand is None:
            base_embed = await modules.utility.make_simple_embed(
                'Current configs for userauth',
                await modules.utility.userauth_to_str(ctx))

            await ctx.send(embed=base_embed)


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

        await ctx.send(':thumbsup: Role: **{rl}** has been saved.'\
                        .format(rl=role.name))


    @userauth_set.command(name='emoji')
    async def userauth_set_emoji(self, ctx, *, emo: modules.utility.AllEmoji):
        '''Takes a discord.emoji and converts it to usable str, write to xml'''
        xml_emoji_id = ctx.userauth.find('emoji').find('id')
        xml_emoji_id.text = html.unescape(str(emo))

        await modules.utility.write_xml(ctx)

        xml_message_id = ctx.userauth.find('embed').find('id').text
        if xml_message_id is not None:
            try:
                msg = await ctx.get_message(int(xml_message_id))
                await msg.clear_reactions()
                await msg.add_reaction(emo)
            except (discord.NotFound, TypeError):
                pass

        await ctx.send(
            ':thumbsup: Emoji: **{}** has been saved and message (if exists) has been updated.'.format(emo))


    @userauth_set.command(name='desc')
    async def userauth_set_message(self, ctx, *, desc):
        '''Takes a description, edits existing, write to xml'''
        xml_embed = ctx.userauth.find('embed')
        xml_embed.find('desc').text = desc

        await modules.utility.write_xml(ctx)

        await utility.edit_userauth(ctx, xml_embed.find('title').text, desc)

        await ctx.send(
            ':thumbsup: Embed Description has been saved and message (if exists) has been updated.')


    @userauth_set.command(name='title')
    async def userauth_set_title(self, ctx, *, title):
        '''Takes a title, edits existing, write to xml'''
        xml_embed = ctx.userauth.find('embed')
        xml_embed.find('title').text = title

        await modules.utility.write_xml(ctx)

        await utility.edit_userauth(ctx, title, xml_embed.find('desc').text)

        await ctx.send(content=':thumbsup: Message has been saved and message (if exists) has been updated.')


    @userauth.command(name='make')
    @commands.check(modules.utility.check_userauth_role_set)
    async def userauth_make(self, ctx):
        '''Deletes old userauth and creates a message based from configs for userauth'''
        await utility.delete_userauth(ctx)
        xml_embed = ctx.userauth.find('embed')
        embed = await modules.utility.make_userauth_embed(
            xml_embed.find('title').text,
            xml_embed.find('desc').text)

        msg = await ctx.send(embed=embed)

        xml_embed.find('id').text = str(msg.id)

        await modules.utility.write_xml(ctx)

        xml_emoji = ctx.userauth.find('emoji')
        await msg.add_reaction(await modules.utility.AllEmoji().convert(ctx, xml_emoji.find('id').text))


    @userauth.group(name='reset',
                    invoke_without_subcommand=True)
    async def userauth_reset(self, ctx):
        '''With no subommands passed, reset all of userath's configs, deletes old userauth'''
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
        await utility.edit_userauth(
            ctx,
            factory.USERAUTH_DEFAULT_TITLE,
            factory.USERAUTH_DEFAULT_DESC)

        await factory.WorkerUserAuth(ctx.userauth).reset_embed()
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs for the User Authenticaton'
            ' message has been reset to defaults.')


    @commands.group(name='greet',
                    aliases=['greeting'])
    async def greet(self, ctx):
        ctx.tree = await utility.load_tree(ctx)
        ctx.greet = ctx.tree.find('greet')

        if ctx.invoked_subcommand is None:
            embed = await utility.make_simple_embed(
                'Current settings for greet',
                await utility.greet_to_str(ctx))

            await ctx.send(embed=embed)


    @greet.group(name='set')
    async def greet_set(self, ctx):
        pass

    @greet_set.command(name='feature')
    async def greet_set_feature(self, ctx, arg: utility.StatusStr):
        ctx.greet.find('feature').text = arg[1]

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Greetings are now **{a}**.'.format(a=arg[0]))

    @greet_set.command(name='message')
    async def greet_set_message(self, ctx, *, msg):
        ctx.greet.find('message').find('content').text = msg

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Message has been set to **``{m}``**.'.format(m=msg))

    @greet_set.command(name='channel')
    async def greet_set_channel(self, ctx, channel: discord.TextChannel):
        xml_channel = ctx.greet.find('channel')
        xml_channel.find('id').text = str(channel.id)

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Greetings will now show up on {ch}.'.format(ch=channel.mention))


    @greet_set.command(name='userauth')
    async def greet_set_userauth(self, ctx, arg: utility.StatusStr):
        ctx.greet.find('userauth_dependence').text = arg[0]

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Userauth dependency for greetings are now **{bo}**.'.format(bo=arg[0]))


    @greet_set.command(name='title')
    async def greet_set_title(self, ctx, *, title: str):
        ctx.greet.find('embed').find('title').text = title

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Greeting title has been saved.')


    @greet_set.command(name='desc')
    async def greet_set_desc(self, ctx, *, desc: str):
        ctx.greet.find('embed').find('desc').text = desc

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Greeting description has been saved.')


    @greet.group(name='reset',
                 invoke_without_subcommand=True)
    async def greet_reset(self, ctx):
        #print(ctx.greet.find('embed').find('desc').text)
        await factory.WorkerGreet(ctx.tree.getroot()).reset_all()

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs for greetings has been reset to defaults.')


    @greet_reset.command(name='embed')
    async def greet_reset_embed(self, ctx):
        await factory.WorkerGreet(ctx.greet).reset_embed()

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs greetings embed have been reset to defaults.')


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


    @commands.command(name='embed')
    async def embed(self, ctx, *, titledesc):
        try:
            title, desc = titledesc.split('|')
        except ValueError:
            raise commands.BadArgument('Command requires ``|` to divide the title and description.')
        embed = await utility.make_simple_embed(title, desc)
        await ctx.send(embed=embed)
        await ctx.message.delete()



def setup(bot):
    bot.add_cog(AdminCog(bot))
