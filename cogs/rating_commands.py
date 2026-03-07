import discord
import utils
import os
import matplotlib.pyplot as plt
from discord.ext import commands
import pandas as pd
from collections import defaultdict
import math
import misc_programs.players as players
import glicko2

# --- EloManager ---
class EloManager:
    def __init__(self, initial_rating=1500, k=32):
        self.initial_rating = initial_rating
        self.k = k
        self.ratings = defaultdict(lambda: initial_rating)
        self.history = defaultdict(list)
        self.leaderboard = []
        self.load_ratings()

    def load_ratings(self):
        df = utils.get_record_sheet()
        for _, row in df.iterrows():
            p1, p2, winner = row["Player 1"].lower(), row["Player 2"].lower(), row["Winner"]
            if winner == '1':
                w, l = p1, p2
            elif winner == '2':
                w, l = p2, p1
            else:
                continue
            r_w, r_l = self.ratings[w], self.ratings[l]
            new_r_w = r_w + self.k * (1 - self.expected_score(r_w, r_l))
            new_r_l = r_l + self.k * (0 - self.expected_score(r_l, r_w))
            self.ratings[w], self.ratings[l] = new_r_w, new_r_l
            self.history[w].append(round(new_r_w))
            self.history[l].append(round(new_r_l))
        self.leaderboard = sorted(
            [{"Player": p, "Rating": round(r)} for p, r in self.ratings.items()],
            key=lambda x: -x["Rating"]
        )

    def expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def get_rating_string(self, name):
        key = name.lower()
        rating = self.ratings.get(key)
        if rating is None:
            return f"Player `{name}` not found in league data."
        return f"**{name}** Elo: **{round(rating)}**"

    def get_leaderboard(self):
        sorted_ratings = sorted(self.ratings.items(), key=lambda item: -item[1])
        lines = [
            f"**{name}**: {int(rating)}"
            for (name, rating) in sorted_ratings
            if players.get_attribute_by_value("alias", "active", name) == True
        ]
        return "\n".join(lines)

    def get_peak_elo_leaderboard(self):
        # Returns a list of dicts: [{"Player": name, "PeakElo": peak_elo}]
        peaks = []
        for name, history in self.history.items():
            if history:
                peaks.append({"Player": name, "PeakElo": max(history)})
        return sorted(peaks, key=lambda x: -x["PeakElo"])

    def plot_elo_history(self, name):
        key = name.lower()
        if key not in self.history or not self.history[key]:
            return None
        y = self.history[key]
        x = list(range(len(y)))
        df = utils.get_record_sheet()
        seasons = []
        for _, row in df.iterrows():
            p1, p2 = row["Player 1"].lower(), row["Player 2"].lower()
            if key == p1 or key == p2:
                seasons.append(str(row["Season"]))
        season_to_index = {}
        for idx, season in enumerate(seasons):
            if season not in season_to_index:
                season_to_index[season] = idx
        unique_seasons = sorted(season_to_index.items(), key=lambda x: x[1])
        tick_indices = [idx for season, idx in unique_seasons]
        tick_labels = [season for season, idx in unique_seasons]
        plt.figure(figsize=(8, 4))
        plt.plot(x, y, marker='o', label='Elo')
        peak_elo = max(y)
        plt.axhline(peak_elo, color='red', linestyle='--', label=f'Peak: {peak_elo}')
        plt.title(f"Elo Rating Over Time: {name}")
        plt.xlabel("Season")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(ticks=tick_indices, labels=tick_labels, rotation=45)
        plt.legend()
        filename = f"{key}_elo_history.png"
        plt.savefig(filename)
        plt.close()
        return filename

# --- GlickoManager ---
class GlickoManager:
    def __init__(self):
        self.players = {}
        self.leaderboard = []
        self.history = defaultdict(list)
        self.load_ratings()

    def ensure_player(self, name):
        key = name.lower()
        if key not in self.players:
            self.players[key] = glicko2.Player()
        return self.players[key]

    def load_ratings(self):
        df = utils.get_record_sheet()
        for _, row in df.iterrows():
            p1, p2, winner = row["Player 1"].lower(), row["Player 2"].lower(), row["Winner Name"].lower()
            pl1 = self.ensure_player(p1)
            pl2 = self.ensure_player(p2)
            if winner == p1:
                pl1.update_player([pl2.rating], [pl2.rd], [1])
                pl2.update_player([pl1.rating], [pl1.rd], [0])
            elif winner == p2:
                pl2.update_player([pl1.rating], [pl1.rd], [1])
                pl1.update_player([pl2.rating], [pl2.rd], [0])
            self.history[p1].append(int(pl1.rating))
            self.history[p2].append(int(pl2.rating))
        self.leaderboard = sorted(
            [{"Player": name, "Rating": int(player.rating)} for name, player in self.players.items()],
            key=lambda x: -x["Rating"]
        )

    def get_rating_string(self, name):
        key = name.lower()
        player = self.players.get(key)
        if player is None:
            return f"Player `{name}` not found in league data."
        return f"**{name}** Glicko-2: **{int(player.rating)} ± {int(2 * player.rd)}**"

    def get_leaderboard(self):
        sorted_ratings = sorted(self.players.items(), key=lambda item: -item[1].rating)
        lines = [
            f"**{name}**: {int(player.rating)} ± {int(2 * player.rd)}"
            for (name, player) in sorted_ratings
            if players.get_attribute_by_value("alias", "active", name) == True
        ]
        return "\n".join(lines)

    def get_peak_glicko_leaderboard(self):
        # Returns a list of dicts: [{"Player": name, "PeakGlicko": peak_glicko}]
        peaks = []
        for name, history in self.history.items():
            if history:
                peaks.append({"Player": name, "PeakGlicko": max(history)})
        return sorted(peaks, key=lambda x: -x["PeakGlicko"])

    def plot_glicko_history(self, name):
        key = name.lower()
        if key not in self.history or not self.history[key]:
            return None
        y = self.history[key]
        x = list(range(len(y)))
        df = utils.get_record_sheet()
        seasons = []
        for _, row in df.iterrows():
            p1, p2 = row["Player 1"].lower(), row["Player 2"].lower()
            if key == p1 or key == p2:
                seasons.append(str(row["Season"]))
        season_to_index = {}
        for idx, season in enumerate(seasons):
            if season not in season_to_index:
                season_to_index[season] = idx
        unique_seasons = sorted(season_to_index.items(), key=lambda x: x[1])
        tick_indices = [idx for season, idx in unique_seasons]
        tick_labels = [season for season, idx in unique_seasons]
        plt.figure(figsize=(8, 4))
        plt.plot(x, y, marker='o', label='Glicko-2')
        peak_elo = max(y)
        plt.axhline(peak_elo, color='red', linestyle='--', label=f'Peak: {peak_elo}')
        plt.title(f"Glicko-2 Rating Over Time: {name}")
        plt.xlabel("Season")
        plt.ylabel("Glicko-2 Rating")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(ticks=tick_indices, labels=tick_labels, rotation=45)
        plt.legend()
        filename = f"{key}_glicko2_history.png"
        plt.savefig(filename)
        plt.close()
        return filename

class RatingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.elo = EloManager()
        self.glicko = GlickoManager()

    def plot_combined_history(self, name):
        key = name.lower()
        # Get Elo and Glicko-2 histories
        elo_y = self.elo.history.get(key, [])
        glicko_y = self.glicko.history.get(key, [])
        if not elo_y and not glicko_y:
            return None
        # Use the longer of the two for x
        max_len = max(len(elo_y), len(glicko_y))
        x = list(range(max_len))
        # Collect seasons for each match involving the player
        df = utils.get_record_sheet()
        seasons = []
        for _, row in df.iterrows():
            p1, p2 = row["Player 1"].lower(), row["Player 2"].lower()
            if key == p1 or key == p2:
                seasons.append(str(row["Season"]))
        season_to_index = {}
        for idx, season in enumerate(seasons):
            if season not in season_to_index:
                season_to_index[season] = idx
        unique_seasons = sorted(season_to_index.items(), key=lambda x: x[1])
        tick_indices = [idx for season, idx in unique_seasons]
        tick_labels = [season for season, idx in unique_seasons]
        plt.figure(figsize=(10, 5))
        if elo_y:
            plt.plot(range(len(elo_y)), elo_y, marker='o', label='Elo')
            plt.axhline(max(elo_y), color='blue', linestyle='--', alpha=0.3, label=f'Elo Peak: {max(elo_y)}')
        if glicko_y:
            plt.plot(range(len(glicko_y)), glicko_y, marker='o', label='Glicko-2')
            plt.axhline(max(glicko_y), color='orange', linestyle='--', alpha=0.3, label=f'Glicko-2 Peak: {max(glicko_y)}')
        plt.title(f"Elo & Glicko-2 Rating Over Time: {name}")
        plt.xlabel("Season")
        plt.ylabel("Rating")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(ticks=tick_indices, labels=tick_labels, rotation=45)
        plt.legend()
        filename = f"{key}_combined_rating_history.png"
        plt.savefig(filename)
        plt.close()
        return filename

    @commands.command()
    async def rating(self, ctx, *, name: str = None):
        if name is None:
            name = ctx.author.display_name  # fallback to Discord nickname
        glicko_msg = self.glicko.get_rating_string(name)
        elo_msg = self.elo.get_rating_string(name)
        combined_graph = self.plot_combined_history(name)
        msg = f"{glicko_msg}\n{elo_msg}"
        files = []
        if combined_graph:
            files.append(discord.File(combined_graph))
        if files:
            await ctx.send(msg, files=files)
            for f in files:
                try:
                    os.remove(f.filename)
                except Exception:
                    pass
        else:
            await ctx.send(f"{msg}\n(No match history graph for `{name}`.)")

    @commands.command()
    async def ratings(self, ctx):
        glicko_board = self.glicko.get_leaderboard()
        elo_board = self.elo.get_leaderboard()
        embed = discord.Embed(
            title="🏆 Glicko-2 & Elo Leaderboards",
            description=f"**Glicko-2**\n{glicko_board}\n\n**Elo**\n{elo_board}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def peak_ratings(self, ctx):
        """
        Show leaderboards for peak Elo and peak Glicko-2 ratings.
        """
        # Elo peak leaderboard
        elo_peaks = self.elo.get_peak_elo_leaderboard()
        elo_lines = [f"**{entry['Player']}**: {entry['PeakElo']}" for entry in elo_peaks]
        elo_text = "\n".join(elo_lines)
        # Glicko-2 peak leaderboard
        glicko_peaks = self.glicko.get_peak_glicko_leaderboard()
        glicko_lines = [f"**{entry['Player']}**: {entry['PeakGlicko']}" for entry in glicko_peaks]
        glicko_text = "\n".join(glicko_lines)
        embed = discord.Embed(
            title="🏆 Peak Elo & Glicko-2 Leaderboards",
            description=f"**Peak Elo**\n{elo_text}\n\n**Peak Glicko-2**\n{glicko_text}",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RatingCog(bot))
