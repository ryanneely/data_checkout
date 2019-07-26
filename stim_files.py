##stim_files.py

##functions for loading and processing stimulation data stim_files

##by Ryan Neely 6/11/19

import numpy as np
import nptdms
import os
import h5py
from tdms_files import order_files
from scipy.signal import find_peaks

stim_chan = 'stim_mon'

def get_stim_times(stim,thresh1,thresh2,minimal_dist):
    """
    A function to extract the times at which stimulation occurs
    from the raw recorded waveform. 
    Args:
        -stim: stim data array containing the continuously recorded stim output
        -minimal_dist: the minimum distance two waveforms need to be apart from 
            each other in order to be considered a separate train (in samples)
        -thresh1: the threshold ABOVE which to consider an active stim pulse. Note 
            that these values have to be set manually 
        -thresh2: the threshold BELOW which to consider an active stim pulse
    Returns:
        start_idx: timestamps (scaled in ms) at the start of a stim train
        stop_idx: timestamps (scaled in ms) at the end of a stim train
        z: a waveform showing when the stim train is occurring
    """
    ##get rid of any NaN values from the data; replace with 0's
    to_replace = np.where(np.isnan(stim))[0]
    stim[to_replace] = 0.0
    ##find out where stim is NOT occurring based on the threshold values,
    ##and set these time points to 0
    off = np.where((stim<thresh1)&(stim>thresh2))[0]
    stim[off] = 0
    #now we perform some tricks to figure out where a stim train is taking place
    ##first make a padded version of y
    stim_pad = np.hstack([np.zeros(minimal_dist),stim,np.zeros(minimal_dist)]) 
    ##allocate some memory here
    z = np.zeros(stim.shape)
    ##now we ask: does point n have samples before AND after it in the
    ##minimalDist range that are non-zero? If yes, then it counts as part
    ##of the stim train
    for i in range(z.size):
        if np.any(stim_pad[i:i+minimal_dist+1]) and np.any(stim_pad[i-1+minimal_dist:i+2*minimal_dist]):
            z[i] = 1.0
    ##now, we take the difference between any two points, and the locations where this ==1
    ##is the rising edge, and the locations where this == -1 are the falling edge
    ##TODO: see if this holds in all cases, especially different sample rates
    start_idx = np.where(np.diff(z)==1)[0]
    stop_idx = np.where(np.diff(z)==-1)[0]
    return start_idx, stop_idx, z

def save_stim(files,path_out=None):
    """
    Function to create hdf5 file from ephys data.
    Args:
        -files: iterable of ephys/stim file paths from one experiment (TDMS files)
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
    Returns:
        None; data saved in specified location
    """
    ##order the files
    files = order_files(files)
    ##create path
    if path_out == None:
        path_out = os.path.dirname(files[0])
    path_out = os.path.join(path_out,'stim_data.hdf5')
    f_out = h5py.File(path_out,'w')
    starts = []
    stops = []
    zs = []
    offset = 0
    for f in files:
        print("loading "+f)
        start,stop,z,fs = load_stim(f,offset)
        starts.append(start)
        stops.append(stop)
        zs.append(z)
        offset+=z.size
    ##now add to the data file
    f_out.create_dataset("start",data=np.hstack(starts)/fs)
    f_out.create_dataset("stop",data=np.hstack(stops)/fs)
    f_out.create_dataset("z",data=np.hstack(zs))
    f_out.close()


def process_stim(files):
    """
    Function to create a data dictionary from stim data.
    Args:
        -files: iterable of ephys/stim file paths from one experiment (TDMS files)
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
    Returns:
        data: dictionary with data from stim file, processed accordingly
    """
    ##order the files
    files = order_files(files)
    data = {}
    starts = []
    stops = []
    zs = []
    offset = 0
    for f in files:
        print("loading "+f)
        start,stop,z,fs = load_stim(f,offset)
        starts.append(start)
        stops.append(stop)
        zs.append(z)
        offset+=z.size
    ##now add to the data dict
    data['start']=np.hstack(starts)/fs
    data['stop']=np.hstack(stops)/fs
    data['z']=np.hstack(zs)
    return data


def load_stim(path,offset=0):
    """
    A function to load a stim channel from a TDMS file, and extract the times when stimulation is "on"
    Args: 
        -path: full path to the datafile
        -offset: the number of samples to offset the start,stop sample values by (in case we are concatenating multiple files)
    Returns:
        -start: start times of stim wf
        -stop: end times of stim wf
        -z: binary stim on/off array for full sample rate
        -fs: sample rate for this dataset
    """
    global stim_chan
    ##load the file
    tdms_file = nptdms.TdmsFile(path)
    channel_object = tdms_file.object('Group Name',stim_chan)
    raw = channel_object.data
    fs = 1/channel_object.properties['wf_increment']
    ##process the stim output (guessing on parameters here)
    start,stop,z = get_stim_times(raw,0.1,-0.1,25)
    start = start+offset
    stop = stop+offset
    return start,stop,z,fs
