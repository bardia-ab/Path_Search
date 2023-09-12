import re, os, math
from Functions import load_data, create_folder
import networkx as nx
from joblib import Parallel, delayed
from resources.rtl import *
from relocation.relative_location import DLOC

from resources.edge import Edge
from resources.path import Path
from resources.cut import CUT
from resources.primitive import *
import Global_Module as GM

def get_tile (wire, delimiter='/'):
    return wire.split(delimiter)[0]

def get_port (wire, delimiter='/'):
    return wire.split(delimiter)[1]

def get_direction(clb_node):
    if clb_node.startswith('CLEL_R'):
        dir = 'E'
    else:
        dir = 'W'

    return dir

def get_coordinate(tile):
    return re.findall('X-*\d+Y-*\d+', tile)[0]

def get_pip_FASM(*pips, mode=None):
    value = {'set': 1, 'clear': 0, None:'{}'}
    exception = [
        ('INT_NODE_IMUX_18_INT_OUT0', 'BYPASS_E14'),
        ('INT_NODE_IMUX_37_INT_OUT0', 'BYPASS_W8'),
        ('INT_NODE_IMUX_50_INT_OUT0', 'BYPASS_W14'),
        ('INT_NODE_IMUX_5_INT_OUT0','BYPASS_E8')
    ]
    FASM_list = []
    for pip in pips:
        if (pip.u_port, pip.v_port) in exception:
            suffix = '.REV'
        elif (pip.v_port, pip.u_port) in exception:
            suffix = '.FWD'
        else:
            suffix = ''

        FASM_list.append(f'{pip.u_tile}.PIP.{pip.v_port}.{pip.u_port}{suffix} = {value[mode]}\n')

    return FASM_list

def get_CLB_FASM2(device, TC, path: Path, clk):
    configurations = set()
    FF_pins_dct = {
        'C'     :   {'B': 'CTRL_{}4', 'T': 'CTRL_{}5'},
        'SR'    :   {'B': 'CTRL_{}6', 'T': 'CTRL_{}7'},
        'CE'    :   {'B': 'CTRL_{}0', 'T': 'CTRL_{}2'},
        'CE2'   :   {'B': 'CTRL_{}1', 'T': 'CTRL_{}3'}
    }
    i6_dct = {
        'A' : 'IMUX_{}18',
        'B' : 'IMUX_{}19',
        'C' : 'IMUX_{}20',
        'D' : 'IMUX_{}21',
        'E' : 'IMUX_{}34',
        'F' : 'IMUX_{}35',
        'G' : 'IMUX_{}46',
        'H' : 'IMUX_{}47'
    }

    ffs = {node for node in path.nodes if node.clb_node_type=='FF_out'}
    for ff in ffs:
        CE_key = 'CE2' if ff.index == 2 else 'CE'
        FFMUX = f'FFMUX{ff.bel}{ff.index}'
        tile = f'INT_{ff.coordinate}'
        C = FF_pins_dct['C'][ff.bel_group[-1]].format(ff.bel_group[0])
        C = f'{tile}/{C}'
        SR = FF_pins_dct['SR'][ff.bel_group[-1]].format(ff.bel_group[0])
        CE = FF_pins_dct[CE_key][ff.bel_group[-1]].format(ff.bel_group[0])

        path_index = path.nodes.index(ff)
        if path.nodes[path_index-1].clb_node_type == 'FF_in':
            FFMUX_pin = 'BYP'
        else:                                       # LUT_in
            LUT_in = path.nodes[path_index-1]
            if LUT_in.is_i6:
                FFMUX_pin = 'D6'
            else:
                subLUTs = TC.get_LUTs(tile=LUT_in.tile, letter=LUT_in.bel)
                subLUT = {lut for lut in subLUTs if LUT_in.name in lut.inputs}.pop()
                FFMUX_pin = f'D{subLUT.LUT_type[0]}'


        configurations.add(f'{tile}.PIP.{SR}.VCC_WIRE = 1\n')
        configurations.add(f'{tile}.PIP.{CE}.VCC_WIRE = 1\n')
        configurations.add(f'{ff.tile}.{FFMUX}.{FFMUX_pin} = 1\n')
        ### Find path from the clock pin to C
        clk = f'{tile}/{clk}'
        clk_path = nx.shortest_path(TC.G, clk, C)
        clk_path = Path(device, TC, clk_path)
        configurations.update(get_pip_FASM(*clk_path.pips, mode='set'))
        ######
    used_LUTs = LUT.integrate(*TC.get_LUTs(usage='used'))
    for lut in used_LUTs:
        tile = f'INT_{lut.coordinate}'
        i6_port = i6_dct[lut.letter].format(lut.direction)
        configurations.add(f'{tile}.PIP.{i6_port}.VCC_WIRE = 1\n')
        configurations.add(f'{lut.tile}.{lut.bel}.INIT[63:0] = {lut.init}\n')

    clb_muxes = [node for node in path.nodes if node.clb_node_type == 'CLB_muxed']
    for clb_mux in clb_muxes:
        OUTMUX = f'OUTMUX{clb_mux.bel}'
        path_index = path.nodes.index(clb_mux)
        LUT_in = path.nodes[path_index - 1]
        if LUT_in.is_i6:
            OUTMUX_pin = 'D6'
        else:
            subLUTs = TC.get_LUTs(tile=LUT_in.tile, letter=LUT_in.bel)
            subLUT = {lut for lut in subLUTs if LUT_in.name in lut.inputs}.pop()
            OUTMUX_pin = f'D{subLUT.LUT_type[0]}'

        configurations.add(f'{clb_mux.tile}.{OUTMUX}.{OUTMUX_pin} = 1\n')

    return configurations

