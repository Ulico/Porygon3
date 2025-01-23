import json

from munch import DefaultMunch

player_list = list()


def get_player_data():
    player_file = open('resources//players.json')
    player_data = json.load(player_file)

    for player in player_data['players']:
        player_list.append(DefaultMunch.fromDict(player))


def get_attribute_by_value(search_attribute: str, return_attribute: str, value: str) -> str:
    get_player_data()
    if isinstance(value, str):
        value = value.lower()
    for player in player_list:
        if search_attribute == "alias":
            if value == player.name.lower() or player.aliases and value in [alias.lower() for alias in player.aliases]:
                return getattr(player, return_attribute)
        elif search_attribute == "username":
            if player.username and value in [username.lower() for username in player.username]:
                return getattr(player, return_attribute)
        else:
            if hasattr(player, search_attribute):
                if isinstance(getattr(player, search_attribute), str):
                    if getattr(player, search_attribute).lower() == value:
                        return getattr(player, return_attribute)
                else:
                    if getattr(player, search_attribute) == value:
                        return getattr(player, return_attribute)
    raise ValueError(f"No player found with {search_attribute} '{value}'")
