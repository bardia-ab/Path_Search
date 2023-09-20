import time, os
from resources.constraint import gen_rtl
from Functions import load_data

start_time = time.time()
Data_path = '/home/bardia/Desktop/bardia/Timing_Characterization/CR_X2Y1'
load_path = os.path.join(Data_path, 'Load')
results_path = os.path.join(Data_path, 'Results')

invalid_TCs = set()
with open(os.path.join(results_path, 'validation.txt')) as lines:
    for line in lines:
        invalid_TCs.add(line.split(' => ')[0])

#with open(os.path.join(Data_path, 'TCs_path.txt')) as file:
    #TCs_path = file.read().rstrip('\n')

TCs_path = '/home/bardia/Desktop/bardia/Timing_Characterization/CR_X2Y1/DLOC_dicts/iter48'

name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
slices_dict = load_data(load_path, 'clb_site_dict2.data')
N_Parallel = 50
for TC_file in invalid_TCs:
    TC_file = f'{TC_file}.data'
    gen_rtl(TC_file, TCs_path, Data_path, N_Parallel, name_prefix, slices_dict, even_odd='even')
    gen_rtl(TC_file, TCs_path, Data_path, N_Parallel, name_prefix, slices_dict, even_odd='odd')

print('--- %s seconds ---' %(time.time() - start_time))