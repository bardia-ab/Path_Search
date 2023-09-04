import time, os, re
import resources.validation as vd
import Global_Module as GM
from Functions import load_data
from tqdm import tqdm
import concurrent.futures
from itertools import product

#####################################
def func1(file):
    TC_idx = int(re.search('\d+', file)[0])
    #pbar.set_description(f'{TC_idx}')
    TC = load_data(os.path.join(GM.DLOC_path, f'iter{l}'), f'TC{TC_idx}.data')
    result, invalid_keys = vd.check_DCUT_LUT_utel(TC)
    if result:  # LUT overutelization
        #breakpoint()
        print(TC_idx)

    #pbar.update(1)
#####################################

start_time = time.time()
l = 2
store_path = os.path.join(GM.store_path, f'iter{l}')
files = sorted(os.listdir(store_path), key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
files = [file for file in files if int(re.search('\d+', file)[0]) in {96, 106, 108, 110, 121, 123, 122, 130}]

with concurrent.futures.ProcessPoolExecutor() as executor:
    executor.map(func1, files)

print('\n--- %s seconds ---' %(time.time() - start_time))