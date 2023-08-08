from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import Global_Module as GM
from Functions import *

start_time = time.time()

origin = 'X46Y90'
tile = f'INT_{origin}'
l = len(os.listdir(GM.store_path))
GM.store_path = os.path.join(GM.store_path, f'iter{l}')
GM.DLOC_path = os.path.join(GM.DLOC_path, f'iter{l}')
#create_folder(GM.DLOC_path)


device = Arch('ZCU9')
INTs = device.limit(38, 51, 60, 119)
INTs = device.sort_INTs(INTs, tile)

files = sorted(os.listdir(GM.store_path), key= lambda x: int(re.findall('\d+', x).pop()), reverse=False)
for TC_idx, file in enumerate(files):
    TC = Configuration()
    conf = load_data(GM.store_path, file)
    conf.CUTs = [cut for cut in conf.CUTs if len(cut.paths) == 3]

    for cut_idx, cut in enumerate(conf.CUTs):
        RLOC_idx = (l - 1) * 16 + cut_idx
        R_CUT = RLOC(cut, RLOC_idx)
        TC.CUTs.append(R_CUT)
        for i, INT in enumerate(INTs):
            coord = INT.name.split('_')[-1]
            #DLOC_G = R_CUT.get_DLOC_G(device, coord)
            D_CUT = DLOC(device, TC, R_CUT, coord)
            #if DLOC_G is None:
            if D_CUT.G is None:
                continue

            #if TC.add_DLOC_CUT(DLOC_G):
            if TC.add_DLOC_CUT(D_CUT.G):
                R_CUT.origins.add(coord)
                R_CUT.D_CUTs.add(D_CUT)


    print(f'TC{TC_idx} => {time.time() - start_time}')

store_data(GM.Data_path, 'covered_pips_dict.data', Configuration.covered_pips_dict)
print('--- %s seconds ---' %(time.time() - start_time))