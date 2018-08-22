import discord, os, traceback, sys
from discord.ext import commands
import xml.etree.ElementTree as ET
from asyncio import sleep
from discord import PartialEmoji
from discord import Emoji
import cogs.help as help
import html

class AdminCog():

    # Static variable
    #emotes_to_define = ['cirnoWow', 'cirnoBaka', 'cirnoNoWork']

    def __init__(self, bot):
        self.bot = bot
        self.help = help.me(bot)

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

    async def status(self, ctx, v):
        class sta():
            def __init__(self, s):
                self.id = s
                self.name = s

        return sta(v) if v.lower() in ['enabled', 'disabled'] else False

    # async def role(self, ctx, v):
    #     try:
    #         return (await commands.RoleConverter().convert(ctx, v)).name
    #     except commands.CommandError:
    #         return v
    #
    #
    # async def message(self, ctx, v):
    #     try:
    #         return (await ctx.get_message(int(v))).id
    #     except ValueError:
    #         return v
    #
    #
    # async def emoji(self, ctx, v):
    #     try:
    #         return await commands.EmojiConverter().convert(ctx, v)
    #     except commands.BadArgument:
    #         return v
    # Curently writing into converters


    # Write message and status as converters


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def init(self, ctx):
        if not os.path.isdir('server_data/{}'.format(ctx.guild.id)):
            os.makedirs('server_data/{}'.format(str(ctx.guild.id)))

        root = ET.Element('data')
        userauth = ET.SubElement(root, 'userauth')

        # auth_status = ET.SubElement(userauth, 'status').text = 'None'

        auth_role = ET.SubElement(userauth, 'role')
        ET.SubElement(auth_role, 'id').text = 'None'
        ET.SubElement(auth_role, 'name').text = 'None'

        auth_message = ET.SubElement(userauth, 'message')
        ET.SubElement(auth_message, 'id').text = 'None'
        ET.SubElement(auth_message, 'context').text = 'You better add that rection if you\'re going to get into the server'

        auth_emoji = ET.SubElement(userauth, 'emoji')
        ET.SubElement(auth_emoji, 'custom').text = 'False'
        ET.SubElement(auth_emoji, 'id').text = html.unescape('&#128077;')

        ctx.tree = ET.ElementTree(root)

        selfroles = ET.SubElement(root, 'selfroles')
        ET.SubElement(selfroles, 'msg_id', Value='-42')
        ET.SubElement(selfroles, 'ch_id', Value='-42')

        cirnoWow, cirnoBaka, cirnoNoWork = None, None, None
        for emoji in self.bot.emojis:
            if emoji.name == 'cirnoWow':
                cirnoWow = emoji.id
            elif emoji.name == 'cirnoBaka':
                cirnoBaka = emoji.id
            elif emoji.name == 'cirnoNoWork':
                cirnoNoWork = emoji.id

        ET.SubElement(
            root,
            'command_emojis',
            Wow=str(cirnoWow),
            Baka=str(cirnoBaka),
            NoWork=str(cirnoNoWork))

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

    # Currently broken
    #
    #
    # @commands.command()
    # async def configs(self, ctx):
    #     root = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id)).getroot()
    #     msg = ''
    #     dis = '    {0}: {1}\n'
    #
    #     for E in root:
    #         msg += '**{}**\n'.format(E.tag)
    #         for e in E:
    #             cvalue = await eval('self.{0}(ctx, "{1}")'.format(e.tag, e.text))
    #             if e.tag in ['role']:
    #                 msg += dis.format(e.tag, cvalue)
    #             elif e.tag in ['emoji']:
    #                 msg += dis.format(e.tag, cvalue)
    #             elif e.tag in ['status', 'message']:
    #                 msg += dis.format(e.tag, cvalue)
    #         msg += '\n'
    #     await ctx.send(msg)


    # @commands.group()
    # async def edit(self, ctx, group, setting, *value):
    #     tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
    #     root = tree.getroot()
    #
    #     if group.lower() in (element.tag for element in root):
    #         E = root.find(group)
    #         e = E.find(setting)
    #
    #         val =  ' '.join(value)
    #         obj = await eval('self.{}(ctx, val)'.format(setting))
    #         print(type(obj), obj)
    #         if obj.id:
    #
    #             e.text = str(obj.id)
    #
    #         tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))


    @commands.group(name='userauth')
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def userauth(self, ctx):
        '''
        Create the ctx.userauth attribute, used in subcommands.
        When no arguments are given, default show status.
        '''
        ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
        ctx.userauth = ctx.tree.find('userauth')

        if ctx.invoked_subcommand is None:
            await ctx.send('Here is yer current settings for userauth\
                    \n{}'.format(await self.help.userauth_to_str(ctx.userauth)))


    @userauth.group(name='set')
    async def userauth_set(self, ctx):
        '''
        Command group based userauth. Splits into below.
        '''
        pass


    @userauth_set.command(name='role')
    async def userauth_set_role(self, ctx, role: discord.Role):
        '''
        Convert arg status into discord.Role object, write into xml under role -> id, name.
        '''
        xml_role = ctx.userauth.find('role')
        xml_role.find('id').text = str(role.id)
        xml_role.find('name').text = role.name
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))

        await ctx.send(':thumbsup: Role: **{}** has been saved.'\
                        .format(role.name))


    @userauth_set.command(name='emoji')
    async def userauth_set_emoji(self, ctx, emo: help.AllEmoji):
        '''
        Convert arg into a compatable reaction emoji, write into xml under emoji -> custom, id, name.
        '''
        xml_emoji = ctx.userauth.find('emoji')
        if await help.is_custom_emoji(emo):
            xml_emoji.find('custom').text = 'True'
            xml_emoji.find('id').text = str(emo)
        else:
            xml_emoji.find('custom').text = 'False'
            xml_emoji.find('id').text = emo

        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))

        xml_message = ctx.userauth.find('message')
        xml_emoji = ctx.userauth.find('emoji')
        if xml_message.find('id') != 'None':
            msg = await ctx.get_message(int(xml_message.find('id').text))
            await msg.clear_reactions()
            await msg.add_reaction(await help.AllEmoji().convert(ctx, xml_emoji.find('id').text))

        await ctx.send(':thumbsup: Emoji: **{}** has been saved and message (if exists) has been updated.'\
                        .format(emo))


    def check_role_set(ctx):
        role = ctx.userauth.find('role')
        if role.find('id').text != 'None':
            return True
        return False


    @userauth.command(name='make')
    @commands.check(check_role_set)
    async def userauth_make(self, ctx):
        xml_message = ctx.userauth.find('message')
        msg = await ctx.send(xml_message.find('context').text)
        xml_message.find('id').text = str(msg.id)

        xml_emoji = ctx.userauth.find('emoji')
        ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))

        await msg.add_reaction(await help.AllEmoji().convert(ctx, xml_emoji.find('id').text))


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
