from tqdm import tqdm
from joblib import Parallel, delayed
import time

def func(entry):
    entry.pop()
    return entry

entry = list(range(1000))
pbar = tqdm(range(len(entry)))

while pbar:
    l_prev = len(entry)
    entry = func(entry)
    time.sleep(0.2)
    pbar.update(l_prev - len(entry))