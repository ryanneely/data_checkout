##metadata.py

##functions to parse metadata XML files and extract
##useful experiment info

##by Ryan Neely 6/10/19

import os
import xml.etree.ElementTree as ET

def get_fname(d):
    """
    a function to look for a metadata file, and then grab the 
    experiment name to use as the end file name, if it exists
    inputs: 
        -d: directory to search
    returns:
        fname(str): filename
    """
    ##first check to see if there is any XML files in the folder
    xml_files = [x for x in os.listdir(d) if x.endswith('.xml')]
    if len(xml_files) == 0:
        ##case where there is no XML file
        print("No metadata found for "+d+", default filename used")
        ID = 'processed_data'
    elif len(xml_files) > 1:
        ##ambiguous case where there is more than 1 XML file present
        print("Multiple candidate XML files found for "+d+", default filename used")
        ID = 'processed_data'
    elif len(xml_files) == 1:
        ##now go into the file and look for the experiment 
        mdata = parse_meta_xml(os.path.join(d,xml_files[0]))
        ID = mdata['Experiment ID']
    return ID

def parse_meta_xml(f):
    """
    A function to parse an XML metadata  (from labview) into a easier to handle
    Python dictionary.
    Inputs:
        -f: full path to the XML file in question
    Returns:
        -mdata: metadata dictionary with key:value pairs
    """
    mdata = {}
    root = ET.parse(f).getroot()
    for child in root:
        if 'String' in child.tag:
            mdata[child[0].text] = child[1].text
    for child in root:
        if 'Boolean' in child.tag:
            mdata[child[0].text] = child[1].text
    return mdata


def match_folder(m,d):
    """
    A function to use the data file name in the metadata
    to find the associated data folder in a directory
    Args:
        -m: metadata file to use
        -d: directory to look in for matched file
    returns:
        -f: path to the folder match for the metadata, or None if none is found
    """
    m = parse_meta_xml(m)
    experiment_id = m['Experiment ID']
    folders = os.listdir(d)
    try:
        folder_idx = folders.index(experiment_id)
        folder_path = os.path.join(d,folders[folder_idx])
    except ValueError:
        print("Can't find a folder match for {}".format(experiment_id))
        folder_path = None
    return folder_path


