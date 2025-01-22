import utils
import math
import itertools
from trueskill import Rating, rate_1vs1, TrueSkill

def express(p):
    # return p.mu - 3*p.sigma
    return p.mu

rankings = []
env = TrueSkill(25, 25/3, 25/6, 25/3 * 0.08, 0)

def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (env.beta * env.beta) + sum_sigma)
    # ts = trueskill.global_env()
    return env.cdf(delta_mu / denom)

# print(records)

# for t in [25/3 * 0.001, 25/3 * 0.01, 25/3 * 0.1, 25/3 * 1]:
# env.tau = t
records = utils.get_record_sheet()
players = {}

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
        # eloLeague.addPlayer(p1, rating = 1600)
        players[p1] = env.create_rating()
    if p2 not in players:
        players[p2] = env.create_rating()

    # if index == 200:
    #     eloLeague.k = 32
    # if game['Week'] == 'Playoffs':
    #      env.tau = 25/3 * 0.15
    # else:
    #      env.tau = 25/3 * 0.01

    if game['Winner Name'] == p1:
        players[p1], players[p2] = env.rate_1vs1(players[p1] , players[p2])
    else:
        players[p2], players[p1] = env.rate_1vs1(players[p2], players[p1] )
        
    # print(eloLeague.ratingDict)
    # print(players)

    # print(sorted(players.values(), key=env.expose, reverse=True))

    # for item in dict(sorted(players.items(), key=lambda item: item[1].mu)).items():
    #     if item[1].sigma < 2.5:
    #         #  print('*', end='')
    #         print(f'{item[0]}: {item[1].mu} ({item[1].sigma})')

for item in dict(sorted(players.items(), key=lambda item: item[1].mu)).items():
    #  print('*', end='')
# print(f'{item[0]}: {item[1].rating - 3 * item[1].rd}')
    if (item[1].sigma < 3):

        print(f'{item[0]}: {item[1].mu} ± {2 * item[1].sigma}')

    # for item in dict(sorted(players.items(), key=lambda item: item[1].mu - 3 * item[1].sigma)).items():
    #     if item[1].sigma < 2.5:
    #         #  print('*', end='')
    #         print(f'{item[0]}: {item[1].mu - 3 * item[1].sigma}')

    
#     rankings.append(f'{p[0]} ({express(p[1])})' for p in dict(sorted(players.items(), key=lambda item: express(item[1]))).items())

# for (r1, r2, r3, r4) in zip(rankings[0], rankings[1], rankings[2], rankings[3]):
#     print('{0:<40} {1:<40} {2:<40} {3:<40}'.format(r1, r2, r3, r4))

# players['Praspian'], players['Cyb3r'] = env.rate_1vs1(players['Praspian'] , players['Cyb3r'])
# players['Alchemilla'], players['Cyb3r'] = env.rate_1vs1(players['Alchemilla'] , players['Cyb3r'])

# print('\n-----------------------------\n')

# for item in dict(sorted(players.items(), key=lambda item: item[1].mu)).items():
#     if item[1].sigma < 2.5:
#         #  print('*', end='')
#         print(f'{item[0]}: {item[1].mu} ({item[1].sigma})')

# print(win_probability([players['Cyb3r']], [players['Joel']]))

# print(eloLeague.expectResult(eloLeague.ratingDict['Jdawgin13'],eloLeague.ratingDict['Ulico']))