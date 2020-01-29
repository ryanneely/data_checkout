##ephys_files.py

##functions to parse/process/save ephys data from
##TDMS files saved in Labview

##by Ryan Neely 6/10/19

import numpy as np
import nptdms
from tdms_files import file_ids, downsample, get_duration_seconds, order_files
import os
import h5py
import multiprocessing as mp

def get_ephys_chans(tdms_file):
    """
    Function to look for ephys channel names in a tdms file.
    Returns a list of assumed ephys channel names that are present.
    In addition to the fact that some ephys channels are saved under different
    names, there could also be a variable number of channels in the file.
    Inputs:
        -tdms_file: nptdms file object
    Returns:
        -ephys_chans: list of ephys channels present in the file
    """
    ##start by getting the channel names in a dictionary
    ids = file_ids(tdms_file)
    ephys_chans = []
    for group in ids:
        for chan in ids[group]:
            if "amp" in chan:
                ephys_chans.append(chan)
    return ephys_chans

def save_ephys(files,path_out=None,resample=False,load_time=True):
    """
    Function to create hdf5 file from ephys data.
    Args:
        -files: iterable of ephys file paths from one experiment (TDMS files)
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
        -resample: if a number, resamples to 'resample' Hz
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        None; data saved in specified location
    """
    ##order the files
    files = order_files(files)
    ##create path
    if path_out == None:
        path_out = os.path.dirname(files[0])
    path_out = os.path.join(path_out,'ephys_data.hdf5')
    f_out = h5py.File(path_out,'w')
    dsets = load_ephys_mp(files,resample,load_time)
    ##standardize the channel names
    ephys_chans = [x for x in list(dsets[0]) if x != 'time']
    for i,chan in enumerate(ephys_chans):
        f_out.create_dataset("amp_"+str(i),data=np.hstack([x[chan] for x in dsets]))
    if load_time:
        times = [x['time'] for x in dsets]
        f_out.create_dataset("time",data=np.asarray(np.sum(times)))
    f_out.close()

def process_ephys(files,resample=False,load_time=True):
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
    files = order_files(files)
    dsets = {}
    tdms = load_ephys_mp(files,resample,load_time)
    ##extract the channel names from the last dataset processed
    ephys_chans = [x for x in list(tdms[0]) if x != 'time']
    for i,chan in enumerate(ephys_chans):
        dsets["amp_"+str(i)] = np.hstack([x[chan] for x in tdms])
    if load_time:
        times = [x['time'] for x in tdms]
        dsets['time'] = np.sum(times)
    return dsets

def process_ephys2(files, resample=False, load_time=True, hd5_output_name=None):
    """
    A function to load the contents of all bp monitor
    files from one experiment folder into memory
    Args:
        -files: list of files to load/concatinate
        -resample: if a number, resamples to 'resample' Hz
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        -dsets: full concatinated data sets

    Note: In this version, we added the possibilities to save the ephys files
    after processing it, if the 'hd5_output_name' is specified.
    """
    files = order_files(files)
    dsets = {}
    tdms = load_ephys_mp(files,resample,load_time)
    ##extract the channel names from the last dataset processed
    ephys_chans = [x for x in list(tdms[0]) if x != 'time']
    for i,chan in enumerate(ephys_chans):
        dsets["amp_"+str(i)] = np.hstack([x[chan] for x in tdms])
    if load_time:
        times = [x['time'] for x in tdms]
        dsets['time'] = np.sum(times)

    if hd5_output_name is not None:
        f_out = h5py.File(hd5_output_name, 'w')
        for i,chan in enumerate(ephys_chans):
            f_out.create_dataset("amp_" + str(i), data=np.hstack([x[chan] for x in tdms]))
        if load_time:
            f_out.create_dataset("time", data=np.asarray(np.sum(times)))
        f_out.close()

    return dsets



def load_ephys(path,resample=False,load_time=True,index=0):
    """
    A function to load data from ephys files, and
    resample them to a lower rate if necessary
    Args:
        -path: full path to the datafile
        -resample: if False, loads the full dataset. If a number is given,
            it will resample the data to roughly that sample rate (in Hz)
        -load_time: if True, loads the duration of the recording in seconds
        -index: useful for ordering after asynchronous multiprocessing
    Returns:
        -data: dictionary with labeled data arrays
    """
    ##load the file
    tdms_file = nptdms.TdmsFile(path)
    ##figure out which channels here are ephys channels
    ephys_chans = get_ephys_chans(tdms_file)
    data = {}
    for chan in ephys_chans:
        try:
            channel_object = tdms_file.object('Group Name',chan)
        except KeyError:
            ##case where the group name is different
            channel_object = tdms_file.object("ephys",chan)
        if resample:
            chan_data = downsample(channel_object,resample)
        else:
            chan_data = channel_object.data
        data[chan] = chan_data
    if load_time:
        data['time'] = get_duration_seconds(channel_object)
    return data, index

def load_ephys_mp(paths,resample=False,load_time=True):
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
        result = p.starmap(load_ephys,args)
    ##make sure results are all in the same order that they were passed
    ##to the pool
    index = [x[1] for x in result]
    sort_idx = np.argsort(index)
    data = [result[i][0] for i in sort_idx]
    return data

def load_ephys2(paths):
    """
    TODO: create a function to load these files that doesn't take up so much memory.

    What is the most efficient way of doing this? Right now memory and transfer speeds from disk
    are the biggest bottleneck. I want to avoid having a lot of data arrays present in memory all at
    once. It may be possible to split this across multiple cores, but it needs to be done in a way
    that doesn't involve operating and loading many different files/arrays at once.

    The problem for a single data array is this:
    -load the entire TDMS file into memory. This is unavoidable, but each file is only ~600MB or so.
    -grab the data array corresponding to one signal
    -repeat for each file until we have each piece of the data arrays, which are then concatenated into one
    -repeat this whole process for each signal

    So, maybe the way to do it is to go signal-by-signal. That would look like this, assuming multiprocessing is used:
    -create a shared memory map for the pool
    -spawn one process for each file to load
    -grab the data chunks, and add them to the shared memory in order
    -repeat for each signal

    (note: check the pagefile loading options in nptdms)

    """
