import os, re, time, filecmp, sys
import Global_Module as GM
from Functions import load_data, create_folder
from joblib import Parallel, delayed

start_time = time.time()

#TC_file = 'TC0.data'
Data_path = sys.argv[1]
load_path = os.path.join(Data_path, 'Load')
store_path = os.path.join(Data_path, 'Vivado_Sources')
DLOC_path = os.path.join(Data_path, 'DLOC_dicts')
N_Parallel = 50
name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
slices_dict = load_data(load_path, 'clb_site_dict2.data')
create_folder(store_path)
##############################################################
def generate_constrate(TCs_path, TC_file, store_path, N_Parallel, name_prefix, even_odd=''):
    os.system(f'python const_gen.py {TCs_path} {TC_file} {store_path} {N_Parallel} {name_prefix} {even_odd}')

##############################################################
folders = [folder for folder in os.listdir(DLOC_path)]
folders.sort(key=lambda x: int(re.findall('\d+', x)[0]))
while 1:
    file1 = os.path.join(Data_path, 'covered_pips_dict.data')
    file2 = os.path.join(os.path.join(DLOC_path, folders[-1]), 'covered_pips_dict.data')
    if filecmp.cmp(file1, file2):
        TCs_path = os.path.join(DLOC_path, folders[-1])
        break
    else:
        time.sleep(5*60)

with open(os.path.join(Data_path, 'TCs_path.txt'), 'w+') as file:
    file.write(TCs_path)

TC_files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
TC_files.sort(key=lambda x: int(re.findall('\d+', x)[0]))
#tuple1 = (zip(TC_files[:10], ['-e', '-o', '-o', '-e', '', '', '' ,'' ,'' '']))
Parallel(n_jobs=-1)(delayed(generate_constrate)(TCs_path, TC_file, store_path, N_Parallel, name_prefix) for TC_file in TC_files)


print('--- %s seconds ---' %(time.time() - start_time))