import discord
import gspread
from discord.ext import commands

import misc_programs.players as players
import misc_programs.replay_analyzer as replay_analyzer
import utils

import re
from urllib.request import Request, urlopen
import matplotlib.pyplot as plt


def get_team(name: str):
    values = utils.get_values_from_sheet(
        players.get_attribute_by_value("alias", "league", name), "Teams"
    )

    start_loc = (1, 1)
    row_jump = utils.NUM_POKEMON + 4
    col_jump = 4
    row_size = 6
    distance_from_name_to_pokemon = 2

    for i in range(utils.NUM_TEAMS):
        row = start_loc[0] + row_jump * (i // row_size)
        col = start_loc[1] + col_jump * (i % row_size)
        if name.casefold() in values[row][col].casefold():
            return [
                f"{values.T[col][row + distance_from_name_to_pokemon + i]}"
                for i in range(0, utils.NUM_POKEMON)
            ]
    raise ValueError(f"Player {name} not found.")


class NominationModal(
    discord.ui.Modal,
    title=f"Nomindation",
):
    def __init__(self, bot, **kw):
        super().__init__(**kw)
        self.bot = bot

    # drop = discord.ui.TextInput(
    #     label="Which Pokemon are you dropping?",
    #     max_length=100,
    #     placeholder="Pokemon name here...",
    # )

    category = discord.ui.Select(
        options=[discord.SelectOption(label=c) for c in ["1", "2", "3"]]
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(utils.SBL_TRANSACTIONS)
        await interaction.response.defer()
        await interaction.message.delete()
        name = players.get_attribute_by_value("id", "name", self.player.id)
        # await channel.send(
        #     f"<@&{utils.COMMISSIONER_ID}> {name} is dropping {self.drop.value.title()} for {self.add.value.title()}."
        # )
        # await channel.send(
        #     view=ApproveFreeAgencyView(
        #         name,
        #         self.add.value.title(),
        #         self.drop.value.title(),
        #         utils.get_current_week() + 1,
        #     )
        # )


class NominateView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_buttons()

    def add_buttons(self):
        nominate_button = discord.ui.Button(
            label="Nominate", style=discord.ButtonStyle.blurple
        )

        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(NominationModal(self.bot))

        nominate_button.callback = callback
        self.add_item(nominate_button)


class SeasonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Current schedule for given player.",
        help="Displays the current season schedule for the given player, according to the official SBL document.",
    )
    async def schedule(self, ctx, *, name: str = None):
        async with ctx.typing():
            gc = gspread.service_account(filename="resources\\service_account.json")

            if name is None:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )
                print(name)
            name = players.get_attribute_by_value("alias", "name", name)
            name_of_team = players.get_attribute_by_value("name", "team", name)
            ws = gc.open_by_key(
                utils.SBL_SEASON_DOC_KEY[
                    players.get_attribute_by_value("name", "league", name)
                ]
            ).worksheet("Schedule Table")

            start_loc = ("B", 28)

            team_range = f"{start_loc[0]}{start_loc[1]}:{start_loc[0]}{start_loc[1] + utils.NUM_TEAMS - 1}"
            teams = ws.batch_get([team_range])[0]
            # print(teams)
            print(teams)
            try:
                offset = next(
                    i
                    for i, team_name in enumerate(teams)
                    if name.casefold() in team_name[0].casefold()
                    or name_of_team
                    and name_of_team.casefold() in team_name[0].casefold()
                )
            except StopIteration:
                await ctx.send(f"Player {name} not found.")
                return
            loc_row_to_int = ord(start_loc[0]) - 64
            schedule_string = "\n".join(
                [
                    "Week {}: {}".format(i + 1, team_name)
                    for i, team_name in enumerate(
                        ws.row_values(start_loc[1] + offset)[
                            loc_row_to_int : utils.NUM_WEEKS + loc_row_to_int
                        ]
                    )
                ]
            )
            await ctx.send(
                embed=discord.Embed(
                    title=f"{name_of_team if name_of_team else name}'s Season {utils.SEASON_NUMBER} Schedule",
                    description=schedule_string,
                )
            )

    @commands.command(
        brief="Current team for given player.",
        help="Displays the current team for the given player, according to the official SBL document.",
    )
    async def team(self, ctx, *, name: str = None):
        async with ctx.typing():
            if name is None:
                name = players.get_attribute_by_value(
                    "id", "name", ctx.message.author.id
                )
            name = players.get_attribute_by_value("alias", "name", name)
            team_strings = get_team(name)
            name_of_team = players.get_attribute_by_value("name", "team", name)
            if team_strings is None:
                await ctx.send(f"Player {name} not found.")
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title=f"{name_of_team if name_of_team else name.capitalize()}'s Team",
                        description="\n".join(team_strings),
                    )
                )

    @commands.command(
        brief="Current SBL season week.", help="Displays the current SBL season week."
    )
    async def week(self, ctx):
        cur_week = utils.get_current_week()

        if cur_week < 1:
            await ctx.send("Season {} has not started yet.".format(utils.SEASON_NUMBER))
        elif cur_week <= utils.NUM_WEEKS:
            await ctx.send(
                "It is Week {} of Season {}.".format(cur_week, utils.SEASON_NUMBER)
            )
        else:
            await ctx.send("Season {} is over.".format(utils.SEASON_NUMBER))

    @commands.command(
        brief="Matches remaining for the week.",
        help="Displays the remaining matches for the current SBL season week. This data is fetched from the official SBL document, "
        "so matches are concluded when their scores are reported on the Schedule and Results page.",
    )
    async def matchesleft(self, ctx):
        async with ctx.typing():
            current_week, match_strings = utils.get_matchesleft()
            print(current_week, match_strings)
            title = ""
            if current_week > utils.NUM_WEEKS:
                title = f"Remaining Matches for Post-Season Week {current_week - utils.NUM_WEEKS - utils.POST_SEASON_BREAK}"
            else:
                title = f"Remaining Matches for Week {current_week}"
            await ctx.send(
                embed=discord.Embed(title=title, description="\n".join(match_strings))
            )

    @commands.command(hidden=True)
    async def data(self, ctx, *, name):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            async with ctx.typing():
                await ctx.send(
                    embed=discord.Embed(
                        title=f"{name} Data", description=replay_analyzer.get_data(name)
                    )
                )

    @commands.command(hidden=True)
    async def tsdata(self, ctx, *, name):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            async with ctx.typing():
                text = replay_analyzer.get_ots_data(name)
                # print(text.split("Name: "))

                embed = discord.Embed(title=f"{name} Data")
                print(text)
                # print(text.split("Name: ")[1:])
                for item in text.split("Name: ")[1:]:
                    field_name = item.split("\n")[0]
                    field_value = item[len(item.split("\n")[0]) :]
                    # print(field_name)
                    embed.add_field(name=field_name, value=field_value, inline=False)
                    # embed.add_field(name="test", value="test")
                #
                await ctx.send(embed=embed)

    @commands.command()
    async def teras(self, ctx):

        # EXTRA TERAS: Fairy+1, Water+1

        tera_dict = {}

        with open("resources/teras.txt", "r") as file:
            # Read the first line to get the week number (not used in the dictionary)
            stop_index = int(file.readline())

            # Read subsequent lines and populate the dictionary
            for line in file:
                key, value = line.strip().split(";")
                tera_dict[key] = int(value)

        # print(tera_dict)

        # stop_index = len(utils.remove_empty_strings_from_ends(utils.get_values_from_sheet("Main", "Match Logging")[:,2]))

        values = utils.get_values_from_sheet("Main", "Match Logging")[:, 4][
            stop_index + 1 :
        ]
        # print(values)

        link_list = [
            line.strip() for line in values if line.strip().startswith("https")
        ]
        # print(link_list)
        links = [str(x.strip()) + ".log" for x in link_list]

        for link in links:
            # print(link)
            req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
            data = urlopen(req).read().decode("utf-8")
            # print(data)
            for tera in re.findall(r"\|-terastallize\|.*\|(.*)", data):
                tera_dict[tera] = tera_dict.get(tera, 0) + 1
        #
        # print(tera_dict)
        sorted_data = {
            k: v
            for k, v in sorted(
                tera_dict.items(), key=lambda item: item[1], reverse=True
            )
        }
        # print(sorted_data)
        # Extract the sorted labels and values
        labels = list(sorted_data.keys())
        values = list(sorted_data.values())
        # print(values)
        # print(
        #     utils.remove_empty_strings_from_ends(
        #         utils.get_values_from_sheet("Main", "Match Logging")[:, 2]
        #     )
        # )
        stop_index = len(
            utils.remove_empty_strings_from_ends(
                utils.get_values_from_sheet("Main", "Match Logging")[:, 2]
            )
        )
        print(stop_index)

        with open("resources/teras.txt", "w") as file:
            # Write the week number as the first line
            file.write(str(stop_index) + "\n")

            # Write the key-value pairs from the dictionary
            for key, value in sorted_data.items():
                file.write(f"{key};{value}\n")

        # Set up the figure and axis
        color_dict = {
            "normal": "#A8A77A",
            "fire": "#EE8130",
            "water": "#6390F0",
            "electric": "#F7D02C",
            "grass": "#7AC74C",
            "ice": "#96D9D6",
            "fighting": "#C22E28",
            "poison": "#A33EA1",
            "ground": "#E2BF65",
            "flying": "#A98FF3",
            "psychic": "#F95587",
            "bug": "#A6B91A",
            "rock": "#B6A136",
            "ghost": "#735797",
            "dragon": "#6F35FC",
            "dark": "#705746",
            "steel": "#B7B7CE",
            "fairy": "#D685AD",
            "stellar": "#d9d1d0",
        }
        # Convert hex values to RGBA values
        # type_colors_rgba = {k: mcolors.to_rgb(v) for k, v in color_dict.items()}
        # Set up the figure and axis
        fig, ax = plt.subplots()

        # print(type_colors_rgba)

        # Create the bar graph with colored bars
        # print(labels, values)
        bars = ax.bar(
            labels, values, color=[color_dict[label.lower()] for label in labels]
        )

        # Rotate x-axis labels for better visibility
        plt.xticks(rotation=90)

        # Set the axis labels and title
        ax.set_xlabel("Types")
        ax.set_ylabel("Count")
        ax.set_title(f"SBL Season {utils.SEASON_NUMBER} Tera Types (as of now)")

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                str(height),
                ha="center",
                va="bottom",
            )

        # Display the graph
        plt.tight_layout()
        plt.savefig("tera.png")
        await ctx.send(file=discord.File("tera.png"))

    @commands.command(aliases=["nom"])
    async def nominate(self, ctx):
        await ctx.send(view=NominateView(self.bot))


async def setup(bot):
    await bot.add_cog(SeasonCog(bot))
