import os, time
from tqdm import tqdm
from relocation.arch_graph import Arch

device = Arch('ZCU9')
remainig_pips_dict = device.get_remaining_pips_dict()
pbar = tqdm(total=len(remainig_pips_dict))
l_prev = len(remainig_pips_dict)
while remainig_pips_dict:
    coords = list(remainig_pips_dict.keys())
    coord = coords[0].split('_')[1]
    commands = [f'python Compressed_Graph.py {coord}', f'python temp.py {coord}', f'python Relocate_CUTs.py {coord}']
    for command in commands:
        pbar.set_description(command)
        os.system(command)
        time.sleep(10)
        remainig_pips_dict = device.get_remaining_pips_dict()
        l_curr = len(remainig_pips_dict)
        pbar.update(l_curr - l_prev)