def get_FFs_FASM(device, TC):
    configurations = set()
    FF_pins_dct = {
        'C': {'B': 'CTRL_{}4', 'T': 'CTRL_{}5'},
        'SR': {'B': 'CTRL_{}6', 'T': 'CTRL_{}7'},
        'CE': {'B': 'CTRL_{}0', 'T': 'CTRL_{}2'},
        'CE2': {'B': 'CTRL_{}1', 'T': 'CTRL_{}3'}
    }
    FFs_dict = {}
    for key, value in TC.FFs.items():
        tile = f'INT_{get_tile(key).split("_")[-1]}'
        cr, half = device.get_tile_half(tile)
        extend_dict(FFs_dict, (cr.name, tile, half), value[0])

    for (cr, tile, half), ffs in FFs_dict.items():
        G = device.get_tile_graph(tile)
        x = device.get_x_coord(tile)
        for ff in ffs:
            ff =Node(ff)
            CE_key = 'CE2' if ff.index == 2 else 'CE'
            FFMUX = f'FFMUX{ff.bel}{ff.index}'
            #tile = f'INT_{ff.coordinate}'
            C = f"{tile}/{FF_pins_dct['C'][ff.bel_group[-1]].format(ff.bel_group[0])}"
            SR = FF_pins_dct['SR'][ff.bel_group[-1]].format(ff.bel_group[0])
            CE = FF_pins_dct[CE_key][ff.bel_group[-1]].format(ff.bel_group[0])

            if ff.clb_node_type == 'FF_in':
                FFMUX_pin = 'BYP'
                configurations.add(f'{ff.tile}.{FFMUX}.{FFMUX_pin} = {{}}\n')
            else:
                configurations.update(get_not_FF_configuration(TC, ff.tile, ff.bel, ff.index))

            configurations.add(f'{tile}.PIP.{SR}.VCC_WIRE = {{}}\n')
            configurations.add(f'{tile}.PIP.{CE}.VCC_WIRE = {{}}\n')

            if ff.clb_node_type == 'FF_out':
                if (cr, half, x) not in device.CR_l_clk_pins_dict:
                    extend_dict(device.dummy, 'launch', (cr, half, x))
                    continue

                clk_pin = f'{tile}/{next(iter(device.CR_l_clk_pins_dict[(cr, half, x)]))}'
            if ff.clb_node_type == 'FF_in':
                if (cr, half, x) not in device.CR_s_clk_pins_dict:
                    extend_dict(device.dummy, 'sample', (cr, half, x))
                    continue

                clk_pin = f'{tile}/{next(iter(device.CR_s_clk_pins_dict[(cr, half, x)]))}'

            clk_path = nx.shortest_path(G, clk_pin, C)
            pips = {Edge(edge) for edge in zip(clk_path, clk_path[1:]) if Edge.is_pip(edge)}
            configurations.update(get_pip_FASM(*pips))

    return configurations
