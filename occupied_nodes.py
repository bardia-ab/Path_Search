import pickle, os, time
from Functions import *

start_time = time.time()

pips_file = r'C:\Users\t26607bb\Desktop\used_pips.txt'
used_pips = get_occupied_pips2(pips_file)
#store_data(GM.Data_path, 'used_pips.data', occupied_pips)
#occupied_pips = load_data(GM.Data_path, 'used_pips.data')
#nodes = {node for pip in used_pips for node in pip}
#clk_nodes = set(filter(lambda x: re.match('INT_X.*GCLK', x), nodes))


print('--- %s seconds ---' %(time.time() - start_time))