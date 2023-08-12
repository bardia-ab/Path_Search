from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import Global_Module as GM
from Functions import *
from tqdm import tqdm
from joblib import Parallel, delayed

start_time = time.time()

origin = 'X45Y90'
tile = f'INT_{origin}'

l = len(os.listdir(GM.store_path))
DLOC_path = os.path.join(GM.DLOC_path, f'iter{l}')
store_path = os.path.join(GM.store_path, f'iter{l}')
create_folder(DLOC_path)
covered_pips_dict = load_data(os.path.join(GM.DLOC_path, f'iter{l-1}'), 'covered_pips_dict.data') if l > 1 else {}
Configuration.covered_pips_dict = covered_pips_dict.copy()

device = Arch('ZCU9')
INTs = device.limit(38, 51, 60, 119)
INTs = device.remove_covered_INTs(l, covered_pips_dict, INTs)
INTs = device.sort_INTs(INTs, tile)

files = sorted(os.listdir(store_path), key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
pbar = tqdm(total=len(files))
#pbar=None

for TC_idx, file in enumerate(files):
    if l == 1:
        TC = Configuration()
    else:
        TC = load_data(os.path.join(GM.DLOC_path, f'iter{l-1}'), f'TC{TC_idx}.data')

    conf = load_data(store_path, file)

    for cut_idx, cut in enumerate(conf.CUTs):
        RLOC_idx = (l - 1) * 16 + cut_idx
        R_CUT = RLOC(cut, RLOC_idx)
        TC.CUTs.append(R_CUT)

        for i, INT in enumerate(INTs):
            coord = INT.name.split('_')[-1]
            D_CUT = DLOC(device, TC, R_CUT, coord)
            if D_CUT.G is None:
                continue

            if TC.add_DLOC_CUT(D_CUT.G):
                R_CUT.origins.add(coord)
                R_CUT.D_CUTs.add(D_CUT)
            else:
                breakpoint()

    #print(f'TC{TC_idx} => {time.time() - start_time}')
    TC.set_blocked_invalid_primitives()
    TC.CD = conf.CD.copy()
    #covered_pips_dict = TC.covered_pips_dict.copy()
    store_data(DLOC_path, f'TC{TC_idx}.data', TC)
    pbar.update(1)
    pbar.set_description(f'TC{TC_idx}')


Configuration.sort_covered_pips(38, 51, 60, 119)
store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
store_data(DLOC_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
#print('--- %s seconds ---' %(time.time() - start_time))