def get_LUTs_FASM(LUTs):
    i6_dct = {
        'A': 'IMUX_{}18',
        'B': 'IMUX_{}19',
        'C': 'IMUX_{}20',
        'D': 'IMUX_{}21',
        'E': 'IMUX_{}34',
        'F': 'IMUX_{}35',
        'G': 'IMUX_{}46',
        'H': 'IMUX_{}47'
    }

    configurations = set()
    for LUT, subLUTs in LUTs.items():
        tile = get_tile(LUT)
        INT_tile = f'INT_{get_coordinate(tile)}'
        bel = get_port(LUT)[0]

        if len(LUTs[LUT]) == 1:    #6LUT
            input_idx = int(LUTs[LUT][0][0][-1]) - 1
            function = LUTs[LUT][0][1]
            INIT = f"64'h{cal_init(input_idx, function, 6)}"
            if LUTs[LUT][0][2] == 'MUX':
                configurations.add(get_OUTMUX_FASM(tile, bel, 6))
        else:                           #5LUT & 6LUT
            #subLUTs = sorted(TC.LUTs[LUT], key=lambda x: 0 if x[2]=='O' else 1)
            INIT = []
            for s_idx, subLUT in enumerate(subLUTs):
                subLUT_idx = 6 - s_idx
                input_idx = int(subLUT[0][-1]) - 1
                function = subLUT[1]
                if input_idx == 6:
                    INIT = f"64'h{cal_init(input_idx, function, 6)}"
                    break
                else:
                    INIT.append(cal_init(input_idx, function, 5))
                    if subLUT[2] == 'MUX':
                        configurations.add(get_OUTMUX_FASM(tile, bel, subLUT_idx))
            else:
                INIT = f"64'h{INIT[0]}{INIT[1]}"

        INIT_conf = f'{tile}.{bel}LUT.INIT[63:0] = {INIT}'
        i6_port = i6_dct[bel].format(get_direction(LUT))
        configurations.add(f'{INT_tile}.PIP.{i6_port}.VCC_WIRE = {{}}\n')
        configurations.add(INIT_conf)

    return configurations

def get_truth_table(n_entry):
    truth_table = list(product((0, 1), repeat=n_entry))
    return [entry[::-1] for entry in truth_table]

def cal_init(input_idx, function, N_inputs):
    entries = get_truth_table(N_inputs)
    if function == 'not':
        init_list = [str(int(not(entry[input_idx]))) for entry in entries]
    elif function == 'buffer':
        init_list = [str(entry[input_idx]) for entry in entries]
    else:
        init_list = [str(0) for _ in entries]

    init_list.reverse()
    init_binary = ''.join(init_list)
    init = format(int(init_binary, base=2), f'0{2**N_inputs//4}X')

    return init

def get_OUTMUX_FASM(tile, bel, subLUT_idx):
    return f'{tile}.OUTMUX{bel}.D{subLUT_idx} = {{}}\n'

def get_not_FF_configuration(TC, tile, bel, FF_index):
    configuration = set()
    LUT_key = f'{tile}/{bel}LUT'
    subLUTs = [subLUT for subLUT in TC.LUTs[LUT_key] if subLUT[1] == 'not']
    for idx in range(len(subLUTs)):
        FFMUX_pin = f'D{6 - idx}'
        configuration.add(get_FFMUX_FASM(tile, bel, FF_index, FFMUX_pin))

    return configuration

def get_FFMUX_FASM(tile, bel, FF_index, FFMUX_pin):
    return f'{tile}.FFMUX{bel}{FF_index}.{FFMUX_pin} = {{}}\n'



