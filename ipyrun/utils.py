
"""
this module contains utility functions. these are copied from the main mf library.
"""

import os 
import subprocess
import glob
import pandas as pd
from IPython.display import Markdown
import json
import yaml
import time 
from datetime import datetime

from mf_modules.excel_in import ExcelIn, mfexcel_in
import applauncher_wrapper as al

#  from mf_modules.pandas_operations import del_matching
#  ------------------------------------------------------------------------------------------------
def del_cols(df, cols):
    """delete a pandas column if it is in
    the column index otherwise ignore it. """
    if type(cols) == str:
        try:
            del df[cols]
        except:
            print(cols + ' is not in column index')
    else:
        for col in cols:
            try:
                del df[col]
            except:
                print(col + ' is not in column index')
    return df

def del_matching(df, string):
    """
    deletes columns if col name matches string
    """
    matching = [s for s in list(df) if string in s]
    df = del_cols(df, matching)
    return df

#  from mf_modules.jupyter_formatting import md_fromfile, display_python_file
#  ------------------------------------------------------------------------------------------------
def md_fromfile(fpth):
    """
    read an md file and display in jupyter notebook
    Args:
        fpth:

    Returns:
        displays in IPython notebook
    """
    file = open(fpth,mode='r',encoding='utf-8') # Open a file: file
    all_of_it = file.read() # read all lines at once
    file.close() # close the file
    display(Markdown(all_of_it))

def display_python_file(fpth):
    """
    pass the fpth of a python file and get a
    rendered view of the code.
    """
    with open(fpth, 'r') as myfile:
        data = myfile.read()
    return Markdown("\n ```Python \n" + data + " \n ```")

#  from mf_modules.file_operations import open_file, recursive_glob, time_meta_data, make_dir
def open_file(filename):
    """Open document with default application in Python."""
    if sys.platform == 'linux':
        al.open_file(filename)
        #  note. this is an MF custom App for opening folders and files
        #        from a Linux file server on the local network
    else:
        try:
            os.startfile(filename)
        except AttributeError:
            subprocess.call(['open', filename])

def recursive_glob(rootdir='.', pattern='*', recursive=True):
    """ 
    Search recursively for files matching a specified pattern.
    
    name: 
        20180506~3870~code~pyfnctn~jg~recursive_glob~A~0
    tags: 
        rootdir, pattern, finding-files
    Reference: 
        Adapted from: http://stackoverflow.com/questions/2186525/use-a-glob-to-find-files-recursively-in-python
        string pattern matching: https://jakevdp.github.io/WhirlwindTourOfPython/14-strings-and-regular-expressions.html
    Args:
        **rootdir (string): the directory that you would like to recursively search. 
            recursive means it will automatically look in all folders within this directory
        **pattern (string): the filename pattern that you are looking for.
		**recursive (bool): define if you want to search recursively (in sub-folders) or not. 
		
	Returns:
		matches(list): list of filedirectories that match the pattern
    Example:
        rootdir='J:\J'+'J9999'
        pattern='????????_????_?*_?*_?*_?*_?*_?*'
        recursive_glob(rootdir=rootdir, pattern=pattern, recursive=True)
    """
    matches=[]
    if recursive ==True:
        for root, dirnames, filenames in os.walk(rootdir):
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))

    else:
        for filename in glob.glob1(rootdir,pattern):
            matches.append(os.path.join(rootdir,filename))
            
    return matches


def time_meta_data(fpth,
                   as_DataFrame: bool = True,
                   timeformat: str = 'strftime'):
    '''
    extract time based metadata about a file

    Name:
        20180916~3870~dev~pyfnctn~jg~get time based metadata for a file~A~0

    Args:
        fdir (string): file-directory
        as_DataFrame: bool =True
        timeformat: str = 'strftime' or 'datetime'


    See Also:
        list of metadata available from os.stat(fdir): https://docs.python.org/3/library/os.html
        write docstrings like google: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
        Google python code style guide: https://github.com/google/styleguide/blob/gh-pages/pyguide.md

    References:
        https://docs.python.org/3/library/os.html
            shows other info available from os.stat

    Returns:
        df (pd.DataFrame):
            time_of_file_creation (string):
            time_of_most_recent_access (string):
            time_of_most_recent_content_modification (string):

    To Do:
        add optionally extract other meta-data available from os.stat
        this should be *args inputs
    '''

    def string_of_time(t):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

    di = {}
    try:
        meta = os.stat(fpth)
    except:
        return None
    di['fpth'] = fpth
    if timeformat == 'strftime':
        di['time_of_file_creation'] = string_of_time(meta.st_ctime)
        di['time_of_most_recent_access'] = string_of_time(meta.st_atime)
        di['time_of_most_recent_content_modification'] = string_of_time(meta.st_mtime)
    else:
        di['time_of_file_creation'] = datetime.utcfromtimestamp(meta.st_ctime)
        di['time_of_most_recent_access'] = datetime.utcfromtimestamp(meta.st_atime)
        di['time_of_most_recent_content_modification'] = datetime.utcfromtimestamp(meta.st_mtime)

    if as_DataFrame:
        return pd.DataFrame.from_dict(di, orient='index').T
    else:
        return di
        
def make_dir(directory):
    '''
    check if folder exists, if not, make a new folder using python
    '''
    import os, errno

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

#  from mf_modules.pydtype_operations flatten_list, import read_json, read_txt, read_yaml
#  ------------------------------------------------------------------------------------------------
def flatten_list(list_of_lists: list)-> list: 
    """Flatten a list of (lists of (lists of strings)) for any level 
    of nesting
    
    Args:
        list_of_lists: with mix of lists and other
    Returns:
        rt: list with no nested lists
        
    """
    rt = []
    for i in list_of_lists:
        if isinstance(i,list): rt.extend(flatten_list(i))
        else: rt.append(i)
    return rt

def read_json(fpth, encoding='utf8'):
    '''
    read info in a .json file
    '''
    with open(fpth, 'r', encoding=encoding) as f:
        json_file = json.load(f)
    return json_file

def read_txt(fpth,encoding='utf-8',delim=None,read_lines=True):
    '''
    read a .txt file
    
    Args:
        fpth(string): filepath
        encoding(string): https://docs.python.org/3/library/codecs.html, examples:
            utf-16, utf-8, ascii
        delim(char): character to string split, examples:
            '\t', ','
        read_lines(bool): readlines or whole string (delim may not work if read_lines==False

    '''
    with codecs.open(fpth, encoding=encoding) as f:
        if read_lines==True:
            content = f.readlines()
        else:
            content = f.read()
    f.close()
    if delim!=None:
        li = []
        for n in range(0, len(content)):
            li.append(content[n].split(delim))
        return li
    else:
        return content

def read_yaml(fpth, encoding='utf8'):
    """
    read yaml file.

    Ref:
        https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python"""
    with open(fpth, encoding=encoding) as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data
#  ------------------------------------------------------------------------------------------------


