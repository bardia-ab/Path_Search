import re
from Functions import load_data, store_data, extend_dict
import networkx as nx
import Global_Module as GM
from resources.node import Node
from itertools import chain

def check_collision(TC):
    G_TC = nx.DiGraph()
    for cut in TC.CUTs:
        G_TC = nx.compose(G_TC, cut.G)

    return nx.is_forest(G_TC)

def check_FFs(path, TC):
    result = True
    FFs = []
    if path.FF_in:
        FFs.append(path.FF_in)

    if path.FF_out:
        FFs.append(path.FF_out)

    for FF in FFs:
        if TC.filter_FFs(key=Node(FF).key)[0].usage == 'blocked':
            result = False
            break

    return result

def check_LUTs(path, TC):
    result = True
    for LUT_in in path.LUT_type_dict:
        type = path.LUT_type_dict[LUT_in]
        LUT_func = path.get_LUT_func(type)
        LUT1 = TC.filter_LUTs(key=LUT_in.key)
        try:
            subLUT = LUT1[0].get_free_subLUT(LUT_in.name, LUT_func)
        except:
            result = False
            break

    return result

def check_LUT_utel(TC):
    LUTs_dict = {}
    for cut in TC.CUTs:
        muxed_node = list(filter(lambda x: re.match(GM.MUXED_CLB_out_pattern, x), cut.G))
        for function, LUT_ins in cut.LUTs_func_dict.items():
            for LUT_in in LUT_ins:
                if muxed_node:
                    muxed_node = muxed_node[0]
                    pred = Node(next(cut.G.predecessors(muxed_node)))
                    MUX_flag = pred.bel_group == LUT_in.bel_group and pred.bel == LUT_in.bel
                else:
                    MUX_flag = False

                subLUT_usage = 2 if (LUT_in.is_i6 or not GM.LUT_Dual or MUX_flag) else 1
                if LUT_in.bel_key not in LUTs_dict:
                    LUTs_dict[LUT_in.bel_key] = subLUT_usage
                else:
                    LUTs_dict[LUT_in.bel_key] += subLUT_usage

    over_utel_LUTs = {key for key in LUTs_dict if LUTs_dict[key] > 2}
    if over_utel_LUTs:
        breakpoint()
        return False
    else:
        return True

def check_DCUT_LUT_utel(TC):
    LUTs_dict = {}
    for key, subLUTs in TC.LUTs.items():
        LUTs_dict[key] = 0
        for subLUT in subLUTs:
            usage = 2 if re.match(GM.LUT_in6_pattern, subLUT[0]) else 1
            LUTs_dict[key] += usage

    invalid_keys= {k:TC.LUTs[k] for k,v in LUTs_dict.items() if v > 2}
    return bool(len(invalid_keys)), invalid_keys


def check_clb_mux(TCs_path, TC_file):
    invalid_D_CUTs = []
    TC = load_data(TCs_path, TC_file)
    for R_CUT in TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            if 'buffer' in D_CUT.LUTs_func_dict:
                buffer_in = D_CUT.LUTs_func_dict['buffer'][0]
                neigh = list(D_CUT.G.neighbors(buffer_in.name))[0]
                brnch_node = [node for node in D_CUT.G if D_CUT.G.out_degree(node) > 1]
                if brnch_node:
                    brnch_node = brnch_node[0]
                elif D_CUT.LUTs_func_dict['not'][0].name == D_CUT.LUTs_func_dict['buffer'][0].name:
                    brnch_node = D_CUT.LUTs_func_dict['not'][0].name
                else:
                    breakpoint()

                if re.match(GM.MUXED_CLB_out_pattern, neigh):
                    if re.match(GM.LUT_in_pattern, brnch_node) or len(TC.LUTs[buffer_in.bel_key]) == 2:
                        invalid_D_CUTs.append((TC_file, D_CUT))

    return invalid_D_CUTs

def remove_invalid_D_CUTs(TCs_path, TC_file, D_CUTs):
    TC = load_data(TCs_path, TC_file)
    for D_CUT in D_CUTs:
        R_CUT_idx = {TC.CUTs.index(RCUT) for RCUT in TC.CUTs if RCUT.index == D_CUT.index}.pop()
        D_CUT = {DCUT for DCUT in TC.CUTs[R_CUT_idx].D_CUTs if
                 DCUT.origin == D_CUT.origin and DCUT.index == D_CUT.index}.pop()
        TC.CUTs[R_CUT_idx].D_CUTs.remove(D_CUT)

        for function, LUT_ins in D_CUT.LUTs_func_dict.items():
            for LUT_in in LUT_ins:
                lut_key = LUT_in.bel_key
                s_lut = {lut for lut in TC.LUTs[lut_key] if LUT_in.name == lut[0]}.pop()
                TC.LUTs[lut_key].remove(s_lut)

        for ff in D_CUT.FFs_set:
            del TC.FFs[ff]

    print(TC_file)
    return TC

def get_TC_DCUT_dict(invalid_D_CUTs):
    dct = {}
    for element in invalid_D_CUTs:
        extend_dict(dct, element[0], element[1])

    return dct
