##tdms_files.py

##generic functions for looking at/sorting through TDMS tdms_files

##by Ryan Neely 6/10/19

"""
Possible variations of  data files:

Rig1, ephys 2.1:
-2 types of TDMS data files:
    -DAQ
        -group name = Group Name
        -channels = heart_rate1, pulse_wf, mean_bp, systolic_bp, diastolic_bp, stim_mon, amplifier
    -serial
        -group name = Untitled
        -channels = Time, Untitled, Untitled1, ...Untitled5 
        'Untitled':'percent_isoflurane',
        'Untitled 1':'pad_temp','Untitled 2':'core_temp',
        'Untitled 3':'sp02',
        'Untitled 4':'heart_rate2',
        'Untitled 5':'perfusion'


Rig1, ephys 3.0:
-2 types of TDMS data files:
    -DAQ
        -group name = Group Name
        -channels = amp_1, amp_n, pulse_wf, mean_bp, systolic_bp, diastolic_bp, stim_mon
    -serial
        -group name = Untitled
        -channels = Time, Untitled, Untitled1, ...Untitled5 
        'Untitled':'percent_isoflurane',
        'Untitled 1':'pad_temp','Untitled 2':'core_temp',
        'Untitled 3':'sp02',
        'Untitled 4':'heart_rate2',
        'Untitled 5':'perfusion'

Rig2, ephys 3.0:
-3 types of TDMS data files:
    -ephys
        -group name = ephys
        -channels = amp_0, ...amp_n, stim_mon
    -physioMon
        -group name = Untitled
        -channels = Time, Untitled, Untitled1, ...Untitled5
        'Untitled':'percent_isoflurane',
        'Untitled 1':'pad_temp','Untitled 2':'core_temp',
        'Untitled 3':'sp02',
        'Untitled 4':'heart_rate2',
        'Untitled 5':'perfusion'
    -bpMon
        -group name = Group Name
        -channels = heart_rate1, mean_bp, systolic_bp, diastolic_bp, pulse_wf

Rig2, ephys 2.0:
-2 types of TDMS data files:
    -DAQ
        -group name = Group Name
        -channels = heart_rate1, mean_bp, systolic_bp, diastolic_bp, pulse_wf, amplifier
    -serial
        -group name = Untitled
        -channels = Time, Untitled, Untitled1, ...Untitled5 
        'Untitled':'percent_isoflurane',
        'Untitled 1':'pad_temp','Untitled 2':'core_temp',
        'Untitled 3':'sp02',
        'Untitled 4':'heart_rate2',
        'Untitled 5':'perfusion'

"""
import numpy as np
import nptdms
import os
from scipy.signal import decimate

def sort_tdms(d):
    """
    A function to look for all of the relevant TDMS files, and group them accordingly. 
    Inputs:
        d- directory to search
    Returns:
        -dictionary of lists of file paths, grouped according to what kinds of data are in each file.
            results will vary based on the version of acquisition software that was used.
    """
    ##set up the results dictionary
    result = {
        'physio':[], ##at time of writing these should be universal across builds (serial port data)
        'highspeed':[], ##this may include ephys, stim monitors, and BP monitors
        'lowspeed':[], ##this would be any DAQ devices sampling at a lower rate; i.e. the BP monitor
        'RC':[] ##this would be data files from recruitment curves
    }
    ##find all the TDMS files in the folder; exclude the index files
    files = [os.path.join(d,x) for x in os.listdir(d) if x.endswith(".tdms")]
    ##now parse into the individual folders, taking into account the naming conventions
    ##of different possible sources
    result['physio'] = [x for x in files if 'serial' in x or 'physioMon' in x]
    result['highspeed'] = [x for x in files if 'DAQ' in x or 'ephys' in x]
    result['lowspeed'] = [x for x in files if 'bpMon' in x]
    result['RC'] = [x for x in files if 'uA' in x or 'mA' in x]
    return result

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

def file_ids(tdms_file):
    """
    Function to get the group and channel IDs for a tdms file
    Inputs:
        -tdms_file: nptdms
    Returns:
        -dictionary with group:[chan_1,chan_2...] pairs
        """
    ids = {}
    groups = tdms_file.groups()
    for g in groups:
        ##a list of channel objects in the group
        channels= tdms_file.group_channels(g)
        ids[g] = []
        for c in channels:
            ##get a dictionary of channel properties for each group
            props = c.properties
            ##get just the channel name
            name = props['NI_ChannelName']
            ids[g].append(name)
    return ids


def get_group_fs(tdms_file,tdms_group):
    """
    Function to get the sample rate of all channels in a group
    (and make sure they are all the same)
    Args:
        -tdms_file: the file object to pull data from
        -tdms_group: nptmds file group name(str)
    Returns:   
        -fs: sample rate of the channels in this group
    """
    wf_intervals = []
    for chan in tdms_file.group_channels(tdms_group):
        wf_intervals.append(chan.properties['wf_increment'])
    assert len(set(wf_intervals))==1, "Different sample rates detected in "+tdms_group
    return 1.0/wf_intervals[0]

def get_duration_seconds(channel_object):
    """
    Gets the time array in seconds. This is technically an
    estimate, because we don't timestamp each sample, so the 
    time array is reconstructed from the wf_increment and the total 
    number of samples.
    Args:
        -channel_object: tdms_file channel object
    Returns:
        -Time: duration in seconds of the collected data
    """
    wf_increment = channel_object.properties['wf_increment']
    n_samples = channel_object.data.size
    return n_samples*wf_increment

def downsample(channel_object,new_fs):
    """
    A function to resample a data array at a new, lower sample
    rate to reduce its size. 
    Args:
        -channel_object: nptdms channel object to resample
        -new_fs: desired sample rate, in hz (should be lower than original fs)
    Returns: 
        -data: resampled array of values
    """
    ##get the starting fs of the data
    old_fs = 1/channel_object.properties['wf_increment']
    ##make sure this is a request for downsampling
    assert new_fs < old_fs, "Error: requested sample rate is higher than original rate"
    factor = int(np.round(old_fs/new_fs))
    resampled = decimate(channel_object.data,factor,ftype='fir')
    return resampled

def order_files(file_list):
    """
    A function to order files based on an assumed naming convention
    Args:
        -file_list: a list of files to order
    Returns:
        -file_list: same list with the files in ascending order
    """
    ##don't bother if there's only one file in the list
    if len(file_list) <= 1:
        pass
    else:
        unnumbered = []
        numbered = []
        try:
            file_numbers = np.array([int(x[-9:-5]) for x in file_list])
            numbered = file_list
        except ValueError:
            ##the first file in a sequence from Labview doesn't have a numeric tag, so handle this
            for i,f in enumerate(file_list):
                if not f[-9:-5].isdigit():
                    unnumbered.append(file_list[i])
                else:
                    numbered.append(file_list[i])
            file_numbers = np.array([int(x[-9:-5]) for x in numbered])
        ##put the files (numbers) in order
        order = np.argsort(file_numbers)
        numbered = [numbered[i] for i in order]
        ##if we have more than one un-numbered file, warn the user (not sure why this would be)
        if len(unnumbered)>1:
            print("Warning- more than one un-numbered file detected")
        file_list = unnumbered+numbered
    return file_list