import discord
import gspread
import pandas as pd
from bing_image_urls import bing_image_urls
from discord.ext import commands
from collections import Counter

import sblglicko
import players
import utils


class SBLCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["name"],
        brief="Player Showdown username",
        help="Displays the Pokemon Showdown username of a player.",
    )
    async def username(self, ctx, *, name):
        async with ctx.typing():
            await ctx.send(players.get_attribute_by_value("alias", "username", name)[0])

    @commands.command(
        brief="The history of a Pokemon in SBL.",
        help="Displays the drafting and transaction history of a Pokemon throughout all season of SBL. "
        "Some transactions made during the initial season 24 hour period are not documented. Data is from the Trade History document.",
    )
    async def history(self, ctx, *, name):
        async with ctx.typing():
            gc = gspread.service_account(filename="resources\\service_account.json")

            df = pd.DataFrame(gc.open("Trade History").sheet1.get_all_values())
            df.columns = df.iloc[0]
            df = df[1:]
            # print(df)

            dfa = df[(df["Add"].apply(lambda v: v.lower() == name.lower()))]
            dfd = df[(df["Drop"].apply(lambda v: v.lower() == name.lower()))]
            history_string = ""
            df = pd.concat([dfa, dfd], axis=0)
            df = df.sort_values(by=["Drop"], key=lambda x: x.str.len())
            df = df.sort_values(by=["Week"])
            df = df.sort_values(by=["Week"], key=lambda x: x.str.len())
            df = df.sort_values(by=["Season"])
            if df.empty:
                await ctx.send("No data.")
            else:
                for i, line in df.iterrows():
                    history_string += f"In Season {line['Season']}"
                    if line["League"] != "N/A":
                        history_string += f" ({line['League']})"
                    if line["Type"] == "Draft":
                        history_string += f", {line['Player']} drafted {line['Add']}.\n"
                    else:
                        if line["Week"] == "Post-Season":
                            history_string += f" Post Season, "
                        else:
                            history_string += f" Week {line['Week']}, "

                        if line["Type"] == "Free Agency":
                            history_string += f"{line['Player']} dropped {line['Drop']} for {line['Add']}.\n"
                        else:
                            history_string += f"{line['Player']} and {line['Player With']} traded {line['Drop']} for {line['Add']}.\n"

                pokemon_df = pd.read_csv("resources\\pokemon.csv")
                row = pokemon_df[
                    pokemon_df["Name"].apply(lambda v: v.lower() == name.lower())
                ]
                embed = None
                if row.empty:
                    embed = discord.Embed(
                        title=name.capitalize(), description=history_string
                    )
                if not row.empty:
                    number = utils.get_pokedex_number(row["Number"].item())
                    type1 = row["Type 1"].item().capitalize()
                    embed = discord.Embed(
                        title=name.capitalize(),
                        description=history_string,
                        color=utils.color_dict[type1.lower()],
                    )
                    embed.title = row["Name"].item()

                    embed.set_thumbnail(url=utils.get_image_from_number(number))

                await ctx.send(embed=embed)

    @commands.command()
    async def winstreak(self, ctx, *, name: str = None):
        df = utils.get_record_sheet()

        if name is None:
            try:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )
            except ValueError:
                await ctx.send(f"Could not find player {ctx.message.author.name}!")
                return

        name = players.get_attribute_by_value("alias", "name", name)

        df = df[
            df["Player 1"].apply(utils.equals_ic(name))
            | df["Player 2"].apply(utils.equals_ic(name))
        ]
        count = 0
        for i, line in df[::-1].iterrows():
            # print(row['Winner Name'], name)
            if line["Winner Name"].lower() != name.lower():
                await ctx.send(
                    f'{name.capitalize()} has a winning streak of {count} matches, their last loss being Season {line["Season"]} {utils.format_week(line["Week"])} against {line["Winner Name"]}.'
                )
                break
            count += 1

        # Max Winstreak:

        max_count = -1
        max_start = None
        max_finish = None
        count = 0
        start = None
        finish = None

        for i, line in df[::-1].iterrows():
            if line["Winner Name"].lower() != name.lower():
                # finish = int(i)
                if count > max_count:
                    max_count = count
                    max_start = start
                    max_finish = finish
                count = 0
                finish = line
            else:
                start = line
                count += 1

        # print(max_start)
        if max_start is None:
            await ctx.send(
                f"Could not find data on player {name}, (or this player does not have a win streak)."
            )
        else:
            first_loser = max_start[f"Player {3 - int(max_start['Winner'])}"]
            if max_finish is None:
                await ctx.send("This is their longest winstreak.")

            else:
                await ctx.send(
                    f'{name.capitalize()} has a longest winning streak of {max_count} matches, starting in Season {max_start["Season"]} '
                    f'{utils.format_week(max_start["Week"])} against {first_loser} and ending with their loss in Season {max_finish["Season"]} '
                    f'{utils.format_week(max_finish["Week"])} against {max_finish["Winner Name"]}.'
                )

    @commands.command()
    async def playcount(self, ctx, *, name: str = None):
        df = utils.get_record_sheet()

        if name is None:
            try:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )
            except ValueError:
                await ctx.send(f"Could not find player {ctx.message.author.name}!")
                return

        name = players.get_attribute_by_value("alias", "name", name)

        print(name)

        df1 = df[df["Player 1"].apply(utils.equals_ic(name))]

        df2 = df[df["Player 2"].apply(utils.equals_ic(name))]
        count = Counter()
        for i, line in df1[::-1].iterrows():
            # print(line["Player 2"])
            count[line["Player 2"]] += 1

        for i, line in df2[::-1].iterrows():
            # print(line["Player 1"])
            count[line["Player 1"]] += 1

        history_string = ""
        for p, c in count.most_common():
            # print(p, c)
            history_string += f"{p} {c} {'times' if c > 1 else 'time'}\n"

        embed = discord.Embed(
            title=f"{name.capitalize()} has played...", description=history_string
        )
        # embed.add_field(name="History", value=history_string)
        await ctx.send(embed=embed)

    @commands.command(
        brief="Match/game record between players.",
        help="Displays the match and game record (count and percentages) between two SBL players. Uses match data from Shrug's Records Document.",
    )
    async def matchup(self, ctx, *, search):
        async with ctx.typing():
            p1, p2 = search.split(" ")
            p1 = players.get_attribute_by_value("alias", "name", p1)
            p2 = players.get_attribute_by_value("alias", "name", p2)
            df = utils.get_record_sheet()
            df = df[
                df["Player 1"].apply(
                    lambda v: v.casefold() in [p1.casefold(), p2.casefold()]
                )
                & df["Player 2"].apply(
                    lambda v: v.casefold() in [p1.casefold(), p2.casefold()]
                )
            ]
            if df.empty:
                await ctx.send("Could not find any matches.")
                return

            p1_matches = df[df["Winner Name"].apply(utils.equals_ic(p1))].shape[0]
            p2_matches = df[df["Winner Name"].apply(utils.equals_ic(p2))].shape[0]
            p1_games = (df[df["Player 1"].apply(utils.equals_ic(p1))])[
                "Player 1 Game Count"
            ].astype(int).sum() + (df[df["Player 2"].apply(utils.equals_ic(p1))])[
                "Player 2 Game Count"
            ].astype(
                int
            ).sum()
            p2_games = (df[df["Player 2"].apply(utils.equals_ic(p2))])[
                "Player 2 Game Count"
            ].astype(int).sum() + (df[df["Player 1"].apply(utils.equals_ic(p2))])[
                "Player 1 Game Count"
            ].astype(
                int
            ).sum()

            num_matches = df.shape[0]
            num_games = p1_games + p2_games

            embed = discord.Embed(title=f"{p1.capitalize()} vs. {p2.capitalize()}")
            embed.add_field(
                name="Matches", value=f"{p1_matches} vs. {p2_matches}", inline=False
            )
            embed.add_field(
                name="Games", value=f"{p1_games} vs. {p2_games}", inline=False
            )
            embed.add_field(
                name="Match %",
                value=f'{"%.1f" % (p1_matches / num_matches * 100)} vs. {"%.1f" % (p2_matches / num_matches * 100)}',
                inline=False,
            )
            embed.add_field(
                name="Game %",
                value=f'{"%.1f" % (p1_games / num_games * 100)} vs. {"%.1f" % (p2_games / num_games * 100)}',
                inline=False,
            )

            history_string = ""
            for i, line in df.iterrows():
                winner_num = line["Winner"]
                history_string += (
                    f'In Season {line["Season"]} {utils.format_week(line["Week"])},'
                    f' {line["Winner Name"].capitalize()} won {line[f"Player {winner_num} Game Count"]}-{line[f"Player {3 - int(winner_num)} Game Count"]}.\n'
                )

            embed.add_field(name="History", value=history_string)
            await ctx.send(embed=embed)

    @commands.command(
        brief="Match/game record for player.",
        help="Displays the match and game record (count and percentages) for an SBL player. By default, all seasons are included, but season number can be specified with a second parameter.",
    )
    async def record(self, ctx, name: str = None, season: float = 0):
        async with ctx.typing():
            df = utils.get_record_sheet()

            if name is None:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )

            name = players.get_attribute_by_value("alias", "name", name)

            df = df[
                df["Player 1"].apply(utils.equals_ic(name))
                | df["Player 2"].apply(utils.equals_ic(name))
            ]
            season = int(season) if season % 1 == 0 else season
            if season > 0:
                df = df[df["Season"] == str(season)]

            if df.empty:
                await ctx.send("Could not find any matches.")
                return
            matches = df.shape[0]
            games = df["Player 1 Game Count"].astype(int).sum() + (
                df["Player 2 Game Count"].astype(int).sum()
            )
            matches_won = df[df["Winner Name"].apply(utils.equals_ic(name))].shape[0]
            games_won = (
                df[df["Player 1"].apply(utils.equals_ic(name))]["Player 1 Game Count"]
                .astype(int)
                .sum()
                + df[df["Player 2"].apply(utils.equals_ic(name))]["Player 2 Game Count"]
                .astype(int)
                .sum()
            )

            embed = discord.Embed(title=name.capitalize(), description="All Seasons")
            if season > 0:
                embed.description = f"Season {season}"
            embed.add_field(
                name="Matches",
                value=f"{matches_won}-{matches - matches_won}",
                inline=False,
            )
            embed.add_field(
                name="Games", value=f"{games_won}-{games - games_won}", inline=False
            )
            embed.add_field(
                name="Match Win %",
                value="%.1f" % (matches_won / matches * 100),
                inline=False,
            )
            embed.add_field(
                name="Game Win %",
                value="%.1f" % (games_won / games * 100),
                inline=False,
            )
            await ctx.send(embed=embed)

    @commands.command(
        brief="Match/game record for player.",
        help="Displays the match and game record (count and percentages) for an SBL player. By default, all seasons are included, but season number can be specified with a second parameter.",
    )
    async def recordplayoffs(self, ctx, name: str = None, season: float = 0):
        async with ctx.typing():
            df = utils.get_record_sheet()

            if name is None:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )

            name = players.get_attribute_by_value("alias", "name", name)

            df = df[
                df["Player 1"].apply(utils.equals_ic(name))
                | df["Player 2"].apply(utils.equals_ic(name))
            ]

            df = df[(df["Week"] == str("Amateur")) | (df["Week"] == str("Playoffs"))]
            # print(df)
            season = int(season) if season % 1 == 0 else season
            if season > 0:
                df = df[df["Season"] == str(season)]

            if df.empty:
                await ctx.send("Could not find any matches.")
                return
            matches = df.shape[0]
            games = df["Player 1 Game Count"].astype(int).sum() + (
                df["Player 2 Game Count"].astype(int).sum()
            )
            matches_won = df[df["Winner Name"].apply(utils.equals_ic(name))].shape[0]
            games_won = (
                df[df["Player 1"].apply(utils.equals_ic(name))]["Player 1 Game Count"]
                .astype(int)
                .sum()
                + df[df["Player 2"].apply(utils.equals_ic(name))]["Player 2 Game Count"]
                .astype(int)
                .sum()
            )

            embed = discord.Embed(title=name.capitalize(), description="All Seasons")
            if season > 0:
                embed.description = f"Season {season}"
            embed.add_field(
                name="Matches",
                value=f"{matches_won}-{matches - matches_won}",
                inline=False,
            )
            embed.add_field(
                name="Games", value=f"{games_won}-{games - games_won}", inline=False
            )
            embed.add_field(
                name="Match Win %",
                value="%.1f" % (matches_won / matches * 100),
                inline=False,
            )
            embed.add_field(
                name="Game Win %",
                value="%.1f" % (games_won / games * 100),
                inline=False,
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def rating(self, ctx, name: str = None):
        if name is None:
            name = players.get_attribute_by_value("id", "name", ctx.message.author.id)

        await ctx.send(sblglicko.get_rating_string(name))

    @commands.command()
    async def ratings(self, ctx):

        await ctx.send(
            embed=discord.Embed(
                title="Leaderboard", description=sblglicko.get_leaderboard()
            )
        )
        # await ctx.send(sblglicko.get_rating_string(name))


async def setup(bot):
    await bot.add_cog(SBLCog(bot))
