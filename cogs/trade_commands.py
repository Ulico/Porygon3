import traceback
import utils
import re

import discord
import gspread
from discord import Interaction
from discord.ext import commands

import misc_programs.players as players


class Trade:
    def __init__(self, p1, p2, d, a):
        self.player1 = p1
        self.player2 = p2
        self.drop = d
        self.add = a


class ConfirmView(discord.ui.View):
    def __init__(self, current_trade, bot):
        super().__init__(timeout=None)
        self.trade = current_trade
        self.bot = bot
        self.add_buttons()

    def add_buttons(self):
        accept_button = discord.ui.Button(
            label="Accept", style=discord.ButtonStyle.green
        )
        deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red)

        async def accept_button_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Trade accepted.")
            channel = self.bot.get_channel(utils.SBL_TRANSACTIONS)
            accept_button.disabled = True
            deny_button.disabled = True
            await interaction.message.edit(view=self)
            await self.trade.player1.send(
                f"{self.trade.player2.name} has accepted your offer."
            )
            await channel.purge(
                limit=1, check=lambda x: x.author.id == self.bot.user.id
            )
            name1 = players.get_attribute_by_value("id", "name", self.trade.player1.id)
            name2 = players.get_attribute_by_value("id", "name", self.trade.player2.id)
            await channel.send(
                f"<@&{utils.COMMISSIONER_ID}> {name1} and {name2} are trading {self.trade.drop} for {self.trade.add}."
            )
            await channel.send(view=ApproveTradeView(self.trade))

        async def deny_button_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Trade denied.")
            accept_button.disabled = True
            deny_button.disabled = True
            await self.trade.player1.send(
                f"{self.trade.player2.name} has denied your offer."
            )
            await interaction.message.edit(view=self)

        accept_button.callback = accept_button_callback
        deny_button.callback = deny_button_callback

        self.add_item(accept_button)
        self.add_item(deny_button)


class FreeAgencyTransaction(
    discord.ui.Modal,
    title=f"Transaction (Effective Week {utils.get_current_week() + 1})",
):
    def __init__(self, player, bot, **kw):
        super().__init__(**kw)
        self.bot = bot
        self.player = player

    drop = discord.ui.TextInput(
        label="Which Pokemon are you dropping?",
        max_length=100,
        placeholder="Pokemon name here...",
    )

    add = discord.ui.TextInput(
        label="Which Pokemon are you adding?",
        max_length=100,
        placeholder="Pokemon name here...",
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(utils.SBL_TRANSACTIONS)
        await interaction.response.defer()
        await interaction.message.delete()
        name = players.get_attribute_by_value("id", "name", self.player.id)
        await channel.send(
            f"<@&{utils.COMMISSIONER_ID}> {name} is dropping {self.drop.value.title()} for {self.add.value.title()}."
        )
        await channel.send(
            view=ApproveFreeAgencyView(
                name,
                self.add.value.title(),
                self.drop.value.title(),
                utils.get_current_week() + 1,
            )
        )


class TradeTransaction(
    discord.ui.Modal,
    title=f"Transaction (Effective Week {utils.get_current_week() + 1})",
):
    def __init__(self, player, bot, **kw):
        super().__init__(**kw)
        self.player = player
        self.bot = bot

    drop = discord.ui.TextInput(
        label="Which Pokemon are you dropping?",
        max_length=100,
        placeholder="Pokemon name here...",
    )

    add = discord.ui.TextInput(
        label="Which Pokemon are you adding?",
        max_length=100,
        placeholder="Pokemon name here...",
    )

    player_with = discord.ui.TextInput(
        label="Who are you trading with?",
        max_length=100,
        placeholder="Player name here...",
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        players.get_player_data()
        if self.player_with.value.casefold() not in [
            player.name.casefold() for player in players.player_list
        ]:
            await self.player.send(
                f'Trade failed: could not find player "{self.player_with.value}".'
            )
        else:
            player2 = self.bot.get_user(
                players.get_attribute_by_value("alias", "id", self.player_with.value)
            )
            current_trade = Trade(
                self.player, player2, self.drop.value.title(), self.add.value.title()
            )
            await player2.send(
                f"{current_trade.player1.name} would like to trade {current_trade.drop} for {current_trade.add}.",
                view=ConfirmView(current_trade, self.bot),
            )


class TradeButtonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_buttons()

    def add_buttons(self):
        free_agency_button = discord.ui.Button(
            label="Free Agency", style=discord.ButtonStyle.blurple
        )
        player_trade_button = discord.ui.Button(
            label="Player Trade", style=discord.ButtonStyle.blurple
        )

        async def free_agency_button_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                FreeAgencyTransaction(interaction.user, self.bot)
            )

        async def player_trade_button_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                TradeTransaction(interaction.user, self.bot)
            )

        free_agency_button.callback = free_agency_button_callback
        player_trade_button.callback = player_trade_button_callback

        self.add_item(free_agency_button)
        self.add_item(player_trade_button)


