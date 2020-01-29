"""
Functions for loading and processing stimulation data stim_files

Author: Ryan Neely and Marius Guerard
"""
import os

import numpy as np
import nptdms
import h5py
from scipy.signal import find_peaks
from sklearn.mixture import GaussianMixture as GMM
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.interactive(False)

from tdms_files import order_files


stim_chan = 'stim_mon'


def save_raw_stim(files, group_name='Group Name', path_out=None, record_raw='screenshot'):
    """
    Function to create hdf5 file from ephys data.
    Args:
        -files: iterable of ephys/stim file paths from one experiment (TDMS files)
        - group_name: Name of the group storing the stim data in the tdms file
        -path_out: optional alternative path to save the data file. If
            not specified, file is saved in same location as input files.
        - record_raw: 'full' will record the full stim recording (~4GB), 'screenshot'
        will just save a plot of it with the start and stop of the stim (but takes longer).
    Returns:
        - the stim raw vector (memory intensive), the start and the stop of the stim
    """
    ## Order the files.
    files = order_files(files)
    offset = 0
    raw_list = []
    fs_list = []
    for f in files:
        print("loading " + f)
        raw, fs = _load_raw_stim(f, group_name=group_name)
        raw_list.append(raw)
        fs_list.append(fs)
        offset += raw.size
    raw_stim = np.hstack(raw_list)
    ### Check that the sampling rate does not change during the recording.
    assert len(set(fs_list)) == 1, "Error: Sampling rate changes"
    ### Find start and stop time of stim.
    stim_start, stim_stop = _get_stim_times(raw_stim)
    ##now add to the data file
    if path_out == None:
        path_out = os.path.join(os.path.dirname(files[0]), 'stim_data.hdf5')
    f_out = h5py.File(path_out, 'a')
    if record_raw == 'full':
        f_out.create_dataset("raw", data=raw_stim)
    elif record_raw == 'screenshot':
        fig = plt.figure()
        plt.vlines([stim_start, stim_stop], 0, max(raw_stim), color='r')
        plt.plot(raw_stim, zorder=1)
        plt.savefig(path_out + '.png')
        plt.close(fig)
    f_out.create_dataset("fs_stim", data=fs)
    f_out.create_dataset("time_stim", data=len(raw_stim)/fs)
    f_out.create_dataset("stim_start", data=stim_start)
    f_out.create_dataset("stim_stop", data=stim_stop)
    f_out.close()
    return raw_stim, stim_start, stim_stop


def _load_raw_stim(path, group_name='Group Name'):
    """
    A function to load a stim channel from a TDMS file, and extract the
    raw values of stim and the sampling rate (usually 25kHz).
    Args:
        - path: full path to the datafile
        - group_name: Name of the group storing the stim data in the tdms file
    Returns:
        -raw: raw stim.
        -fs: sample rate for this dataset.
    """
    global stim_chan
    ##load the file
    tdms_file = nptdms.TdmsFile(path)
    # channel_object = tdms_file.object('Group Name', stim_chan)
    channel_object = tdms_file.object(group_name, stim_chan)
    raw = channel_object.data
    fs = 1/channel_object.properties['wf_increment']
    return raw, fs


def _get_stim_times(raw_stim, thresh=None, margin=2.5):
    """ Find the start and the stop of the stim on the raw complete recording
    by fitting a gaussian to the distribution of the value above the 'thresh'
    and taking the start and stop as the edge of the gaussian.

    Args:
        - raw_stim: the array containing the raw values of stimulation.
        - thresh: The threshold (usually defined to be max(raw) / 10.
        - margin: The margin around the stimulation bloc.
    Returns:
        -stim_start: raw stim.
        -stim_stop: sample rate for this dataset.


    Note: Here GMM could be replaced by standard unimodal gaussian fitting,
    However, GMM allows for multimodal gaussian fitting in the case we have
    multiple stimulations times.
    """
    if thresh is None:
        thresh = max(raw_stim) / 10
    in_stim = np.where(raw_stim > thresh)[0]
    X = in_stim.reshape(-1, 1)
    # Feat a Gaussian Mixture Model.
    gmm = GMM(n_components=1, covariance_type='diag').fit(X)
    middle = gmm.means_[0][0]
    std = np.sqrt(gmm.covariances_[0][0])
    stim_start = middle - margin * std
    stim_stop = middle + margin * std
    return stim_start, stim_stop
