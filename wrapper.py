import os, time
from tqdm import tqdm
from relocation.arch_graph import Arch

device = Arch('ZCU9')
#coords = ['X46Y90', 'X45Y90', 'X44Y90']
coords = []
for coord in coords:
    #commands = [f'python3 Compressed_Graph.py {coord}', f'python3 temp.py {coord}', f'python3 Relocate_CUTs.py {coord}']
    commands = [f'python3 temp.py {coord}', f'python3 Relocate_CUTs.py {coord}']
    for command in commands:
        try:
            os.system(command)
        except:
            raise ValueError

        time.sleep(5)

remainig_pips_dict = device.get_remaining_pips_dict()
pbar = tqdm(total=len(remainig_pips_dict))
while remainig_pips_dict:
    l_prev = len(remainig_pips_dict)
    coords = list(remainig_pips_dict.keys())
    coord = coords[0].split('_')[1]
    commands = [f'python3 Compressed_Graph.py {coord}', f'python3 temp.py {coord}', f'python3 Relocate_CUTs.py {coord}']
    for command in commands:
        pbar.set_description(command)
        try:
            os.system(command)
        except:
            raise ValueError

        time.sleep(5)

    remainig_pips_dict = device.get_remaining_pips_dict()
    l_curr = len(remainig_pips_dict)
    pbar.update(l_prev - l_curr)
