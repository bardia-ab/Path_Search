import os, time, re
import Global_Module as GM
from Functions import load_data, store_data
from resources.constraint import split_D_CUTs

start_time = time.time()
TCs_path = os.path.join(GM.DLOC_path, 'iter32')
TC_files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
for TC_file in TC_files:
    TC = load_data(TCs_path, TC_file)
    D_CUT_even, D_CUT_odd = split_D_CUTs(TC, 'FF_in_index')
    print(f'Even= {len(D_CUT_even)}\tOdd= {len(D_CUT_odd)}')


print('\n--- %s seconds ---' %(time.time() - start_time))