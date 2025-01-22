import re

from urllib.request import Request, urlopen
import matplotlib.pyplot as plt
from datetime import datetime
import pickle
import utils

tera_dict = {}

# tera_dict['Ghost'] = 4
# tera_dict['Fighting'] = 2
# tera_dict['Water'] = 2
# tera_dict['Electric'] = 4
# tera_dict['Fairy'] = 4
# tera_dict['Flying'] = 2
# tera_dict['Fire'] = 2
# tera_dict['Steel'] = 1


with open("all_games.txt", "r") as file:
    link_list = [line.strip() for line in file if line.strip().startswith("https")]

# return
# r = Replay('replays/test.txt')
# f = open("replays\\test.txt", "r")
# print(re.findall(r'https:\/\/replay.*\n', f.read()))
links = [str(x.strip()) + ".log" for x in link_list]


for link in links:
    # print(link)
    req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
    data = urlopen(req).read().decode("utf-8")

    for tera in re.findall(r"\|-terastallize\|.*\|(.*)", data):
        tera_dict[tera] = tera_dict.get(tera, 0) + 1

sorted_data = {
    k: v for k, v in sorted(tera_dict.items(), key=lambda item: item[1], reverse=True)
}

# Extract the sorted labels and values
labels = list(sorted_data.keys())
values = list(sorted_data.values())

with open("resources/teras.txt", "w") as file:
    # Write the week number as the first line
    file.write(str(utils.get_current_week()) + "\n")

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
    "stellar": "#FFFFFF",
}
# Convert hex values to RGBA values
# type_colors_rgba = {k: mcolors.to_rgb(v) for k, v in color_dict.items()}
# Set up the figure and axis
fig, ax = plt.subplots()

# print(type_colors_rgba)

# Create the bar graph with colored bars
bars = ax.bar(labels, values, color=[color_dict[label.lower()] for label in labels])


# Rotate x-axis labels for better visibility
plt.xticks(rotation=90)

# Set the axis labels and title
ax.set_xlabel("Types")
ax.set_ylabel("Count")
ax.set_title("SBL Season 5 Tera Types")

for bar in bars:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2, height, str(height), ha="center", va="bottom"
    )


# Display the graph
plt.tight_layout()
plt.show()
