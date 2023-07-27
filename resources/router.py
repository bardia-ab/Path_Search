import re
from resources.node import Node
import Global_Module as GM

def source_path_first(TC, pip):
    launch_groups = [key for key, value in TC.CD.items() if value != 'sample']
    sample_groups = [key for key, value in TC.CD.items() if value != 'launch']
    launch_dist = min([GM.source_dict[pip.str()[0]][group] for group in launch_groups])
    sample_dist = min([GM.sink_dict[pip.str()[1]][group] for group in sample_groups])

    #if Node(next(self.G_copy.neighbors(pip.str()[1]))).i6:
        #return False
    #elif launch_dist < sample_dist:
    if launch_dist < sample_dist:
        return True
    else:
        return False