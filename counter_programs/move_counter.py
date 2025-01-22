import re

from urllib.request import Request, urlopen
import matplotlib.pyplot as plt

from collections import Counter

with open("all_games.txt", "r") as file:
    link_list = [
        line.strip() for line in file if line.strip().startswith("https://replay")
    ]

links = [str(x.strip()) + ".log" for x in link_list]

move_list = []

mode = 1  # 0 is given, 1 is received

for link in links:
    # print(link)
    req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
    data = urlopen(req).read().decode("utf-8")
    # print(link)
    for move in re.findall(r"\|move\|p[12].*?\|([\w !-]*)\|", data):
        print(move)

        move_list.append(move)
    # move_dict[] += 1

print(move_list)
print(len(move_list))

# data = {'robbyrabs': 12, 'hippojust': 9, 'callmeshrug': 6, 'alchemillavgc': 12, 'tr1pl3-33': 7, 'satmaofever': 15, 'pixixy': 9, 'jdawgin13': 12, 'ulico': 9, 'richerpeach': 5, 'busenbb': 4, 'shellshock20': 8, 'saget69': 9, 'cyb3rstr4w': 10, 'damage77': 6, 'icyyymatt': 16, 'kamplayskirby': 9, 'legostarwarsyoda': 9, 'tzim14': 10, 'praspian': 8, 'trainer zorro': 8}

# Sort the data in descending order based on values
filtered_data = {k: v for k, v in Counter(move_list).items() if v >= 1 and v < 3}
sorted_data = {
    k: v
    for k, v in sorted(filtered_data.items(), key=lambda item: item[1], reverse=False)
}

# Extract the usernames and values
usernames = list(sorted_data.keys())
values = list(sorted_data.values())

# Create a bar graph
plt.barh(usernames, values)

# Set labels and title
plt.xlabel("# of Moves")
plt.ylabel("Move Names")
plt.title("SBL Season 7 Move Count")

# Rotate the x-axis labels for better visibility
# plt.xticks(rotation=90)

# Display the bar graph
plt.show()
