# search_attrib

# Functions to search through metadata files and return a subset with 
# a given set of attributes

# by Ryan Neely 9/18/19

import metadata

def search(files,**kwargs):
    """
    This function takes a list of metadata files and looks through them
    for files that have matching attribues to what is passed in through
    **kwargs.
    Args:
        -files: list of full file paths to XML metadata files
        -kwargs: can be any number of key:value pairs to use as criteria
            for including a file in the eventual output list. Any keys
            not included here won't be checked, meaning they can be
            anything. Values here are allowed to be ranges or lists. 
            **The function will interpret any two-element, integer tuple
                as a range, while any list will be interpreted as containing 
                inclusive values.***
    """
    matches = [] #eventual output of matching files
    for f in files:
        ###start by assuming an inclusion:
        include = True
        while include == True and i < len(kwargs):
            for key,val in kwargs.items():
                ##first decide if we are talking about a range or list here
                if type(val) == tuple: ##case where input is a range
                    

