##stim_period.py

##trying to write a more efficient function to just grab the stimulation
##star/stop times from raw TDMS data

##by Ryan Neely 1/6/2020

import numpy as np
import nptdms
import multiprocessing as mp
from tdms_files import order_files

stim_chan = 'stim_mon' ##this should be the name of the stim channel in all files

def get_period(files):
    """
    A function to get the stimulation onset and offset times
    (for the whole stimulation block), in ms, relative to the start
    of the data file.
    Args:
        -files: list of tdms files that contain the stim waveform data
    Returns:
        -start, stop: times, in ms
    """
    global stim_chan
    ##make sure that the files are in the correct order
    files = order_files(files)
    start = None
    stop = None
    files = iter(files)
    ##this will churn through the files until a start value is found
    while start == None:
        path = next(files)
        tdms_file = nptdms.TdmsFile(path)
        ##here are a couple diffent possibilities for how things could be named
        try:
            channel_object = tdms_file.object('Group Name',stim_chan)
        except KeyError:
            try:
                channel_object = tdms_file.object('ephys',stim_chan)
            except KeyError:
                channel_object = tdms_file.object('Untitled',stim_chan)
        start,stop = find_stim(channel_object)
    ##now we'll keep going until there aren't any stim pulses detected
    end = stop ##start by storing 'stop' in a new var, so we don't overwrite 'stop' in the event
    ##that all of the stim data is in the first file
    while end != None:
        ##if end is not None, we must have found a continuation of the stim block in the previous file,
        ##so update 'stop' to reflect this
        stop = end
        path = next(files)
        tdms_file = nptdms.TdmsFile(path)
        ##here are a couple diffent possibilities for how things could be named
        try:
            channel_object = tdms_file.object('Group Name',stim_chan)
        except KeyError:
            try:
                channel_object = tdms_file.object('ephys',stim_chan)
            except KeyError:
                channel_object = tdms_file.object('Untitled',stim_chan)
        ##here we want to ignore any new values of start, because the start value we found in 
        ##an earlier file should be the true start
        ignore,end = find_stim(channel_object)
    return start,stop

def find_stim(channel_object,thresh=0.1,min_dist=50,min_pulses=30):
    """
    A function to find the index of a stim onset and offset,
    if it exists, in a tdms channel object.
    Args:
        -channel_object: nptdms channel object containing the stim monitor data
        -thresh: threshold value of the stim monitor recording to consider the 
            presence of a stim pulse
        -min_dist: the minimum distance (samples) between points to count as an additional pulse.
            At 25kHz, the pulses have a little more than 80pts between them.  
        -min_pulses: the minimum number of pulses needed to count as a real stim train.
    Returns:
        -start,stop: indices of the onset and offset of the stim block in this data array
    """
    start = None
    stop = None
    pts = np.where(np.abs(channel_object.data)>thresh)[0] ##any place that the wf crosses the thresh
    dist = np.diff(pts) ##the distance between points exceeding the threshold
    n_pulses = np.where(dist>min_dist)[0] #these should be the points of all the separate pulses
    if n_pulses.size>min_pulses:
        start = pts[0]
        stop = pts[-1]
    return start,stop