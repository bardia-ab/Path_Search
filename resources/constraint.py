import networkx as nx

from resources.edge import Edge
from resources.path import Path
from resources.cut import CUT
from resources.primitive import *

def get_pip_FASM(*pips, mode='set'):
    value = {'set': 1, 'clear': 0}
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

def get_CLB_FASM(device, TC, path: Path, clk):
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