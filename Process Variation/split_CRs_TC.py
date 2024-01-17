from relocation.configuration import Configuration
from relocation.arch_graph import Arch
from Functions import load_data, store_data, create_folder
import os, time, re
from tqdm import tqdm
from joblib import Parallel, delayed
import multiprocessing, threading
start_time = time.time()
#######################################
def get_coordinate(node):
    return re.findall('X-*\d+Y-*\d+', node)[0]

def split(DLOC_path, TC_file, store_path, CR: str):
    TC = load_data(DLOC_path, TC_file)
    for i in range(len(TC.CUTs)):
        TC.CUTs[i].D_CUTs = [D_CUT for D_CUT in TC.CUTs[i].D_CUTs if D_CUT.origin in CR_coords]

    #TC.LUTs = {k:v for k, v in TC.LUTs.items() if get_coordinate(k) in CR_coords}
    #TC.FFs = {k: v for k, v in TC.FFs.items() if get_coordinate(k) in CR_coords}
    del TC.used_nodes_dict
    del TC.blocked_LUTs
    del TC.invalid_source_FFs
    del TC.CD

    store_data(os.path.join(store_path, CR), TC_file, TC)

#######################################
DLOC_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/DLOC_local/iter1'
store_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/split_TCs'
create_folder(store_path)
device =Arch('ZCU9')

TC_files = [file for file in os.listdir(DLOC_path) if file.startswith('TC')]
TC_files.sort(key=lambda x: int(re.findall('\d+', x)[0]))
pbar = tqdm(total=len(device.get_CRs()))

for CR in device.get_CRs():
    create_folder(os.path.join(store_path, CR.name))
    CR_coords = CR.get_coordinates()
    #split(DLOC_path, TC_files[0], store_path, CR.name)
    Parallel(n_jobs=-1)(delayed(split)(DLOC_path, TC_file, store_path, CR.name) for TC_file in TC_files)
    pbar.update(1)

print(f'--- {time.time() - start_time} seconds ---')