##physio_files.py

##functions for processing the physiological monitor data
##produced by the SomnoSuite and streamed over serial port 
##into labview TDMS format.

#by Ryan Neely 6/10/19

import numpy as np
import h5py
import nptdms
import os
from tdms_files import downsample, get_duration_seconds, order_files

##a lookup table for channel names in serial data
serial_chans = {
    'Untitled':'percent_isoflurane',
    'Untitled 1':'pad_temp',
    'Untitled 2':'core_temp',
    'Untitled 3':'sp02',
    'Untitled 4':'heart_rate2',
    'Untitled 5':'perfusion'
}


def save_physio(files,path_out=None,resample=False,load_time=True):
    """
    Function to create hdf5 file from physiological monitor data.
    Args:
        -files: iterable of physio monitor file paths from one experiment (TDMS files)
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
        -resample: if a number, will resample at "resample" hz
        -load_time: if True, loads duration of the recording in seconds       
    Returns:
        None; data saved in specified location
    """
    global serial_chans
    ##order the files
    files = order_files(files)
    ##create the output data file
    if path_out == None:
        path_out = os.path.dirname(files[0])
    path_out = os.path.join(path_out,'physio_data.hdf5')
    f_out = h5py.File(path_out,'w')
    dsets = []
    for f in files:
        print("loading "+f)
        data = load_physio(f,resample,load_time)
        dsets.append(data)
    for chan in serial_chans.values():
        f_out.create_dataset(chan,data=np.hstack([x[chan] for x in dsets]))
    if load_time:
        times = [x['time'] for x in dsets]
        f_out.create_dataset("time",data=np.asarray(np.sum(times)))
    f_out.close()

def process_physio(files,resample=False,load_time=True):
    """
    A function to load the contents of all physio monitor 
    files from one experiment folder into memory
    Args:
        -files: list of files to load/concatinate
        -resample: if a number, will resample at "resample" hz
        -load_time: if True, loads the duration of the recording in seconds
    Returns:
        -dsets: full concatinated data sets
    """
    global serial_chans
    ##order the files 
    files = order_files(files)
    tdms = []
    dsets = {}
    for f in files:
        print("loading "+f)
        data = load_physio(f,resample,load_time)
        tdms.append(data)
    for chan in serial_chans.values():
        dsets[chan] = np.hstack([x[chan] for x in tdms])
    if load_time:
        times = [x['time'] for x in tdms]
        dsets['time'] = np.sum(times)
    return dsets

def load_physio(path,resample=False,load_time=True):
    """
    A function to load a TDMS dataset aquired from the SomnoSuite
    serial pipe.
    Args:
        -path: full path to the datafile
        -resample: if a number, resamples the data to 'resample' Hz
        -load_time: if True, includes the duration of the recording in seconds
    Returns:
        -data: dictionary of data arrays arranged by channel names
    """
    global serial_chans
    ##load our file
    tdms_file = nptdms.TdmsFile(path)
    ##load the data into arrays and put into a dictionary
    data = {}
    for chan in list(serial_chans.keys()):
        channel_object = tdms_file.object('Untitled',chan)
        if resample:
            chan_data = downsample(channel_object,resample)
        else:
            chan_data = channel_object.data
        data[serial_chans[chan]] = chan_data
    if load_time:
        data['time'] = get_duration_seconds(channel_object)/10.0 ##not sure why I need to use this scale factor here, but LabView seems to be saving the wf increment at the wrong value (1 instead of 10?)
    return data
