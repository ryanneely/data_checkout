##bp_files.py

##functions to process data recorded from BP transducers and saved as TDMS files

##author: Ryan Neely 5/31/19

import numpy as np
import h5py
import nptdms
import os
from tdms_files import downsample, get_duration_seconds, order_files
import multiprocessing as mp

##list of channel names in blood pressure data
bp_chans = ['mean_bp','systolic_bp','diastolic_bp','pulse_wf']

def save_bp(files,path_out=None,resample=False,load_time=True):
    """
    Function to create hdf5 file from bp monitor data.
    Args:
        -files: iterable of physio monitor file paths from one experiment (TDMS files)
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
        -resample: if a number, resamples to 'resample' Hz
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        None; data saved in specified location
    """
    global bp_chans
    ##order the files
    files = order_files(files)
    ##create the output data file
    if path_out == None:
        path_out = os.path.dirname(files[0])
    path_out = os.path.join(path_out,'bp_data.hdf5')
    f_out = h5py.File(path_out,'w')
    dsets = load_bp_mp(files,resample,load_time)
    for chan in bp_chans:
        f_out.create_dataset(chan,data=np.hstack([x[chan] for x in dsets]))
    if load_time:
        times = [x['time'] for x in dsets]
        f_out.create_dataset("time",data=np.asarray(np.sum(times)))
    f_out.close()

def process_bp(files,resample=False,load_time=True):
    """
    A function to load the contents of all bp monitor 
    files from one experiment folder into memory
    Args:
        -files: list of files to load/concatinate
        -resample: if a number, resamples to 'resample' Hz
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        -dsets: full concatinated data sets
    """
    global bp_chans
    files = order_files(files)
    tdms = []
    dsets = {}
    tdms = load_bp_mp(files,resample,load_time)
    for chan in bp_chans:
        dsets[chan] = np.hstack([x[chan] for x in tdms])*100.0 ##convert to mmHg
    if load_time:
        times = [x['time'] for x in tdms]
        dsets['time'] = np.sum(times)
    return dsets

def load_bp(path,resample=False,load_time=True,index=0):
    """
    A function to load data from blood pressure monitors, and 
    resample them to a lower rate if necessary
    Args: 
        -path: full path to the datafile
        -resample: if False, loads the full dataset. If a number is given,
            it will resample the data to roughly that sample rate (in Hz)
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        -data: dictionary with labeled data arrays
    """
    global bp_chans
    ##load the file
    tdms_file = nptdms.TdmsFile(path)
    data = {}
    for chan in bp_chans:
        channel_object = tdms_file.object('Group Name',chan)
        if resample:
            chan_data = downsample(channel_object,resample)
        else:
            chan_data = channel_object.data
        data[chan] = chan_data
    if load_time:
        data['time'] = get_duration_seconds(channel_object)
    return data, index

def load_bp_mp(paths,resample=False,load_time=True):
    """
    Function to distribute the loading of multiple files
    across multiple cores. 
    Args:
        -paths: ordered list of file paths where data is stored
        -resample: if a number, resamples the data to 'resample' Hz
        -load_time: if True, includes the duration of the recording in seconds
    Returns:    
        -dsets: ordered list of data dictionaries containing the files
    """
    ##create the argument lists for each version of the function
    args = []
    for i,p in enumerate(paths):
        args.append((p,resample,load_time,i))
    ##now apply the pool to the function
    with mp.Pool(3) as p:
        result = p.starmap(load_bp,args)
    ##make sure results are all in the same order that they were passed
    ##to the pool
    index = [x[1] for x in result]
    sort_idx = np.argsort(index)
    data = [result[i][0] for i in sort_idx]
    return data