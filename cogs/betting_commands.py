import re
from functools import cmp_to_key

import discord
import gspread
import numpy as np
from discord import Interaction
from discord.ext import commands
from datetime import datetime, timezone
import misc_programs.players as players
import utils


class Bet:
    def __init__(self, user_id, amount, winner, loser, multiplier):
        self.multiplier = multiplier
        self.loser = loser
        self.winner = winner
        self.amount = amount
        self.user_id = user_id

    def save(self):
        with open("resources/bets.txt", "a") as f:
            f.write(
                f"{self.winner},{self.loser},{self.amount},{self.user_id},{self.multiplier}\n"
            )

    def __str__(self):
        return (
            f"{self.winner},{self.loser},{self.amount},{self.user_id},{self.multiplier}"
        )


def bet_multiplier(seed1, seed2):
    if seed1 == seed2:
        return 1.75, 1.75
    else:
        if seed2 > seed1:
            difference = seed2 - seed1 + 1
            return 1 / difference + 1, difference
        else:
            difference = seed1 - seed2 + 1
            return difference, 1 / difference + 1


def get_coins(id):
    user_coins = 0
    with open("resources/coins.txt") as f:
        for line in f:
            if line.startswith(str(id)):
                user_coins = float(line.split(", ")[1])
    return user_coins


def change_coins(id, coins):
    with open("resources/coins.txt", "r") as file:
        # read a list of lines into data
        data = file.readlines()

    # now change the 2nd line, note that you have to add a newline
    data[0] = str(datetime.now().isocalendar()[1]) + "\n"
    index = next(i for i, line in enumerate(data) if line.startswith(str(id)))
    data[index] = f"{id}, {coins}\n"

    # and write everything back
    with open("resources/coins.txt", "w") as file:
        file.writelines(data)


def give_everyone_coins(coins):
    with open("resources/coins.txt", "r") as file:
        # read a list of lines into data
        data = file.readlines()

    # now change the 2nd line, note that you have to add a newline
    data[0] = str(datetime.now().isocalendar()[1]) + "\n"
    for i in range(1, len(data)):
        data[i] = (
            data[i].split(", ")[0]
            + ", "
            + str((float(data[i].split(", ")[1]) + coins))
            + "\n"
        )

    # and write everything back
    with open("resources/coins.txt", "w") as file:
        file.writelines(data)


def get_bets():
    with open("resources/bets.txt", "r") as file:
        bets = []
        for line in file:
            winner, loser, amount, user_id, multiplier = line.split(",")
            bets.append(Bet(user_id, int(amount), winner, loser, float(multiplier)))
        return bets


def get_bets_of_match(player1, player2):
    bets = get_bets()
    total_coins = 0
    count = 0
    for bet in bets:
        if (
            bet.winner == player1
            and bet.loser == player2
            or bet.winner == player2
            and bet.loser == player1
        ):
            count += 1
            total_coins += bet.amount
    return count, total_coins


def update_bets(bets):
    with open("resources/bets.txt", "w") as f:
        for bet in bets:
            f.write(
                f"{bet.winner},{bet.loser},{bet.amount},{bet.user_id},{bet.multiplier}\n"
            )


def update_previous_bets(bets):
    with open("resources/previous_bets.txt", "a") as f:
        for bet in bets:
            f.write(
                f"{bet.winner},{bet.loser},{bet.amount},{bet.user_id},{bet.multiplier}\n"
            )


class BetModal(discord.ui.Modal, title="Bet"):
    def __init__(self, user, winner, loser, multiplier):
        super().__init__()
        self.multiplier = multiplier
        self.winner = winner
        self.loser = loser
        self.user = user
        # name = players.get_attribute_by_value('team', 'name', winner)
        name = re.search(r"\(([^)]+)", winner).group(1) if "(" in winner else winner
        self.title = f"Bet on {name}"

        self.amount = discord.ui.TextInput(
            label=f"How much would you like to bet?", placeholder="Enter amount here..."
        )

        self.add_item(self.amount)

    async def on_submit(self, interaction: Interaction) -> None:
        num_coins = get_coins(self.user.id)
        try:
            bet_amount = int(self.amount.value)
            if bet_amount > num_coins:
                await interaction.response.send_message(
                    "You do not have enough coins to place this bet.", ephemeral=True
                )
            else:
                num_coins -= bet_amount
                current_bet = Bet(
                    self.user.id, bet_amount, self.winner, self.loser, self.multiplier
                )
                current_bet.save()
                change_coins(self.user.id, num_coins)
                await interaction.response.send_message(
                    f"Bet placed, you now have {int(num_coins)} coins.", ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "Invalid bet amount.", ephemeral=True
            )


