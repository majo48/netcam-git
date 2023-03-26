# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# Tool for measuring the average cpu load over a period of time.
# At the end of the measurement, the measurements are copied to a file.
# The assessment is done offline with e.g. excel

# References:
# psutil library: https://pypi.org/project/psutil/
# psutil documents: https://psutil.readthedocs.io/en/latest/

import psutil
import json
import csv
from datetime import datetime


def run(vals):
    """ execute the tool application """
    # gives a single float value
    pct = psutil.cpu_percent(interval=1) # ignore once
    print('Acquiring CPU load data (once per second), quit with ^C ...')
    try:
        while True:
            pct = psutil.cpu_percent(interval=1) # blocking
            vals.append(pct)
        pass
    except KeyboardInterrupt:
        # catch Ctrl+C in IDE Console
        # set in Run/Debug configuration: Emuluate terminal in output console
        pass
    return vals

def save_json(vals):
    """ save the measurements to a json file """
    # format data
    json_string = json.dumps(vals, indent=4)
    # build filename
    now = datetime.now()
    fname = now.strftime('logs/netcam-tool-cpu-%H%M%S.log')
    # write to file
    with open(fname, 'w') as outfile:
        outfile.write(json_string)
    pass

def save_csv(vals):
    """ save data to a .csv file """
    # build filename
    now = datetime.now()
    fname = now.strftime('logs/netcam-tool-cpu-%H%M%S.csv')
    # write to file
    with open(fname, 'w') as outfile:
        wr = csv.writer(outfile)
        wr.writerow(vals)
    pass

if __name__ == "__main__":
    """ initialize the tool application """
    values = []
    values = run(values)
    save_json(values)
    save_csv(values)
    # finished
    exit(0)