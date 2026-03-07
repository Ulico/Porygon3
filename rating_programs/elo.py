import utils
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt


# === CONFIGURATION ===
INITIAL_RATING = 1500
K_FACTOR = 32

# === ELO FUNCTIONS ===
def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(rating_winner, rating_loser, k=K_FACTOR):
    expected_win = expected_score(rating_winner, rating_loser)
    expected_lose = expected_score(rating_loser, rating_winner)

    new_winner_rating = rating_winner + k * (1 - expected_win)
    new_loser_rating = rating_loser + k * (0 - expected_lose)

    return new_winner_rating, new_loser_rating

# === MAIN FUNCTION: Calculates Elo ratings and returns leaderboard ===
def calculate_elo_ratings():
    df = utils.get_record_sheet()
    ratings = defaultdict(lambda: INITIAL_RATING)

    for _, row in df.iterrows():
        p1 = row["Player 1"]
        p2 = row["Player 2"]
        winner = row["Winner"]

        if winner == 1:
            winner_name, loser_name = p1, p2
        elif winner == 2:
            winner_name, loser_name = p2, p1
        else:
            continue

        r_win = ratings[winner_name]
        r_lose = ratings[loser_name]
        ratings[winner_name], ratings[loser_name] = update_elo(r_win, r_lose)

    for player, rating in ratings.items():
        print(f"{player}: {int(round(rating))}")

    leaderboard = pd.DataFrame(
        [
            {"Player": player, "Elo Rating": int(round(rating))}
            for player, rating in ratings.items()
        ]
    )
    leaderboard = leaderboard.sort_values(by="Elo Rating", ascending=False).reset_index(drop=True)

    # # Create a leaderboard DataFrame
    # leaderboard = pd.DataFrame(
    #     [
    #         {"Player": player, "Elo Rating": int(round(rating))}
    #         for player, rating in ratings.items()
    #     ]
    # )
    # leaderboard = leaderboard.sort_values(by="Elo Rating", ascending=False).reset_index(
    #     drop=True
    # )
    # print(leaderboard)
    return leaderboard

# === FUNCTION: Plots Elo progression for a given player ===
def plot_elo_progression(player_name):
    df = utils.get_record_sheet()
    ratings = defaultdict(lambda: INITIAL_RATING)
    player_elo_history = []

    for i, row in df.iterrows():
        p1 = row["Player 1"]
        p2 = row["Player 2"]
        winner = row["Winner"]

        if winner == 1:
            winner_name, loser_name = p1, p2
        elif winner == 2:
            winner_name, loser_name = p2, p1
        else:
            continue

        r_win = ratings[winner_name]
        r_lose = ratings[loser_name]
        new_r_win, new_r_lose = update_elo(r_win, r_lose)

        ratings[winner_name], ratings[loser_name] = new_r_win, new_r_lose

        # Track Elo for the selected player
        if player_name == p1 or player_name == p2:
            player_elo_history.append(ratings[player_name])

    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, len(player_elo_history) + 1), player_elo_history, marker="o")
    plt.title(f"Elo Rating Over Time: {player_name}")
    plt.xlabel("Match Number")
    plt.ylabel("Elo Rating")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

