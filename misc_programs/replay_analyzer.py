import datetime
import os
import re
import sys
import traceback
from collections import Counter
from io import StringIO
from urllib.request import Request, urlopen
import misc_programs.showdown_data as showdown_data
import gspread
import numpy as np

import misc_programs.players as players
import utils


name_replacement_dict = {
    "Lycanroc": "Lycanroc-Midday",
    "Maushold-Four": "Maushold",
    "Vivillon-Fancy": "Vivillon",
    "Dudunsparce-*": "Dudunsparce",
    "Keldeo-Resolute": "Keldeo",
    "Florges-Red": "Florges",
    "Florges-Yellow": "Florges",
    "Florges-Orange": "Florges",
    "Florges-Blue": "Florges",
    "Florges-White": "Florges",
    "Tauros-Paldea-Combat": "Tauros-Paldea",
    "Tauros-Paldea-Blaze": "Tauros-Paldea-Fire",
    "Tauros-Paldea-Aqua": "Tauros-Paldea-Water",
    "Basculegion": "Basculegion-M",
    "Meowstic": "Meowstic-M",
    "Squawkabilly-Blue": "Squawkabilly",
    "Squawkabilly-White": "Squawkabilly",
    "Squawkabilly-Green": "Squawkabilly",
    "Squawkabilly-Yellow": "Squawkabilly",
    "Ogerpon-Wellspring-Tera": "Ogerpon-Wellspring",
    "Palafin-Hero": "Palafin",
    "Tornadus-Therian": "Tornadus-T",
    "Thundurus-Therian": "Thundurus-T",
    "Urshifu-*": "Urshifu-RS",
    "Urshifu-Rapid-Strike": "Urshifu-RS",
    "Tatsugiri-Stretchy": "Tatsugiri",
    "Sinistcha-Masterpiece": "Sinistcha",
}


