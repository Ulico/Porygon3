import re

from urllib.request import Request, urlopen
import matplotlib.pyplot as plt

with open("all_games.txt", "r") as file:
    link_list = [
        line.strip() for line in file if line.strip().startswith("https://replay")
    ]

links = [str(x.strip()) + ".log" for x in link_list]

crit_dict = {}

mode = 0  # 0 is given, 1 is received

for link in links:
    # print(link)
    req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
    data = urlopen(req).read().decode("utf-8")

    player1 = re.search(r"\|player\|p1\|([\w !-]*)\|", data).group(1).lower()
    player2 = re.search(r"\|player\|p2\|([\w !-]*)\|", data).group(1).lower()

    num_crits_p1 = len(re.findall(r"\|-miss\|p1", data))
    num_crits_p2 = len(re.findall(r"\|-miss\|p2", data))
    print(player1, player2, num_crits_p1, num_crits_p2)

    if mode == 0:

        crit_dict[player1] = crit_dict.get(player1, 0) + num_crits_p1
        crit_dict[player2] = crit_dict.get(player2, 0) + num_crits_p2

    else:
        crit_dict[player1] = crit_dict.get(player1, 0) + num_crits_p2
        crit_dict[player2] = crit_dict.get(player2, 0) + num_crits_p1

print(crit_dict)

# data = {'robbyrabs': 12, 'hippojust': 9, 'callmeshrug': 6, 'alchemillavgc': 12, 'tr1pl3-33': 7, 'satmaofever': 15, 'pixixy': 9, 'jdawgin13': 12, 'ulico': 9, 'richerpeach': 5, 'busenbb': 4, 'shellshock20': 8, 'saget69': 9, 'cyb3rstr4w': 10, 'damage77': 6, 'icyyymatt': 16, 'kamplayskirby': 9, 'legostarwarsyoda': 9, 'tzim14': 10, 'praspian': 8, 'trainer zorro': 8}

# Sort the data in descending order based on values
sorted_data = {
    k: v for k, v in sorted(crit_dict.items(), key=lambda item: item[1], reverse=False)
}

# Extract the usernames and values
usernames = list(sorted_data.keys())
values = list(sorted_data.values())

# Create a bar graph
plt.barh(usernames, values)
plt.xticks([n for n in range(int(max(values)) + 1)])
# Set labels and title
plt.xlabel("# of Misses")
plt.ylabel("Usernames")
plt.title(f"SBL Season 7 Miss Count ({'Given' if mode == 0 else 'Received'})")

# Rotate the x-axis labels for better visibility
# plt.xticks(rotation=90)

# Display the bar graph
plt.show()