class BetButtonView(discord.ui.View):
    def __init__(self, player1, player2, multiplier1, multiplier2, **kw):
        super().__init__(**kw)
        self.multiplier2 = multiplier2
        self.multiplier1 = multiplier1
        self.player2 = player2
        self.player1 = player1
        self.add_buttons()

    def add_buttons(self):
        player_one_button = discord.ui.Button(
            label=f"Bet on {self.player1}", style=discord.ButtonStyle.blurple
        )
        player_two_button = discord.ui.Button(
            label=f"Bet on {self.player2}", style=discord.ButtonStyle.blurple
        )

        async def player_one_button_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                BetModal(interaction.user, self.player1, self.player2, self.multiplier1)
            )

        async def player_two_button_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                BetModal(interaction.user, self.player2, self.player1, self.multiplier2)
            )

        player_one_button.callback = player_one_button_callback
        player_two_button.callback = player_two_button_callback

        self.add_item(player_one_button)
        self.add_item(player_two_button)


class BetView(discord.ui.View):
    def __init__(self):
        super().__init__()
        select = discord.ui.Select(
            options=[
                discord.SelectOption(label=match_string)
                for match_string in utils.get_matchesleft()[1]
            ]
        )

        async def callback(interaction):
            player1, player2 = select.values[0].split(" vs. ")
            name1 = (
                re.search(r"\(([^)]+)", player1).group(1) if "(" in player1 else player1
            )
            name2 = (
                re.search(r"\(([^)]+)", player2).group(1) if "(" in player2 else player2
            )
            mult1, mult2 = bet_multiplier(
                players.get_attribute_by_value("alias", "seed", name1),
                players.get_attribute_by_value("alias", "seed", name2),
            )
            # mult1 = mult1 if mult1 % 1 == 0
            str_mult1 = str(int(mult1)) if mult1 % 1 == 0 else str(("%.2f" % mult1))
            str_mult2 = str(int(mult2)) if mult2 % 1 == 0 else str(("%.2f" % mult2))

            process_bets(get_bets())
            check_weekly_coins()
            # await ctx.send(f"You have {int(get_coins(ctx.message.author.id))} coins.")

            await interaction.response.send_message(
                content=f"You have {int(get_coins(interaction.user.id))} coins.\nIf you bet on {name1} and they win, you get {str_mult1}x your bet.\nIf you bet on {name2} and they win, you get {str_mult2}x your bet.",
                view=BetButtonView(player1, player2, mult1, mult2),
                ephemeral=True,
            )

        select.callback = callback
        self.add_item(select)


class StakeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        select = discord.ui.Select(
            options=[
                discord.SelectOption(label=match_string)
                for match_string in utils.get_matchesleft()[1]
            ]
        )

        async def callback(interaction):
            player1, player2 = select.values[0].split(" vs. ")
            count, total_coins = get_bets_of_match(player1, player2)
            await interaction.response.send_message(
                f"There are {count} bets on {select.values[0]}, for a total of {total_coins} coins."
            )

        select.callback = callback
        self.add_item(select)


def process_bets(bets):
    gc = gspread.service_account(filename="resources/service_account.json")

    found_bet = {bet: False for bet in bets}

    processed_bets = set()
    for doc in utils.SBL_SEASON_DOC_KEY.values():
        # print(f'\nLooking at doc {doc}\n')
        ws = gc.open_by_key(doc).worksheet("Schedule and Results")
        values = np.array(ws.get_all_values())
        # print(values)
        num = utils.get_current_week()

        num = 10

        for week_num in [num, num - 1]:

            row, col = utils.get_row_col_from_number(week_num)
            matches_tuples = list(
                zip(
                    values.T[col + 1][row + 1 : row + utils.MATCHES_PER_WEEK + 1],
                    values.T[col + 5][row + 1 : row + utils.MATCHES_PER_WEEK + 1],
                )
            )
            # print(matches_tuples)

            # remaining_matches = [matches_tuples[i] for i, score in enumerate(values.T[col][row + 1:row + MATCHES_PER_WEEK + 1]) if not score]

            for current_bet in bets:
                if not found_bet[current_bet]:
                    for i, match in enumerate(matches_tuples):
                        # print(f'Looking for match for bet {current_bet}')
                        # print(match, current_bet.winner, current_bet.loser)
                        if (
                            match[0] == current_bet.winner
                            and match[1] == current_bet.loser
                            or match[1] == current_bet.winner
                            and match[0] == current_bet.loser
                        ):
                            # print(f'\nFound match for bet {current_bet}\n')
                            score_left = values.T[col][row + 1 + i]
                            score_right = values.T[col + 8][row + 1 + i]
                            if score_left:
                                if (
                                    score_left == "2"
                                    and current_bet.winner == match[0]
                                    or score_right == "2"
                                    and current_bet.winner == match[1]
                                ):
                                    change_coins(
                                        current_bet.user_id,
                                        get_coins(current_bet.user_id)
                                        + current_bet.amount * current_bet.multiplier,
                                    )
                                processed_bets.add(current_bet)
                                found_bet[current_bet] = True
                                # print(f'\nRemoved bet {current_bet}\n')
                                # bets.remove(current_bet)
                            else:
                                break
        # print(found_bet)
        update_bets([bet for bet, found in found_bet.items() if not found])
        update_previous_bets([bet for bet, found in found_bet.items() if found])


