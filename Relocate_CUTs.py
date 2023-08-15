from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import Global_Module as GM
from Functions import *
from tqdm import tqdm
from joblib import Parallel, delayed
import shutil

start_time = time.time()

origin = sys.argv[1]
#origin = 'X51Y119'
tile = f'INT_{origin}'

l = len(os.listdir(GM.store_path))
DLOC_path = os.path.join(GM.DLOC_path, f'iter{l}')
store_path = os.path.join(GM.store_path, f'iter{l}')
create_folder(DLOC_path)
covered_pips_dict = load_data(os.path.join(GM.DLOC_path, f'iter{l-1}'), 'covered_pips_dict.data') if l > 1 else {}
Configuration.covered_pips_dict = covered_pips_dict.copy()

device = Arch('ZCU9')
INTs = device.limit(38, 51, 60, 119) if l == 1 else device.remove_covered_INTs()
INTs = device.sort_INTs(INTs, tile)

files = sorted(os.listdir(store_path), key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
pbar = tqdm(total=len(files))
#pbar=None

for idx, file in enumerate(files):
    TC_idx = int(re.search('\d+', file)[0])
    if l == 1:
        TC = Configuration()
    else:
        TC = load_data(os.path.join(GM.DLOC_path, f'iter{l-1}'), f'TC{TC_idx}.data')

    conf = load_data(store_path, file)

    R_CUTs = []
    for cut_idx, cut in enumerate(conf.CUTs):
        RLOC_idx = (l - 1) * 16 + cut_idx
        R_CUT = RLOC(cut, RLOC_idx)
        TC.CUTs.append(R_CUT)
        R_CUTs.append(R_CUT)

        D_CUT = DLOC(device, TC, R_CUT, origin)
        if D_CUT.G is None:
            breakpoint()

        TC.add_DLOC_CUT(D_CUT.G)
        R_CUT.origins.add(origin)
        R_CUT.D_CUTs.add(D_CUT)

    for R_CUT in R_CUTs:
        for i, INT in enumerate(INTs[1:]):
            coord = INT.name.split('_')[-1]
            D_CUT = DLOC(device, TC, R_CUT, coord)
            if D_CUT.G is None:
                continue

            TC.add_DLOC_CUT(D_CUT.G)
            R_CUT.origins.add(coord)
            R_CUT.D_CUTs.add(D_CUT)

    TC.set_blocked_invalid_primitives()
    TC.CD = conf.CD.copy()
    store_data(DLOC_path, f'TC{TC_idx}.data', TC)
    pbar.update(1)
    pbar.set_description(f'TC{TC_idx}')


Configuration.sort_covered_pips(38, 51, 60, 119)
store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
store_data(DLOC_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)

if l > 1:
    DLOC_path_old = os.path.join(GM.DLOC_path, f'iter{l-1}')
    missing_files = set(os.listdir(DLOC_path_old)) - set(os.listdir(DLOC_path))
    for file in missing_files:
        src = os.path.join(DLOC_path_old, file)
        dst = os.path.join(DLOC_path, file)
        shutil.copy(src, dst)

print('\n--- %s seconds ---' %(time.time() - start_time))