
from joblib import Parallel, delayed
import time, os, re
import Global_Module as GM
from Functions import load_data, get_tile, get_port
from itertools import product

def get_origin_CUTs_len(idx, path, file, coord):
    TC = load_data(path, file)
    i = 0
    for cut in TC.CUTs:
        if coord in cut.origins:
            i += 1

    return (f'TC{idx}', i)

def sort_TCs(l, coord):
    path = os.path.join(GM.DLOC_path, f'iter{l-1}')
    files = list(os.listdir(path))
    TC_CUT_len = []
    TC_CUT_len.extend(Parallel(n_jobs=-1)(delayed(get_origin_CUTs_len)(idx, path, file, coord) for idx, file in enumerate(files)))
    keys = sorted(TC_CUT_len, key=lambda x: x[1])
    dct = {k[0]: k[1] for k in keys}
    files.sort(key=lambda x: dct[x.split('.')[0]])
    last_file = sorted(files, key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)[-1]

    return files, last_file

def block_nodes(TC, TC_idx, l):
    TC_total = load_data(os.path.join(GM.DLOC_path, f'iter{l - 1}'), f'TC{TC_idx}.data')
    nodes = {f'{tile}/{port}' for tile in TC_total.used_nodes_dict for port in TC_total.used_nodes_dict[tile]}
    TC.G.remove_nodes_from(nodes)
    TC.block_nodes = nodes

    return TC, TC_total

def block_FFs(TC, TC_idx, l):
    TC_total = load_data(os.path.join(GM.DLOC_path, f'iter{l - 1}'), f'TC{TC_idx}.data')
    removeable_FFs = set()
    for ff in TC_total.FFs:
        removeable_FFs.update(TC.get_FFs(name=ff))

    TC.FFs = TC.FFs - removeable_FFs

    return TC

def block_LUTs(dev, TC, TC_idx, l):
    TC_total = load_data(os.path.join(GM.DLOC_path, f'iter{l - 1}'), f'TC{TC_idx}.data')
    removeable_LUTs = set()
    FF_outs = set()
    for lut in TC_total.LUTs:
        for i, subLUT in enumerate(TC_total.LUTs[lut]):
            idx = 6 - i
            tile = get_tile(lut)
            bel = get_port(lut)[0]
            removeable_LUTs.update(TC.get_LUTs(name=f'{tile}/{bel}{idx}LUT'))
            if i == 1:
                FF_outs.update(dev.get_nodes(tile=tile, bel=bel, clb_node_type='FF_out'))

    TC.LUTs = TC.LUTs - removeable_LUTs
    FF_outs = {node.name for node in FF_outs}
    edges = set(product({'s'}, FF_outs))
    TC.G.remove_edges_from(edges)

    return TC

def update_CD(dev, TC, tile, l, TC_prev):
    TC1 = load_data(os.path.join(GM.store_path, f'iter{l - 1}'), TC_prev)
    TC.CD = TC1.CD.copy()
    for group in TC.CD:
        TC.remove_source_sink(dev, group, TC.CD[group], tile)

    return TC

