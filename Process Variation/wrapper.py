import os

os.system("python3 split_CRs_TC.py")
os.system("python3 gen_constraints_wrapper.py")
os.system("python3 gen_bitstream.py")