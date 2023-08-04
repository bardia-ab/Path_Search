import re, pickle, os, platform, json

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
    with open('init.json') as file:
        init = json.load(file)

    root = init[os_name]['root']
    Data_path = init[os_name]['Data_path']

    return root, Data_path

############################################################
root, Data_path = init_paths()
store_path = os.path.join(Data_path, 'Store2')
load_path = os.path.join(Data_path, 'Load')
graph_path = os.path.join(Data_path, 'Compressed Graphs')
excluded_path = os.path.join(Data_path, 'No-Path Ports')
const_path = os.path.join(Data_path, 'Constraints')
fasm_path = os.path.join(Data_path, 'FASM')
DLOC_path = os.path.join(Data_path, 'DLOC_dicts')

######## LUT Dual Mode
print_message = True
LUT_Dual = True
block_mode = 'global'   #global|local
route_thru = True
pips_length_dict = {}

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