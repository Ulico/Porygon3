import datetime
import json
import re
import traceback
from urllib.request import Request, urlopen

import db

POKEMON_JSON_URL = "https://planner.springfieldbattleleague.com/pokemon.json"

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
    "Landorus-Therian": "Landorus-T",
    "Urshifu-*": "Urshifu-RS",
    "Urshifu-Rapid-Strike": "Urshifu-RS",
    "Tatsugiri-Stretchy": "Tatsugiri",
    "Tatsugiri-Droopy": "Tatsugiri",
    "Ogerpon-Hearthflame-Tera": "Ogerpon-Hearthflame",
    "Sinistcha-Masterpiece": "Sinistcha",
    "Greninja-*": "Greninja",
    "Alcremie-Salted-Cream": "Alcremie",
    "Alcremie-Caramel-Swirl": "Alcremie",
    "Alcremie-Mint-Cream": "Alcremie",
    "Alcremie-Ruby-Cream": "Alcremie",
    "Gastrodon-East": "Gastrodon",
}


def replace_name(name):
    return name_replacement_dict.get(name, name)


def load_pokemon_ids():
    req = Request(url=POKEMON_JSON_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urlopen(req).read().decode("utf-8"))
    return {entry["name"]: entry["id"] for entry in data["pokemon"] if "name" in entry and "id" in entry}


