import functools
import traceback
import typing
import logging

import discord
from discord.ext import commands
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import utils
import misc_programs.players
import misc_programs.replay_analyzer as replay_analyzer


class UploadReplayButton(discord.ui.Button):
    def __init__(self, link: str):
        super().__init__()
        self.label = "Upload Replay"
        self.style = discord.ButtonStyle.green
        self.link = link
        self.success = False

    async def callback(self, interaction: discord.Interaction):
        # if not self.success:
        if (
            interaction.user.get_role(utils.SBL_STAFF_ID)
            or interaction.user.get_role(utils.SBL_ROTOM_CODER_ID)
        ) and not self.success:
            await interaction.response.defer()
            result = replay_analyzer.upload_replay(self.link)
            await interaction.message.clear_reactions()

            if result == 0:
                await interaction.message.add_reaction("✅")
                self.success = True
            else:
                await interaction.message.add_reaction("❌")
        elif self.success:
            await interaction.response.send_message(
                "Replay was already successfully uploaded!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You do not have permission to approve trades.", ephemeral=True
            )


class DeleteReplayButton(discord.ui.Button):
    def __init__(self):
        super().__init__()
        self.label = "Delete Replay"
        self.style = discord.ButtonStyle.red

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.get_role(utils.SBL_STAFF_ID) or interaction.user.get_role(
            utils.SBL_ROTOM_CODER_ID
        ):
            await interaction.message.delete()
        else:
            await interaction.response.send_message(
                "You do not have permission to delete replays.", ephemeral=True
            )


# def get_browser_log_entries(driver):
#         """get log entreies from selenium and add to python logger before returning"""
#         loglevels = { 'NOTSET':0 , 'DEBUG':10 ,'INFO': 20 , 'WARNING':30, 'ERROR':40, 'SEVERE':40, 'CRITICAL':50}

#         #initialise a logger
#         browserlog = logging.getLogger("chrome")
#         #get browser logs
#         slurped_logs = driver.get_log('browser')
#         for entry in slurped_logs:
#             #convert broswer log to python log format
#             rec = browserlog.makeRecord("%s.%s"%(browserlog.name,entry['source']),loglevels.get(entry['level']),'.',0,entry['message'],None,None)
#             rec.created = entry['timestamp'] /1000 # log using original timestamp.. us -> ms
#             try:
#                 #add browser log to python log
#                 browserlog.handle(rec)
#             except:
#                 print(entry)
#         #and return logs incase you want them
#         return slurped_logs


class UploadReplayView(discord.ui.View):
    def __init__(self, link: str):
        super().__init__(timeout=None)
        if utils.ALLOW_UPLOAD:
            self.add_item(UploadReplayButton(link))
        self.add_item(DeleteReplayButton())


# async def start_listening(listener):
#     async for event in listener:
#         print(event)


def attempt_replay(driver):
    print("Attempting to fetch replay...")
    for i in range(0, 5):
        print(f"Attempt {i}")
        try:
            # for log in driver.get_log('browser'):
            #     print(log)
            # print(get_browser_log_entries(driver))
            save_button = WebDriverWait(driver, 3600).until(
                EC.presence_of_element_located((By.NAME, "saveReplay"))
            )
            driver.execute_script("arguments[0].click();", save_button)
            # save_button.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "close"))
            )

            utils.allow_bets = True

            # return embed
            return 0
        except TimeoutException:
            # return None
            print("Here is the printout:")
            traceback.print_exc()

    return 1


