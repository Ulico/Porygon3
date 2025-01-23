import utils
from elosports.elo import Elo

records = utils.get_record_sheet()

# print(records)

players = {}
eloLeague = Elo(k = 50)

for index, game in records.iterrows():
    # if int(index) > 394 and int(index) < 495:

        # if (int(index) % 10 == 5):
        #     for item in dict(sorted(eloLeague.ratingDict.items(), key=lambda item: item[1])).items():
        #         print(item[0], item[1])
        #     print('\n-----------------------------------\n')
        # print(game)
        p1 = game['Player 1']
        p2 = game['Player 2']
        if p1 not in players:
            eloLeague.addPlayer(p1, rating = 1600)
            players[p1] = 1
        else:
            players[p1] += 1
        if p2 not in players:
            eloLeague.addPlayer(p2, rating = 1600)
            players[p2] = 1
        else:
            players[p2] += 1

        # if index == 200:
        #     eloLeague.k = 32

        if game['Winner Name'] == p1:
            eloLeague.gameOver(p1, p2, False)
        else:
            eloLeague.gameOver(p2, p1, False)
    
# print(eloLeague.ratingDict)
print(players)

limit = 1

for item in dict(sorted(eloLeague.ratingDict.items(), key=lambda item: item[1])).items():
    if (players[item[0]] >= limit):
     print(item[0], item[1])

# print(eloLeague.expectResult(eloLeague.ratingDict['Jdawgin13'],eloLeague.ratingDict['Ulico']))
# from elosports.elo import Elo
# eloLeague = Elo(k = 20)
# eloLeague.addPlayer("Daniel", rating = 1600)
# eloLeague.addPlayer("Harry")
# eloLeague.expectResult(eloLeague.ratingDict['Daniel'],eloLeague.ratingDict['Harry'])