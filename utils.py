import gspread
import datetime
import requests
import numpy as np
import time
import os
import math
import pandas as pd

DEBUG = False

SBL_MATCH_REPLAYS_ID = 988627307801509929
SBL_TRANSACTIONS = 988631759304396800
COMMISSIONER_ID = 988624003080028221
SBL_GAME_CORNER_ID = 997596303804596324
SBL_STAFF_ID = 988624438876573726
SBL_ROTOM_CODER_ID = 988967432062390293
TEST_CHANNEL_ID = 884553177104523377

NUM_TEAMS = 24
NUM_POKEMON = 10
START_WEEK = 29
MATCHES_PER_WEEK = 10

SEASON_NUMBER = 9
# DIVISIONS = ['Wayward', 'Iron', 'Hallowed']
SBL_SEASON_DOC_KEY = {
    "Main": "1upgmr3T10W08RLPArnJBeTgYUx3ju75nulKIPfNecQA",
}

FORMAT_ABBR = "gen9vgc2025regg"

NUM_WEEKS = 10
POST_SEASON_BREAK = 2
ALLOW_UPLOAD = True
WEEKLY_COINS = 250
allow_bets = True

stat_names = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
color_dict = {
    "normal": 0xA8A77A,
    "fire": 0xEE8130,
    "water": 0x6390F0,
    "electric": 0xF7D02C,
    "grass": 0x7AC74C,
    "ice": 0x96D9D6,
    "fighting": 0xC22E28,
    "poison": 0xA33EA1,
    "ground": 0xE2BF65,
    "flying": 0xA98FF3,
    "psychic": 0xF95587,
    "bug": 0xA6B91A,
    "rock": 0xB6A136,
    "ghost": 0x735797,
    "dragon": 0x6F35FC,
    "dark": 0x705746,
    "steel": 0xB7B7CE,
    "fairy": 0xD685AD,
    "": 0,
}


def get_current_week():
    # return 2
    week = datetime.datetime.now().isocalendar()[1] - START_WEEK
    if week <= 0:
        return 1
    else:
        return week


def get_values_from_sheet(league_name, wsname):
    gc = gspread.service_account(filename="resources\\service_account.json")
    ws = gc.open_by_key(SBL_SEASON_DOC_KEY[league_name]).worksheet(wsname)
    # np.set_printoptions(threshold=np.inf)
    return np.array(ws.get_all_values())


