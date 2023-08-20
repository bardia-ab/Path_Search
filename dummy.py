import os, re, time
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict, get_tile ,get_port
from relocation.arch_graph import Arch
from relocation.clock_region import CR
from relocation.configuration import Configuration
from relocation.relative_location import RLOC
import resources.constraint as const
from resources.edge import Edge
from tqdm import tqdm
from joblib import Parallel, delayed
from itertools import chain


start_time = time.time()

device = Arch('ZCU9')
TCs_path = os.path.join(GM.DLOC_path, 'iter24')
files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
files = sorted(files, key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)

src_tiles = set(chain(*Parallel(n_jobs=-1)(delayed(const.get_src_sink_tiles)(TCs_path, file, GM.FF_out_pattern) for file in files)))
sink_tiles = set(chain(*Parallel(n_jobs=-1)(delayed(const.get_src_sink_tiles)(TCs_path, file, GM.FF_in_pattern) for file in files)))

files, Init_TC_file = const.get_Init_TC(TCs_path)
Init_TC = load_data(TCs_path, Init_TC_file)
Init_src_tiles = {f'INT_{const.get_coordinate(get_tile(ff[0]))}' for key, ff in Init_TC.FFs.items() if re.match(GM.FF_out_pattern, ff[0])}
Init_sink_tiles = {f'INT_{const.get_coordinate(get_tile(ff[0]))}' for key, ff in Init_TC.FFs.items() if re.match(GM.FF_in_pattern, ff[0])}

dummy_src_tiles = src_tiles - Init_src_tiles
dummy_sink_tiles = sink_tiles - Init_sink_tiles
#store_data(GM.load_path, 'dummy_src_tiles.data', dummy_src_tiles)
#store_data(GM.load_path, 'dummy_sink_tiles.data', dummy_sink_tiles)

slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')
net_name = 'design_1_i/top_0/U0/Dummy_Srcs[{}].launch_FF'
dummy_src_constraints = []
idx = 0
l_dummy_tuple = set()
for tile in dummy_src_tiles:
    for key, value in device.tiles_map[const.get_coordinate(tile)].items():
        if value is None or key == 'INT':
            continue

        direction = key.split('_')[-1]
        top_bottom = [k for k, v in Init_TC.CD.items() if (v == 'launch' and k.startswith(direction))][0][-1]
        bel = 'AFF' if top_bottom == 'B' else 'EFF'
        loc = slices_dict[value]
        l_dummy_tuple.add((bel, loc))
        dummy_src_constraints.append(f'set_property BEL {bel} [get_cells {net_name.format(idx)}]\n')
        dummy_src_constraints.append(f'set_property LOC {loc} [get_cells {net_name.format(idx)}]\n')
        idx += 1

net_name = 'design_1_i/top_0/U0/Dummy_Sinks[{}].sample_FF'
dummy_sink_constraints = []
idx = 0
s_dummy_tuple = set()
for tile in dummy_sink_tiles:
    for key, value in device.tiles_map[const.get_coordinate(tile)].items():
        if value is None or key == 'INT':
            continue

        direction = key.split('_')[-1]
        top_bottom = [k for k, v in Init_TC.CD.items() if (v == 'sample' and k.startswith(direction))][0][-1]
        bel = 'AFF' if top_bottom == 'B' else 'EFF'
        loc = slices_dict[value]
        s_dummy_tuple.add((bel, loc))
        dummy_sink_constraints.append(f'set_property BEL {bel} [get_cells {net_name.format(idx)}]\n')
        dummy_sink_constraints.append(f'set_property LOC {loc} [get_cells {net_name.format(idx)}]\n')
        idx += 1

with open(os.path.join(GM.Data_path, 'XDC/dummy_srcs.xdc'), 'w+') as file:
    file.writelines(dummy_src_constraints)

with open(os.path.join(GM.Data_path, 'XDC/dummy_sinks.xdc'), 'w+') as file:
    file.writelines(dummy_sink_constraints)

store_data(GM.Data_path, 's_dummy_tuple.data', s_dummy_tuple)
store_data(GM.Data_path, 'l_dummy_tuple.data', l_dummy_tuple)
print(f'Dummy Source FFs: {len(dummy_src_constraints)//2}')
print(f'Dummy Sink FFs: {len(dummy_sink_constraints)//2}')
print('--- %s seconds ---' %(time.time() - start_time))