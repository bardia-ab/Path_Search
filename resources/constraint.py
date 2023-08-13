import re

import networkx as nx

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

def get_FFs_FASM(TC):
    configurations = set()
    FF_pins_dct = {
        'C': {'B': 'CTRL_{}4', 'T': 'CTRL_{}5'},
        'SR': {'B': 'CTRL_{}6', 'T': 'CTRL_{}7'},
        'CE': {'B': 'CTRL_{}0', 'T': 'CTRL_{}2'},
        'CE2': {'B': 'CTRL_{}1', 'T': 'CTRL_{}3'}
    }

    for ff in TC.FFs:
        ff =FF(ff)
        CE_key = 'CE2' if ff.index == 2 else 'CE'
        FFMUX = f'FFMUX{ff.letter}{ff.index}'
        tile = f'INT_{ff.coordinate}'
        C = FF_pins_dct['C'][ff.bel_group[-1]].format(ff.bel_group[0])
        C = f'{tile}/{C}'
        SR = FF_pins_dct['SR'][ff.bel_group[-1]].format(ff.bel_group[0])
        CE = FF_pins_dct[CE_key][ff.bel_group[-1]].format(ff.bel_group[0])

        if re.match(GM.FF_in_pattern, TC.FFs[ff.name][0]):
            FFMUX_pin = 'BYP'
            configurations.add(f'{ff.tile}.{FFMUX}.{FFMUX_pin} = {{}}\n')
        else:
            configurations.update(get_not_FF_configuration(TC, ff.tile, ff.letter, ff.index))

        configurations.add(f'{tile}.PIP.{SR}.VCC_WIRE = {{}}\n')
        configurations.add(f'{tile}.PIP.{CE}.VCC_WIRE = {{}}\n')

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
        configurations.add(f'{tile}.PIP.{i6_port}.VCC_WIRE = {{}}\n')
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