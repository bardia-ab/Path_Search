import re, pickle, os, platform

def globalize_regex_patterns():
    global LUT_in_pattern, LUT_in6_pattern, FF_in_pattern, FF_out_pattern, CLB_out_pattern, MUXED_CLB_out_pattern, \
        East_CLB, West_CLB, FF_key_pattern, LUT_key_pattern, top_group, bottom_group, Source_pattern, Sink_pattern
    LUT_in_pattern = re.compile('^CLE.*_[A-H][1-6]$')
    LUT_in6_pattern = re.compile('^CLE.*_[A-H]6$')
    FF_in_pattern = re.compile('^CLE.*_[A-H][_XI]+$')
    FF_out_pattern = re.compile('^CLE.*_[A-H]Q2*$')
    Source_pattern = re.compile('^CLE.*_[A-H]Q2*$')
    Sink_pattern = re.compile('^CLE.*_[A-H][_XI]+$')
    CLB_out_pattern = re.compile('^CLE.*_[A-H]_O$')
    MUXED_CLB_out_pattern = re.compile('^CLE.*_[A-H]MUX$')
    East_CLB = re.compile('^CLEL_R.*')
    West_CLB = re.compile('^CLEL_L.*|^CLEM.*')
    FF_key_pattern = re.compile('^CLE.*/[A-H]FF2*$')
    LUT_key_pattern = re.compile('^CLE.*/[A-H]LUT$')
    top_group = re.compile('^CLE.*_[E-H].*')
    bottom_group = re.compile('^CLE.*_[A-D].*')

def get_tiles_coord_dict(wires_dict):
    tiles_coord_dict = {}
    for key in wires_dict:
        coordinate = re.findall('X\d+Y\d+', key)[0]
        if key.startswith('INT'):
            tile_type = 'INT'
        elif key.startswith('CLEL_R'):
            tile_type = 'CLB_E'
        else:
            tile_type = 'CLB_W'

        if coordinate not in tiles_coord_dict:
            tiles_coord_dict.update({coordinate: {'CLB_W':None, 'INT': None, 'CLB_E':None}})

        tiles_coord_dict[coordinate][tile_type] = key

    return tiles_coord_dict

def load_data(Path, FileName):
    with open(os.path.join(Path, FileName), 'rb') as file:
        data = pickle.load(file)

    return data

def init_paths():
    os_name = platform.system()
    init = load_data('.', 'init.data')
    root = init[os_name]['root']
    store_path = init[os_name]['store_path']

    return root, store_path

############################################################
'''root, Data_path = init_paths()
store_path = os.path.join(Data_path, 'Store')
load_path = os.path.join(Data_path, 'Load')
graph_path = os.path.join(Data_path, 'Compressed Graphs')
excluded_path = os.path.join(Data_path, 'No-Path Ports')
const_path = os.path.join(Data_path, 'Constraints')'''

####### Constant Objects
'''INTs = set()
CLBs = set()
long_capture_process_time = 100
long_TC_process_time = 140
reconstruction = False
wires_dict = load_data(load_path, 'wires_dict.data')
tiles_coord_dict = get_tiles_coord_dict(wires_dict)
clb_site_dict = load_data(load_path, 'clb_site_dict.data')'''

####### main_TC Objects
'''TC = []
not_TC = []
xor_TC = []
LUTs_dict = {}
FFs_dict = {}
LUTs_map = []
covered_pips = []
configurations = []
tried_pips = set()
num_long_process = 0
start_TC_time = 0
counter = 0
blocked_FFs = set()
blocked = set()
New_TC = True'''

####### PIP Objects
'''long_long_pip = False
reversed_pip = None
bidir_pip = False
long_process = False
same_not_launch = False
other_pip_end = set()'''

######## LUT Dual Mode
LUT_Dual = True
block_mode = 'global'   #global|local
route_thru = True

#globalize_regex_patterns()
LUT_in_pattern = re.compile('^CLE.*_[A-H][1-6]$')
LUT_in6_pattern = re.compile('^CLE.*_[A-H]6$')
FF_in_pattern = re.compile('^CLE.*_[A-H][_XI]+$')
FF_out_pattern = re.compile('^CLE.*_[A-H]Q2*$')
Source_pattern = re.compile('^CLE.*_[A-H]Q2*$')
Sink_pattern = re.compile('^CLE.*_[A-H][_XI]+$')
CLB_out_pattern = re.compile('^CLE.*_[A-H]_O$')
MUXED_CLB_out_pattern = re.compile('^CLE.*_[A-H]MUX$')
Unregistered_CLB_out_pattern = re.compile('^CLE.*_[A-H]_O$|^CLE.*_[A-H]MUX$')
East_CLB = re.compile('^CLEL_R.*')
West_CLB = re.compile('^CLEL_L.*|^CLEM.*')
FF_key_pattern = re.compile('^CLE.*/[A-H]FF2*$')
LUT_key_pattern = re.compile('^CLE.*/[A-H]LUT$')
top_group = re.compile('^CLE.*_[E-H].*')
bottom_group = re.compile('^CLE.*_[A-D].*')