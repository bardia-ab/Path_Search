import os, time


start_time = time.time()

input_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\input.bit'
output_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\output.bit'
fasm_path = r'C:\Users\t26607bb\Desktop\CPS_Project\Vivado_Projects\pyteman_test\FASM\LED_other_clock_group_LUT\new.fasm'
pyteman_path = r' C:\Users\t26607bb\Desktop\Pyteman\pyteman_dist\fasm2bit.py'

command = f'python {pyteman_path} {fasm_path} {input_path} {output_path}'

os.system(command)

print('--- %s seconds ---' %(time.time() - start_time))