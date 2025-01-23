import discord
import numpy as np
from discord.ui import View, Button


class VoltorbTile(Button):
    def __init__(self, board_view, value, num):
        super().__init__(label="\255")
        self.num = num
        self.value = value
        self.board_view = board_view

    async def callback(self, interaction):
        self.style = (
            discord.ButtonStyle.red if self.value == 0 else discord.ButtonStyle.blurple
        )

        self.label = "💣" if self.value == 0 else str(self.value)
        self.disabled = True

        if self.value > 1:
            self.board_view.count += 1
        if self.board_view.count >= self.num or self.value == 0:
            end_tile = Button(
                label=(
                    "You Win 🤓" if self.board_view.count >= self.num else "You Lose 😔"
                ),
                style=(
                    discord.ButtonStyle.green
                    if self.board_view.count >= self.num
                    else discord.ButtonStyle.red
                ),
            )

            async def end_callback(interaction):
                await interaction.response.defer()

            end_tile.callback = end_callback
            self.board_view.add_item(end_tile)
            for i, item in enumerate(self.board_view.children[:20]):
                if i % 5 != 4:
                    item.style = (
                        discord.ButtonStyle.red
                        if item.value == 0
                        else discord.ButtonStyle.blurple
                    )
                    item.label = "💣" if item.value == 0 else str(item.value)
                    item.disabled = True
        await interaction.response.edit_message(view=self.board_view)


class StaticTile(Button):
    def __init__(self, label):
        super().__init__(label=label, disabled=True, style=discord.ButtonStyle.gray)

    async def callback(self, interaction):
        await interaction.response.defer()


class BoardView(View):
    count = 0


class VoltorbFlipGame:
    def __init__(self):
        # self.max = 16
        self.board = np.random.randint(4, size=(4, 4))
        # for x in range(0, self.board.shape[0]):
        #     for y in range(0, self.board.shape[1]):
        #         if self.board[x][y] < 3:
        #             self.board[x][y] = 0

    async def send_board(self, ctx):
        view = BoardView()

        for i in range(0, 5):
            for j in range(0, 5):
                if i == 4 and j == 4:
                    pass

                elif j == 4:
                    view.add_item(
                        StaticTile(
                            f"{self.board[i].sum()}/{np.count_nonzero(self.board[i] == 0)}"
                        )
                    )
                elif i == 4:
                    view.add_item(
                        StaticTile(
                            f"{self.board.T[j].sum()}/{np.count_nonzero(self.board.T[j] == 0)}"
                        )
                    )
                else:
                    view.add_item(
                        VoltorbTile(
                            view, self.board[i][j], np.count_nonzero(self.board > 1)
                        )
                    )

        await ctx.send(view=view)
