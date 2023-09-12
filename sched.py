import os, time, schedule
import Global_Module as GM
from Functions import create_folder, load_data
from resources.constraint import gen_rtl

def job():
    create_folder(os.path.join(GM.Data_path, 'Bitstreams'))
    create_folder(os.path.join(GM.Data_path, 'DCPs'))
    N_TCs = len(os.listdir(os.path.join(GM.DLOC_path, 'iter1')))
    os.system(f'python3 const_rtl.py')
    os.system(f'vivado -mode batch -source /home/bardia/Downloads/gen_bit.tcl -tclargs "0" "{N_TCs}" "None"')
    files = filter(lambda x: x.startswith('vivado'), os.listdir(os.getcwd()))
    for file in files:
        os.remove(file)

    #########################################
    N_Parallel = 50
    name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
    slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')
    with open(os.path.join(GM.Data_path, 'TCs_path.txt')) as file:
        TCs_path = file.read()

    files = {file for file in os.listdir(os.path.join(GM.DLOC_path, 'iter1')) if file.startswith('TC')}
    failed_TCs = {file for file in os.listdir(os.path.join(GM.Data_path, 'Bitstreams')) if file not in files}
    for TC_file in failed_TCs:
        gen_rtl(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict, even_odd='even')
        gen_rtl(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict, even_odd='odd')

schedule.every().friday.at('23:30').do(job)

while True:
    schedule.run_pending()
    time.sleep(1)