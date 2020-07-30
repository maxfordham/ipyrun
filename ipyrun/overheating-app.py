# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python [conda env:mf_main] *
#     language: python
#     name: conda-env-mf_main-py
# ---

# +
import os
NBFDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import update_display, display, Image, JSON, Markdown, HTML, clear_output
import subprocess
from shutil import copyfile
import getpass
import importlib.util
import copy 

import plotly.io as pio
import plotly.graph_objects as go

# widget stuff
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet

# core mf_modules
from mf_modules.file_operations import make_dir
from mf_modules.pandas_operations import del_matching
from mf_modules.mydocstring_display import display_module_docstring
from mf_modules.jupyter_formatting import display_python_file
from mf_modules.pydtype_operations import read_json, write_json 

# from this repo
# this is an unpleasant hack. should aim to find a better solution
from ipyrun import *
try:
    from ipyrun._runconfig import RunConfig
    from ipyrun._ipyeditcsv import EditCsv
    from ipyrun._ipyeditjson import EditJson
    from ipyrun._ipydisplayfile import DisplayFile, DisplayFiles
except:
    from _runconfig import RunConfig
    from _ipyeditcsv import EditCsv
    from _ipyeditjson import EditJson
    from _ipydisplayfile import DisplayFile, DisplayFiles

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0]+user[2]


# -

if __name__ == '__main__':


    # Example6 --------------------------
    # Set of RunApps and comparison tools, for ModelRun

    # Parameters
    fdir_modelruninput = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\05 Model Files') 
    fdir_data = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\datadriven\data')
    fdir_scripts = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\datadriven\src')
    display_ignore = ['.jpg','.jpeg','.png','.xlsx']
    
    # Create Model Run Outputs
    fpth_create_script = os.path.join(fdir_scripts,r'create_model_run_file.py')

    create_config = {
        'fpth_script':os.path.realpath(fpth_create_script),
        'fdir':os.path.join(fdir_scripts),
        'display_ignore':display_ignore,
        "script_outputs": {
            '0': {
                'fdir':'.', # relative to the location of the App / Notebook file
                'fnm': r'.',
                'description': "Folder for data output"
            },
            '1': {
                'fdir':'.', # relative to the location of the App / Notebook file
                'fnm': r'.',
                'description': "Folder for analysis output"
            }
        }
    } 

    # Compare Model Run Outputs
    fdir_interim_data = os.path.join(fdir_data,r'interim')
    fdir_processed_data = os.path.join(fdir_data,r'processed')

    fdir_tm59 = os.path.join(fdir_processed_data, r'tm59')
    fpth_comp_script = os.path.join(fdir_scripts, r'compare_model_run_file.py')
    fdir_comp_out = os.path.join(fdir_processed_data, r'datacomparison')

    compare_config = {
        'fpth_script':os.path.realpath(fpth_comp_script),
        'fdir':fdir_scripts,
        'display_ignore':display_ignore,
        'script_outputs': {
            '0': {
                    'fdir':os.path.realpath(fdir_comp_out),
                    'fnm': '',
                    'description': "a pdf report from word"
            }
        },
        'fdir_compareinputs': fdir_interim_data
    }    


    runapps = RunAppsMruns(di=create_config, fdir_input=fdir_modelruninput, fdir_data=fdir_interim_data, fdir_analysis=fdir_tm59)  
    compare_runs = RunAppComparison(compare_config)  

    # Display Model Runs
    display(Markdown('### Overheating Analysis - Toolbox'))
    display(Markdown('---'))
    display(Markdown('##### Step 1: Setup Inputs and Run Models'))
    display(Markdown('''Setup runs, and their inputs. Then, multiple runs can be analysed.'''))
    display(runapps, display_id=True)
    display(Markdown('---'))
    display(Markdown('##### Step 2: Compare Runs'))
    display(Markdown('''Choose multiple runs, which can be compared'''))
    display(compare_runs)