def upload_replay(gamelink: str):
    try:
        req = Request(url=gamelink, headers={"User-Agent": "Mozilla/5.0"})
        data = urlopen(req).read().decode("utf-8")
        name_dict = {}

        player1 = re.search(r"\|player\|p1\|(.*?)\|", data).group(1)
        player2 = re.search(r"\|player\|p2\|(.*?)\|", data).group(1)

        teams = {player1: set(), player2: set()}

        for poke in re.findall(r"\|poke\|p([12])\|(.*?),", data):
            teams[player1 if poke[0] == "1" else player2].add(
                name_replacement_dict.get(poke[1], poke[1])
            )

        for name in re.findall(
            r"\|(?:switch|drag|replace)\|p[12][ab]: (.*?)\|([\w\s\-.]*)", data
        ):
            name_dict[name[0]] = name_replacement_dict.get(name[1], name[1])

        print(name_dict)
        # print(teams)
        death_dict = {name: 0 for name in name_dict.values()}

        for death in re.findall(r"\|faint\|p[12][ab]: (.*)\s", data):
            death_dict[name_dict[death]] += 1

        kill_dict = {name: 0 for name in name_dict.values()}
        print(death_dict)
        for kill in re.findall(
            r"\|move\|p1[ab]: ([^|]*?)\|[\w -]*\|.*\n(?:^(?:(?!\|move\||\|\n).)*$\n)*?\|faint\|p2[ab].*\n(?:\|(faint)\|p2[ab].*\n)?",
            data,
            re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[1] else 1
        for kill in re.findall(
            r"\|move\|p2[ab]: ([^|]*?)\|[\w -]*\|.*\n(?:^(?:(?!\|move\||\|\n).)*$\n)*?\|faint\|p1[ab].*\n(?:\|(faint)\|p1[ab].*\n)?",
            data,
            re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[1] else 1

        for kill in re.findall(
            r"(?=\|move\|p[12][ab]: (.*?)\|Toxic\|(p[12][ab]: .*)(?:.|\n)*\|-damage\|\2\|0 fnt\|\[from\] psn)",
            data,
            re.MULTILINE,
        ):  # toxic
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Will-O-Wisp\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data,
            re.MULTILINE,
        ):  # will-o-wisp
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Scald\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data,
            re.MULTILINE,
        ):  # will-o-wisp
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Tri Attack\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data,
            re.MULTILINE,
        ):  # will-o-wisp
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Heat Wave\|(?:.|\n)*\|-status\|(.*?)\|brn\n(?:.|\n)*\2\|0 fnt\|\[from\] brn)",
            data,
            re.MULTILINE,
        ):  # heatwave
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|-weather\|Sandstorm\|\[from\] ability: Sand Stream\|\[of\] p1[ab]: (.*)\n(?:.|\n)*\|-damage\|p2[ab]: (.*?)\|0 fnt\|\[from\] Sandstorm(?:.|\n)*\|faint\|p2[ab]: \2)",
            data,
            re.MULTILINE,
        ):  # sand
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|-weather\|Sandstorm\|\[from\] ability: Sand Stream\|\[of\] p2[ab]: (.*)\n(?:.|\n)*\|-damage\|p1[ab]: (.*?)\|0 fnt\|\[from\] Sandstorm(?:.|\n)*\|faint\|p1[ab]: \2)",
            data,
            re.MULTILINE,
        ):  # sand
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"\|-damage\|p[12][ab]: ([^|]*?)\|0 fnt\|\[from\] ability: Rough Skin\|\[of\] p[12][ab]: ([^|]*?)$",
            data,
            re.MULTILINE,
        ):  # rough skin
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Perish Song\|(p[12][ab]: .*)\n(?:.|\n)*\|perish0(?:.|\n)*\|faint\|(.*\n\|faint)?)",
            data,
            re.MULTILINE,
        ):  # perish song
            kill_dict[name_dict[kill[0]]] += 2 if kill[1] else 1

        for kill in re.findall(
            r"(?:p[12][ab]: ([^|]*?)\|0 fnt\|\[from\] Leech Seed\|\[of\] p[12][ab]: ([^|]*?)$)",
            data,
            re.MULTILINE,
        ):  # leech seed
            kill_dict[name_dict[kill[0]]] += 1

        winner = re.search(r"\|win\|([\w\- !]*)", data).group(1)

        gc = gspread.service_account(filename="resources\\service_account.json")
        print()

        # doc_id = '14IPwnyeKxohvc__aZz1HuspPHHaLmWSBzzIIX4wWi-U'
        doc_id = utils.SBL_SEASON_DOC_KEY[
            players.get_attribute_by_value("username", "league", player1)
        ]

        ws = gc.open_by_key(doc_id).worksheet("Match Logging")
        values = np.array(ws.get_all_values())

        update_array = np.empty((6, 6), dtype=object)
        update_array[0] = [player1, "", "", player2, "", ""]
        i = 2
        update_array[1] = ["Pokemon", "Kills", "Deaths", "Pokemon", "Kills", "Deaths"]
        for name in teams[player1]:
            if name in kill_dict.keys():
                update_array[i][0:3] = [name, kill_dict[name], death_dict[name]]
                i += 1

        i = 2
        for name in teams[player2]:
            if name in kill_dict.keys():
                update_array[i][3:6] = [name, kill_dict[name], death_dict[name]]
                i += 1

        search_column = values.T[17]

        # print(update_array)

        first_open = (
            next(
                (
                    i
                    for i in range(len(search_column) - 1, -1, -1)
                    if search_column[i] and search_column[i] != "Kills"
                ),
                -1,
            )
            + 2
        )
        # print(first_open)
        looking_for_top = first_open - 2

        while (
            search_column[looking_for_top] == "Kills"
            or search_column[looking_for_top].isdigit()
            or (
                search_column[looking_for_top] == ""
                and values[looking_for_top][20] != ""
            )
        ):
            looking_for_top -= 1
        # print(looking_for_top)
        if [player1, player2] in [
            [values[looking_for_top][16], values[looking_for_top][19]],
            [values[looking_for_top][19], values[looking_for_top][16]],
        ]:
            first_open -= 1
            while search_column[first_open] != "Kills":
                first_open += 1
            first_open += 2

            if player2 == values[looking_for_top][16]:
                update_array = np.c_[update_array[:, 3:], update_array[:, :3]]

            looking_for_next_link = next(
                i + 1
                for i in range(looking_for_top + 15, looking_for_top + 25)
                if not values[i][4]
            )
            index_of_winner = looking_for_top + (
                0 if winner == values[looking_for_top][16] else 7
            )
            update_data = [
                {
                    "range": f"Q{first_open}:V{first_open + 3}",
                    "values": update_array[-4:].tolist(),
                },
                {"range": f"E{looking_for_next_link}", "values": [[gamelink]]},
                {
                    "range": f"J{index_of_winner + 1}:J{index_of_winner + 1}",
                    "values": [[int(values[index_of_winner][9]) + 1]],
                },
            ]
            print(f"This has been a problem number: {int(values[index_of_winner][9])}")
            ws.batch_update(update_data)

            week = utils.get_current_week()
            set_winner_score = int(values[index_of_winner][9]) + 1
            if week <= 9:
                if set_winner_score >= 2:
                    set_score = (
                        max(
                            int(values[looking_for_top][9]),
                            int(values[looking_for_top + 7][9]),
                        )
                        + 1,
                        min(
                            int(values[looking_for_top][9]),
                            int(values[looking_for_top + 7][9]),
                        ),
                    )

                    ws = gc.open_by_key(doc_id).worksheet("Schedule and Results")
                    values = ws.get_all_values()
                    winner_name = players.get_attribute_by_value(
                        "username", "name", winner
                    )
                    # winner_name = 'Shellshock'
                    loser_name = players.get_attribute_by_value(
                        "username", "name", player1 if player2 == winner else player2
                    )
                    # loser_name = 'Tagtree Mischievous Creatures (Saget)'
                    row, col = utils.get_row_col_from_number(week)

                    for i in range(1, utils.MATCHES_PER_WEEK + 1):
                        if (
                            winner_name in values[row + i][col + 1]
                            and loser_name in values[row + i][col + 5]
                        ):
                            # update_score_and_format(
                            #     ws, row + i + 1, col + 1, set_score[0], 'green')
                            ws.update_cell(row + i + 1, col + 1, set_score[0])
                            ws.update_cell(row + i + 1, col + 9, set_score[1])
                        elif (
                            loser_name in values[row + i][col + 1]
                            and winner_name in values[row + i][col + 5]
                        ):
                            ws.update_cell(row + i + 1, col + 1, set_score[1])
                            ws.update_cell(row + i + 1, col + 9, set_score[0])
        else:
            print("That's not me!")
            while values[first_open][7] != "K/D" or values[first_open - 7][7] == "K/D":
                first_open += 1
            first_open += 1
            looking_for_next_link = next(
                i + 1
                for i in range(first_open + 14, first_open + 25)
                if not values[i][4]
            )
            # print(winner, player1, player2)
            update_data = [
                {
                    "range": f"Q{first_open}:V{first_open + 5}",
                    "values": update_array.tolist(),
                },
                {
                    "range": f"E{first_open + 1}:E{first_open + 6}",
                    "values": np.array(list(teams[player1])).reshape(6, 1).tolist(),
                },
                {
                    "range": f"E{first_open + 8}:E{first_open + 13}",
                    "values": np.array(list(teams[player2])).reshape(6, 1).tolist(),
                },
                {
                    "range": f"J{first_open}:J{first_open}",
                    "values": [["1" if winner == player1 else "0"]],
                },
                {"range": f"E{looking_for_next_link}", "values": [[gamelink]]},
                {
                    "range": f"J{first_open + 7}:J{first_open + 7}",
                    "values": [["1" if winner == player2 else "0"]],
                },
            ]
            ws.batch_update(update_data, value_input_option="USER_ENTERED")

        return 0
    except Exception:
        traceback.print_exc()
        return 1


