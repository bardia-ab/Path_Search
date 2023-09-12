import os, time, schedule
import Global_Module as GM
from Functions import create_folder

def job():
    create_folder(os.path.join(GM.Data_path, 'Bitstreams'))
    create_folder(os.path.join(GM.Data_path, 'DCPs'))
    N_TCs = len(os.listdir(os.path.join(GM.DLOC_path, 'iter1')))
    os.system(f'python3 const_rtl.py')
    os.system(f'vivado -mode batch -source /home/bardia/Downloads/gen_bit.tcl -tclargs "{N_TCs}"')
    files = filter(lambda x: x.startswith('vivado'), os.listdir(os.getcwd()))
    for file in files:
        os.remove(file)

schedule.every().friday.at('23:30').do(job)

while True:
    schedule.run_pending()
    time.sleep(1)