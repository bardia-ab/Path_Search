from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import Global_Module as GM
from Functions import *
from tqdm import tqdm

start_time = time.time()

origin = 'X46Y90'
tile = f'INT_{origin}'
if origin == 'X46Y90':
    GM.store_path = os.path.join(GM.store_path, 'iter1')
    create_folder(GM.store_path)
else:
    l = len(os.listdir(GM.store_path))
    GM.store_path = os.path.join(GM.store_path, f'iter{l}')
    create_folder(GM.store_path)

device = Arch('ZCU9')
INTs = device.limit(38, 51, 60, 119)
INTs = device.sort_INTs(INTs, tile)

files = sorted(os.listdir(GM.store_path), key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
qbar = tqdm(total=len(files))

for TC_idx, file in enumerate(files):
    TC = Configuration()
    conf = load_data(GM.store_path, file)

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
    store_data(GM.DLOC_path, f'TC{TC_idx}', TC)
    qbar.update(TC_idx)
    qbar.set_description(f'TC{TC_idx}')

store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
print('--- %s seconds ---' %(time.time() - start_time))