class Pokemon:
    def __init__(self, name, player):
        self.player = player
        self.name = name
        self.moves = list()
        self.items = list()
        self.ability = set()
        self.teras = list()
        self.count = 0


def get_data(name):
    name = players.get_attribute_by_value("alias", "name", name)
    gc = gspread.service_account(filename="resources\\service_account.json")

    # doc_id = '14IPwnyeKxohvc__aZz1HuspPHHaLmWSBzzIIX4wWi-U'
    doc_id = utils.SBL_SEASON_DOC_KEY[
        players.get_attribute_by_value("name", "league", name)
    ]

    ws = gc.open_by_key(doc_id).worksheet(name)
    values = np.array(ws.get_all_values())
    r = re.compile("https://.*$")
    link_list = list(filter(r.match, values[:, 13]))

    # return
    # r = Replay('replays/test.txt')
    # f = open("replays\\test.txt", "r")
    # print(re.findall(r'https:\/\/replay.*\n', f.read()))
    links = [str(x.strip()) + ".log" for x in link_list]

    # print(len(links))
    pokemon = {}
    player_names = players.get_attribute_by_value("name", "username", name)
    player_names = [name.lower() for name in player_names]

    for link in links:
        # print(link)
        req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
        data = urlopen(req).read().decode("utf-8")

        name_dict = {}

        #
        # print(data)
        player1 = re.search(r"\|player\|p1\|([\w !-]*)\|", data).group(1).lower()
        player2 = re.search(r"\|player\|p2\|([\w !-]*)\|", data).group(1).lower()

        player = 1 if player1 in player_names else 2

        # if '|showteam|' in data:

        switched_pokemon = set()

        for name in re.findall(
            r"\|(switch|drag|replace)\|p([12])[ab]: (.*?)\|([\w\s\-.]*)", data
        ):
            name_dict[name[2]] = name[3]
            # print(name[3])
            pokemon_trainer = player1 if name[1] == "1" else player2

            if not name[3] in pokemon:
                # print(name_dict)
                pokemon[name[3]] = Pokemon(name[3], pokemon_trainer)

            # print(pokemon_trainer, player_name)
            if pokemon_trainer in player_names:
                # print(switched_pokemon)
                if name[3] not in switched_pokemon:
                    pokemon[name[3]].count += 1
                    switched_pokemon.add(name[3])

        used_moves = set()
        used_items = set()
        # print(name_dict)
        for thing in re.findall(
            r"\|move\|p%s[ab]: (.*)\|(.*)\|p[12][ab]: (.*?)[|\n]" % player, data
        ):
            # print('eher')
            move_string = name_dict[thing[0]] + "|" + thing[1]
            if move_string not in used_moves:
                pokemon[name_dict[thing[0]]].moves.append(thing[1])
                used_moves.add(move_string)

        for item in re.findall(r"p%s[ab]: (.*?)\|.*item: ([\w\s]*)\n" % player, data):
            item_string = name_dict[item[0]] + "|" + item[1]
            if item_string not in used_items:
                pokemon[name_dict[item[0]]].items.append(item[1])
                used_items.add(item_string)
            # pokemon[name_dict[item[0]]].items.add(item[1])

        for item in re.findall(r"item\|p%s[ab]: (.*?)\|([\w\s]*?)[\n|]" % player, data):
            item_string = name_dict[item[0]] + "|" + item[1]
            if item_string not in used_items:
                pokemon[name_dict[item[0]]].items.append(item[1])
                used_items.add(item_string)

        for item in re.findall(
            r"item: ([\w\s]*)\|\[of\] p%s[ab]: (.*?)\n" % player, data
        ):
            item_string = name_dict[item[1]] + "|" + item[0]
            if item_string not in used_items:
                pokemon[name_dict[item[1]]].items.append(item[0])
                used_items.add(item_string)

        for terastallize in re.findall(
            r"\|-terastallize\|p%s[ab]: (.*?)\|(.*)\n" % player, data
        ):
            # print(terastallize[1])
            pokemon[name_dict[terastallize[0]]].teras.append(terastallize[1])

        for ability in re.findall(
            r"ability\|p%s[ab]: ([^|]*?)\|([^|]*?)[|\n](?!\[from\] ability: Trace)(?:.*?)[|\n]"
            % player,
            data,
        ):
            if name_dict[ability[0]] != "Gardevoir" or ability[1] not in ["Intimidate"]:
                pokemon[name_dict[ability[0]]].ability.add(ability[1])

        for ability in re.findall(
            r"p%s[ab]: ([\w\s]*)\|(?:.*)\|\[from\] ability: (Trace)" % player, data
        ):  # Trace
            pokemon[name_dict[ability[0]]].ability.add(ability[1])

        for ability in re.findall(
            r"ability: (?!Trace)([\w\s]*)\|\[of] p%s[ab]: (.*?)[|\n]" % player, data
        ):
            pokemon[name_dict[ability[1]]].ability.add(ability[0])

        for ability in re.findall(
            r"(setboost|immune)\|p%s[ab]: (.*?)\|.*\[from] ability: (.*?)[|\n]"
            % player,
            data,
        ):
            pokemon[name_dict[ability[1]]].ability.add(ability[2])

        for ability in re.findall(
            r"p%s[ab]: (.*?)\|ability: (\w*)[|\n]" % player, data
        ):
            pokemon[name_dict[ability[0]]].ability.add(ability[1])

        #

    result = StringIO()
    sys.stdout = result
    # print(*[f'{move[0]} ({"{:.1%}".format(move[1] / value.count)})' for move in Counter(value.moves).most_common()], sep=', ')

    for key, value in pokemon.items():
        # print(key, value.player)

        if value.player in player_names:
            print(f"Name: {key}")
            print("Moves:", end=" ")
            # print(Counter(value.moves))
            if value.moves:
                print(
                    *[
                        f'{move[0]} ({"{:.1%}".format(move[1] / value.count)})'
                        for move in Counter(value.moves).most_common()
                    ],
                    sep=", ",
                )
            else:
                print("None revealed")
            print("Ability:", end=" ")
            if value.ability:
                print(*value.ability, sep=", ")

            else:
                print("None revealed")
            print("Tera Types:", end=" ")
            if value.teras:
                print(
                    *[
                        f'{tera[0]} ({"{:.1%}".format(tera[1] / value.count)})'
                        for tera in Counter(value.teras).most_common()
                    ],
                    sep=", ",
                )

            else:
                print("None revealed")
            print("Items:", end=" ")
            if value.items:
                print(
                    *[
                        f'{item[0]} ({"{:.1%}".format(item[1] / value.count)})'
                        for item in Counter(value.items).most_common()
                    ],
                    sep=", ",
                )
            else:
                print("None revealed")
            print(f"Count: {value.count}")
            print()

    output = result.getvalue()
    sys.stdout = sys.__stdout__
    return output