class ShowdownCog(commands.Cog):
    def __init__(self, bot):
        self.most_recent_link = None
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            await ctx.send(
                f"Please wait {int(error.retry_after)} seconds to use this command..."
            )

    def has_moved(self):
        # decoded_string = repr()
        # logs = self.driver.get_log("browser")
        # return True
        # print(self.driver.get_log("browser"))
        for log in self.driver.get_log("browser"):
            message = log["message"]
            if (
                log["level"] == "INFO"
                and log["source"] == "console-api"
                # and "834:13" in message
                # and "queryresponse" not in message  # client.js line that prints info
                and "|t:|" in message
            ):
                print(message.encode("utf-8").decode("unicode_escape"))
        # return len(self.driver.get_log("browser")) != 0
        # if logs:
        # s = [
        #     log
        #     for log in self.driver.get_log("browser")
        #     if log["level"] == "INFO"
        #     and log["source"] == "console-api"
        #     and "|turn|" in log["message"]
        # ][-1]["message"]
        # decoded_string = bytes(s, "utf-8").decode("unicode_escape")
        # print("Something happened")
        # else:
        # print("Nothing has happened.")

        # if decoded_string:
        #     print(decoded_string)
        # else:
        #     print("Nothing has happened.")
        # print(f"here: {decoded_string}")

    async def watch_game(self, ctx, game_link, title):
        async def run_blocking(
            blocking_func: typing.Callable, *args, **kwargs
        ) -> typing.Any:
            """Runs a blocking function in a non-blocking way"""
            func = functools.partial(
                blocking_func, *args, **kwargs
            )  # `run_in_executor` doesn't support kwargs, `functools.partial` does
            return await self.bot.loop.run_in_executor(None, func)

        self.most_recent_link = game_link
        self.driver.get(game_link)
        # driver.execute_script("console.log = function(message){window.console.log(message);};")
        # print(self.driver.find_elements(By.CLASS_NAME, "chat"))
        print("here1")
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chat"))
            )
        except TimeoutException:
            print("here3")
        print("here2")

        embed = discord.Embed(
            title=title,
            description=game_link.replace("play", "replay").replace("/battle-", "/"),
        )
        result = await run_blocking(attempt_replay, self.driver)
        channel = self.bot.get_channel(utils.SBL_MATCH_REPLAYS_ID)
        if utils.DEBUG:
            channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)
        #
        if result != 0:
            await ctx.send("Failed to fetch replay.")
        else:
            await channel.send(embed=embed, view=UploadReplayView(embed.description))

        if "a best-of" in self.driver.page_source:
            # if "bo3" in game_link:
            print("This is a Bo3")
            print(self.driver.find_elements(By.CLASS_NAME, "notice uhtml-bestof"))
            print(self.driver.find_elements(By.CLASS_NAME, "battle-log"))
            print(self.driver.find_elements(By.CLASS_NAME, "inner message-log"))
            bo3_link = (
                self.driver.find_elements(By.CLASS_NAME, "battle-log")[0]
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href")
            )
            print(f"bo3 link: {bo3_link}")

            print("started looking")

            self.driver.get(bo3_link)
            center = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.TAG_NAME,
                        "center",
                    )
                )
            )
            # print("here1")
            set_over = (
                len(center.find_elements(By.XPATH, "//*[contains(text(), 'won!')]"))
                != 0
            )
            # print(set_over)

            if not set_over:
                self.driver.get(game_link)
                try:
                    WebDriverWait(self.driver, 50).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//div[text()='Next: ']",
                            )
                        )
                    )
                except TimeoutException:
                    print("couldn't find next game")

                print("both players are ready!")

                self.driver.get(bo3_link)
                center = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.TAG_NAME,
                            "center",
                        )
                    )
                )
                # print("here1")
                # print(center.find_elements(By.XPATH, "//*[contains(text(), 'won!')]"))
                # if not center.find_elements_by_xpath("//*[contains(text(), 'won!')]"):
                # print("here2")
                links = [
                    element.get_attribute("href")
                    for element in self.driver.find_element(
                        By.CLASS_NAME, "battle-controls"
                    ).find_elements(By.TAG_NAME, "a")
                ]
                try:
                    print(links)
                    current_index = next(
                        i for i, link in enumerate(links) if link == game_link
                    )
                    if current_index < len(links) - 1:
                        link = links[current_index + 1]
                        await ctx.send(
                            embed=discord.Embed(
                                title=f"Game {current_index + 2}: {title}",
                                description=link,
                            )
                        )
                        await self.watch_game(ctx, link, title)
                        return
                except StopIteration:
                    print("Could not find current link")
            else:
                print("Set is done!")

        self.driver.quit()

    async def find_game(self, ctx, name):
        game_link = None
        options = webdriver.EdgeOptions()
        if not utils.DEBUG:
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
        options.set_capability(
            "goog:loggingPrefs", {"browser": "ALL"}  # old: loggingPrefs
        )
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service()
        driver = webdriver.Edge(service=service, options=options)

        self.driver = driver

        if not name:
            driver.get("https://play.pokemonshowdown.com/battles")
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//p[text()='100+  battles']")
                )
            )
            driver.find_element(By.CLASS_NAME, "list")
            links = driver.find_elements(By.CLASS_NAME, "ilink")
            for link in links:
                if "battle-" in link.get_attribute("href"):
                    await ctx.send(
                        embed=discord.Embed(
                            title=link.text.split("\n")[-1].replace("v.", "vs."),
                            description=link.get_attribute("href"),
                        )
                    )
                    break
            return

        driver.get("https://play.pokemonshowdown.com/")
        driver.find_element(By.NAME, "finduser").click()
        driver.find_element(By.NAME, "data").send_keys(
            players.get_attribute_by_value("alias", "username", name)[0]
        )
        form = driver.find_element(By.CLASS_NAME, "ps-popup")
        form.find_element(By.TAG_NAME, "button").click()

        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rooms"))
            )
            game_link = [
                game_link
                for game_link in element.find_elements(By.TAG_NAME, "a")
                if "battle-" in game_link.get_attribute("href")
            ][-1].get_attribute("href")
            title = element.find_elements(By.TAG_NAME, "span")[-1].get_attribute(
                "title"
            )
            utils.allow_bets = False

            if self.most_recent_link == game_link:
                await ctx.send("Attempted to fetch repeated game.")
                return None, None

            # bo3_link = None
            # if bo3:
            g1_title = title
            if "bo3" in game_link:
                g1_title = f"Game 1: {title}"

            await ctx.send(embed=discord.Embed(title=g1_title, description=game_link))

            return game_link, title

        except (IndexError, NoSuchElementException):
            await ctx.send("No games found.")
        except TimeoutException:
            await ctx.send("User not found.")

    @commands.command(
        brief="Grabs the most recent Pokemon Showdown game link.",
        help="Attempts to fetch the most recent Pokemon Showdown game link of a specified user, sending this as a message. "
        "While the match is in progress, this command checks every 30 seconds to whether the match has concluded. "
        "If so, it saves and uploads the replays, in addition to sending the replay link in the #sbl-match-replays channel.",
        aliases=["gt"],
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.guild)
    async def gametime(self, ctx, *, name=None):
        async with ctx.typing():
            game_link, title = await self.find_game(ctx, name)
        print("result:")
        print(game_link, title)
        if game_link:
            await self.watch_game(ctx, game_link, title)
        else:
            self.driver.quit()

    @commands.command()
    async def gt3(self, ctx, *, name=None):
        print(self.has_moved())

    @commands.command()
    async def upload(self, ctx, game_link):
        result = replay_analyzer.upload_replay(game_link)
        # ctx.
        print(result)
        await ctx.message.clear_reactions()
        # print(ctx)

        if result == 0:
            await ctx.message.add_reaction("✅")
            # self.success = True
        else:
            # print("here")
            await ctx.message.add_reaction("❌")


async def setup(bot):
    await bot.add_cog(ShowdownCog(bot))
