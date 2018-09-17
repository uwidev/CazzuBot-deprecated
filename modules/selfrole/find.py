def find_group(groups_list: list, name: str):
    """
    Finds the specified group with name 'name' in the list groups_list, if the group exists. Returns None otherwise.
    """
    for group in groups_list:
        if group.find('name').text == name:
            return group
    return None
