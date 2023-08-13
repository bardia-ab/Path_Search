import os
from tqdm import tqdm



coords = ['X45Y90', 'X44Y90']
commands = ['python Compressed_Graph.py {}', 'python temp.py {}', 'python Relocate_CUTs.py {}']
pbar = tqdm(total=len(coords) * len(commands))
for coord in coords:
    for command in commands:
        pbar.set_description(command.format(coord))
        pbar.update(1)
        os.system(command.format(coord))