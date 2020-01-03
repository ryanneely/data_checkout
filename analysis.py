##analysis.py

##functions to analyze recorded data

##by Ryan Neely 1/3/19

import numpy as np
import tdms_files as tf
import stim_files as sf
import physio_files as pf
import bp_files as bf

def get_stim_window(data,start,stop,pad_min=10.0,fix_outliers=[0.25,5]):
    """
    function to get data around the time of a stim block.
    Args:
        -data: dictionary of data arrays, including the time value. Can have different
            sample rates as long as they were recorded synchronously. 
        -start: start time, in ms, of stim block
        -stop: stop time, in ms, of stim block
        -pad_min = time, in min, before and after stim to pad the data windows
        -fix_outliers: if False, does nothing. Otherwise, should be a 2-element interable
            in which the first value is the max_perc_change variable, and the second element
            is the sigma variable to use for determining which outliers to remove.
    Returns:
        -data: array of data that only includes the data windows requested, and also 
            has elements corresponding to the start, stop times (in ms) of the stim window.
    """
    time = data['time']*1000.0 ##total time of recording, in ms
    pad = pad_min*60.0*1000.0 ##everything will be in ms for 
    var = [x for x in list(data) if x !='time']
    for v in var:
        y = data[v]
        if fix_outliers:
            y = remove_outliers(y,max_perc_change=fix_outliers[0],max_sigma=fix_outliers[1])
        tbase = np.linspace(0,time,y.size) ##the timebase/sample times for this data array
        ##replace the data array in the dictionary with just the requested window
        start_idx = np.where(tbase>start-pad)[0][0]
        end_idx = np.where(tbase<stop+pad)[0][-1]
        data[v] = y[start_idx:end_idx]
    data['start'] = 0
    data['stop'] = stop-start
    data['pad'] = pad 
    return data

def get_stim_info(path):
    """
    A function that looks at a experiment folder path, finds the
    data files containing the stim records, parses them, and returns
    the clean stim information, including the binary stim on/off record,
    and the stim pulse onset/offset times.
    Args:
        -path: folder path containing the experiment data
    Returns:
        data: dictionary with the following elements:
            -start: stim pulse onset times
            -stop: stim pulse offset times 
            -z: binary stim on/off array spanning the fill recording time
    """
    files = tf.search_files(path) ##dictionary of valid tdms files
    data = sf.process_stim(files['highspeed']) ##assume that the stim mon channel is always in the highspeed data set
    return data

def get_tstim(start,stop):
    """
    Returns the time, in ms, of the onset and offset of a stimulation
    block for a given experiment. Assumes that there is only one stim
    block per experiment!
    Args:
        -start: array of stim pulse start times in ms
        -stop: array of stim pulse stop times in ms
    Returns:
        -start: single value, in ms, of when as stim block starts
        -stop: single value, in ms, of when a stop block ends
    """
    return start[0]*1000, stop[-1]*1000

def remove_outliers(data,max_perc_change=0.25,max_sigma=5):
    """
    A function to remove outlier values from data. Sometimes the physiological
    montitors drop data points or generate spike values that aren't reflective of 
    anything real. This function does a good first pass at removing those values.
    We're using a 2-step process; the first uses percent changes from point-to-point,
    and the second uses the output of the first process and looks for major changes from the 
    std deviation. 
    Args:
        -data: raw data array to process
        -max_sigma: multiple of the std deviation to use as a threshold for detecting outlier points. 
    Returns:
        -data: same data with outlier values removed
    """
    ##because we sample much faster than variables change, we can assume that any fast changes 
    ##are due to error.
    ##find the median value of these data; won't use the mean because it's more sensitive to outliers
    median = np.median(data)
    ##find the abs change point-to-point
    dt = np.abs(np.diff(data))
    ##the max allowable change
    max_dt = median*max_perc_change
    ##flag indexes with erroneous dt's
    flag = np.where(dt>max_dt)[0]
    ##for each flagged index, replace the data val with the val from the previous sample
    for i in flag:
        data[i+1] = data[i]
    ##now run a second pass using the std deviation
    std = np.std(data)
    max_sigma = std*max_sigma
    ##find difference from the median at each point
    delta = np.abs(data-median)
    ##find where the difference exceeds the max allowable change
    flag = np.where(delta>max_sigma)[0]
    ##for each flagged index, replace the data val with the val from the previous sample
    for i in flag:
        data[i] = data[i-1] ##this should be able to handle multiple dropped points in a row
    return data
