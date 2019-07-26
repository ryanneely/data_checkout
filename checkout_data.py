##checkout_data.py

##functions to peek at some of the data collected from an experiment
##without having to load and plot everything manually

#Ryan Neely 6/10/19

import numpy as np
import sys
import matplotlib.pyplot as plt
import os
from tdms_files import sort_tdms
from bp_files import process_bp
from physio_files import process_physio
from ephys_files import process_ephys
import matplotlib.pyplot as plt
import filtering as filt
import multiprocessing as mp
mp.freeze_support()

def search_files(path):
    """
    A function to print out a summary of the files present
    in a data directory.
    Args:
        -path: the folder to search
    Returns:
        -prints summary to console
    """
    file_dict = sort_tdms(path)
    print("Discovered {0} high-speed file(s):".format(len(file_dict['highspeed'])))
    for i in file_dict['highspeed']:
        print(" -"+os.path.basename(i))
    print("Discovered {0} low-speed file(s):".format(len(file_dict['lowspeed'])))
    for i in file_dict['lowspeed']:
        print(" -"+os.path.basename(i))
    print("Discovered {0} physiological monitor record(s):".format(len(file_dict['physio'])))
    for i in file_dict['physio']:
        print(" -"+os.path.basename(i))
    print("Discovered {0} recruitment curve file(s)".format(len(file_dict['RC'])))
    print("...")
    print("...")
    print("Loading TDMS files and generating sample plots...")
    return file_dict

def bp_sample(file_dict):
    """
    A function to look in a file dictionary for BP monitor data,
    and print a downsampled version of the pulse waveform
    (for the whole file)
    Args:
        -file_dict: dictionary of all experiment files
    Returns:
        -plot with data from the pulse wf
    """
    resample = 100 ##fixed resampling rate
    ##case where bp data is saved in it's own file
    if len(file_dict['lowspeed']) > 0:
        files = file_dict['lowspeed']
    ##case where it's saved along with the ephys data
    else:
        files = file_dict['highspeed']
    data = process_bp(files,resample=resample,load_time=True)
    y = data['pulse_wf']*100
    x = np.linspace(0,data['time']/60.0,y.size)
    fig,ax = plt.subplots(1)
    ax.plot(x,y,color='r')
    fig.suptitle("Blood pressure waveform",fontsize=12)
    ax.set_xlabel("Time, mins",fontsize=12)
    ax.set_ylabel("Pressure, mmHg",fontsize=12)
    plt.show()

def physio_sample(file_dict):
    """
    Checks for physiomonitor files in the dictionary and prints the physio data, downsampled and
    smoothed with a lowpass filter
    Args:
        -file_dict: dictionary of experiment files
    Returns:
        -plot of several parameters
    """
    ##the wf_increment value in physio data is wrong, so this will resample to 1Hz
    resample = 0.1
    files = file_dict['physio']
    data = process_physio(files,resample=resample,load_time=True)
    sp02 = filt.gauss_convolve(data['sp02'],10000,1)
    hr = filt.gauss_convolve(data['heart_rate2'],10000,1)
    temp = filt.gauss_convolve(data['core_temp'],10000,1)
    x = np.linspace(0,data['time']/60.0,hr.size)
    fig,(ax1,ax2,ax3) = plt.subplots(nrows=3,ncols=1,sharex=True)
    ax1.plot(x,sp02,color='blue')
    ax1.set_title("Oxygen saturation",fontsize=12)
    ax1.set_ylabel("Percent saturated",fontsize=12)
    ax2.plot(x,hr,color='black')
    ax2.set_title("Heart rate",fontsize=12)
    ax2.set_ylabel("BPM",fontsize=12)
    ax3.plot(x,temp,color='green')
    ax3.set_title("Core temperature",fontsize=12)
    ax3.set_ylabel("Degrees Celcius",fontsize=12)
    ax3.set_xlabel("Time, mins",fontsize=12)
    plt.tight_layout()
    plt.show()

def ephys_sample(file_dict):
    resample = 5000
    files = file_dict['highspeed']
    data = process_ephys(files,resample=resample,load_time=True)
    y = data['amp_0']*1000.0
    x = np.linspace(0,data['time'],y.size)
    fig,(ax1,ax2,ax3) = plt.subplots(nrows=3,ncols=1,sharey=True,sharex=False)
    midpoint = int(y.size/2)
    ax1.plot(x[0:5000*5],y[0:5000*5],color='orange')
    ax1.set_ylabel("Voltage, uA",fontsize=12)
    ax1.set_title("Start",fontsize=12)
    ax2.plot(x[midpoint:5000*5+midpoint],y[midpoint:5000*5+midpoint],color='orange')
    ax2.set_ylabel("Voltage, uA",fontsize=12)
    ax2.set_title("Middle",fontsize=12)
    ax3.plot(x[-5000*5:],y[-5000*240:-5000*235],color='orange')
    ax3.set_ylabel("Voltage, uA",fontsize=12)
    ax3.set_title("End",fontsize=12)
    fig.tight_layout()
    plt.show()

def create_plots():
    ##get the dictionary of files in this experiment folder
    file_dict = search_files(path)
    p1 = mp.Process(target=physio_sample,args=(file_dict,))
    p1.start()
    p2 = mp.Process(target=bp_sample,args=(file_dict,))
    p2.start()
    p3 = mp.Process(target=ephys_sample,args=(file_dict,))
    p3.start()

if __name__ == "__main__": 
    path = sys.argv[1]
    create_plots()


