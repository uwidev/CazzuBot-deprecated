import discord, os
import xml.etree.ElementTree as ET
from modules import factory, utility
from discord.ext import commands

class gowner():
    def __init__(self, bot):
        self.bot = bot


    def __local_check(self, ctx):
        if ctx.author == ctx.guild.owner:
            return True

        if ctx.author.id == self.bot.owner_id:
            return True

        return False


    @commands.group(name='init')
    async def init(self, ctx):
        '''Initializes the server configs based on modules.factory properties'''
        if not os.path.isdir('server_data/{}'.format(ctx.guild.id)):
            os.makedirs('server_data/{}'.format(str(ctx.guild.id)))

        if ctx.invoked_subcommand is None:
            print('DOING ALL')
            ctx.root = ET.Element('data')
            ctx.tree = ET.ElementTree(ctx.root)

            await factory.create_all(ctx.root)

            selfroles = ET.SubElement(ctx.root, 'selfroles')
            ET.SubElement(selfroles, 'associations')
            msg = ET.SubElement(selfroles, 'message')
            msg_id = ET.SubElement(msg, 'id')
            msg_id.text = '-42'
            ch = ET.SubElement(selfroles, 'channel')
            ch_id = ET.SubElement(ch, 'id')
            ch_id.text = '-42'

            selfrole_status = ET.SubElement(selfroles, 'status')
            selfrole_status.text = 'enabled'

            await utility.write_xml(ctx)
            await ctx.send(':thumbsup: **{}** (`{}`) server config has been initialized.'.format(ctx.guild.name, ctx.guild.id))

        else:
            print('DOING SUBCOMMAND')
            ctx.tree = await utility.load_tree(ctx)
            ctx.root = ctx.tree.getroot()


    @init.command(name='userauth')
    async def init_userauth(self, ctx):
        print('INIT USERAUTH')
        worker = factory.WorkerUserAuth(ctx.root)
        await worker.clear()
        await worker.create_all()

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: User Authentication has been initialized.')


    @init.command(name='greet')
    async def init_greet(self, ctx):
        worker = factory.WorkerGreet(ctx.root)
        await worker.clear()
        await worker.create_all()

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Server Greeting has been initialized.')


    @init.command(name='server')
    async def init_server(self, ctx):
        worker = factory.WorkerServer(ctx.root)
        await worker.clear()
        await worker.create_all()

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Server specific configs has been initialized.')


    @init.before_invoke
    async def init_verify(self, ctx):
        '''Asks the user before initializing server configs'''
        def verification(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']

        await ctx.send(':exclamation: Are you sure you want to initialize server configs? [`Yes`/`No`]')
        reply = await self.bot.wait_for('message', check=verification, timeout = 5)

        if reply.content.lower() == 'no':
            raise commands.CommandInvokeError(':octagonal_sign: Initialization has been cancelled.')


    @commands.command(name='configs')
    async def configs(self, ctx):
        ctx.tree = await utility.load_tree(ctx)
        ctx.server = ctx.tree.find('server')
        ctx.userauth = ctx.tree.find('userauth')
        ctx.greet = ctx.tree.find('greet')

        # desc = ''
        # desc += '**__Server__**\n' + await utility.server_to_str(ctx)
        # desc += '\n\n**__Userauth__**\n' + await utility.userauth_to_str(ctx)
        # desc += '\n\n**__Greet__**\n' + await utility.greet_to_str(ctx)

        embed = await utility.make_simple_embed(
            'All Guild Configurations', desc=None)

        embed.add_field(name='**Server**', value=await utility.server_to_str(ctx))
        embed.add_field(name='**User Authentication**', value=await utility.userauth_to_str(ctx))
        embed.add_field(name='**Greet**', value=await utility.greet_to_str(ctx))

        await ctx.send(embed=embed)



    @commands.group(name='server')
    async def server(self, ctx):
        '''Config commands specifically for the server

        If "!userauth set" sets configs for userauth, this one
        applies to the foudation.
        '''
        ctx.tree = await utility.load_tree(ctx)
        ctx.server = ctx.tree.find('server')

        if ctx.invoked_subcommand is None:
            embed = await utility.make_simple_embed(
                'Current Server Configurations',
                await utility.server_to_str(ctx))

            await ctx.send(embed=embed)


    @server.group(name='set')
    async def server_set(self, ctx):
        pass


    @server_set.command(name='admin')
    async def server_set_admin(self, ctx, admin: discord.Role):
        xml_admin = ctx.tree.find('server').find('admin')
        xml_admin.find('id').text = str(admin.id)

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Admin role has been set to **{ad}**.'.format(ad=admin.name))


    @server_set.command(name='mod')
    async def server_set_mod(self, ctx, mod: discord.Role):
        xml_admin = ctx.tree.find('server').find('mod')
        xml_admin.find('id').text = str(mod.id)

        await utility.write_xml(ctx)

        await ctx.send(':thumbsup: Mod role has been set to **{md}**.'.format(md=mod.name))


    @server.group(name='clear')
    async def server_clear(self, ctx):
        pass




def setup(bot):
    bot.add_cog(gowner(bot))
