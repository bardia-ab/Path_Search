import os, time, pickle, re
import networkx as nx

from Functions import *
from resources.node import *
from resources.tile import *
from resources.edge import *
from resources.path import *
from resources.cut import *
from resources.primitive import *
from resources.configuration import *
from resources.arch_graph import Arch
import resources.constraint as const
start_time = time.time()

################### Graph Initialization ###################
root = 'C:\\Users\\t26607bb\\Desktop\\graph_zcu9eg'
coordinate = 'X65Y72'
desired_tile = f'INT_{coordinate}'
[x, y] = re.findall('\d+', desired_tile)
x = int(x)
y = int(y)
xlim_down = x - 2   #12:long_wires 4: quad wires
xlim_up = x + 2
ylim_down = y - 2
ylim_up = y + 16
G = get_graph(root, default_weight=1, xlim_down=xlim_down, xlim_up=xlim_up, ylim_down=ylim_down, ylim_up=ylim_up)
dev = Arch(G)

################### PIPs Initialization ###################
#prev_block_mode = GM.block_mode
#prev_LUT_mode = GM.LUT_Dual
GM.block_mode = 'local'
GM.LUT_Dual = True

pips_file = r'C:\Users\t26607bb\Desktop\used_pips.txt'
occupied_pips = get_occupied_pips(pips_file)
clear_pips = {('INT_X65Y72/VCC_WIRE', 'INT_X65Y72/IMUX_E36')}
dest2 = 'INT_X65Y72/IMUX_E36'
dest1 = 'CLEL_R_X64Y88/CLE_CLE_L_SITE_0_F_I'
src2 = 'CLEL_R_X64Y88/CLE_CLE_L_SITE_0_FQ2'
src1 = 'INT_X65Y72/LOGIC_OUTS_W2'
clk = 'GCLK_B_0_0'
################### Main ###################
TC = Configuration(dev)
#TC.create_CUT(coordinate, '')
clk_pips = set()
for pip in occupied_pips:
    if list(filter(lambda x: re.search('CTRL_[EW][45]|GCLK', x), pip)):
        clk_pips.add(pip)

occupied_pips = occupied_pips - clear_pips
occupied_nodes = {node for pip in occupied_pips for node in pip if node in TC.G}
occupied_nodes = {node for node in occupied_nodes if Node(node).set_INT_node_mode(dev.G) != 'in'}
TC.block_nodes = occupied_nodes
TC.G.remove_edges_from(occupied_pips)
TC.G.add_edges_from(clear_pips)

path1 = nx.shortest_path(TC.G, src1, dest1, weight='weight')
path1 = Path(dev, TC, path1, 'main_path')
TC.update_FFs('used', path1.FFs())
TC.set_LUTs(dev, 'used', path1.LUTs_dict())
#TC.add_path(dev, path1)
path2 = nx.shortest_path(TC.G, src2, dest2, weight='weight')
path2 = Path(dev, TC, path2, 'main_path')
TC.update_FFs('used', path2.FFs())
TC.set_LUTs(dev, 'used', path2.LUTs_dict())
#TC.add_path(dev, path2)
#path3 = nx.shortest_path(TC.G, clk, C, weight='weight')
#path3 = Path(dev, TC, path3, None)

consts = set()
clear_pips = {Edge(pip) for pip in clear_pips}
consts.update(const.get_pip_FASM(*clear_pips, mode='clear'))
consts.update(const.get_pip_FASM(*path1.pips, mode='set'))
consts.update(const.get_pip_FASM(*path2.pips, mode='set'))
clk_nodes = {node for node in clk_pips}
TC.G.add_edges_from(clk_pips, weight=1)
TC.unblock_nodes(dev, clk_nodes)
consts.update(const.get_CLB_FASM(dev, TC, path1 + path2, clk))
#consts.update(const.get_pip_FASM(*path3.pips, mode='set'))

store_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT'
with open(os.path.join(store_path, 'new.fasm'), 'w+') as file:
    file.writelines(sorted(consts, reverse=True))

################## pyteman
input_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\input.bit'
output_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\output.bit'
fasm_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\new.fasm'
pyteman_path = r' C:\Users\t26607bb\Desktop\Pyteman\pyteman_dist\fasm2bit.py'

command = f'python {pyteman_path} {fasm_path} {input_path} {output_path}'
os.system(command)

print('--- %s seconds ---' %(time.time() - start_time))