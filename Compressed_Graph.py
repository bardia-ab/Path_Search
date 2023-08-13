from Functions import *
from resources.configuration import Configuration
from resources.arch_graph import Arch
start_time = time.time()

coordinate = sys.argv[1]
desired_tile = 'INT_' + coordinate
device = 'ZU9'

FF_out_pattern = re.compile('CLE.*_[A-H]Q2*$')
FF_in_pattern = re.compile('CLE.*_[A-H][_XI]+$')

[x, y] = re.findall('\d+', desired_tile)
x = int(x)
y = int(y)
xlim_down = x - 12 - 4   #12:long_wires 4: quad wires
xlim_up = x + 12 + 4
ylim_down = y - 12 - 4
ylim_up = y + 12 + 4

G = get_graph(GM.root, default_weight=1, xlim_down=xlim_down, xlim_up=xlim_up, ylim_down=ylim_down, ylim_up=ylim_up)
#dev = Arch(G)

Sources = list(filter(GM.Source_pattern.match, G))
Sinks = list(filter(GM.Sink_pattern.match, G))
edges = set(product({'s'}, Sources))
G.add_edges_from(edges, weight=0)
edges = set(product(Sinks, {'t'}))
G.add_edges_from(edges, weight=0)


#in_ports = dev.get_nodes(tile=desired_tile, mode='in')
#out_ports = dev.get_nodes(tile=desired_tile, mode='out')
in_ports = get_tile_ports(G, desired_tile, categorization='wire', wire_mode='in_port')
out_ports = get_tile_ports(G, desired_tile, categorization='wire', wire_mode='out_port')
all_tiles = set()
no_path_ports = set()
for pipjunc in in_ports:
    try:
        path = path_finder(G, 's', pipjunc, weight='weight', dummy_nodes=['s', 't'], conflict_free=False)[1:]
        all_tiles.update([get_tile(node) for node in path])
    except:
        no_path_ports.add(pipjunc)

for pipjunc in out_ports:
    try:
        path = path_finder(G, pipjunc, 't', weight='weight', dummy_nodes=['s', 't'], conflict_free=False)[:-1]
        all_tiles.update([get_tile(node) for node in path])
    except:
        no_path_ports.add(pipjunc)

#print('No Path Ports: ', len(no_path_ports))
removable_nodes = set()

for node in G:
    tile = get_tile(node)
    if tile not in all_tiles:
        removable_nodes.add(node)

G.remove_nodes_from(removable_nodes)
store_data(GM.graph_path, f'G_{device}_{desired_tile}.data', G)

print('\n--- %s seconds ---' %(time.time() - start_time))