def get_row_col_from_number(num):
    row_jump = MATCHES_PER_WEEK + 2
    col_jump = 10

    row = 0
    col = 0

    if 0 < num <= NUM_WEEKS:
        row = row_jump * ((num - 1) // 2)
        col = col_jump * ((num - 1) % 2)

    return row, col


def equals_ic(p):
    return lambda v: v.casefold() == p.casefold()


def get_pokedex_number(num: str) -> str:
    split_num = str(num).split("-")
    if split_num[0].isdigit():
        number = "%03d" % int(split_num[0])
    else:
        number = "%03d" % int(split_num[0][:-1])
    if len(split_num) > 1:
        number += f"-{split_num[1]}"
    return number


def get_image_from_number(number):
    # sv_image_exists = is_url_image(
    #     f"https://www.serebii.net/swordshield/pokemon/{number}.png"
    # )

    # return f'https://www.serebii.net/{"swordshield" if sv_image_exists else "scarletviolet"}/pokemon/new/{number}.png'
    # print()
    print(f"https://www.serebii.net/scarletviolet/pokemon/new/{number}.png")
    return f"https://www.serebii.net/scarletviolet/pokemon/new/{number}.png"


def format_week(week_str):
    if week_str == "Amateur":
        return "Amateur Cup"
    elif week_str in ["Tiebreaker", "Playoffs"]:
        return week_str
    else:
        return "Week " + week_str


def get_record_sheet():
    gc = gspread.service_account(filename="resources\\service_account.json")
    df = pd.DataFrame(
        gc.open("Records").sheet1.get_all_values(),
        columns=[
            "Match #",
            "Season",
            "Week",
            "Player 1",
            "Player 2",
            "Player 1 Game Count",
            "Player 2 Game Count",
            "Winner",
            "Winner Name",
        ],
    )
    df = df[1:]
    df = df.set_index("Match #")
    return df


def is_url_image(image_url):
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    r = requests.head(image_url)
    if r.headers["content-type"] in image_formats:
        return True
    return False


def get_time_elapsed_str() -> str:
    modification_time = os.path.getmtime("resources\\coins.txt")

    # Calculate the time elapsed since the file was last edited
    current_time = time.time()
    time_elapsed = current_time - modification_time

    # Convert the time elapsed to a human-readable format
    if time_elapsed < 60:
        # File was edited less than a minute ago
        time_elapsed_str = "less than a minute ago"
    elif time_elapsed < 3600:
        # File was edited less than an hour ago
        time_elapsed_minutes = int(time_elapsed / 60)
        time_elapsed_str = f"{time_elapsed_minutes} minutes ago"
    elif time_elapsed < 86400:
        # File was edited less than a day ago
        time_elapsed_hours = int(time_elapsed / 3600)
        time_elapsed_str = f"{time_elapsed_hours} hours ago"
    else:
        # File was edited more than a day ago
        time_elapsed_days = int(time_elapsed / 86400)
        time_elapsed_str = f"{time_elapsed_days} days ago"
    return time_elapsed_str


def get_matchesleft():
    num = get_current_week()

    HEADER_LENGTH = 1

    if num > NUM_WEEKS:
        pairs = []
        for page in ["Playoffs", "Season 8 Cup"]:
            values = get_values_from_sheet("Main", page)
            playoff_week = (
                num - NUM_WEEKS - POST_SEASON_BREAK
            )  # -1 for all star if necesarry
            # print(playoff_week)
            matches = []
            # playoff_week = 2
            for week in range(playoff_week, 0, -1):
                players = values.T[2 * week - 1][HEADER_LENGTH:]
                scores = values.T[2 * week][HEADER_LENGTH:]
                matches += [
                    " ".join(m.split(" ")[:-1])
                    for (m, s) in zip(players, scores)
                    if m and not s
                ]
            print(matches)
            # Pair up the remaining strings

            for i in range(0, math.floor(len(matches) / 2) * 2, 2):
                pair = f"{matches[i]} vs. {matches[i+1]}"
                if (
                    "Winner" not in pair
                    and "Loser" not in pair
                    and "Grands" not in pair
                ):
                    pairs.append(pair)

        return num, pairs
    else:
        remaining_matches = []
        for league in SBL_SEASON_DOC_KEY.keys():
            values = get_values_from_sheet(league, "Schedule and Results")
            print(values)
            row, col = get_row_col_from_number(num)
            print(row, col)
            matches_tuples = list(
                zip(
                    values.T[col + 1][row + 1 : row + MATCHES_PER_WEEK + 1],
                    values.T[col + 5][row + 1 : row + MATCHES_PER_WEEK + 1],
                )
            )

            print(matches_tuples)

            remaining_matches.extend(
                [
                    matches_tuples[i]
                    for i, score in enumerate(
                        values.T[col][row + 1 : row + MATCHES_PER_WEEK + 1]
                    )
                    if not score
                ]
            )

            if num > 1:
                prev_row, prev_col = get_row_col_from_number(num - 1)
                old_matches = list(
                    zip(
                        values.T[prev_col + 1][
                            prev_row + 1 : prev_row + MATCHES_PER_WEEK + 1
                        ],
                        values.T[prev_col + 5][
                            prev_row + 1 : prev_row + MATCHES_PER_WEEK + 1
                        ],
                    )
                )
                remaining_matches.extend(
                    [
                        old_matches[i]
                        for i, score in enumerate(
                            values.T[prev_col][
                                prev_row + 1 : prev_row + MATCHES_PER_WEEK + 1
                            ]
                        )
                        if not score
                    ]
                )
        return num, ["{} vs. {}".format(pair[0], pair[1]) for pair in remaining_matches]


def remove_empty_strings_from_ends(arr):
    # Find the indices of non-empty strings from the beginning and end
    start_idx = 0
    end_idx = len(arr)

    for i, s in enumerate(arr):
        if s != "":
            start_idx = i
            break

    for i in range(len(arr) - 1, -1, -1):
        if arr[i] != "":
            end_idx = i + 1
            break

    # Slice the array to remove empty strings from the ends
    trimmed_arr = arr[start_idx:end_idx]

    return trimmed_arr
