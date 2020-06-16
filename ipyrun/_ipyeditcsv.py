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
# main imports
import os 
FDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import Markdown, clear_output
from markdown import markdown
from datetime import datetime
import time
from pprint import pprint

# widget stuff
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet

# core mf_modules
from mf_modules.file_operations import make_dir
from mf_modules.datamine_functions import time_meta_data
from mf_modules.pandas_operations import del_matching


# from this repo
# this is an unpleasant hack. should aim to find a better solution
try:
    from ipyrun._runconfig import RunConfig
    from ipyrun._filecontroller import FileConfigController
except:
    from _runconfig import RunConfig
    from _filecontroller import FileConfigController

# -

class SimpleEditCsv():
    """NOTE IN USE"""
    def __init__(self, fpth_in, fpth_out=None):
        self.fpth_in = fpth_in
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.sheet = self._sheet_from_fpth(self.fpth_in)
        self.form()
        self._init_controls()
        self.out = widgets.Output()
        
    def form(self):
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self.button_bar = widgets.HBox([self.save_changes])
        self.layout = self.sheet
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet_from_fpth(self, fpth):
        df=del_matching(pd.read_csv(fpth),'Unnamed')
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_out)
        display(Markdown('changes saved to: {0}'.format(self.fpth_out)))
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes saved to: {1}'.format(timestampStr,self.fpth_out)))
        self.display()

    def display(self):
        display(self.button_bar, self.out, self.layout)
        
    def _ipython_display_(self):
        self.display() 


class EditCsv(FileConfigController):

    def __init__(self,config):
        self.config = config
        self.out = widgets.Output()
        self._errors()
        self.user_keys = list(config.keys())
        self._update_config()
        self.file_control_form()
        self._init_file_controller()
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)
        self.display_sheet()
        
    def _sheet_from_fpth(self, fpth):
        df=del_matching(pd.read_csv(fpth),'Unnamed')
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def display_sheet(self):
        with self.out:
            clear_output()
            display(self.sheet)
            
    def _revert(self, sender):
        """revert to last save of working inputs file"""
        fpth = self.fpth_inputs
        self.temp_message.value = markdown('revert to inputs in last save of: {0}'.format(fpth))
        
        # add code here to revert to last save
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)
        
        self.display_sheet()
        self.update_display()
        self.display()


    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.fpth_inputs
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))
        
        # add code here to save changes to file
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_inputs)
        
        self.update_display()
        self.display()
        
    def _load_inputs(self,sender):
        """launches the inputs from file dialog"""
        self.temp_message.value = markdown('update the user input form with data from file')
        if self.load_inputs.value:
            self.inputform.children = [self.load_button, self.choose_inputs]
        else:
            self.temp_message.value = markdown('')
            self.inputform.children = []
        self.update_display()
        self.display()

    def _load(self,sender):

        fpth = self.choose_inputs.value
        
        # add code here to load form from file
        self.sheet = self._sheet_from_fpth(fpth)
        self.temp_message.value = markdown('input form load data from: {0}'.format(fpth))
        
        self.display_sheet()
        self.update_display()
        self.display()

if __name__ == "__main__":
    # SIMPLE EDIT CSV
    #fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv')
    #editcsv = SimpleEditCsv(fpth)
    #display(editcsv)
    
    
    # EDIT CSV with custom config and file management
    config={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    'fdir':'.',
    }
    editcsv = EditCsv(config)
    display(editcsv)


