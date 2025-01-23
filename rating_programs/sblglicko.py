import utils
import glicko2
import math
import players


def get_rating_string(name):
    rating = get_rating(name)
    return f"Glicko: {int(rating.rating)} ± {int(2 * rating.rd)}"


def get_rating(name):
    records = utils.get_record_sheet()

    name = players.get_attribute_by_value("alias", "name", name)

    playerratings = {}
    for _, game in records.iterrows():
        p1 = game["Player 1"]
        p2 = game["Player 2"]
        if p1 not in playerratings:
            playerratings[p1] = glicko2.Player(vol=0.08)
        if p2 not in playerratings:
            playerratings[p2] = glicko2.Player(vol=0.08)

        if game["Winner Name"] == p1:
            playerratings[p1].update_player(
                [playerratings[p2].rating], [playerratings[p2].rd], [1]
            )
            playerratings[p2].update_player(
                [playerratings[p1].rating], [playerratings[p1].rd], [0]
            )
        else:
            playerratings[p1].update_player(
                [playerratings[p2].rating], [playerratings[p2].rd], [0]
            )
            playerratings[p2].update_player(
                [playerratings[p1].rating], [playerratings[p1].rd], [1]
            )

    return playerratings[name]


def get_leaderboard():
    records = utils.get_record_sheet()
    # print(records)
    playerratings = {}
    for _, game in records.iterrows():
        p1 = game["Player 1"]
        p2 = game["Player 2"]
        if p1 not in playerratings:
            playerratings[p1] = glicko2.Player(vol=0.08)
        if p2 not in playerratings:
            playerratings[p2] = glicko2.Player(vol=0.08)

        if game["Winner Name"] == p1:
            playerratings[p1].update_player(
                [playerratings[p2].rating], [playerratings[p2].rd], [1]
            )
            playerratings[p2].update_player(
                [playerratings[p1].rating], [playerratings[p1].rd], [0]
            )
        else:
            playerratings[p1].update_player(
                [playerratings[p2].rating], [playerratings[p2].rd], [0]
            )
            playerratings[p2].update_player(
                [playerratings[p1].rating], [playerratings[p1].rd], [1]
            )

    # return playerratings[name]
    return_string = ""
    # for item in dict(sorted(playerratings.items(), key=lambda item: -item[1].rating)).items():
    # #     if item[1].sigma < 2.5:
    # #         #  print('*', end='')
    #         print(f'{item[0]}: {int(item[1].rating)} ± {int(2 * item[1].rd)}')

    activeratings = {}

    for p in playerratings.items():
        # print(p)
        if players.get_attribute_by_value("alias", "active", p[0]) == True:
            activeratings[p[0]] = p[1]

    return "\n".join(
        [
            f"{item[0]}: {int(item[1].rating)} ± {int(2 * item[1].rd)}"
            for item in dict(
                sorted(activeratings.items(), key=lambda item: -item[1].rating)
            ).items()
        ]
    )
