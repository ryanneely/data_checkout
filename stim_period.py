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
    start = 0
    stop = 0
    for path in files:
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
        """
        TODO: figure out how to end this. Basically the first time start isn't None, 
        you want to keep that as the start forever. But stop should change every time
        it isn't None, because you're moving down the list. Also, if start and stop are
        already defined, you want to stop looking if you come across the next file and there
        isn't any start and stop.
        """


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