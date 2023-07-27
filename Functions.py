import networkx as nx
import re, os, pickle, shutil
import Global_Module as GM
from itertools import count, product
from heapq import heappop, heappush

def extend_dict(dict_name, key, value, extend=False, value_type='list'):
    if value_type == 'set':
        if key not in dict_name:
            if isinstance(value, str) or isinstance(value, tuple):
                dict_name[key] = {value}
            else:
                dict_name[key] = set(value)
        else:
            if isinstance(value, str) or isinstance(value, tuple):
                dict_name[key].add(value)
            else:
                dict_name[key].update(value)
    else:
        if extend:
            if key not in dict_name:
                dict_name[key] = [value]
            else:
                dict_name[key].extend(value)
        else:
            if key not in dict_name:
                dict_name[key] = [value]
            else:
                dict_name[key].append(value)

    return dict_name

def get_tile (wire, delimiter='/'):
    return wire.split(delimiter)[0]

def get_port (wire, delimiter='/'):
    return wire.split(delimiter)[1]

def get_coord_graph(coord):
    G = nx.DiGraph()
    root = r'C:\Users\t26607bb\Desktop\graph'
    for txt in [f'wires\WIREs.INT_{coord}.txt', f'pips\PIPs.INT_{coord}.txt']:
        with open(f'{root}\\{txt}') as file:
            lines = file.readlines()

        wires = get_wires_list(lines)
        G.add_edges_from(wires, weight=1)

    return G

def get_wires_dict(G, coord):
    dct = {}
    tile = 'INT_' + coord
    for edge in G.edges():
        if len(list(filter(lambda x: re.search(tile, x), edge))) != 2:
            for node in edge:
                if re.search(tile, node):
                    key = node

                if not re.search(tile, node):
                    value = node

            dct[key] = value

    return dct

def rmv_off_wires(G, coord):
    removed = []
    for node in G:
        if not get_tile(node).endswith(coord):
            removed.append(node)

    G.remove_nodes_from(removed)

    return G

def extract_path_pips(path):
    pips = set()
    for edge in zip(path, path[1:]):
        if get_tile(edge[0]) == get_tile(edge[1]):
            pips.add(edge)

    return pips

def store_data(Path, FileName, data, SubFolder=False, FolderName=None):
    if SubFolder:
        folder_path = os.path.join(Path, FolderName)
        try:
            os.mkdir(folder_path)
        except FileExistsError:
            shutil.rmtree(folder_path)
            os.mkdir(folder_path)

        data_path = os.path.join(folder_path, FileName)
    else:
        data_path = os.path.join(Path, FileName)

    with open(data_path, 'wb') as file:
        pickle.dump(data, file)

def load_data(Path, FileName):
    with open(os.path.join(Path, FileName), 'rb') as file:
        data = pickle.load(file)

    return data

def get_occupied_pips(pips_file):
    file = open(pips_file)
    lines = file.readlines()
    pips = set()
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
        start_port = tile + '/' + get_port(line[0]).split('.')[1]
        end_port = tile + '/' + line[1]
        pips.add((start_port, end_port))
        if bidir:
            pips.add((end_port, start_port))

    file.close()

    return pips

def get_graph(root, default_weight=0, xlim_down=None, xlim_up=None, ylim_down=None, ylim_up=None):
    G = nx.DiGraph()
    files_list = [os.path.join(dirpath, file) for (dirpath, dirnames, filenames) in os.walk(root) for file in filenames]
    files_list = [file for file in files_list if check_coord_range(file, xlim_down, xlim_up, ylim_down, ylim_up)]
    for file in files_list:
        with open(file) as data:
            lines = data.readlines()

        lines = get_wires_list(lines)
        #G = add_edges(G, *lines, G_copy=None, weight = default_weight)
        G.add_edges_from(lines, weight=default_weight)

    return G

def check_coord_range(FilePath, xlim_down=None, xlim_up=None, ylim_down=None, ylim_up=None):
    FileName = os.path.basename(FilePath)
    [x, y] = re.findall('\d+', FileName)
    x = int(x)
    y = int(y)
    if (xlim_down <= x <= xlim_up) and (ylim_down <= y <= ylim_up):
        return True
    else:
        return False

def get_wires_list(lines, delimiter='/'):
    wires_list = []
    for line in lines:
        line = line.replace('.', delimiter)
        edge = tuple(line.rstrip('\n').lstrip('\t').split('\t'))
        wires_list.append(edge)

    return wires_list

def remove_no_path_pips(G, queue, coord):
    tile = f'INT_{coord}'
    excluded_path = r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\No-Path Ports'
    no_path_ports = load_data(excluded_path, '{}.data'.format(tile))
    pips = set()
    for port in no_path_ports:
        pips.update(G.in_edges(port))
        pips.update(G.out_edges(port))

    queue = [pip.name for pip in queue if pip.name not in pips]
    return queue

def create_folder(FolderPath):
    try:
        os.mkdir(FolderPath)
    except FileExistsError:
        shutil.rmtree(FolderPath)
        os.mkdir(FolderPath)

