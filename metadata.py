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
        mdata = parse_meta_xml(xml_files[0])
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

def check_for_xml(d):
    """
    A function to look through an upper-level directory, containing
    folders with experimental data, and then report which folders 
    do NOT contain an XML file (assuming here that the presence
    of an XML file equates with the presence of a metadata file)
    Args:
        -d: the path to the upper-level directory containing the experimental 
        data folders
    Returns:
        -no_xml: list of folder paths that do not contain an xml file
    """
