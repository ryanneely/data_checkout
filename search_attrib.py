# search_attrib

# Functions to search through metadata files and return a subset with 
# a given set of attributes

# by Ryan Neely 9/18/19

import metadata

def search(files,kwargs):
    """
    This function takes a list of metadata files and looks through them
    for files that have matching attribues to what is passed in through
    **kwargs.
    Args:
        -files: list of full file paths to XML metadata files
        -kwargs: dictionary of any number of key:value pairs to use as criteria
            for including a file in the eventual output list. Any keys
            not included here won't be checked. Values here are allowed to be ranges or lists. 
            **The function will interpret any two-element, integer tuple
                as a range, while any list will be interpreted as containing 
                inclusive values.***
    """
    ##TODO: decide if all inputs should be str to match metadata, and then converted as needed...?
    matches = [] #eventual output of matching files
    for f in files:
        ###start by assuming an inclusion:
        include = True
        i = 0
        ##load the data dictionary
        m = metadata.parse_meta_xml(f)
        while include == True and i < len(kwargs):
            for key,val in kwargs.items():
                ##TODO: make this work for odd string inputs in the metadata. 
                # Ex: 'Blood sample times (min from start)': '13,90,135,180,225'
                ##first decide if we are talking about a range or list here
                mval = m[key]
                if type(val) == tuple: ##case where input is a range
                    ##if range, assume we need to convert to float
                    try:
                        mval = float(mval)
                        if not mval > val[0] and mval < val[1]:
                            include = False
                    except TypeError:
                        print("No {} entry for {}".format(key,f))
                        include = False
                    except ValueError:
                        print("Invalid entry ({}) for {} in {}".format(mval,key,f))
                        include = False
                elif type(val) == list:
                    if not mval in val:
                        include = False
                else:
                    if not mval == val:
                        include = False
                i+=1
            if include:
                matches.append(f)
    return matches

                    

