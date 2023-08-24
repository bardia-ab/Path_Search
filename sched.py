import os, time, schedule

def job():
    os.system(f'python3 Relocate_CUTs.py X46Y90')
    coords = {'X45Y90', 'X44Y90'}
    for coord in coords:
        commands = [f'python3 Compressed_Graph.py {coord}', f'python3 temp.py {coord}', f'python3 Relocate_CUTs.py {coord}']
        for command in commands:
            os.system(command)
            time.sleep(10)

schedule.every().day.at('23:00').do(job)

while True:
    schedule.run_pending()
    time.sleep(1)