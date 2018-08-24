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

    # Static variable
    #emotes_to_define = ['cirnoWow', 'cirnoBaka', 'cirnoNoWork']

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

        await modules.factory.worker_userauth.create.all(userauth)

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
<<<<<<< HEAD


    @userauth.group(name='set')
    async def userauth_set(self, ctx):
        '''Command group based userauth. Splits into below'''
        pass


    @userauth_set.command(name='role')
<<<<<<< HEAD
    async def userauth_set_role(self, ctx, *, role: discord.Role):
=======
    async def userauth_set_role(self, ctx, role: discord.Role):
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
        '''Takes the discord.role and converts it to a str(id), write to xml'''
        xml_role = ctx.userauth.find('role')
        xml_role.find('id').text = str(role.id)
        xml_role.find('name').text = role.name

<<<<<<< HEAD
        await modules.utility.write_xml(ctx)
=======
        await ctx.send(':thumbsup: Role: **{}** has been saved.'\
                        .format(role.name))
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4

        await ctx.send(':thumbsup: Role: **{}** has been saved.'\
                        .format(role.name))

<<<<<<< HEAD

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

=======


    @userauth.group(name='set')
    async def userauth_set(self, ctx):
        '''Command group based userauth. Splits into below'''
        pass
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4

    @userauth_set.command(name='message')
    async def userauth_set_message(self, ctx, *, msg:str):
        '''Takes a message, write to xml'''
        xml_message = ctx.userauth.find('message')
        xml_message.find('content').text = msg
        await modules.utility.write_xml(ctx)

<<<<<<< HEAD
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


=======
    @userauth_set.command(name='emoji')
    async def userauth_set_emoji(self, ctx, emo: modules.utility.AllEmoji):
        '''Takes a discord.emoji and converts it to usable str, write to xml'''
        xml_emoji = ctx.userauth.find('emoji')
        if await modules.utility.is_custom_emoji(emo):
            xml_emoji.find('id').text = str(emo)
        else:
            xml_emoji.find('id').text = html.unescape(emo)

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


=======
    @userauth_set.command(name='role')
    async def userauth_set_role(self, ctx, role: discord.Role):
        '''Takes the discord.role and converts it to a str(id), write to xml'''
        xml_role = ctx.userauth.find('role')
        xml_role.find('id').text = str(role.id)
        xml_role.find('name').text = role.name

        await ctx.send(':thumbsup: Role: **{}** has been saved.'\
                        .format(role.name))


    @userauth_set.command(name='emoji')
    async def userauth_set_emoji(self, ctx, emo: modules.utility.AllEmoji):
        '''Takes a discord.emoji and converts it to usable str, write to xml'''
        xml_emoji = ctx.userauth.find('emoji')
        if await modules.utility.is_custom_emoji(emo):
            xml_emoji.find('id').text = str(emo)
        else:
            xml_emoji.find('id').text = html.unescape(emo)

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


>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
    @userauth.group(name='clear')
    async def userauth_clear(self, ctx):
        '''With no subommands passed, reset all of userath's configs'''
        if ctx.subcommand_passed == 'clear':
            await modules.factory.worker_userauth.reset.all(ctx.userauth)
            await ctx.send(':thumbsup: Config userauth has been reset to defaults')
<<<<<<< HEAD


>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
    @userauth_clear.command(name='role')
    async def userauth_clear_role(self, ctx):
        '''Resets userauth:role configs'''
        await modules.factory.worker_userauth.reset.role(ctx.userauth)
<<<<<<< HEAD
        await modules.utility.write_xml(ctx)

=======
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
        await ctx.send(':thumbsup: Config userauth:role has been reset to defaults')


    @userauth_clear.command(name='emoji')
    async def userauth_clear_emoji(self, ctx):
        '''Resets userauth:emoji configs'''
        await modules.factory.worker_userauth.reset.emoji(ctx.userauth)
<<<<<<< HEAD
        await modules.utility.write_xml(ctx)

        await ctx.send(':thumbsup: Configs userauth:emoji has been reset to defaults')

=======
=======


    @userauth_clear.command(name='role')
    async def userauth_clear_role(self, ctx):
        '''Resets userauth:role configs'''
        await modules.factory.worker_userauth.reset.role(ctx.userauth)
        await ctx.send(':thumbsup: Config userauth:role has been reset to defaults')


    @userauth_clear.command(name='emoji')
    async def userauth_clear_emoji(self, ctx):
        '''Resets userauth:emoji configs'''
        await modules.factory.worker_userauth.reset.emoji(ctx.userauth)
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
        await ctx.send(':thumbsup: Configs userauth:emoji has been reset to defaults')


    @userauth_clear.command(name='message')
    async def userauth_clear_message(self, ctx):
        '''Resets userauth:message configs'''
        await modules.factory.worker_userauth.reset.message(ctx.userauth)
        await ctx.send(':thumbsup: Configs userauth:message has been reset to defaults')
<<<<<<< HEAD
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
=======
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4

    @userauth_clear.command(name='message')
    async def userauth_clear_message(self, ctx):
        '''Resets userauth:message configs'''
        await modules.factory.worker_userauth.reset.message(ctx.userauth)
        await modules.utility.write_xml(ctx)

<<<<<<< HEAD
<<<<<<< HEAD
        await ctx.send(':thumbsup: Configs userauth:message has been reset to defaults')
=======
=======
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
    @userauth_clear.after_invoke
    @userauth_set.after_invoke
    async def after_userauth_clear(self, ctx):
        '''After certain commands, write xml.'''
        await modules.utility.write_xml(ctx)
<<<<<<< HEAD
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4
=======
>>>>>>> ee0569f462ef68fde119cccd54222c92883f41a4


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
