import math
import re
import urllib.error
import urllib.request
from functools import cmp_to_key
from urllib.parse import quote
import discord
import openai
import pandas as pd
from bs4 import BeautifulSoup
from discord.ext import commands

import utils


def type_string(t1, t2) -> str:
    return t1 if not t2 else f"{t1}/{t2}"


class GeneralPokemonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["random", "randpoke", "randpokemon", "randompoke"],
        brief="Displays a random pokemon.",
        # help='Displays a random pokemon from a specific range. By default, this is only Pokemon from Generations 1 through 4, but appending "all" will include all Pokemon.',
    )
    async def randompokemon(self, ctx):
        async with ctx.typing():
            pokemon_df = pd.read_csv("resources\\pokemon.csv")
            row = pokemon_df.sample(1)
            number = utils.get_pokedex_number(row["Number"].item())
            type1 = row["Type 1"].item().capitalize()
            type2 = (
                row["Type 2"].item().capitalize()
                if not row["Type 2"].item() != row["Type 1"].item()
                else ""
            )
            embed = discord.Embed(
                title=row["Name"].item(), color=utils.color_dict[type1.lower()]
            )

            embed.set_thumbnail(url=utils.get_image_from_number(number))
            stat_string = ""
            for name in utils.stat_names:
                stat_string += f"{name}: {int(row[name].item())}\n"

            embed.add_field(name="Stats", value=stat_string, inline=False)

            embed.add_field(name="Type", value=type_string(type1, type2))
            abilities = [
                ability
                for ability in [
                    row["Ability 1"].item(),
                    row["Ability 2"].item(),
                    row["Ability 3"].item(),
                ]
                if ability == ability
            ]
            embed.add_field(name="Abilities", value="\n".join(abilities), inline=False)

            await ctx.send(embed=embed)

    # @commands.command()
    # async def guess(self, ctx, *, question=None):
    #     global guessing_pokemon
    #     if question and guessing_pokemon != "":
    #         if guessing_pokemon.casefold() in question.casefold():
    #             await ctx.send(f"The pokemon is {guessing_pokemon}!")
    #             guessing_pokemon = ""
    #             return
    #         response = openai.Completion.create(
    #             model="text-davinci-003",
    #             prompt=question.casefold()
    #             .replace("it", guessing_pokemon)
    #             .replace("this pokemon", guessing_pokemon)
    #             .replace("the pokemon", guessing_pokemon),
    #             temperature=0,
    #             max_tokens=1024,
    #             top_p=1,
    #             frequency_penalty=0.5,
    #             presence_penalty=0,
    #         )
    #         await ctx.send(
    #             str(
    #                 response["choices"][0]["text"]
    #                 .replace(guessing_pokemon, "It")
    #                 .replace(guessing_pokemon.lower(), "it")
    #             ).strip()
    #         )
    #     elif guessing_pokemon != "":
    #         await ctx.send("Please finish the current guessing game.")
    #     else:
    #         pokemon_df = pd.read_csv("resources\\pokemon.csv")

    #         while True:
    #             row = pokemon_df.sample(1)

    #             guessing_pokemon = row["Name"].item()
    #             if "-" not in guessing_pokemon:
    #                 break
    #         print(guessing_pokemon)
    #         await ctx.send(
    #             "I am thinking of a Pokemon. Ask me questions to guess which one."
    #         )

    @commands.command(
        aliases=["mon"],
        brief="Displays information about a Pokemon.",
        help="Displays information about a Pokemon. "
        f"If a Pikalytics entry is not found, this command will attempt to fetch the {utils.FORMAT_ABBR} Pikalytics entry. "
        "If this is not found, this command will display a basic entry with the Pokemon's name, typing, stats, and abilities.",
    )
    async def pokemon(self, ctx, *, name):

        async with ctx.typing():
            pokemon_df = pd.read_csv("resources\\pokemon.csv")
            stats = []

            # print(name)
            # print(
            #     f"https://www.pikalytics.com/pokedex/{FORMAT_ABBR}/{quote(name, safe='')}"
            # )
            try:
                # print(
                #     f"https://www.pikalytics.com/pokedex/{utils.FORMAT_ABBR}/{quote(name, safe='')}"
                # )
                page = urllib.request.Request(
                    f"https://www.pikalytics.com/pokedex/{utils.FORMAT_ABBR}/{quote(name, safe='')}",
                    headers={"User-Agent": "Mozilla/5.0"},
                )

                infile = urllib.request.urlopen(page).read()
                data = infile.decode("ISO-8859-1")
            except urllib.error.HTTPError as err:
                print(err)
                await ctx.send("Could not find Pikalytics entry.")
                row = pokemon_df[
                    pokemon_df["Name"].apply(lambda v: v.lower() == name.lower())
                ]
                if not row.empty:
                    number = utils.get_pokedex_number(row["Number"].item())
                    type1 = row["Type 1"].item().capitalize()
                    type2 = (
                        row["Type 2"].item().capitalize()
                        if not row["Type 2"].item() != row["Type 2"].item()
                        else ""
                    )
                    embed = discord.Embed(
                        title=row["Name"].item(), color=utils.color_dict[type1.lower()]
                    )
                    embed.set_thumbnail(url=utils.get_image_from_number(number))
                    stat_string = ""
                    for name in utils.stat_names:
                        stat_string += "{}: {}\n".format(name, int(row[name].item()))

                    embed.add_field(name="Stats", value=stat_string, inline=False)

                    embed.add_field(name="Type", value=type_string(type1, type2))
                    abilities = [
                        ability
                        for ability in [
                            row["Ability 1"].item(),
                            row["Ability 2"].item(),
                            row["Ability 3"].item(),
                        ]
                        if ability == ability
                    ]

                    embed.add_field(
                        name="Abilities", value="\n".join(abilities), inline=False
                    )
                    # embed.set_footer(text='Powered by Pikalytics')
                    await ctx.send(embed=embed)
                return
            soup = BeautifulSoup(data, "html.parser")
            format_name = soup.find(id="format_dd").get_text().strip().splitlines()[0]
            page = "\n".join(
                [
                    tag.text.strip()
                    for tag in soup.find_all(
                        "div", attrs={"class": "inline-block pokemon-stat-container"}
                    )
                ]
            )
            # print(page)
            for stat in utils.stat_names:
                stats.append(re.findall(r"{}[\r\n]+([^\r\n]+)".format(stat), page)[0])
            # print(stats)
            move_data = [
                elem
                for elem in page.split("Moves")[1].split("Teammates")[0].splitlines()
                if elem.strip()
            ]
            move_string = ""
            for i in range(0, len(move_data) - 3, 3):
                move_string += "{} ({}): {}\n".format(
                    move_data[i], move_data[i + 1], move_data[i + 2]
                )
            move_string += "Other: {}\n".format(move_data[-1])
            # print(move_string)
            tera_string = ""
            if "Terastalize Types" in page:
                tera_data = [
                    elem
                    for elem in page.split("Terastalize Types")[1]
                    .split("Item")[0]
                    .splitlines()
                    if elem.strip()
                ]

                if "No data yet!" not in tera_data:
                    for i in range(0, len(tera_data), 3):
                        tera_string += "{}: {}\n".format(
                            tera_data[i].title(), tera_data[i + 2]
                        )
                tera_string = tera_string.rstrip()
            # print(tera_string)
            item_data = [
                elem
                for elem in page.split("Item")[1].split("Ability")[0].splitlines()
                if elem.strip()
            ]
            item_string = ""
            if "No data yet!" not in item_data:
                for i in range(0, len(item_data), 2):
                    item_string += "{}: {}\n".format(item_data[i], item_data[i + 1])

            item_string = item_string.rstrip()
            # print(item_string)
            ability_data = [
                elem
                for elem in page.split("Ability")[1]
                .split("Nature")[0]
                .split("EV Spreads")[0]
                .splitlines()
                if elem.strip()
            ]

            ability_string = ""
            if "No data yet!" not in ability_data:
                for i in range(0, len(ability_data), 2):
                    ability_string += "{}: {}\n".format(
                        ability_data[i], ability_data[i + 1]
                    )
            # print(ability_string)
            row = pokemon_df[
                pokemon_df["Name"].apply(lambda v: v.lower() == name.lower())
            ]
            # print(row)

            types = [
                tag.text.capitalize()
                for tag in soup.find(
                    "span", attrs={"class": "inline-block pokedex-header-types"}
                ).findAll("span", recursive=False)
            ]
            type1 = types[0]
            type2 = types[1] if len(types) == 2 else ""

            embed = discord.Embed(
                title=name,
                description=format_name,
                color=utils.color_dict[type1.lower()],
            )
            # print(row)
            if not row.empty:
                # print("here")
                # print(math.isnan(int(row["Number"].item())))
                # if not math.isnan(int(row["Number"].item())):
                number = utils.get_pokedex_number(row["Number"].item())
                # print("here")
                embed.set_thumbnail(url=utils.get_image_from_number(number))
                # print(utils.get_image_from_number(number))
                embed.title = row["Name"].item()
            stat_string = ""
            for pair in zip(utils.stat_names, stats):
                stat_string += f"{pair[0]}: {pair[1]}\n"

            embed.add_field(name="Stats", value=stat_string, inline=False)

            embed.add_field(name="Type", value=type_string(type1, type2))
            embed.add_field(name="Common Moves", value=move_string, inline=False)
            if item_string:
                embed.add_field(name="Common Items", value=item_string, inline=False)

            if ability_string:
                embed.add_field(name="Abilities", value=ability_string, inline=False)

            if tera_string:
                embed.add_field(
                    name="Common Terastalize Types", value=tera_string, inline=False
                )
            embed.set_footer(text="Powered by Pikalytics")
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GeneralPokemonCog(bot))
