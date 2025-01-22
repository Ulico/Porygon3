import random

from bing_image_urls import bing_image_urls
from discord.ext import commands


from voltorb import VoltorbFlipGame


class MiscCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def delete(self, ctx, num):
        await ctx.channel.purge(
            limit=int(num), check=lambda x: x.author.id == self.bot.user.id
        )

    @commands.command(
        help="Creates an instance of the Voltorb Flip game. On the edges of the board, the first number is the number of points in that row/column, "
        "while the second number is the number of bombs in the column. "
        "You win if you find all of the 2 or 3 tiles, and you lose if you select a bomb."
    )
    async def voltorb(self, ctx):
        v = VoltorbFlipGame()
        # v.get_board()
        await v.send_board(ctx)

    @commands.command(brief="Displays Wooper.", help="Displays Wooper.")
    async def wooper(self, ctx):
        await ctx.send(random.choice(bing_image_urls("wooper", limit=500)))

    @commands.command(brief="Displays Tinkaton.", help="Displays Tinkaton.")
    async def tinkaton(self, ctx):
        await ctx.send(random.choice(bing_image_urls("tinkaton", limit=500)))

    @commands.command()
    async def chicanery(self, ctx):
        await ctx.send(
            "I am not crazy! I know they swapped those usernames! I knew it was Joel vs Robby. One after bingo vs Shellshock. As if I could ever make such a mistake. "
            "Never. Never! I just – I just couldn't prove it. They – they covered their tracks, they got that bot in the replays channel to lie for them. "
            "You think this is something? You think this is bad? This? This chicanery? They've done worse. Hippo vs Kam! "
            "Are you telling me that the economy just happens to fall like that? No! They orchestrated it! SBL! They parahaxed with an Illumise! And I believed them! "
            "And I shouldn't have. What was I thinking? They'll never change. They'll never change! "
            "Ever since season 1, always the same! Couldn't keep their schedule out of the next week! But not our SBL! Couldn't be precious SBL! "
            '"I was thinking Tuesday"?! And they get to be a trainer!? What a sick joke! I should\'ve stopped them when I had the chance! And you – you have to stop them! You-'
        )


async def setup(bot):
    await bot.add_cog(MiscCog(bot))