def count_D_CUTs(path, file):
    TC = load_data(path, file)
    D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs]

    return len(D_CUTs)

def get_src_sink_tiles(path, file, pattern):
    TC = load_data(path, file)
    tiles = {f'INT_{get_coordinate(get_tile(ff[0]))}' for key, ff in TC.FFs.items() if re.match(pattern, ff[0])}

    return tiles

def get_Init_TC(path):
    files = [file for file in os.listdir(path) if file.startswith('TC')]
    files = sorted(files, key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
    len_D_CUTs = Parallel(n_jobs=-1)(delayed(count_D_CUTs)(path, file) for file in files)

    max_idx = len_D_CUTs.index(max(len_D_CUTs))
    Init_TC = files[max_idx]
    files.remove(Init_TC)

    return files, Init_TC
def get_occupied_pips(pips_file):
    used_pips  = set()
    with open(pips_file) as lines:
        for line in lines:
            if '<<->>' in line:
                line = line.rstrip('\n').split('<<->>')
                bidir = True
            elif '->>' in line:
                line = line.rstrip('\n').split('->>')
                bidir = False
            else:
                line = line.rstrip('\n').split('->')
                bidir = False

            tile = get_tile(line[0])
            start_port = f'{tile}/{get_port(line[0]).split(".")[1]}'
            end_port = f'{tile}/{line[1]}'
            used_pips.add((start_port, end_port))
            if bidir:
                used_pips.add((end_port, start_port))

    return used_pips


def get_Init_used_pips_nodes_dict(device, TCs_path, Init_TC_file):
    Init_dynamic_pips = set()
    Init_TC = load_data(TCs_path, Init_TC_file)
    srcs = {ff[0] for key, ff in Init_TC.FFs.items() if re.match(GM.FF_out_pattern, ff[0])}
    TC_G = nx.DiGraph()
    '''for R_CUT in Init_TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            srcs.update(node for node in D_CUT.G if D_CUT.G.in_degree(node) == 0)
            TC_G = nx.compose(TC_G, D_CUT.G)'''
            #Init_dynamic_pips.update(edge for edge in D_CUT.G.edges() if Edge.is_pip(edge))
    TC_G.add_edges_from(edge for R_CUT in Init_TC.CUTs for D_CUT in R_CUT.D_CUTs for edge in D_CUT.G.edges())

    for src in srcs:
        Init_dynamic_pips.update(nx.dfs_edges(TC_G, src))

    interface_paths = os.path.join(GM.load_path, 'nets')
    net_files = {f'{interface_paths}/{file}' for file in os.listdir(interface_paths)}
    interface_pips = Parallel(n_jobs=-1)(delayed(get_occupied_pips)(file) for file in net_files)
    Init_dynamic_pips.update(pip for pips in interface_pips for pip in pips)

    Init_dynamic_pips.update(get_VCC_i6_pips(Init_TC.LUTs))
    Init_dynamic_pips.update(get_FFs_CTRL_pips(device, Init_TC.FFs))


    Init_used_pips_dict = {}
    Init_used_nodes_dict = {}
    for pip in Init_dynamic_pips:
        tile = get_tile(pip[0])
        pip = (get_port(pip[0]), get_port(pip[1]))
        extend_dict(Init_used_pips_dict, tile, pip, value_type='set')

    for key in Init_used_pips_dict:
        Init_used_nodes_dict[key] = {node for pip in Init_used_pips_dict[key] for node in pip}


    return Init_used_pips_dict, Init_used_nodes_dict

def get_VCC_i6_pips(LUTs):
    i6_dct = {
        'A': 'IMUX_{}18',
        'B': 'IMUX_{}19',
        'C': 'IMUX_{}20',
        'D': 'IMUX_{}21',
        'E': 'IMUX_{}34',
        'F': 'IMUX_{}35',
        'G': 'IMUX_{}46',
        'H': 'IMUX_{}47'
    }

    pips = set()
    for LUT in LUTs:
        tile = get_tile(LUT)
        INT_tile = f'INT_{get_coordinate(tile)}'
        bel = get_port(LUT)[0]
        i6_port = f'{INT_tile}/{i6_dct[bel].format(get_direction(LUT))}'
        VCC_Wire = f'{INT_tile}/VCC_WIRE'
        pips.add((VCC_Wire, i6_port))

    return pips

def get_FFs_CTRL_pips(device, FFs):
    pips = set()
    FF_pins_dct = {
        'C': {'B': 'CTRL_{}4', 'T': 'CTRL_{}5'},
        'SR': {'B': 'CTRL_{}6', 'T': 'CTRL_{}7'},
        'CE': {'B': 'CTRL_{}0', 'T': 'CTRL_{}2'},
        'CE2': {'B': 'CTRL_{}1', 'T': 'CTRL_{}3'}
    }
    FFs_dict = {}
    for key, value in FFs.items():
        tile = f'INT_{get_tile(key).split("_")[-1]}'
        cr, half = device.get_tile_half(tile)
        extend_dict(FFs_dict, (cr.name, tile, half), value[0])

    for (cr, tile, half), ffs in FFs_dict.items():
        G = device.get_tile_graph(tile, block=False)
        x = device.get_x_coord(tile)
        for ff in ffs:
            ff = Node(ff)
            CE_key = 'CE2' if ff.index == 2 else 'CE'
            C = f"{tile}/{FF_pins_dct['C'][ff.bel_group[-1]].format(ff.bel_group[0])}"
            SR = FF_pins_dct['SR'][ff.bel_group[-1]].format(ff.bel_group[0])
            CE = FF_pins_dct[CE_key][ff.bel_group[-1]].format(ff.bel_group[0])

            if ff.clb_node_type == 'FF_out':
                clk_pin = f'{tile}/{next(iter(device.CR_l_clk_pins_dict[(cr, half, x)]))}'
            if ff.clb_node_type == 'FF_in':
                clk_pin = f'{tile}/{next(iter(device.CR_s_clk_pins_dict[(cr, half, x)]))}'

            clk_path = nx.shortest_path(G, clk_pin, C)
            clk_pips = {edge for edge in zip(clk_path, clk_path[1:]) if Edge.is_pip(edge)}

            SR_node = f'{tile}/{SR}'
            CE_node = f'{tile}/{CE}'
            VCC_Wire = f'{tile}/VCC_WIRE'
            pips.update(product({VCC_Wire}, {SR_node, CE_node}))
            pips.update(clk_pips)

    return pips

def gen_rtl(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict, even_odd=None):
    Cell.cells = []
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
    ########################################################
    TC_idx = int(re.search('\d+', TC_file)[0])
    #src_path = os.path.join(GM.Data_path, f'Vivado_Sources/TC{TC_idx}')
    #create_folder(src_path)
    TC = load_data(TCs_path, TC_file)
    if even_odd == 'even':
        src_path = os.path.join(GM.Data_path, f'Vivado_Sources/TC{TC_idx}_even')
        create_folder(src_path)
        D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs if int(re.findall('\d+', D_CUT.origin)[1]) % 2 == 0]
    elif even_odd == 'odd':
        src_path = os.path.join(GM.Data_path, f'Vivado_Sources/TC{TC_idx}_odd')
        create_folder(src_path)
        D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs if int(re.findall('\d+', D_CUT.origin)[1]) % 2 == 1]
    else:
        src_path = os.path.join(GM.Data_path, f'Vivado_Sources/TC{TC_idx}')
        create_folder(src_path)
        D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs]

    D_CUTs.sort(key=lambda x: x.index * 10000 + DLOC.get_x_coord(x.origin) * 1000 + DLOC.get_y_coord(x.origin))
    ########################################################
    N_Segments = math.ceil(len(D_CUTs) / N_Parallel)
    N_Partial = len(D_CUTs) % N_Parallel
    routing_constraints = []
    for idx, D_CUT in enumerate(D_CUTs):
        CUT_idx = idx % N_Parallel
        Seg_idx = idx // N_Parallel
        w_Error_Mux_In = f'w_Error({Seg_idx})({CUT_idx})'
        #LUT_ins = list(filter(lambda x: re.match(GM.LUT_in_pattern, x), D_CUT.G))

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

    with open(os.path.join(src_path, 'stats.txt'), 'w+') as file:
        if N_Partial > 0:
            file.write(f'N_Segments = {N_Segments - 1}\n')
        else:
            file.write(f'N_Segments = {N_Segments}\n')

        file.write(f'N_Partial = {N_Partial}')

    with open(os.path.join(src_path, 'physical_constraints.xdc'), 'w+') as file:
        file.writelines(cell_constraints)
        file.write('\n')
        file.writelines(routing_constraints)

    VHDL_file.print(os.path.join(src_path, 'CUTs.vhd'))
    print(f'TC{TC_idx} is done.')


