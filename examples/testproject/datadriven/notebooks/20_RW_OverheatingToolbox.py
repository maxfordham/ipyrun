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
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
# %reload_ext autoreload
# %autoreload 2
import os
NBFDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import update_display, display, Image, JSON, Markdown, HTML, clear_output
import subprocess

from ipyrun.ipyrun import RunApp
from ipyrun.ipyrun_overheating import RunAppReport, RunAppsOverheating
import ipyaggrid
# +
# Create set of parameters
parameters = {}
analysis = r'TM59'
parameters['fdir_modelruninput'] = r'../05 Model Files'
parameters['fdir_data'] = r'../data'
parameters['fdir_scripts'] = os.path.join(os.environ['mf_root'], r'ipyrun/src')
parameters['fdir_reports'] = r'../reports'    
parameters['display_ignore'] = ['.jpg','.jpeg','.png','.xlsx']
parameters['fdir_interim_data'] = os.path.join(parameters['fdir_data'],r'interim')
parameters['fdir_processed_data'] = os.path.join(parameters['fdir_data'],r'processed')
parameters['fdir_raw_data'] = os.path.join(parameters['fdir_data'],r'raw', analysis)
parameters['fdir_analysis_interim'] = os.path.join(parameters['fdir_interim_data'], analysis)
parameters['fdir_graphs_interim'] = os.path.join(parameters['fdir_analysis_interim'], r'graphs')
parameters['fdir_analysis_processed'] = os.path.join(parameters['fdir_processed_data'], analysis)
parameters['fpth_comp_script'] = os.path.join(parameters['fdir_scripts'], r'compare_model_run_file.py')
parameters['fpth_report_script'] = os.path.join(parameters['fdir_scripts'], r'report_model_run_file.py')
parameters['fpth_setup_script'] = os.path.join(parameters['fdir_scripts'],r'setup_model_run_file.py')

setup_config = {
    'fpth_script':os.path.realpath(parameters['fpth_setup_script']),
    'display_ignore':parameters['display_ignore'],
    'fdir_inputs_foldername': 'overheating-toolbox',
    "script_outputs": {
        '0': {
            'fdir':'.', # relative to the location of the App / Notebook file
            'fnm': parameters['fdir_graphs_interim'],
            'description': "Folder for data output"
        },
        '1': {
            'fdir':'.', # relative to the location of the App / Notebook file
            'fnm': parameters['fdir_analysis_interim'],
            'description': "Folder for analysis output"
        },
        '2': {
            'fdir':'.', # relative to the location of the App / Notebook file
            'fnm': parameters['fdir_raw_data'],
            'description': "Folder for raw data"
        }
    }
} 
runapps = RunAppsOverheating(setup_config)
parameters['fdir_inputs'] = runapps._fdir_inputs

reporting_config = {
    'fpth_script':os.path.realpath(parameters['fpth_report_script']),
    'script_outputs': {
        '0': {
                'fdir':parameters['fdir_reports'],
                'fnm': '',
                'description': "A markdown report"
        }
    },
    'fpth_parameters': parameters,
    'compare_run_graphs': parameters['fdir_graphs_interim']
}
report_run = RunAppReport(reporting_config, runapps)  


# Display Model Runs
display(Markdown('# Overheating Analysis - Toolbox'))
display(Markdown('---'))
display(Markdown('## Setup Inputs and Run Models'))
display(Markdown('''Setup runs, and their inputs. Then, multiple runs can be analysed.'''))
display(runapps, display_id=True)
display(Markdown('---'))
display(Markdown('## Report Runs'))
display(Markdown('''Create a report'''))
display(report_run)
# -