def add_free_agency(name, add, drop, week):
    # return 0
    try:
        gc = gspread.service_account(filename="resources\\service_account.json")

        doc_id = utils.SBL_SEASON_DOC_KEY[
            players.get_attribute_by_value("alias", "league", name)
        ]
        # doc_id = '14IPwnyeKxohvc__aZz1HuspPHHaLmWSBzzIIX4wWi-U'
        ws = gc.open_by_key(doc_id).worksheet("Transactions")

        # names = ws.col_values(2)
        # print(len(names))

        next_open_row = len(ws.col_values(2)) + 1
        update_data = [
            {
                "range": f"B{next_open_row}:L{next_open_row}",
                "values": [[name, "", add, "", "", drop, "", "", week, "", "x"]],
            },
        ]
        ws.batch_update(update_data)
        ws = gc.open_by_key(doc_id).worksheet("Teams")
        # print(ws)
        cell = ws.find(drop)

        if cell is None:
            print(f"Could not find {drop} on Teams page.")
            return

        ws.update_cell(cell.row, cell.col, add)

        ws = gc.open_by_key(doc_id).worksheet(
            players.get_attribute_by_value("alias", "name", name)
        )
        next_open_row = ws.col_values(2).index("-") + 1
        # print(ws.col_values(2))
        print(next_open_row)

        update_data = [
            {
                "range": f"B{next_open_row}:F{next_open_row}",
                "values": [
                    [
                        drop,
                        f"=iferror(vlookup(B{next_open_row},Index!$B$2:$L$1200,11,0))",
                        f"=sumif(O:O,$B{next_open_row},P:P)+sumif(R:R,$B{next_open_row},S:S)+sumif(U:U,$B{next_open_row},V:V)",
                        f"=sumif(O:O,$B{next_open_row},Q:Q)+sumif(R:R,$B{next_open_row},T:T)+sumif(U:U,$B{next_open_row},W:W)",
                        f"=D{next_open_row}-E{next_open_row}",
                    ]
                ],
            },
        ]
        ws.batch_update(update_data, value_input_option="USER_ENTERED")

        return 0
    except Exception:
        print("Here is the printout:")
        traceback.print_exc()
    return 1