def get_nodes_dict(G, coordinate):
    G1 = nx.DiGraph(G.subgraph(node for node in G if re.findall(coordinate, node))) #Unfreeze Graph
    INT_nodes = {node for node in G1 if node.startswith('INT')}
    Sources = list(filter(GM.Source_pattern.match, G1))
    Sinks = list(filter(GM.Sink_pattern.match, G1))


    for source in Sources:
        G1.add_edge('s', source, weight=0)

    for sink in Sinks:
        G1.add_edge(sink, 't', weight=0)

    nodes_dict = {}
    for node in INT_nodes:
        source_flag = False
        sink_flag = False
        if nx.has_path(G1, 's', node):
            source_flag = True

        if nx.has_path(G1, node, 't'):
            sink_flag = True

        if source_flag and sink_flag:
            nodes_dict[get_port(node)] = 3
        elif source_flag != sink_flag:
            nodes_dict[get_port(node)] = 2
        else:
            nodes_dict[get_port(node)] = 1

    return nodes_dict

def get_pips_dict(nodes_dict, pips):
    pips_dict = {}
    for pip in pips:
        value = nodes_dict[get_port(pip[0])] + nodes_dict[get_port(pip[1])]
        pips_dict[pip] = value

    return pips_dict

def path_finder(G, source, target, weight="weight", conflict_free=True, delimiter='/', dummy_nodes=[]):
    if source not in G or target not in G:
        msg = f"Either source {source} or target {target} is not in G"
        raise nx.NodeNotFound(msg)

    if source == target:
        return [source]

    weight = _weight_function(G, weight)
    push = heappush
    pop = heappop
    # Init:  [Forward, Backward]
    dists = [{}, {}]  # dictionary of final distances
    paths = [{source: [source]}, {target: [target]}]  # dictionary of paths
    fringe = [[], []]  # heap of (distance, node) for choosing node to expand
    seen = [{source: 0}, {target: 0}]  # dict of distances to seen nodes
    c = count()
    # initialize fringe heap
    push(fringe[0], (0, next(c), source))
    push(fringe[1], (0, next(c), target))
    # neighs for extracting correct neighbor information
    if G.is_directed():
        neighs = [G._succ, G._pred]
    else:
        neighs = [G._adj, G._adj]
    # variables to hold shortest discovered path
    # finaldist = 1e30000
    finalpath = []
    finaldist = 0
    dir = 1
    while fringe[0] and fringe[1]:
        # choose direction
        # dir == 0 is forward direction and dir == 1 is back
        dir = 1 - dir
        # extract closest to expand
        (dist, _, v) = pop(fringe[dir])
        if v in dists[dir]:
            # Shortest path to v has already been found
            continue
        # update distance
        dists[dir][v] = dist  # equal to seen[dir][v]
        if v in dists[1 - dir]:
            # if we have scanned v in both directions we are done
            # we have now discovered the shortest path
            if not finalpath:
                raise nx.NetworkXNoPath(f"No path between {source} and {target}.")
            else:
                # finalpath = [node for node in finalpath if node not in dummy_nodes]
                return finalpath

        for w, d in neighs[dir][v].items():
            # weight(v, w, d) for forward and weight(w, v, d) for back direction
            cost = weight(v, w, d) if dir == 0 else weight(w, v, d)
            if cost is None:
                continue
            vwLength = dists[dir][v] + cost
            if w in dists[dir]:
                if vwLength < dists[dir][w]:
                    raise ValueError("Contradictory paths found: negative weights?")
            elif w not in seen[dir] or vwLength < seen[dir][w]:
                # relaxing
                seen[dir][w] = vwLength
                push(fringe[dir], (vwLength, next(c), w))
                paths[dir][w] = paths[dir][v] + [w]
                if w in seen[0] and w in seen[1]:
                    # see if this path is better than the already
                    # discovered shortest path
                    totaldist = seen[0][w] + seen[1][w]
                    if finalpath == [] or finaldist > totaldist:
                        finaldist_prev = finaldist
                        finaldist = totaldist
                        revpath = paths[1][w][:]
                        revpath.reverse()
                        finalpath_prev = finalpath[:]
                        finalpath = paths[0][w] + revpath[1:]
                        if conflict_free:
                            ports_only = [node.split(delimiter)[1] for node in finalpath if node not in dummy_nodes]
                            if len(ports_only) != len(set(ports_only)):
                                finalpath = finalpath_prev
                                finaldist = finaldist_prev

    raise nx.NetworkXNoPath(f"No path between {source} and {target}.")

def _weight_function(G, weight):
    """Returns a function that returns the weight of an edge.

    The returned function is specifically suitable for input to
    functions :func:`_dijkstra` and :func:`_bellman_ford_relaxation`.

    Parameters
    ----------
    G : NetworkX graph.

    weight : string or function
        If it is callable, `weight` itself is returned. If it is a string,
        it is assumed to be the name of the edge attribute that represents
        the weight of an edge. In that case, a function is returned that
        gets the edge weight according to the specified edge attribute.

    Returns
    -------
    function
        This function returns a callable that accepts exactly three subLUT_inputs:
        a node, an node adjacent to the first one, and the edge attribute
        dictionary for the eedge joining those nodes. That function returns
        a number representing the weight of an edge.

    If `G` is a multigraph, and `weight` is not callable, the
    minimum edge weight over all parallel edges is returned. If any edge
    does not have an attribute with key `weight`, it is assumed to
    have weight one.

    """
    if callable(weight):
        return weight
    # If the weight keyword argument is not callable, we assume it is a
    # string representing the edge attribute containing the weight of
    # the edge.
    if G.is_multigraph():
        return lambda u, v, d: min(attr.get(weight, 1) for attr in d.values())
    return lambda u, v, data: data.get(weight, 1)
