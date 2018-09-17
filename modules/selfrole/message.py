import discord
from discord.ext import commands
import xml.etree.ElementTree as ET
import modules.utility
import modules.factory
import modules.selfrole as sr
import modules.selfrole.find


async def build_message(admin_cog, ctx, group_name: str, suppress_output_str: str, channel: discord.TextChannel = None):
    """
    Builds the specified role assignment message(s).
    Automatically avoids duplicating messages by deleting the old copy.
    This function does not permit creation of messages in multiple channels at the same time.
    """
    selfrole_list = ctx.tree.find('selfroles')
    associations = selfrole_list.find('associations')
    curr_channel_id = int(selfrole_list.find('channel').find('id').text)

    if group_name != '*':
        target_group = sr.find.find_group(associations.findall('group'), group_name)
        if not target_group:
            raise ValueError("Group **{}** does not exist".format(group_name))

    if suppress_output_str in ['true', 'false']:
        suppress_output = suppress_output_str == 'true'
    else:  # Default behavior
        suppress_output = channel is None

    if channel is None:  # No channel specified by user
        if curr_channel_id != -42:
            destination_channel = admin_cog.bot.get_channel(curr_channel_id)
            suppress_output = curr_channel_id == ctx.message.channel.id
        else:
            destination_channel = ctx.message.channel
    elif curr_channel_id != channel.id and group_name != '*' and curr_channel_id != -42:
        raise commands.CommandInvokeError(":x: Error: Cannot create role assignment messages in multiple channels")
    else:
        destination_channel = channel

    if curr_channel_id == -42:
        msg_id_list = []
    else:
        msg_id_list = await delete_message(admin_cog, ctx, group_name, suppress_output)  # Receives updated message list

    if len(msg_id_list) == 0:
        msg_obj = await destination_channel.send("Add a reaction of whatever corresponds to the role you want."
                                                 " If you want to remove the role, remove the reaction")
        msg_id_list.append(msg_obj.id)

    for group in associations.findall('group'):
        if group_name != '*' and group.find('name').text != group_name:
            continue
        msg_obj = await destination_channel.send(embed=await get_single_group_msg(group))
        msg_id_list.append(msg_obj.id)
        group.find('message').find('id').text = str(msg_obj.id)

        # Add emoji to message
        for assoc in group.findall('assoc'):
            emoji = await modules.utility.AllEmoji().convert(ctx, assoc.find('emoji').text)
            await msg_obj.add_reaction(emoji)
        if group_name != '*':
            break

    selfrole_list.find('channel').find('id').text = str(destination_channel.id)
    selfrole_list.find('message').find('id').text = admin_cog.conv_to_msg_text(msg_id_list)
    ctx.tree.write('server_data/{}/config.xml'.format(str(ctx.guild.id)))  # Writes the channel and message id

    if not suppress_output:
        await ctx.send(":thumbsup: New selfroles message successfully created!")


async def delete_message(admin_cog, ctx, group_name: str, suppress_output = False) -> [int]:
    """
    Deletes the specified role assignment message(s).
    """
    selfrole_list = ctx.tree.find('selfroles')
    associations = selfrole_list.find('associations')

    msg_id_list = admin_cog.conv_to_id_list(selfrole_list.find('message').find('id').text)
    ch_id = int(selfrole_list.find('channel').find('id').text)
    if ch_id == -42:
        raise commands.CommandInvokeError("Error: no selfrole assignment messages currently exist.")

    channel = admin_cog.bot.get_channel(ch_id)
    groups_list = associations.findall('group')
    msg_deleted = False

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
                msg_deleted = True
                group.find('message').find('id').text = str(-42)
                msg_id_list = admin_cog.remove_item_from_list(msg_id_list, msg_id)
                selfrole_list.find('message').find('id').text = admin_cog.conv_to_msg_text(msg_id_list)
                delmsg = ":bomb: Target message has been destroyed"
            break
        if len(msg_id_list) == 1:
            message = await channel.get_message(msg_id_list[0])
            await message.delete()
            selfrole_list.find('message').find('id').text = str(-42)
            selfrole_list.find('channel').find('id').text = str(-42)
            msg_id_list = []

    await modules.utility.write_xml(ctx)
    if not suppress_output and msg_deleted:
        await ctx.send(delmsg)

    return msg_id_list


async def edit_selfrole_msg(cog, ctx, group: ET.Element, change_emoji: bool, emoji: modules.utility.AllEmoji = None, to_add: bool = None):
    """
    Changes the corresponding assignment message if it exists. Can add or remove roles, or otherwise alter it.
    Does not modify the XML at all, only affects the role assignment message.
    """
    ctx.tree = ET.parse('server_data/{}/config.xml'.format(ctx.guild.id))
    selfrole_list = ctx.tree.find('selfroles')
    channel_id = int(selfrole_list.find('channel').find('id').text)
    if channel_id != -42:
        group_msg_id = int(group.find('message').find('id').text)
        msg_obj = await cog.bot.get_channel(channel_id).get_message(group_msg_id)
        embed = await get_single_group_msg(group)
        await msg_obj.edit(embed=embed)
        if change_emoji:
            if to_add:
                await msg_obj.add_reaction(emoji)
            else:
                await msg_obj.remove_reaction(emoji, cog.bot.user)


async def add_delete_selfrole_msg(cog, ctx, group: ET.Element, to_add: bool):
    """
    Adds or removes a group if necessary/possible.

    Warning: this WILL modify the group's message id parameter. When this function is called,
    the calling function will have to write the XML tree to save the changes.

    This function does not directly write anything to the XML file; the calling function is responsible for doing so.
    """
    selfrole_list = ctx.tree.find('selfroles')
    selfroles_ch_id = int(selfrole_list.find('channel').find('id').text)
    if selfroles_ch_id != -42:
        if to_add:
            msg_obj = await cog.bot.get_channel(selfroles_ch_id).send(
                embed=await get_single_group_msg(group))
            group.find('message').find('id').text = str(msg_obj.id)
        else:
            msg_id = int(group.find('message').find('id').text)
            msg_obj = await cog.bot.get_channel(selfroles_ch_id).get_message(msg_id)
            await msg_obj.delete()
            group.find('message').find('id').text = str(-42)


async def get_single_group_msg(group: ET.Element) -> discord.Embed:
    """
    Args:
        group: A role assignment message group which contains 'assoc' elements.

    Returns: An embed that displays the properties and contents of the specified group.
    """
    title = "Group **{}**\n".format(group.find('name').text)
    desc_list = []
    req_role = group.find('req_role').text
    if req_role:
        desc_list.append("Role requirement: {}".format(req_role))
    max_text = group.find('max').text
    max_text = 'Unlimited' if max_text == 'all' else max_text
    desc_list.append("Limit: {}".format(max_text))
    desc = '\n'.join(desc_list)

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