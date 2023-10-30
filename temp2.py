import time, os, shutil
from Functions import create_folder
start_time = time.time()

Src_Dir = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data/Vivado_Sources'
Proj_Dir = r'/home/bardia/Desktop/bardia/FPGA_Projects/CPS_Parallel_ZCU9'
Store_path = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data'
DLOC_path = os.path.join(Store_path, 'DLOC_dicts')
load_path = os.path.join(Store_path, 'Load')
result_path = os.path.join(Store_path, 'Results')
Failed_path = os.path.join(Store_path, 'Failed')
create_folder(Failed_path)

TCs = set()
files = ['Errors.txt', 'validation.txt']
for file in files:
    with open(os.path.join(result_path, file)) as txt:
        for line in txt.readlines():
            if line == '\n':
                continue

            TC = line.split(' => ')[0]
            TCs.add(TC)
for TC in TCs:
    src_dir = os.path.join(Src_Dir, TC)
    dest_dir = os.path.join(Failed_path, TC)
    shutil.copytree(src_dir, dest_dir)

N_Parallel = 50
os.system(f'vivado -mode batch -nolog -nojournal -source ./tcl_sources/gen_bit.tcl -tclargs "{Failed_path}" "{Proj_Dir}" "{Store_path}" "0" "{0}" "{N_Parallel}" "custom"')
print('--- %s seconds ---' %(time.time() - start_time))