# -*- coding: utf-8 -*-
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

from ipyrun.ipyrun import *

# from this repo
# this is an unpleasant hack. should aim to find a better solution

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

    # Parameters
    parameters = {}
    parameters['fdir_modelruninput'] = r'../../05 Model Files'
    parameters['fdir_data'] = r'../data'
    parameters['fdir_scripts'] = r'../src'
    parameters['fdir_reports'] = r'../reports'
    parameters['display_ignore'] = ['.jpg','.jpeg','.png','.xlsx']

    # Create Model Run Outputs
    parameters['fpth_create_script'] = os.path.join(parameters['fdir_scripts'],r'create_model_run_file.py')

    create_config = {
        'fpth_script':os.path.realpath(parameters['fpth_create_script']),
        'fdir':os.path.realpath(parameters['fdir_scripts']),
        'display_ignore':parameters['display_ignore'],
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
            },
            '2': {
                'fdir':'.', # relative to the location of the App / Notebook file
                'fnm': r'.',
                'description': "Folder for raw data"
            }
        }
    } 

    # Compare Model Run Outputs
    parameters['fdir_interim_data'] = os.path.join(parameters['fdir_data'],r'interim')
    parameters['fdir_processed_data'] = os.path.join(parameters['fdir_data'],r'processed')
    parameters['fdir_raw_data'] = os.path.join(parameters['fdir_data'],r'raw')

    
    parameters['fdir_tm59_interim'] = os.path.join(parameters['fdir_interim_data'], r'TM59')
    parameters['fdir_graphs_interim'] = os.path.join(parameters['fdir_tm59_interim'], r'graphs')
    
    parameters['fpth_comp_script'] = os.path.join(parameters['fdir_scripts'], r'compare_model_run_file.py')
    parameters['fdir_comp_out'] = os.path.join(parameters['fdir_processed_data'], r'TM59')

    parameters['fpth_report_script'] = os.path.join(parameters['fdir_scripts'], r'report_model_run_file.py')

    compare_config = {
        'fpth_script':os.path.realpath(parameters['fpth_comp_script']),
        'fdir':parameters['fdir_scripts'],
        'display_ignore':parameters['display_ignore'],
        'script_outputs': {
            '0': {
                    'fdir':os.path.realpath(parameters['fdir_comp_out']),
                    'fnm': '',
                    'description': "Folder for comparison graphs"
            }
        },
        'fdir_compareinputs': parameters['fdir_graphs_interim']
    }

    runapps = RunAppsMruns(di=create_config, fdir_input=parameters['fdir_modelruninput'], fdir_data=parameters['fdir_graphs_interim'], fdir_analysis=parameters['fdir_tm59_interim'], fdir_raw_data=parameters['fdir_raw_data'])  
    compare_runs = RunAppComparison(compare_config)  
    parameters['fdir_inputs'] = os.path.relpath(runapps.fdir_input, NBFDIR)
    
    reporting_config = {
        'fpth_script':os.path.realpath(parameters['fpth_report_script']),
        'fdir':parameters['fdir_scripts'],
        'script_outputs': {
            '0': {
                    'fdir':parameters['fdir_reports'],
                    'fnm': '',
                    'description': "A markdown report"
            }
        },
        'fpth_parameters': parameters,
        'compare_run_inputs': compare_config['fpth_inputs']
    }

    report_run = RunApp(reporting_config)  
    

    # Display Model Runs
    display(Markdown('# Overheating Analysis - Toolbox'))
    display(Markdown('---'))
    display(Markdown('## Setup Inputs and Run Models'))
    display(Markdown('''Setup runs, and their inputs. Then, multiple runs can be analysed.'''))
    display(runapps, display_id=True)
    display(Markdown('---'))
    display(Markdown('## Compare Runs'))
    display(Markdown('''Choose multiple runs, which can be compared'''))
    display(compare_runs)
    display(Markdown('---'))
    display(Markdown('## Report Runs'))
    display(Markdown('''Create a report'''))
    display(report_run)

