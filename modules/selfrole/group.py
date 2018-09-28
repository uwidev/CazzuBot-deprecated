import discord
from discord.ext import commands
import xml.etree.ElementTree as ET
import modules.utility as utility
import modules.factory
import modules.selfrole.message
import modules.selfrole.find


# ----------------------------------------------------------------------------------------------------------------------
# Commands to add/remove groups

async def groupCreate(admin_cog, ctx, name: str, display_output=True):
    """
    Creates a group which may contain roles. Roles must be placed in a group.

    Group names can contain whitespace, but the group name must be surrounded in quotes.

    required_role: the role required for a user to be able to add or remove roles from this group.

    max_selectable: the maximum number of roles a user can select from the group.
    By default, all roles from a group may be assigned at once.
    If an integer less than or equal to 0 is specified, will default to 'all'.
    """
    required_role = ""
    max_selectable = 'all'

    if name in ['*', 'reset']:
        raise commands.CommandInvokeError(":x: ERROR: Name **{}** is reserved.".format(name))
    if type(max_selectable) == int and max_selectable <= 0:
        max_selectable = 'all'
    selfrole_list = ctx.tree.find('selfroles')
    associations = selfrole_list.find('associations')
    groups_list = associations.findall('group')
    if not modules.selfrole.find.find_group(groups_list, name) is None:
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
    group_max_select = ET.SubElement(group, 'max')
    [msg_id.text, group_role.text, group_max_select.text] = ['-42', str(required_role), str(max_selectable)]

    await modules.selfrole.message.add_delete_selfrole_msg(admin_cog, ctx, group, True)
    msg_id_list = admin_cog.conv_to_id_list(selfrole_list.find('message').find('id').text) + \
                  [group.find('message').find('id').text]
    selfrole_list.find('message').find('id').text = admin_cog.conv_to_msg_text(msg_id_list)
    await modules.utility.write_xml(ctx)
    if display_output:
        await ctx.send("Group **{}** successfully created!".format(name))
        if ' ' in name:
            await ctx.send("<:cirnoWow:489185064224161793> Looks like this group has a space in its name! "
                           "To use/modify groups that contain spaces, surround the name in quotes.\n"
                           "Ex: c!selfrole reset \"sample group\"")


async def groupDelete(admin_cog, ctx, name: str, display_output=True, skip_verification=False):
    """
    Deletes a group.
    """
    selfrole_list = ctx.tree.find('selfroles')
    associations = selfrole_list.find('associations')
    target_group = None
    num_roles = -1
    for group in associations.findall('group'):
        if group.find('name').text == name:
            target_group = group
            num_roles = len(group.findall('assoc'))
            break
    if num_roles == -1:
        raise commands.CommandInvokeError("Group **{}** doesn't exist.".format(name))

    if not skip_verification:
        def verification(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']

        await ctx.send(':exclamation: Are you sure you want to delete group **{}**? ({} role{}) [`Yes`/`No`]'.format(
            name, num_roles, '' if num_roles == 1 else 's'))
        reply = await admin_cog.bot.wait_for('message', check=verification, timeout=5)

        if reply.content.lower() == 'no':
            raise commands.CommandInvokeError(':octagonal_sign: Deletion of group **{}** cancelled.'.format(name))

    msg_id = int(target_group.find('message').find('id').text)
    if msg_id != -42:
        await modules.selfrole.message.add_delete_selfrole_msg(admin_cog, ctx, target_group, False)
        msg_id_list = admin_cog.remove_item_from_list(admin_cog.conv_to_id_list(selfrole_list.find('message').find('id').text), msg_id)
        selfrole_list.find('message').find('id').text = admin_cog.conv_to_msg_text(msg_id_list)

    associations.remove(target_group)
    await modules.utility.write_xml(ctx)
    if display_output:
        await ctx.send("Group **{}** successfully deleted.".format(name))


# ----------------------------------------------------------------------------------------------------------------------
# Commands to modify groups
# Other than add/delete, these commands all assume ctx.tree has already been defined


async def role_add(admin_cog, ctx, group: ET.Element, emoji: modules.utility.AllEmoji, role: discord.Role):
    """
    Adds a role and associates it with an emoji.
    Roles must be placed in a group. See 'c!selfrole group add' for more details.
    Will automatically update role assignment message, if one exists.
    """

    # Check if emoji is bound to role in this group
    for assoc in group.findall('assoc'):
        if assoc.find('emoji').text == str(emoji):
            raise commands.CommandInvokeError(
                "Error: {} is already bound to a role. Please unassign the emoji before assigning it to a different role.".format(
                    emoji))
        if assoc.find('role').find('id').text == str(role.id):
            raise commands.CommandInvokeError(
                "Error: \"{}\" is already bound to an emoji. Please unbind the emoji and the role.".format(role.name))

    # functional code
    await modules.factory.WorkerAddRole.create_role(group, emoji, role)

    await modules.utility.write_xml(ctx)
    await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, True, emoji, True)
    await ctx.send("Emoji {} successfully registered with role \"{}\"".format(emoji, role.name))