class Cell:
    cells = []
    def __init__(self, type, slice, bel, cell_name):
        self.type       = type
        self.slice      = slice
        self.bel        = bel
        self.cell_name  = cell_name
        self._inputs    = []

        self.cells.append(self)

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, input):
        self._inputs.append(input)

    def get_BEL(self):
        return f'set_property BEL {self.bel} [get_cells {self.cell_name}]\n'

    def get_LOC(self):
        return f'set_property LOC {self.slice} [get_cells {self.cell_name}]\n'

    def get_LOCK_PINS(self):
        pairs = []
        for i, input in enumerate(self.inputs):
            pairs.append(f'I{i}:A{input[-1]}')

        return f'set_property LOCK_PINS {{{" ".join(pairs)}}} [get_cells {self.cell_name}]\n'

    @classmethod
    def get_cell_constraints(cls):
        constraints = []
        for cell in cls.cells:
            constraints.append(cell.get_LOC())
            constraints.append(cell.get_BEL())
            if cell.type == 'LUT':
                constraints.append(cell.get_LOCK_PINS())

        return constraints

    @staticmethod
    def get_D_CUT_cells(TC, slices_dict, D_CUT, buffer=False):
        cells = {}
        launch_FF_key = {key for key in D_CUT.FFs_set if re.match(GM.FF_out_pattern, TC.FFs[key][0])}.pop()
        slice = slices_dict[get_tile(launch_FF_key)]
        bel = get_port(launch_FF_key)
        cells['launch_FF'] = (slice, bel)
        sample_FF_key = {key for key in D_CUT.FFs_set if re.match(GM.FF_in_pattern, TC.FFs[key][0])}.pop()
        slice = slices_dict[get_tile(sample_FF_key)]
        bel = get_port(sample_FF_key)
        cells['sample_FF'] = (slice, bel)
        #not_LUT_key = D_CUT.not_LUT[0]
        not_LUT_key = D_CUT.LUTs_func_dict['not'][0].bel_key
        slice = slices_dict[get_tile(not_LUT_key)]
        subLUT = [lut for lut in TC.LUTs[not_LUT_key] if (D_CUT.LUTs_func_dict['not'][0].name == lut[0]) and (lut[1] == 'not')].pop()
        idx = 6 - TC.LUTs[not_LUT_key].index(subLUT)
        input = subLUT[0]
        bel = f'{get_port(not_LUT_key)[0]}{idx}LUT'
        cells['not_LUT'] = (slice, bel, input)

        if D_CUT.get_g_buffer() != "00":
        #if buffer and 'buffer' in D_CUT.LUTs_func_dict:
            for buffer_in in D_CUT.LUTs_func_dict['buffer']:
                buff_LUT_key = buffer_in.bel_key
                slice = slices_dict[get_tile(buff_LUT_key)]
                subLUT = [lut for lut in TC.LUTs[buff_LUT_key] if (buffer_in.name == lut[0]) and (lut[1] == 'buffer')].pop()
                idx = 6 - TC.LUTs[buff_LUT_key].index(subLUT)
                input = buffer_in.name
                bel = f'{get_port(buff_LUT_key)[0]}{idx}LUT'
                extend_dict(cells, 'buff_LUT', (slice, bel, input))

        return cells
