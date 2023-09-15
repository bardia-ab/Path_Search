from Functions import *
from resources.arch_parser import *
start_time = time.time()
##########################################
G = build_graph(GM.root, 46, 90)
########### PIP Category
input_pipjunc = {node for node in G if node.tile == 'INT_X46Y90' and len(get_pips(G, node, dir='downhill')) > 0 and len(get_pips(G, node, dir='uphill')) == 0}
output_pipjunc = {node for node in G if node.tile == 'INT_X46Y90' and len(get_pips(G, node, dir='downhill')) == 0 and len(get_pips(G, node, dir='uphill')) > 0}
mid_pipjunc = {node for node in G if node.tile == 'INT_X46Y90' and len(get_pips(G, node, dir='downhill')) > 0 and len(get_pips(G, node, dir='uphill')) > 0}

########## Wire Cateegory
mult_wires = {node for node in G if node.tile == 'INT_X46Y90' and len(get_wires(G, node)) > 1}
in_wires = {node for node in G if node.tile == 'INT_X46Y90' and get_wire_dir(G, node) == 'in'}
out_wires = {node for node in G if node.tile == 'INT_X46Y90' and get_wire_dir(G, node) == 'out'}
# GCLK.* wires are added to stopovers instead of in_wires dut to their wires being missed form G: 16
stopover_wires = {node for node in G if node.tile == 'INT_X46Y90' and get_wire_dir(G, node) == None}

########### Wires Distance
wires_dist_dict = {}
INT_nodes = {node for node in G if node.tile == 'INT_X46Y90' and len(get_wires(G, node)) > 0}
for node in INT_nodes:
    dists = get_wire_dist(G, node)
    for dist in dists:
        extend_dict(wires_dist_dict, dist, get_regex(node), value_type='set')

regexps = sorted({val for key, value in wires_dist_dict.items() for val in value})
repetitive_regexp = {}
for regexp in regexps:
    keys = {key for key,value in wires_dist_dict.items() if regexp in value}
    if len(keys) > 1:
        repetitive_regexp[regexp] = keys

############# PIPs BiPartite
INT_nodes = {node for node in G if node.tile == 'INT_X46Y90'}
neigh_dict = {}
pred_dict = {}

for node in INT_nodes:
    for neigh in G.neighbors(node):
        if neigh.tile != node.tile:
            continue

        extend_dict(neigh_dict, get_regex(node), get_regex(neigh), value_type='set')

    for pred in G.predecessors(node):
        if pred.tile != node.tile:
            continue

        extend_dict(pred_dict, get_regex(node), get_regex(pred), value_type='set')

print(' --- %s seconds ---' %(time.time() - start_time))