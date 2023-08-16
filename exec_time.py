import time, re, os, pickle

import Global_Module
from Functions import *
import networkx as nx
from resources.node import *
from resources.tile import *
from resources.edge import *
from resources.path import *
from resources.cut import *
from resources.primitive import *
from resources.configuration import *
from resources.arch_graph import Arch
import resources.validation as vd
from itertools import product
import cProfile, pstats

##############################
def Init_tile_node_dicts(dev:Arch):
    dev.tile_dirc_dict = {}
    dev.gnode_dict = {}
    for tile in dev.tiles:
        if tile.type == 'CLB':
            dev.tile_dirc_dict[tile.name] = tile.direction

        for node in tile.used_nodes:
            if node.tile_type == 'INT':
                key = node.port
                value = node.tile
                extend_dict(dev.gnode_dict, key, value, value_type='set')
            else:
                key1 = node.port_suffix
                key2 = node.bel_group[0]
                value = node.tile
                if key1 not in dev.gnode_dict:
                    dev.gnode_dict[key1] = {key2: {value}}
                else:
                    extend_dict(dev.gnode_dict[key1], key2, value, value_type='set')

def get_gnodes(dev, node):
    gnodes = set()
    if node.startswith('INT'):
        port = get_port(node)
        for tile in dev.gnode_dict[port]:
            gnodes.add(f'{tile}/{port}')
    else:
        dirc = dev.tile_dirc_dict[get_tile(node)]
        port_suffix = Configuration.port_suffix(node)
        slice_type = Configuration.get_slice_type(node)
        for tile in dev.tile_dirc_dict[port_suffix][dirc]:
            gnodes.add(f'{tile}/CLE_CLE_{slice_type}_SITE_0_{port_suffix}')

    return gnodes
#############################

start_time = time.time()
coord = 'X46Y90'

graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')

dev = Arch(G)
dev.get_pips_length(coord)
del G
Init_tile_node_dicts(dev)
TC = Configuration(dev)

node1 = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_AQ')
node2 = Node('INT_X46Y90/EE12_BEG0')

with cProfile.Profile() as profile:
    print(len(dev.get_nodes(bel_group=node2.bel_group, port_suffix=node1.port_suffix)))
    print(len(TC.get_global_nodes(node2.name)))
    print(len(get_gnodes(dev, node2.name)))

results = pstats.Stats(profile)
results.sort_stats(pstats.SortKey.TIME)
results.print_stats()


print('--- %s seconds ---' %(time.time() - start_time))