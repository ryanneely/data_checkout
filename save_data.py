# save_data.py

# function to save hdf versions of TDMS files contained in a directory

# by Ryan Neely 9/22/19

import tdms_files
import ephys_files
import physio_files
import stim_files
import bp_files
import metadata
import multiprocessing as mp
import os

def save_exp(f,check_meta=False,**kwargs):
    """
    A function to save all of the data contained in a single experiment directory.
    Args:
        -f: path to the directory containing the experiment data
        -check_meta: if True, requires the directory to contain a metadata
            file, and then only processes signals that were marked "good"
            for this data file.
        -**kwargs: used to specify if any signals should be resampled. Possible kwargs
            include resample_ephys, resample_bp, resample_physio. If you do include these
            kwargs, the paired value should be the desired resample rate in Hz.
    """
    ##get a list of the data files
    file_dict = tdms_files.search_files(f)
    ##parse kwargs
    if 'resample_ephys' in kwargs:
        resample_ephys = kwargs['resample_ephys']
    else:
        resample_ephys = False
    if 'resample_bp' in kwargs:
        resample_bp = kwargs['resample_bp']
    else:
        resample_bp = False
    if 'resample_physio' in kwargs:
        resample_physio = kwargs['resample_physio']
    else:
        resample_physio = False
    ##check metadata, if requested
    ephys_ok = True
    physio_ok = True
    bp_ok = True
    if check_meta:
        if metadata.get_fname == 'processed_data':
            ##if no meta file is found, this function returns 'processed_data'
            ephys_ok = False
            bp_ok = False
            physio_ok = False
            print("No metadata found for {}; skipping".format(f))
        else:
            metafile = [x for x in os.listdir(f) if x.endswith('.xml')][0]
            info = metadata.parse_meta_xml(os.path.join(f,metafile))
            if not info['Ephys good']:
                ephys_ok = False
            if not info['Physio good']:
                physio_ok = False
            if not info['BP good']:
                bp_ok = False
    ##now with all the checks performed, we can save the data:
    if ephys_ok:
        print("Saving ephys data...")
        ephys_files.save_ephys(file_dict['highspeed'],path_out=None,
            resample=resample_ephys,load_time=True)
        print("...done!")
    if bp_ok:
        print("Saving bp data...")
        if len(file_dict['lowspeed']) > 0:
            files = file_dict['lowspeed']
        else:
            files = file_dict['highspeed']
        bp_files.save_bp(files,path_out=None,
            resample=resample_bp,load_time=True)
        print("...done!")
    if physio_ok:
        print("Saving physio data...")
        physio_files.save_physio(file_dict['physio'],path_out=None,
            resample=resample_physio,load_time=True)
        print("...done!")

    
    

