import discord

from discord.ext import commands
import string

COMMAND_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

import asyncio


@client.event
async def on_ready():
    print("SBL Bot is ready!")


@client.event
async def on_message(message):
    lowered_message = message.content.lower()
    if "tuesday" in lowered_message and not message.author.bot:
        with open("resources/tuesday.txt", "r") as file:
            data = file.read()
            tuesday_count = int(data) + lowered_message.count("tuesday")
            await message.channel.send("Tuesday count: " + str(tuesday_count))
        with open("resources/tuesday.txt", "w") as file:
            file.write(str(tuesday_count))
    if "!" in lowered_message and message.author.id == 189879722367385601 and message.channel.id == 989245813865717780:
        total_punctuation = sum(
            1 for char in lowered_message if char in string.punctuation
        )
        # print(total_punctuation)
        exclamation_marks = lowered_message.count("!")
        # print(exclamation_marks)
        percentage = (exclamation_marks / total_punctuation) * 100
        # print(f"Percentage of punctuation that is exclamation marks: {percentage:.2f}%")
        await message.channel.send(
            f"Percentage of punctuation that is exclamation marks: {percentage:.2f}%"
        )
    else:
        await client.process_commands(message)


with open("resources\\discord_secret.txt") as f:
    cogs = ["general", "trade", "betting", "season", "showdown", "sbl", "misc"]

    for cog in cogs:
        asyncio.run(client.load_extension(f"cogs.{cog}_commands"))
    client.run(f.read())