def check_weekly_coins():
    with open("resources/coins.txt", "r") as file:
        lines = file.readlines()
        if str(datetime.now().isocalendar()[1]) + "\n" != lines[0]:

            lines[0] = str(datetime.now().isocalendar()[1]) + "\n"
            for i in range(1, len(lines)):
                lines[i] = (
                    lines[i].split(", ")[0]
                    + ", "
                    + str((float(lines[i].split(", ")[1]) + utils.WEEKLY_COINS))
                    + "\n"
                )

            print("Updated weekly coins.")

            lines[0] = str(datetime.now().isocalendar()[1]) + "\n"

            with open("resources/coins.txt", "w") as f:
                f.writelines(lines)


class BettingCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def change_coins(self, ctx, id, amount):
        change_coins(id, amount)

    @commands.command(hidden=True)
    async def print_bets(self, ctx):
        with open("resources/bets.txt", "r") as f:
            await ctx.send(f.read())

    @commands.command()
    async def coins(self, ctx):
        process_bets(get_bets())
        check_weekly_coins()
        await ctx.send(f"You have {int(get_coins(ctx.message.author.id))} coins.")

    @commands.command()
    async def stakes(self, ctx):
        await ctx.send(
            content="Choose a match to see its stakes.", view=StakeSelectView()
        )

    @commands.command(hidden=True)
    async def give_everyone_coins(self, ctx):
        give_everyone_coins(250)

    @commands.command(aliases=["leaderboard", "coinsleaderboard"])
    async def coinleaderboard(self, ctx):
        process_bets(get_bets())
        check_weekly_coins()

        invested_coins = {}
        with open("resources/bets.txt") as file:
            for line in file.readlines():
                id = line.split(",")[3]
                amount = float(line.split(",")[2])
                if id in invested_coins.keys():
                    invested_coins[id] += amount
                else:
                    invested_coins[id] = amount
        print(invested_coins)

        with open("resources/coins.txt") as file:
            users = file.readlines()[1:]
            # users = sorted(
            #     users,
            #     key=cmp_to_key(
            #         lambda item1, item2:
            #         int(
            #             (float(item2.split(", ")[1]) + float(invested_coins.get(item2.split(", ")[0], 0))) - (float(item1.split(", ")[1]) + float(invested_coins.get(item1.split(", ")[0], 0))) - 1
            #         )
            #     ),
            # )
            leaderboard_strings = {}
            for user in users:
                discord_id, amount = user.split(", ")
                current = int(float(amount))
                invested = int(invested_coins.get(discord_id, 0))
                total = current + invested
                name = players.get_attribute_by_value("id", "name", int(discord_id))
                leaderboard_strings[
                    " {:<15} {:>12} {:>12} {:>12} ".format(
                        name, current, invested, total
                    )
                ] = total
                print(name, total)

            final_string = " {:<15} {:>12} {:>12} {:>12} \n\n".format(
                "Name:", "Current:", "Invested:", "Total:"
            ) + "\n".join(
                dict(
                    sorted(leaderboard_strings.items(), key=lambda item: -item[1])
                ).keys()
            )

            embed = discord.Embed(
                title="Leaderboard", description=f"```{final_string}```"
            )
            embed.set_footer(text=f"Last updated {utils.get_time_elapsed_str()}")
            await ctx.send(embed=embed)

    @commands.command()
    async def bet(self, ctx):
        async with ctx.typing():

            if utils.allow_bets:
                game_corner = self.bot.get_channel(utils.SBL_GAME_CORNER_ID)
                test_channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)
                # print(utils.get_matchesleft())
                if len(utils.get_matchesleft()[1]) == 0:
                    await ctx.send("There are no more matches this week!")
                elif ctx.message.channel in [game_corner, test_channel]:
                    await ctx.send(
                        content="Choose a match to place a bet on.", view=BetView()
                    )
                else:
                    await ctx.send(f"Please use {game_corner.mention} for ")
            else:
                await ctx.send("Bets are currently disabled.")


async def setup(bot):
    await bot.add_cog(BettingCog(bot))
