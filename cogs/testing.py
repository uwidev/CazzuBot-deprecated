import discord, os, traceback, sys
from discord.ext import commands
import discord_emoji


class TestingCog():
    def __init__(self, bot):
        self.bot = bot

    async def __error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == self.bot.owner_id and self.bot.super == True:
                # await ctx.send(':exclamation: Dev cooldown bypass.')
                await ctx.reinvoke()
            else:
                await ctx.channel.send(
                    ':hand_splayed: Command has a {} second cooldown. Please try again after {} seconds.'.format(
                        str(error.cooldown.per)[0:3], str(error.retry_after)[0:3]))

        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send('{}'.format(error.original))

        elif isinstance(error, commands.BadArgument):
            await ctx.send(':x: ERROR: {}'.format(' '.join(error.args)))

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(':x: ERROR: {} is a required argument.'.format(error.param.name))

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    class AllEmoji(commands.EmojiConverter):
        async def convert(self, ctx, argument):
            if argument in discord_emoji.UNICODE_EMOJI_LIST:
                return argument
            return await super().convert(ctx, argument)

    @commands.command()
    async def test(self, ctx, *, arg: AllEmoji):
        print(arg)
        await ctx.send(arg)


def setup(bot):
    bot.add_cog(TestingCog(bot))