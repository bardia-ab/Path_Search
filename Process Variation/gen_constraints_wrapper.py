from relocation.configuration import Configuration
from relocation.arch_graph import Arch
from resources.constraint import VHDL, split_function, Cell, get_instantiation
from Functions import load_data, store_data, create_folder
import os, time, re
from math import ceil
from tqdm import tqdm
from joblib import Parallel, delayed

start_time = time.time()
###########
def create_VHDL_tempelate():
    VHDL_file = VHDL('CUTs', 'behavioral')
    VHDL_file.add_package('ieee', 'std_logic_1164')
    VHDL_file.add_package('work', 'my_package')
    VHDL_file.add_generic('g_N_Segments', 'integer')
    VHDL_file.add_generic('g_N_Parallel', 'integer')
    VHDL_file.add_port('i_Clk_Launch', 'in', 'std_logic')
    VHDL_file.add_port('i_Clk_Sample', 'in', 'std_logic')
    VHDL_file.add_port('i_CE', 'in', 'std_logic')
    VHDL_file.add_port('i_CLR', 'in', 'std_logic')
    VHDL_file.add_port('o_Error', 'out', 'my_array')
    VHDL_file.add_signal('w_Error', 'my_array(0 to g_N_Segments - 1)(g_N_Parallel - 1 downto 0)',
                         "(others => (others => '0'))")
    VHDL_file.add_assignment('o_Error', 'w_Error')

    return VHDL_file

def fill_VHDL(TC, D_CUTs, slices_dict, VHDL_file, N_Parallel, name_prefix, vivado_src_path):
    Cell.cells = []
    N_Segments = ceil(len(D_CUTs) / N_Parallel)
    N_Partial = len(D_CUTs) % N_Parallel
    routing_constraints = []
    for idx, D_CUT in enumerate(D_CUTs):
        CUT_idx = idx % N_Parallel
        Seg_idx = idx // N_Parallel
        w_Error_Mux_In = f'w_Error({Seg_idx})({CUT_idx})'

        launch_FF_cell_name = name_prefix.format(idx, 'launch_FF')
        sample_FF_cell_name = name_prefix.format(idx, 'sample_FF')
        not_LUT_cell_name = name_prefix.format(idx, 'not_LUT')
        launch_net = name_prefix.format(idx, 'Q_launch_int')

        D_CUT_cells = Cell.get_D_CUT_cells(TC, slices_dict, D_CUT, True)
        launch_FF = Cell('FF', D_CUT_cells['launch_FF'][0], D_CUT_cells['launch_FF'][1], launch_FF_cell_name)
        sample_FF = Cell('FF', D_CUT_cells['sample_FF'][0], D_CUT_cells['sample_FF'][1], sample_FF_cell_name)
        not_LUT = Cell('LUT', D_CUT_cells['not_LUT'][0], D_CUT_cells['not_LUT'][1], not_LUT_cell_name)
        not_LUT.inputs = D_CUT_cells['not_LUT'][2]

        g_Buffer = D_CUT.get_g_buffer()
        if g_Buffer == "00":
            route_thru_net = None
        else:
            buff_LUT_cell_name = name_prefix.format(idx, 'Buff_Gen.buffer_LUT')
            buffer_LUT = Cell('LUT', D_CUT_cells['buff_LUT'][0][0], D_CUT_cells['buff_LUT'][0][1], buff_LUT_cell_name)
            buffer_LUT.inputs = D_CUT_cells['buff_LUT'][0][2]
            route_thru_net = name_prefix.format(idx, 'Route_Thru')

        VHDL_file.add_components(
            ''.join(get_instantiation(idx, 'i_Clk_Launch', 'i_Clk_Sample', 'i_CE', 'i_CLR', w_Error_Mux_In, g_Buffer)))
        routing_constraints.extend(D_CUT.get_routing_constraint(launch_net, route_thru_net))

    cell_constraints = Cell.get_cell_constraints()

    with open(os.path.join(vivado_src_path, 'stats.txt'), 'w+') as file:
        if N_Partial > 0:
            file.write(f'N_Segments = {N_Segments - 1}\n')
        else:
            file.write(f'N_Segments = {N_Segments}\n')

        file.write(f'N_Partial = {N_Partial}')

    with open(os.path.join(vivado_src_path, 'physical_constraints.xdc'), 'w+') as file:
        file.writelines(cell_constraints)
        file.write('\n')
        file.writelines(routing_constraints)

    VHDL_file.print(os.path.join(vivado_src_path, 'CUTs.vhd'))

def gen_CR_TC_sources(CR, DLOC_path, TC_file, opts, vivado_src_path, N_Parallel, name_prefix):
    TC = load_data(DLOC_path, TC_file)
    TC_idx = TC_file.split('.')[0]
    vivado_src_path = os.path.join(vivado_src_path, CR.name)
    slices_dict = load_data('/home/bardia/Desktop/bardia/Timing_Characterization/Data_local/Load', 'clb_site_dict2.data')
    VHDL_file = create_VHDL_tempelate()
    CR_coords = CR.get_coordinates()
    D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs if D_CUT.origin in CR_coords]
    if opts == '-e':
        D_CUTs = [D_CUT for D_CUT in D_CUTs if split_function(D_CUT, 'FF_in_index') == 0]
        TC_idx = TC_idx + 'even'
    elif opts == '-o':
        D_CUTs = [D_CUT for D_CUT in D_CUTs if split_function(D_CUT, 'FF_in_index') == 1]
        TC_idx = TC_idx + 'odd'

    store_path = os.path.join(vivado_src_path, TC_idx)
    create_folder(store_path)

    if opts:
        try:
            store_data(store_path, 'D_CUTs.data', D_CUTs)
        except:
            exit()

    D_CUTs.sort(key=lambda x: (x.index, x.get_x_coord(x.origin), x.get_y_coord(x.origin)))
    fill_VHDL(TC, D_CUTs, slices_dict, VHDL_file, N_Parallel, name_prefix, store_path)

###########
opts= []
N_Parallel = 50
name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
DLOC_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/split_TCs'
store_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data_xczu9eg/Vivado_Sources_local'
create_folder(store_path)
###########

device =Arch('ZCU9')
'''TC_files = [file for file in os.listdir(DLOC_path) if file.startswith('TC')]
TC_files.sort(key=lambda x: int(re.findall('\d+', x)[0]))'''
pbar = tqdm(total=len(device.get_CRs()))

for CR in device.get_CRs():
    create_folder(os.path.join(store_path, CR.name))
    DLOC_path_CR = os.path.join(DLOC_path, CR.name)
    TC_files = [file for file in os.listdir(DLOC_path_CR) if file.startswith('TC')]
    #gen_CR_TC_sources(CR, DLOC_path_CR, TC_files[0], opts, store_path, N_Parallel, name_prefix)
    Parallel(n_jobs=-1)(delayed(gen_CR_TC_sources)(CR, DLOC_path_CR, TC_file, opts, store_path, N_Parallel, name_prefix) for TC_file in TC_files)
    #for TC_file in TC_files:
        #gen_CR_TC_sources(CR, DLOC_path_CR, TC_file, opts, store_path, N_Parallel, name_prefix)

    pbar.update(1)


print(f'--- {time.time() - start_time} seconds ---')