async def role_del(admin_cog, ctx, group: ET.Element, role: discord.Role):
    """
    Removes a role and its corresponding emoji.
    Will automatically update role assignment message, if one exists.
    """

    # Check if emoji is bound to role in this group
    curr_assoc = None
    group_contains_role = False
    for a in group.findall('assoc'):
        print(a.find('role').find('id').text)
        if a.find('role').find('id').text == str(role.id):
            group_contains_role = True
            curr_assoc = a
            break
    if not group_contains_role:
        raise commands.CommandInvokeError("Error: could not find role \"{}\" in group **{}**.".format(
            role, group.find('name').text))

    old_emoji = await modules.utility.AllEmoji().convert(ctx, curr_assoc.find('emoji').text)
    group.remove(curr_assoc)
    await modules.utility.write_xml(ctx)
    await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, True, old_emoji, False)
    await ctx.send("Role \"{}\" successfully removed; previously bound to emoji {}".format(role, old_emoji))


async def group_change_name(admin_cog, ctx, group: ET.Element, new_name: str):
    """
    Renames a group.
    When renaming groups, they will not be automatically sorted (as of right now).
    """
    old_name = group.find('name').text

    selfrole_list = ctx.tree.find('selfroles')
    associations = selfrole_list.find('associations')
    groups_list = associations.findall('group')
    if modules.selfrole.find.find_group(groups_list, new_name) is not None:
        raise commands.BadArgument("Group **{}** already exists; unable to rename **{}**".format(
            new_name, group.find('name').text))

    group.find('name').text = new_name
    await modules.utility.write_xml(ctx)
    await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, False)
    await ctx.send("**{}** has been renamed to **{}**".format(old_name, new_name))


async def group_change_role_req(admin_cog, ctx, group: ET.Element, new_role_str: str):
    """
    Changes the role requirement for the specified group to newRole.
    """
    old_role_name = group.find('req_role').text

    if not new_role_str:
        await ctx.send('Current role requirement to use group **{}**: "{}"'.format(
            group.find('name').text, group.find('req_role').text))
    elif new_role_str == "reset":
        group.find('req_role').text = ""
        await modules.utility.write_xml(ctx)
        await ctx.send("**{}**'s role requirement has been reset (was {})".format(
            group.find('name').text, old_role_name))
    else:
        if old_role_name == new_role_str:
            raise commands.BadArgument("New required role is the same as the old required role")

        new_role = commands.RoleConverter().convert(new_role_str)

        group.find('req_role').text = str(new_role)
        await modules.utility.write_xml(ctx)
        await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, False)
        await ctx.send("**{}**'s required role has been changed from \"{}\" to \"{}\"".format(
            group.find('name').text, old_role_name, new_role_str))


async def group_change_max(admin_cog, ctx, group: ET.Element, new_max: modules.utility.MaxRoleStr):
    old_max = group.find('max').text

    if new_max is None:
        await ctx.send('Current limit for group **{}**: {}'.format(
            group.find('name').text, 'Unlimited' if old_max == 'all' else old_max))
    elif new_max == "reset":
        group.find('max').text = "all"
        await modules.utility.write_xml(ctx)
        await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, False)
        await ctx.send("**{}**'s role limit has been reset to \"all\" (was {})".format(
            group.find('name').text, old_max))
    else:
        group.find('max').text = str(new_max)
        await modules.utility.write_xml(ctx)
        await modules.selfrole.message.edit_selfrole_msg(admin_cog, ctx, group, False)
        await ctx.send('**{}**\'s max roles assignable has been changed from "{}" to "{}"'.format(
            group.find('name').text, old_max, new_max))


async def group_reset(admin_cog, ctx, group: ET.Element):
    g_name = group.find('name').text
    num_roles = len(group.findall('assoc'))

    def verification(m):
        return m.author == ctx.author and m.content.lower() in ['yes', 'no']

    await ctx.send(':exclamation: Are you sure you want to reset group **{}**? ({} role{}) [`Yes`/`No`]'.format(
        g_name, num_roles, '' if num_roles == 1 else 's'))
    reply = await admin_cog.bot.wait_for('message', check=verification, timeout=5)

    if reply.content.lower() == 'no':
        raise commands.CommandInvokeError(':octagonal_sign: Reset of group **{}** cancelled.'.format(g_name))

    await groupDelete(admin_cog, ctx, g_name, False, skip_verification=True)
    await groupCreate(admin_cog, ctx, g_name, False)
    await ctx.send("**{}** has been reset to default settings".format(group.find('name').text))
