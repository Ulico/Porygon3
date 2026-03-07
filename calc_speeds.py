import pokepy
from math import floor

list = [
'Hoopa-Unbound',
'Tornadus-Therian',
'Sinistcha',
'Infernape',
'Rotom-Wash',
'Litten',
'Weezing',
'Voltorb-Hisui',
'Donphan',
'Spewpa'














]


def get_speed_stat(base, change, evs, doubled, pos_nature):
    # print(base)

    stat = (floor((2 * base + 31 + floor(evs/4)) * 50/100) +
            5) * (pos_nature * 0.1 + 1)

    # print(stat)

    multiplier = (2+change)/2 if change >= 0 else 2/(2-change)

    return floor(stat*multiplier)*(1+doubled)


client = pokepy.V2Client()

lines = {}

for pokemon in list:
    print(f'Checking {pokemon}...')
    mon = client.get_pokemon(pokemon.lower())[0]

    base_speed = mon.stats[5].base_stat

    for change in range(-2, 2):
        for doubled in [True, False]:
            for evs in [0, 252]:
                for pos_nature in ([True, False] if evs > 0 else [False]):

                    speed = get_speed_stat(
                        base_speed, change, evs, doubled, pos_nature)
                    lines[f'{speed}: {pokemon}, {change if change < 0 else "+"+str(change)}{", in Tailwind" if doubled else ""}{", +Speed" if pos_nature else ""}{", " + str(evs) + " EVs"}'] = speed

{print(k) for k, v in sorted(lines.items(), key=lambda item: item[1])}