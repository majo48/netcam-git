# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# Tool for measuring the average cpu load over a period of time.
# At the end of the measurement, the measurements are copied to a file.
# The assessment is done offline with e.g. excel

# Reference:
# psutil library: https://pypi.org/project/psutil/
# psutil documents: https://psutil.readthedocs.io/en/latest/

import os
import sys
import psutil
import json


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

def save(vals):
    """ save the measurements to a file """
    json_string = json.dumps(vals, indent=4)
    with open('netcam-tool-cpu.log', 'w') as outfile:
        outfile.write(json_string)
    pass

if __name__ == "__main__":
    """ initialize the tool application """
    values = []
    values = run(values)
    save(values)
    # finished
    exit(0)