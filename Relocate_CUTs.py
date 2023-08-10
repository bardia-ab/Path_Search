from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import Global_Module as GM
from Functions import *
from tqdm import tqdm
from joblib import Parallel, delayed

start_time = time.time()

origin = 'X46Y90'
tile = f'INT_{origin}'

l = len(os.listdir(GM.store_path))
GM.DLOC_path = os.path.join(GM.DLOC_path, f'iter{l}')
store_path = os.path.join(GM.store_path, f'iter{l}')
create_folder(GM.DLOC_path)

device = Arch('ZCU9')
INTs = device.limit(38, 51, 60, 119)
INTs = device.sort_INTs(INTs, tile)

files = sorted(os.listdir(store_path), key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
pbar = tqdm(total=len(files))
#pbar=None

for TC_idx, file in enumerate(files):
    TC = Configuration()
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

    #print(f'TC{TC_idx} => {time.time() - start_time}')
    store_data(GM.DLOC_path, f'TC{TC_idx}.data', TC)
    pbar.update(TC_idx)
    pbar.set_description(f'TC{TC_idx}')


TC.sort_covered_pips(38, 51, 60, 119)
store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
print('--- %s seconds ---' %(time.time() - start_time))