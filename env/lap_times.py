import random
def get_lap_times():
    alltimes=  {0: {'VER':0,'RUS':0, 'MAK':0, 'ASM':0, 'SUF':0, 'RIT':0}}
    for i in range(1,71):
        this_lap_times = {}
        drivers = ['VER','RUS', 'MAK', 'ASM', 'SUF', 'RIT' ]
        for d in drivers:
            this_lap_times[d] = round(85  + random.uniform(-5,5), 3)
        alltimes[i] = this_lap_times

    return alltimes

