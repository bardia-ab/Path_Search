import os, time, schedule
import Global_Module as GM
from Functions import create_folder, load_data
from resources.constraint import gen_rtl

def job():
    Src_Dir = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data/Vivado_Sources'
    Proj_Dir = r'/home/bardia/Desktop/bardia/FPGA_Projects/CPS_Parallel_ZCU9'
    Store_path = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data'
    N_Parallel = 50
    create_folder(os.path.join(GM.Data_path, 'Bitstreams'))
    create_folder(os.path.join(GM.Data_path, 'DCPs'))
    os.system(f'python3 const_gen_wrapper.py')
    with open(os.path.join(GM.Data_path, 'TCs_path.txt')) as file:
        TCs_path = file.read().rstrip('\n')

    N_TCs = len(os.listdir(TCs_path))
    os.system(f'''vivado -mode batch -nolog -nojournal -source ./tcl_sources/gen_bit.tcl -tclargs 
    "{Src_Dir}" "{Proj_Dir}" "{Store_path}" "0" "{N_TCs}" "{N_Parallel}" "None"''')
    files = filter(lambda x: x.startswith('vivado'), os.listdir(os.getcwd()))
    for file in files:
        os.remove(file)

    #########################################
    name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
    slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')

    files = {file for file in os.listdir(os.path.join(GM.Data_path, 'Bitstreams'))}
    failed_TCs = {file for file in os.listdir(os.path.join(GM.DLOC_path, 'iter1')) if file.startswith('TC') if
                  f"{file.split('.')[0]}.bit" not in files}
    store_path = os.path.join(GM.Data_path, 'Vivado_Sources')
    for TC_file in failed_TCs:
        gen_rtl(TC_file, TCs_path, store_path, N_Parallel, name_prefix, slices_dict, even_odd='even')
        gen_rtl(TC_file, TCs_path, store_path, N_Parallel, name_prefix, slices_dict, even_odd='odd')

    os.system(
        f'vivado -mode batch -nolog -nojournal -source /home/bardia/Downloads/gen_bit.tcl -tclargs "0" "{N_TCs}" "{N_Parallel}" "even"')
    files = filter(lambda x: x.startswith('vivado'), os.listdir(os.getcwd()))
    for file in files:
        os.remove(file)

schedule.every().tuesday.at('23:30').do(job)

while True:
    schedule.run_pending()
    time.sleep(1)