def analyze_replay(gamelink: str, pokemon_ids: dict):
    try:
        req = Request(url=gamelink, headers={"User-Agent": "Mozilla/5.0"})
        data = urlopen(req).read().decode("utf-8")

        player1 = re.search(r"\|player\|p1\|(.*?)\|", data).group(1)
        player2 = re.search(r"\|player\|p2\|(.*?)\|", data).group(1)

        teams = {player1: set(), player2: set()}
        for poke in re.findall(r"\|poke\|p([12])\|(.*?),", data):
            teams[player1 if poke[0] == "1" else player2].add(replace_name(poke[1]))

        name_dict = {}
        for nickname, species in re.findall(
            r"\|(?:switch|drag|replace)\|p[12][ab]: (.*?)\|([\w\s\-.]*)", data
        ):
            if nickname not in name_dict:
                name_dict[nickname] = replace_name(species)

        death_dict = {name: 0 for name in name_dict.values()}
        for death in re.findall(r"\|faint\|p[12][ab]: (.*)\s", data):
            death_dict[name_dict[death]] += 1

        kill_dict = {name: 0 for name in name_dict.values()}

        for kill in re.findall(
            r"(?=\|move\|p1[ab]: ([^|]*?)\|[\w -]*\|.*\n(?:^(?:(?!\|move\||\|\n).)*$\n)*?(\|faint\|p2[ab].*\n)(?:.*\n)*?(?:\|(faint)\|p2[ab].*\n)?)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[2] else 1

        for kill in re.findall(
            r"(?=\|move\|p2[ab]: ([^|]*?)\|[\w -]*\|.*\n(?:^(?:(?!\|move\||\|\n).)*$\n)*?(\|faint\|p1[ab].*\n)(?:.*\n)*?(?:\|(faint)\|p1[ab].*\n)?)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[2] else 1

        for kill in re.findall(
            r"(?=\|move\|p[12][ab]: (.*?)\|Toxic\|(p[12][ab]: .*)(?:.|\n)*\|-damage\|\2\|0 fnt\|\[from\] psn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?=\|move\|p[12][ab]: (.*?)\|Poison Jab\|(p[12][ab]: .*)(?:.|\n)*\|-damage\|\2\|0 fnt\|\[from\] psn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Will-O-Wisp\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Scald\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Tri Attack\|(p[12][ab]: .*)\n(?:.|\n)*\|-status\|(\2)\|brn\n(?:.|\n)*0 fnt\|\[from\] brn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Heat Wave\|(?:.|\n)*\|-status\|(.*?)\|brn\n(?:.|\n)*\2\|0 fnt\|\[from\] brn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p[12][ab]: (.*?)\|Sacred Fire\|(?:.|\n)*\|-status\|(.*?)\|brn\n(?:.|\n)*\2\|0 fnt\|\[from\] brn)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|-weather\|Sandstorm\|\[from\] ability: Sand Stream\|\[of\] p1[ab]: (.*)\n(?:.|\n)*\|-damage\|p2[ab]: (.*?)\|0 fnt\|\[from\] Sandstorm(?:.|\n)*\|faint\|p2[ab]: \2)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|-weather\|Sandstorm\|\[from\] ability: Sand Stream\|\[of\] p2[ab]: (.*)\n(?:.|\n)*\|-damage\|p1[ab]: (.*?)\|0 fnt\|\[from\] Sandstorm(?:.|\n)*\|faint\|p1[ab]: \2)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"\|-damage\|p[12][ab]: ([^|]*?)\|0 fnt\|\[from\] ability: Rough Skin\|\[of\] p[12][ab]: ([^|]*?)$",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        for kill in re.findall(
            r"(?:\|move\|p2[ab]: (.*?)\|Perish Song\|(?:p2[ab]: .*)\n(?:.|\n)*\|perish0(?:.|\n)*(?:\|faint\|p1[ab]: (.*))\n(?:\|faint\|p1[ab]: (.*)))",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[2] else 1

        for kill in re.findall(
            r"(?:\|move\|p1[ab]: (.*?)\|Perish Song\|(?:p1[ab]: .*)\n(?:.|\n)*\|perish0(?:.|\n)*(?:\|faint\|p2[ab]: (.*))\n(?:\|faint\|p2[ab]: (.*)))",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 2 if kill[2] else 1

        for kill in re.findall(
            r"(?:p[12][ab]: ([^|]*?)\|0 fnt\|\[from\] Leech Seed\|\[of\] p[12][ab]: ([^|]*?)$)",
            data, re.MULTILINE,
        ):
            kill_dict[name_dict[kill[0]]] += 1

        winner_match = re.search(r"\|win\|([\w\- !]*)", data)
        winner = winner_match.group(1) if winner_match else "Unknown"

        appeared = set(name_dict.values())
        team_data = {}
        for player in [player1, player2]:
            team_data[player] = [
                {
                    "name": poke_name,
                    "pokemon_id": pokemon_ids.get(poke_name, "N/A"),
                    "kills": kill_dict.get(poke_name, 0),
                    "deaths": death_dict.get(poke_name, 0),
                    "appeared": poke_name in appeared,
                }
                for poke_name in sorted(teams[player])
            ]

        return {
            "player1": player1,
            "player2": player2,
            "replay_url": gamelink,
            "winner": winner,
            "teams": team_data,
        }

    except Exception:
        traceback.print_exc()
        return None


def upload_replay(replay_data: dict):
    player1 = replay_data["player1"]
    player2 = replay_data["player2"]
    winner = replay_data["winner"]
    replay_url = replay_data["replay_url"]

    season_id = db.get_current_season_id()
    if not season_id:
        print("ERROR: Could not determine current season ID")
        return
    team1_id = db.get_team_id_for_username(player1, season_id)
    team2_id = db.get_team_id_for_username(player2, season_id)
    if not team1_id or not team2_id:
        print(f"ERROR: Could not resolve team IDs — {player1}={team1_id}, {player2}={team2_id}")
        return
    match = db.get_match_for_teams(team1_id, team2_id, season_id)
    if not match:
        print(f"ERROR: No match found for {player1} vs {player2} in current season")
        return
    match_id = match["id"]  # type: ignore[index]
    team_a_id = match["team_a_id"]  # type: ignore[index]
    team_b_id = match["team_b_id"]  # type: ignore[index]

    game_number = db.count_games_for_match(match_id) + 1

    winner_team_id = team1_id if winner == player1 else team2_id
    game_date = datetime.date.today().isoformat()
    game_id = db.insert_game(match_id, game_number, replay_url, winner_team_id, game_date)
    if not game_id:
        print("ERROR: Failed to insert game row")
        return
    print(f"Inserted game {game_id} (game #{game_number})")

    player_to_team = {player1: team1_id, player2: team2_id}

    stats_rows = [
        {
            "game_id": game_id,
            "team_id": player_to_team[player],
            "pokemon_id": p["pokemon_id"],
            "kills": p["kills"],
            "deaths": p["deaths"],
        }
        for player, pokemon_list in replay_data["teams"].items()
        for p in pokemon_list
        if p["appeared"] and p["pokemon_id"] != "N/A"
    ]
    if stats_rows:
        db.insert_game_pokemon_stats(stats_rows)
        print(f"Inserted {len(stats_rows)} game_pokemon_stats rows")

    match_poke_rows = [
        {
            "match_id": match_id,
            "team_id": player_to_team[player],
            "pokemon_id": p["pokemon_id"],
        }
        for player, pokemon_list in replay_data["teams"].items()
        for p in pokemon_list
        if p["appeared"] and p["pokemon_id"] != "N/A"
    ]
    if match_poke_rows:
        db.upsert_match_pokemon(match_poke_rows)
        print(f"Upserted {len(match_poke_rows)} match_pokemon rows")

    a_score, b_score = db.update_match_scores(match_id, team_a_id, team_b_id)
    print(f"Match scores updated: team_a={a_score}, team_b={b_score}")


def process_replay(gamelink: str):
    """Load IDs, analyze replay, and upload to DB. Returns 0 on success, 1 on failure."""
    try:
        pokemon_ids = load_pokemon_ids()
        replay_data = analyze_replay(gamelink, pokemon_ids)
        if replay_data is None:
            return 1
        upload_replay(replay_data)
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    pokemon_ids = load_pokemon_ids()
    replay_data = analyze_replay(
        "https://replay.pokemonshowdown.com/gen9vgc2024regf-2062315380",
        pokemon_ids,
    )
    if replay_data:
        upload_replay(replay_data)