def add_trade(trade: Trade):
    try:
        gc = gspread.service_account(filename="resources\\service_account.json")

        doc_id = utils.SBL_SEASON_DOC_KEY[
            players.get_attribute_by_value("alias", "league", trade.player1.name)
        ]
        # doc_id = '14IPwnyeKxohvc__aZz1HuspPHHaLmWSBzzIIX4wWi-U'
        ws = gc.open_by_key(doc_id).worksheet("Transactions")

        # names = ws.col_values(2)
        # print(len(names))

        next_open_row = len(ws.col_values(15)) + 1
        update_data = [
            {
                "range": f"O{next_open_row}:Y{next_open_row}",
                "values": [
                    [
                        players.get_attribute_by_value(
                            "alias", "name", trade.player1.name
                        ),
                        "",
                        trade.add,
                        "",
                        players.get_attribute_by_value(
                            "alias", "name", trade.player2.name
                        ),
                        "",
                        trade.drop,
                        "",
                        str(utils.get_current_week() + 1),
                        "",
                        "x",
                    ]
                ],
            },
        ]
        ws.batch_update(update_data)
        ws = gc.open_by_key(doc_id).worksheet("Teams")
        cell = ws.find(trade.add)
        ws.update_cell(cell.row, cell.col, trade.drop)

        cell = ws.find(trade.drop)
        ws.update_cell(cell.row, cell.col, trade.add)

        ws = gc.open_by_key(doc_id).worksheet(
            players.get_attribute_by_value("alias", "name", trade.player1.name)
        )
        next_open_row = ws.col_values(2).index("-") + 1
        # print(ws.col_values(2))
        print(next_open_row)

        update_data = [
            {
                "range": f"B{next_open_row}:F{next_open_row}",
                "values": [
                    [
                        trade.drop,
                        f"=iferror(vlookup(B{next_open_row},Index!$B$2:$L$1200,11,0))",
                        f"=sumif(O:O,$B{next_open_row},P:P)+sumif(R:R,$B{next_open_row},S:S)+sumif(U:U,$B{next_open_row},V:V)",
                        f"=sumif(O:O,$B{next_open_row},Q:Q)+sumif(R:R,$B{next_open_row},T:T)+sumif(U:U,$B{next_open_row},W:W)",
                        f"=D{next_open_row}-E{next_open_row}",
                    ]
                ],
            },
        ]
        ws.batch_update(update_data, value_input_option="USER_ENTERED")

        return 0
    except Exception:
        print("Here is the printout:")
        traceback.print_exc()
    return 1


class ApproveFreeAgencyButton(discord.ui.Button):
    def __init__(self, name, add, drop, week):
        super().__init__()
        self.label = "Approve Trade"
        self.style = discord.ButtonStyle.green
        self.name = name
        self.add = add
        self.drop = drop
        self.week = week
        self.success = False

    async def callback(self, interaction: discord.Interaction):
        # if not self.success:
        if (
            interaction.user.get_role(utils.SBL_STAFF_ID)
            or interaction.user.get_role(utils.SBL_ROTOM_CODER_ID)
        ) and not self.success:
            await interaction.response.defer()

            add_list = self.add.split(",")
            drop_list = self.drop.split(",")

            if len(add_list) != len(drop_list):
                await interaction.response.send_message(
                    "Unequal number of adds and drops.", ephemeral=True
                )
                return

            result = 0

            new_lines = [
                f"{self.name},{pair[0].strip()},{pair[1].strip()},{self.week}\n"
                for pair in zip(add_list, drop_list)
            ]

            with open("resources/free_agency.txt", "a") as f:
                f.writelines(new_lines)

            # for pair in zip(add_list, drop_list):
            #     result += add_free_agency(self.name, pair[0].strip(), pair[1].strip(), self.week)
            # await interaction.message.clear_reactions()

            if result == 0:
                await interaction.message.add_reaction("✅")
                self.success = True
            else:
                await interaction.message.add_reaction("❌")
        elif self.success:
            await interaction.response.send_message(
                "Trade was already successfully approved!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You do not have permission to approve trades.", ephemeral=True
            )


def process_saved_free_agency():
    file = open("resources/free_agency.txt", "r")
    successes = []
    failures = []
    for line in file.readlines():
        info = line.strip().split(",")
        print(info)
        if add_free_agency(info[0], info[1], info[2], info[3]) == 0:
            successes.append(line)
        else:
            failures.append(line)

    return (successes, failures)


