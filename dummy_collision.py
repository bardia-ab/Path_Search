import re, time, os
from Functions import *
import Global_Module as GM

start_time = time.time()

s_FFs_tuple = load_data(GM.Data_path, 's_FFs_tuple.data')
s_dummy_tuple = load_data(GM.Data_path, 's_dummy_tuple.data')
l_FFs_tuple = load_data(GM.Data_path, 'l_FFs_tuple.data')
l_dummy_tuple = load_data(GM.Data_path, 'l_dummy_tuple.data')

print(len(s_FFs_tuple & s_dummy_tuple))
print(len(l_FFs_tuple & l_dummy_tuple))

print('--- %s seconds ---' %(time.time() - start_time))