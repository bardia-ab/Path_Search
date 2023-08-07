from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC
import Global_Module as GM
from Functions import *

start_time = time.time()

l = len(os.listdir(GM.store_path))
GM.store_path = os.path.join(GM.store_path, f'iter{l}')
GM.DLOC_path = os.path.join(GM.DLOC_path, f'iter{l}')
#create_folder(GM.DLOC_path)
TC0 = load_data(GM.store_path, 'TC0.data')
origin = TC0.CUTs[0].origin
tile = f'INT_{origin}'
del TC0

device = Arch('ZCU9')
device.limit(30, 60, 75, 115)
device.sort_INTs(tile)

files = sorted(os.listdir(GM.store_path), key= lambda x: int(re.findall('\d+', x).pop()), reverse=False)
for TC_idx, file in enumerate(files):
    TC = Configuration()
    conf = load_data(GM.store_path, file)

    for cut_idx, cut in enumerate(conf.CUTs):
        RLOC_idx = (l - 1) * 16 + cut_idx
        R_CUT = RLOC(cut, RLOC_idx)
        TC.CUTs.append(R_CUT)
        for i, INT in enumerate(device.INTs):
            coord = INT.name.split('_')[-1]
            DLOC_G = R_CUT.get_DLOC_G(device, coord)
            if DLOC_G is None:
                continue

            if TC.add_DLOC_CUT(DLOC_G):
                R_CUT.origins.add(coord)


    print(f'TC{TC_idx} => {time.time() - start_time}')

store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
print('--- %s seconds ---' %(time.time() - start_time))