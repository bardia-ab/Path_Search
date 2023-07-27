import networkx as nx
import Global_Module as GM
from resources.node import Node

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
        for LUT_in in cut.LUTs_func_dict:
            subLUT_usage = 2 if (LUT_in.is_i6 or not GM.LUT_Dual) else 1
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
