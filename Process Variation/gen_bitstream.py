from Functions import create_folder
from relocation.clock_region import CR
import os, time, re
import schedule


def get_x_coord(tile):
    return int(re.findall('-*\d+', tile)[0])

def job():
    start_time = time.time()
    ###########################################
    Work_Dir = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg'
    Src_Dir = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/Vivado_Sources_local'
    Proj_Dir = r'/home/bardia/Desktop/bardia/FPGA_Projects/CPS_Parallel_ZCU9'
    N_Parallel = 50
    bitstream_path = os.path.join(Work_Dir, 'Bitstreams')
    DCP_path = os.path.join(Work_Dir, 'DCPs')
    log_path = os.path.join(Work_Dir, 'Logs')
    ###########################################
    create_folder(bitstream_path)
    create_folder(DCP_path)
    create_folder(log_path)

    CRs = list(os.listdir(Src_Dir))
    CRs.sort(key=lambda x: (abs(CR.get_y_coord(x) - 3), 6 - CR.get_y_coord(x), CR.get_x_coord(x)), reverse=True)
    for cr in CRs:
        CR_Dir = os.path.join(Src_Dir, cr)
        N_TCs = len(list(os.listdir(CR_Dir)))
        start_index = 0
        create_folder(os.path.join(bitstream_path, cr))
        create_folder(os.path.join(DCP_path, cr))
        create_folder(os.path.join(log_path, cr))
        os.system(
            f'vivado -mode batch -nolog -nojournal -source ./gen_bit.tcl -tclargs "{CR_Dir}" "{Proj_Dir}" "{Work_Dir}" "{cr}" "{start_index}" "{N_TCs}" "{N_Parallel}" "None"')

    print(f'--- {time.time() - start_time} seconds ---')

def job_2():
    start_time = time.time()
    ###########################################
    Work_Dir = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg'
    Src_Dir = r'/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/Vivado_Sources_local'
    Proj_Dir = r'/home/bardia/Desktop/bardia/FPGA_Projects/CPS_Parallel_ZCU9'
    N_Parallel = 50
    bitstream_path = os.path.join(Work_Dir, 'Bitstreams')
    DCP_path = os.path.join(Work_Dir, 'DCPs')
    log_path = os.path.join(Work_Dir, 'Logs')
    ###########################################
    CRs = list(os.listdir(Src_Dir))
    for CR in CRs:
        CR_Dir = os.path.join(Src_Dir, CR)
        if 'Split_Sources' not in os.listdir(CR_Dir):
            continue

        CR_Dir = os.path.join(CR_Dir, 'Split_Sources')
        N_TCs = len(list(os.listdir(CR_Dir)))
        bitstream_CR_path = os.path.join(bitstream_path, CR)
        DCP_CR_path = os.path.join(DCP_path, CR)
        log_CR_path = os.path.join(log_path, CR)
        #create_folder(os.path.join(bitstream_CR_path, 'Split_Bitstreams'))
        #create_folder(os.path.join(DCP_CR_path, 'Split_DCPs'))
        #create_folder(os.path.join(log_CR_path, 'Split_Logs'))
        os.system(
            f'vivado -mode batch -nolog -nojournal -source ./gen_bit.tcl -tclargs "{CR_Dir}" "{Proj_Dir}" "{Work_Dir}" "{CR}" "0" "{N_TCs}" "{N_Parallel}" "custom"')

    print(f'--- {time.time() - start_time} seconds ---')

'''while True:
    schedule.every().thursday.at('20:00').do(job)
    time.sleep(1)'''

job()  # original bitstreams
#job_2() # failed bitstreams