def process_saved_player_trades():
    file = open("resources/player_trade.txt", "r")
    successes = []
    failures = []
    for line in file.readlines():
        info = line.strip().split(",")
        trade = Trade(info[0], info[1], info[2], info[3])
        if add_free_agency(trade) == 0:
            successes.append(line)
        else:
            failures.append(line)

    return (successes, failures)


class ApproveFreeAgencyView(discord.ui.View):
    def __init__(self, name, add, drop, week):
        super().__init__(timeout=None)
        self.add_item(ApproveFreeAgencyButton(name, add, drop, week))


class ApproveTradeButton(discord.ui.Button):
    def __init__(self, trade):
        super().__init__()
        self.label = "Approve Trade"
        self.style = discord.ButtonStyle.green
        self.trade = trade
        self.success = False

    async def callback(self, interaction: discord.Interaction):
        # if not self.success:
        if (
            interaction.user.get_role(utils.SBL_STAFF_ID)
            or interaction.user.get_role(utils.SBL_ROTOM_CODER_ID)
        ) and not self.success:
            await interaction.response.defer()

            add_list = self.trade.add.split(",")
            drop_list = self.trade.drop.split(",")

            result = 0

            new_lines = [
                f"{self.trade.name1},{self.trade.name2},{pair[0].strip()},{pair[1].strip()},{self.week}\n"
                for pair in zip(add_list, drop_list)
            ]

            with open("resources/player_trade.txt", "a") as f:
                f.writelines(new_lines)
            # result = add_trade(self.trade)
            await interaction.message.clear_reactions()

            if result == 0:
                await interaction.message.add_reaction("✅")
                self.success = True
            else:
                await interaction.message.add_reaction("❌")
        elif self.success:
            await interaction.response.send_message(
                "Trade was already successfully approveed!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You do not have permission to approve trades.", ephemeral=True
            )


class ApproveTradeView(discord.ui.View):
    def __init__(self, trade):
        super().__init__(timeout=None)
        self.add_item(ApproveTradeButton(trade))


class TradeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["transaction"])
    async def trade(self, ctx):
        await ctx.send(view=TradeButtonView(self.bot))
        await ctx.message.delete()

    @commands.command(aliases=["processtrades"])
    async def process_trades(self, ctx):
        # print(ctx.author.roles)

        if utils.SBL_STAFF_ID in [
            x.id for x in ctx.author.roles
        ] or utils.SBL_ROTOM_CODER_ID in [x.id for x in ctx.author.roles]:
            # if ctx.author.get_role() or ctx.author.get_role(utils.SBL_ROTOM_CODER_ID):
            successes, failures = process_saved_free_agency()
            s_string = "\n".join([f"{s.strip()}✅" for s in successes])
            f_string = "\n".join([f"{f.strip()}❌" for f in failures])
            # if s_string:
            #     await ctx.author.send(f"Successes:\n{s_string}")
            # if f_string:
            #     await ctx.author.send(f"Failures:\n{f_string}")
            # t_string = '\n'.join([f'{s}✅' for s in successes] + [f'{f}❌' for f in failures])
            await ctx.author.send(s_string + "\n" + f_string)
            file = open("resources/free_agency.txt", "w")
            file.write("".join(failures))
            file.close()

            successes, failures = process_saved_player_trades()
            s_string = "\n".join([f"{s.strip()}✅" for s in successes])
            f_string = "\n".join([f"{f.strip()}❌" for f in failures])
            # if s_string:
            #     await ctx.author.send(f"Successes:\n{s_string}")
            # if f_string:
            #     await ctx.author.send(f"Failures:\n{f_string}")
            # t_string = '\n'.join([f'{s}✅' for s in successes] + [f'{f}❌' for f in failures])
            await ctx.author.send(s_string + "\n" + f_string)
            file = open("resources/player_trade.txt", "w")
            file.write("".join(failures))
            file.close()
        else:
            await ctx.author.send("You do not have permission to process trades.")


async def setup(bot):
    await bot.add_cog(TradeCog(bot))