def get_ots_data(name):
    name = players.get_attribute_by_value("alias", "name", name)
    gc = gspread.service_account(filename="resources\\service_account.json")

    # doc_id = '14IPwnyeKxohvc__aZz1HuspPHHaLmWSBzzIIX4wWi-U'
    doc_id = utils.SBL_SEASON_DOC_KEY[
        players.get_attribute_by_value("name", "league", name)
    ]

    ws = gc.open_by_key(doc_id).worksheet("Match Logging")
    values = np.array(ws.get_all_values())
    # r = re.compile("https://.*$")
    # link_list = list(filter(r.match, values[:, 4]))

    link_list = []
    found = False

    for item in values[:, 4]:
        if name in item:
            found = True
        elif found and re.match(r"https://replay.*$", item):
            link_list.append(item)
        elif found and item == "":
            found = False

    print(link_list)
    # link_list = ["https://replay.pokemonshowdown.com/gen9vgc2024regf-2016216707"]
    # return
    # r = Replay('replays/test.txt')
    # f = open("replays\\test.txt", "r")
    # print(re.findall(r'https:\/\/replay.*\n', f.read()))
    links = [str(x.strip()) + ".log" for x in link_list]

    # print(len(links))
    pokemon = {}
    player_names = players.get_attribute_by_value("name", "username", name)
    player_names = [name.lower() for name in player_names]

    item_dict = showdown_data.get_dict("items")
    ability_dict = showdown_data.get_dict("abilities")
    move_dict = showdown_data.get_dict("moves")

    # print("here")
    # total_iterations = len(links)
    # percent_step = 100 / 10
    # last_printed_progress = 0
    for i, link in enumerate(links):
        print(link)
        # progress_percentage = (i / total_iterations) * 100
        # nearest_ten_percent = round(progress_percentage / percent_step) * percent_step
        # if (
        #     progress_percentage >= nearest_ten_percent
        #     and nearest_ten_percent > last_printed_progress
        # ):
        #     print(f"Progress: {nearest_ten_percent}%")
        #     last_printed_progress = nearest_ten_percent
        req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
        data = urlopen(req).read().decode("utf-8")

        #
        # print(data)
        player1 = re.search(r"\|player\|p1\|([\w !-]*)\|", data).group(1).lower()
        player2 = re.search(r"\|player\|p2\|([\w !-]*)\|", data).group(1).lower()

        # print(player_names)
        if player1 in player_names:
            player = 1
        elif player2 in player_names:
            player = 2
        else:
            continue
        print(player1)
        # player = 1 if player1 in player_names else 2
        # print(player)
        # if '|showteam|' in data:
        ts = re.search(r"\|showteam\|p%s\|(.*?)\n" % player, data)

        # print(ts == None)
        if ts == None:
            continue
        else:
            ts = ts.group(1)
        for line in ts.split("]"):
            name, item, ability, move_string, tera = re.search(
                r"(.*?)\|\|(.*?)\|(.*?)\|(.*?)\|\|.*,(.*)", line
            ).groups()
            # print(name, item, ability, move_string, tera)

            if not name in pokemon:
                pokemon[name] = Pokemon(name, player1 if player == 1 else player2)

            pokemon[name].items.append(item_dict[item.lower()]["name"])
            pokemon[name].ability.add(ability_dict[ability.lower()]["name"])
            pokemon[name].teras.append(tera)
            pokemon[name].count += 1
            for move in move_string.split(","):
                pokemon[name].moves.append(move_dict[move.lower()]["name"])
            # print(pokemon)
        #
    print("here")
    result = StringIO()
    sys.stdout = result
    # print(*[f'{move[0]} ({"{:.1%}".format(move[1] / value.count)})' for move in Counter(value.moves).most_common()], sep=', ')

    for key, value in pokemon.items():
        # print(key, value.player)

        if value.player in player_names:
            print(f"Name: {key}")
            print("Moves:", end=" ")
            # print(Counter(value.moves))
            if value.moves:
                print(
                    *[
                        f'{move[0]} ({"{:.1%}".format(move[1] / value.count)})'
                        for move in Counter(value.moves).most_common()
                    ],
                    sep=", ",
                )
            else:
                print("None revealed")
            print("\nAbility:", end=" ")
            if value.ability:
                print(*value.ability, sep=", ")

            else:
                print("None revealed")
            print("\nTera Types:", end=" ")
            if value.teras:
                print(
                    *[
                        f'{tera[0]} ({"{:.1%}".format(tera[1] / value.count)})'
                        for tera in Counter(value.teras).most_common()
                    ],
                    sep=", ",
                )

            else:
                print("None revealed")
            print("\nItems:", end=" ")
            if value.items:
                print(
                    *[
                        f'{item[0]} ({"{:.1%}".format(item[1] / value.count)})'
                        for item in Counter(value.items).most_common()
                    ],
                    sep=", ",
                )
            else:
                print("None revealed")
            print(f"\nCount: {value.count}\n\n\n")
            print()

    output = result.getvalue()
    sys.stdout = sys.__stdout__
    # print(output)
    return output
