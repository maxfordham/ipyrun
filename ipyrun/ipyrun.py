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
FDIR = os.path.dirname(os.path.realpath('__file__'))

import pandas as pd
from IPython.display import display, Image, JSON, Markdown, HTML, clear_output
import ipywidgets as widgets
import subprocess
from ipysheet import from_dataframe, to_dataframe
import ipysheet
from shutil import copyfile
import getpass
import importlib.util

from _ipydisplayfile import DisplayFile, DisplayFiles

from mf_modules.file_operations import make_dir
from mf_modules.pandas_operations import del_matching
from mf_modules.display_module_docstring import display_module_docstring
from mf_modules.jupyter_formatting import display_python_file

import getpass

# -

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0]+user[2]


di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':FDIR, #os.path.join(FDIR,'notebooks'),
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    }
list(di.keys())


# +
class RunForm():
    """
    simple user input form for running scripts. 
    the buttons are not connected to actions in this class. 
    """
    
    def __init__(self):
        self.config = {'fpth_script':'script fpth','fpth_inputs':'script config','process_name':'process_name'}
        self.form()
        display(self.layout)
        
    def form(self):
        self.reset = widgets.Button(icon='fa-eye-slash',#'fa-repeat'
                                tooltip='removes temporary output view',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.help = widgets.Button(icon='fa-question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.edit_config = widgets.Button(description='edit inputs',
                                tooltip='edit the user input information that is used when the script is executed',
                                button_style='warning',
                                style={'font_weight':'bold'})
        self.show_docstring = widgets.Button(description='show guide',
                                tooltip='read the "docstring", ie. the documentation that was written to accompany the script',
                                button_style='info',
                                style={'font_weight':'bold'})
        self.run_script = widgets.Button(description='run',
                                tooltip='execute the script based on the user inputs',
                                button_style='success',
                                style={'font_weight':'bold'})
        self.preview_outputs = widgets.Button(description='preview outputs',
                                tooltip='show a preview of the output files generated when the script runs',
                                button_style='info',
                                style={'font_weight':'bold'})
        self.show_log = widgets.Button(description='show log',
                                tooltip='show a log of when the script was executed to generate the outputs, and by who',
                                button_style='info',
                                style={'font_weight':'bold'})
        self.scriptfpth = widgets.Text(value=self.config['fpth_script'],
                                description='script',
                                layout=widgets.Layout(indent=False,
                                                      width='auto',
                                                      height='30px'), disabled=True)
        self.configfpth = widgets.Text(value=self.config['fpth_inputs'],
                                description='inputs',
                                layout=widgets.Layout(indent=False,
                                                      width='auto',
                                                      height='30px'), disabled=True)
        self.outputsfpth = widgets.SelectMultiple(description='outputs',
                                           options=[],
                                           rows=4,
                                           layout=widgets.Layout(indent=False,
                                                      width='auto',
                                                      height='30px'))
        self.check = widgets.Checkbox(
                        value=False,
                        disabled=False,
                        indent=False,
                        layout=widgets.Layout(max_width='30px',height='30px', padding='3px')
                        )
        self.form = widgets.HBox([self.reset, self.help, self.show_docstring, self.edit_config, self.run_script, self.preview_outputs, self.show_log],
                    layout=widgets.Layout(width='100%',align_items='stretch'))
        self.paths = widgets.VBox([self.configfpth,self.scriptfpth,self.outputsfpth],
                    layout=widgets.Layout(width='100%',align_items='stretch')) 
        self.acc = widgets.Accordion(children=[widgets.VBox([widgets.Box([self.form]),self.paths])],selected_index=None,layout=widgets.Layout(width='100%'))
        self.acc.set_title(0,self.config['process_name'])
        self.layout = widgets.HBox([self.check,self.acc],layout=widgets.Layout(margin='0px',padding='0px',border='0px'))
    
RunForm()
# -
from _runconfig import RunConfig
from _ipyeditcsv import EditCsv

# +


class EditUserInputs():
    
    def __init__(self, fpth_csv, fdir='.', local_fol='.mfengdev'):
        self.fpth_csv = fpth_csv
        self.fdir = fdir
        self.local_fol = local_fol
        self.fpth_out = self._fpth_out()
        self.sheet = self._sheet()
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self._init_controls()
        self.layout = widgets.VBox([self.save_changes,self.sheet])
        self.out = widgets.Output()
        
    def _fpth_out(self):
        fol = os.path.join(self.fdir, self.local_fol)
        make_dir(fol)
        return os.path.join(fol,os.path.basename(self.fpth_csv))
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet(self):
        df=pd.read_csv(self.fpth_csv)
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        tmp = to_dataframe(self.sheet)
        tmp.to_csv(self.fpth_out)
        
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display() 
        

class RunApp(RunForm, RunConfig):
    """
    app for managing the execution of python scripts using an ipywidgets user interface
    """
    def __init__(self,config):
        
        self.out = widgets.Output()
        self.config = config
        self.user_keys = list(config.keys())
        self.errors = []
        self._update_config()
        self.form()
        self.outputsfpth.options = self.fpths_outputs
        self.show_me_the_code = widgets.Button(description='show source code',
                      tooltip='shows the raw python code in the preview window below',
                      button_style='info')
        self._init_controls()
        
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.edit_config.on_click(self._edit_config)
        self.show_docstring.on_click(self._show_docstring)
        self.run_script.on_click(self._run_script)
        self.show_me_the_code.on_click(self._show_me_the_code)
        self.preview_outputs.on_click(self._preview_outputs)
        self.show_log.on_click(self._show_log)
        self.acc.observe(self._close_acc, names='selected_index')
        
    def _close_acc(self, change):
        if self.acc.selected_index!=0:
            self._reset(None)
        
    def _show_me_the_code(self, sender):
        with self.out:
            clear_output()
            display(display_python_file(self.config['fpth_script']))
            
    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\user_guides\RunApp.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
    
    def _edit_config(self, sender):
        with self.out:
            clear_output()
            #display(EditUserInputs(self.config['fpth_inputs'], self.config['fdir']))
            display(EditCsv(self.config['fpth_inputs'], self.config['fdir']))

    def _show_docstring(self, sender):
        with self.out:
            clear_output()
            display(self.show_me_the_code)
            display_module_docstring(self.config['fpth_script'])
            
    def archive_inputs(self):
        timestamp = str(pd.to_datetime('today'))[:-9].replace(':','').replace('-','').replace(' ','_')
        initals = get_mfuser_initials()
        ext = os.path.splitext(self.fpth_inputs)[1]
        fnm = timestamp + '-' + initals + '-' + os.path.splitext(os.path.basename(self.fpth_inputs))[0] + ext
        self.fpth_inputs_archive = os.path.join(self.fdir_inputs_archive,fnm)
        copyfile(self.fpth_inputs,self.fpth_inputs_archive)
        
    def _run_script(self, sender):
        self.config_to_json()
        self.archive_inputs()
        self._log()
        with self.out:
            clear_output()
            if os.path.isfile(self.config['fpth_inputs']):
                display(self.config['pretty_name'])
                display(subprocess.check_output(['python','-O', self.config['fpth_script'], self.config['fpth_config'], self.config['fpth_inputs']]))
            else:
                display(Markdown("## inputs have not been saved"))
                display(Markdown('click on the "edit inputs" button to edit inputs and hit save when done'))
                display(Markdown('this will save a datafile that is passed to the script when you press run'))
                display(Markdown('the input datafile should be saved here:'))
                display(Markdown('`{0}`'.format(self.config['fpth_inputs'])))

    def _log(self):
        if os.path.isfile(self.fpth_log):
            self.df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
        else:
            di = {
                'processName':[],
                'user':[],
                'datetime':[],
                'formalIssue':[],
                'tags':[],
                'fpthInputs':[]
            }
            self.df_log = pd.DataFrame(di).rename_axis("index")
        
        user = getpass.getuser()
        timestamp = str(pd.to_datetime('today'))
        timestamp = timestamp[:-7]
        
        tmp = pd.DataFrame({
            'processName':[self.process_name],
            'user':[user],
            'datetime':[timestamp],
            'formalIssue':[''],
            'tags':[''],
            'fpthInputs':[self.fpth_inputs_archive]
        })
        self.df_log = self.df_log.append(tmp).reset_index(drop=True)
        make_dir(self.fdir_log)
        self.df_log.to_csv(self.fpth_log)
        
    def _preview_outputs(self, sender):
        with self.out:
            clear_output()
            #fpths = self.outputsfpth.options
            fpths = self.outputsfpth.value
            for fpth in fpths:
                display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(fpth))[0])))
                display(Markdown('`{0}`'.format(fpth)))
                d = DisplayFile(fpth)
                d.preview_fpth()
            if len(fpths)==0:
                display(Markdown('select the file(s) that you would like to display from the "outputs" list above '))
                
    def _show_log(self, sender):
        with self.out:
            clear_output()
            if os.path.isfile(self.fpth_log):
                d = DisplayFile(self.fpth_log)
                d.preview_fpth()
            else:  
                display(Markdown('### A log file does not yet exist.'))
                display(Markdown('### This indicates that the script has not yet been run.'))
             
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display()     
        
def run_py_script(fpth,arg):
    """
    run a script using python magic
    """
    if os.path.isfile(fpth):
        print('run {0}'.format(fpth))
        %run -i $fpth $arg #-i
    elif fpth == 'READ PROCESSED DATA ONLY':
        pass
    else:
        print("{0} doesn't exist".format(fpth))
        
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':FDIR,
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    }  

# dumb form
#form = RunForm()
#form

r = RunApp(di)  
r
# -

r.config

# +


class EditUserInputs():
    
    def __init__(self, fpth_csv, fdir='.', local_fol='.mfengdev'):
        self.fpth_csv = fpth_csv
        self.fdir = fdir
        self.local_fol = local_fol
        self.fpth_out = self._fpth_out()
        self.sheet = self._sheet()
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self._init_controls()
        self.layout = widgets.VBox([self.save_changes,self.sheet])
        self.out = widgets.Output()
        
    def _fpth_out(self):
        fol = os.path.join(self.fdir, self.local_fol)
        make_dir(fol)
        return os.path.join(fol,os.path.basename(self.fpth_csv))
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet(self):
        df=pd.read_csv(self.fpth_csv)
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        tmp = to_dataframe(self.sheet)
        tmp.to_csv(self.fpth_out)
        
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display() 
        

class RunApp(RunForm):
    """
    app for managing the execution of python scripts using an ipywidgets user interface
    """
    def __init__(self,config):
        
        self.out = widgets.Output()
        self.config = config
        self.fdir = config['fdir']
        self.config = self._update_config()
        self.fpths_out = self.config['fpths_outputs']
        self.fpth_log = self.config['fpth_log']
        self.select_li = [self.config['process_name']]
        self.value = self.config['process_name']
        self.form()
        self.outputsfpth.options = self.fpths_out      
        #self.outputsfpth.value = (fpths_out[0],)
        self.show_me_the_code = widgets.Button(description='show source code',
                      tooltip='shows the raw python code in the preview window below',
                      button_style='info')
        self._init_controls()
        
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.edit_config.on_click(self._edit_config)
        self.show_docstring.on_click(self._show_docstring)
        self.run_script.on_click(self._run_script)
        self.run_script.on_click(self._log)
        self.show_me_the_code.on_click(self._show_me_the_code)
        self.preview_outputs.on_click(self._preview_outputs)
        self.show_log.on_click(self._show_log)
        self.acc.observe(self._close_acc, names='selected_index')
        
    def _close_acc(self, change):
        if self.acc.selected_index!=0:
            self._reset(None)
            
    def _find_template_configs(self):
        self.template_configs = {}
        if self.local_template:
            # local (i.e. next to the notebook)
            rootdir = os.path.join(self.fdir,r'configs')
        else:
            # remote (i.e. next to the script)
            rootdir = os.path.join(os.path.dirname(self.config['fpth_script']),r'configs')
        pattern = '*' + os.path.splitext(os.path.basename(self.config['fpth_script']))[0] + '*'
        files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)
        
        # catch error
        if len(files) > 1:
            file = 'ERROR: too many template config files found'
        elif len(files) == 0:
            file = 'ERROR: no template config files found'
            self.local_template = False
        else:
            file = files[0] 
        return file

    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables 
        of the app. e.g filepaths for the script path, user inputs template file etc. 
        where explicit inputs are not given this function updates the config dict with 
        default values, flagging any errors that are spotted on the way.
        """
        di = self.config
        li = di.keys()
        process_name = os.path.splitext(os.path.split(di['fpth_script'])[1])[0]
        fdir_local = os.path.join(self.fdir,'_configs')
        make_dir(fdir_local)
        
        # find config file next to app
        self.local_template = True
        #file = _find_template_configs(self)
        
        config_local = os.path.join(fdir_local,process_name+'.csv')
        config_remote = os.path.join(os.path.split(di['fpth_script'])[0],'configs',process_name+'.csv')
        
        # add process name
        if 'process_name' in li:
            pass
        else:
            di['process_name'] = process_name
            
        # pretty name
        if 'pretty_name' in li:
            pass
        else:
            di['pretty_name'] = process_name
        
        # config dict passed explicitly to the script
        if 'fpth_inputs' in li:
            pass
        elif os.path.isfile(config_local):
            di['fpth_inputs'] = config_local
        elif os.path.isfile(config_remote):
            copyfile(config_remote,config_local)
            di['fpth_inputs'] = config_local #  look for template config file relative to script file
        else:
            di['fpth_inputs'] = 'ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'
            with self.out:
                clear_output()
                display(Markdown('### ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'))
        
        # folder to put the outputs
        if 'fdir_outputs' not in li:
            di['fdir_outputs'] = di['fdir']
        
        # folder to put the outputs
        if 'fdir_log' not in li:
            di['fdir_log'] = di['fdir']
       
        # get a list of fpth outputs
        di['fpths_outputs'] = self._fpths_out()
        
        # fpth log
        di['fpth_log'] = os.path.join(self.config['fdir_log'],'log.csv')
                       
        return di
        
    #remove?    
    def _fpths_out(self):
        spec = importlib.util.spec_from_file_location(self.config['process_name'], self.config['fpth_script'])
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        try:
            li_out = foo.PROCESS_OUTPUTS
            fpths_out = [os.path.join(self.config['fdir_outputs'],l['fnm']) for l in li_out];
        except:
            fpths_out = ['no output files found']
        return fpths_out
        
    def _show_me_the_code(self, sender):
        with self.out:
            clear_output()
            display(display_python_file(self.config['fpth_script']))
            
    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\user_guides\RunApp.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
    
    def _edit_config(self, sender):
        with self.out:
            clear_output()
            display(EditUserInputs(self.config['fpth_inputs'], self.config['fdir']))

    def _show_docstring(self, sender):
        with self.out:
            clear_output()
            display(self.show_me_the_code)
            display_module_docstring(self.config['fpth_script'])
            #%load C:\engDev\git_mf\MF_Toolbox\dev\mf_modules\mydocstring_example.py
        
    def _run_script(self, sender):
        with self.out:
            clear_output()
            display(self.config['pretty_name'])
            display(subprocess.check_output(['python','-O',self.config['fpth_script'], self.config['fdir_outputs'], self.config['fpth_inputs']]))
            #run_py_script(self.config['fpth_script'],self.config['fpth_inputs'])
            
    def _log(self,sender):
        
        if os.path.isfile(self.fpth_log):
            self.df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
        else:
            di = {
                'user':[],
                'datetime':[],
                'formalIssue':[],
                'tags':[],
                'inputsConfig':['']
            }
            self.df_log = pd.DataFrame(di).rename_axis("index")
        
        user = getpass.getuser()
        timestamp = str(pd.to_datetime('today'))
        timestamp = timestamp[:-7]
        
        tmp = pd.DataFrame({
            'user':[user],
            'datetime':[timestamp],
            'formalIssue':[''],
            'tags':[''],
            'inputsConfig':['']
        })
        self.df_log = self.df_log.append(tmp).reset_index(drop=True)
        self.df_log.to_csv(self.fpth_log)
        
    def _archive_config(self):
        # JUST NEED TO COPY AND PASTE FOMR THE fpth_inputs FOLDER!
        fdir = os.path.join(os.path.dirname(self.config['process_name']),'archive')
        make_dir(fdir)
        _time = str(pd.to_datetime('today'))[:-9].replace(':','').replace('-','').replace(' ','-')
        _ext = os.path.splitext(self.config['process_name'])[1]
        fnm = _time + self.config['process_name'] + _ext
        fpth = os.path.join(fdir,fnm)
        li = [
            {
                'old_fpth': 'adf'
            }
        ]
        copy_rename(li, pr=False)
        

    def _preview_outputs(self, sender):
        with self.out:
            clear_output()
            #fpths = self.outputsfpth.options
            fpths = self.outputsfpth.value
            for fpth in fpths:
                display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(fpth))[0])))
                display(Markdown('`{0}`'.format(fpth)))
                d = DisplayFile(fpth)
                d.preview_fpth()
            if len(fpths)==0:
                display(Markdown('select the file(s) that you would like to display from the "outputs" list above '))
            
            
    def _show_log(self, sender):
        with self.out:
            clear_output()
            if os.path.isfile(self.fpth_log):
                d = DisplayFile(self.fpth_log)
                d.preview_fpth()
            else:  
                display(Markdown('### A log file does not yet exist.'))
                display(Markdown('### This indicates that the script has not yet been run.'))
             
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display()     
        
def run_py_script(fpth,arg):
    """
    run a script using python magic
    """
    if os.path.isfile(fpth):
        print('run {0}'.format(fpth))
        %run -i $fpth $arg #-i
    elif fpth == 'READ PROCESSED DATA ONLY':
        pass
    else:
        print("{0} doesn't exist".format(fpth))
        
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    }  

# dumb form
#form = RunForm()
#form

r = RunApp(di)  
r
# -
from mf_modules.file_operations import copy_rename
help(copy_rename)


def _find_template_configs(self):
    self.template_configs = {}
    if self.local_template:
        # local (i.e. next to the notebook)
        rootdir = os.path.join(self.fdir,r'configs')
    else:
        # remote (i.e. next to the script)
        rootdir = os.path.join(os.path.dirname(self.config['fpth_script']),r'configs')
    pattern = '*' + os.path.splitext(os.path.basename(self.config['fpth_script']))[0] + '*'
    files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)

    # catch error
    if len(files) > 1:
        file = 'ERROR: too many template config files found'
    elif len(files) == 0:
        file = 'ERROR: no template config files found'
        self.local_template = False
    else:
        file = files[0] 
    return file



    def display(self):
        display(self.save_changes)
        out = [l.layout for l in self.widgets]
        self.applayout = widgets.VBox(out)
        display(self.applayout)
        for l in self.widgets:
            display(l.out)
        display(self.out)

    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables 
        of the app. e.g filepaths for the script path, user inputs template file etc. 
        where explicit inputs are not given this function updates the config dict with 
        default values, flagging any errors that are spotted on the way.
        """
        di = self.config
        li = di.keys()
        process_name = os.path.splitext(os.path.split(di['fpth_script'])[1])[0]
        fdir_local = os.path.join(self.fdir,'_configs')
        make_dir(fdir_local)
        
        # find config file next to app
        self.local_template = True
        #file = _find_template_configs(self)
        
        config_local = os.path.join(fdir_local,process_name+'.csv')
        config_remote = os.path.join(os.path.split(di['fpth_script'])[0],'configs',process_name+'.csv')
        
        # add process name
        if 'process_name' in li:
            pass
        else:
            di['process_name'] = process_name
            
        # pretty name
        if 'pretty_name' in li:
            pass
        else:
            di['pretty_name'] = process_name
        
        # config dict passed explicitly to the script
        if 'fpth_inputs' in li:
            pass
        elif os.path.isfile(config_local):
            di['fpth_inputs'] = config_local
        elif os.path.isfile(config_remote):
            copyfile(config_remote,config_local)
            di['fpth_inputs'] = config_local #  look for template config file relative to script file
        else:
            di['fpth_inputs'] = 'ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'
            with self.out:
                clear_output()
                display(Markdown('### ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'))
        
        # folder to put the outputs
        if 'fdir_outputs' not in li:
            di['fdir_outputs'] = di['fdir']
        
        # folder to put the outputs
        if 'fdir_log' not in li:
            di['fdir_log'] = di['fdir']
       
        # get a list of fpth outputs
        di['fpths_outputs'] = self._fpths_out()
        
        # fpth log
        di['fpth_log'] = os.path.join(self.config['fdir_log'],'log.csv')
                       
        return di





# +
from mf_modules.datamine_functions import recursive_glob

class ManageInputConfig():
    
    def __init__(self,config):
        self.config = config
        self.user_keys = list(config.keys())
        self.errors = []
        self.fpths_out_template = self._fpths_out_template()
        self._update_config()
        
    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables 
        of the app. e.g filepaths for the script path, user inputs template file etc. 
        where explicit inputs are not given this function updates the config dict with 
        default values, flagging any errors that are spotted on the way.
        """
        di = self.config       
        di['fdir'] = self.fdir
        di['process_name'] = self.process_name
        di['pretty_name'] = self.pretty_name
        di['fdir_inputs'] = self.fdir_inputs
        di['fpth_input'] = self.fpth_input
        di['fpth_input_options'] = self.fpth_input_options() #dict
        di['fpths_out'] = self._update_fpths_out() #dict
        di['fdir_log'] = self.fdir_log 
        di['fnm_log'] = self.fnm_log
        di['fpth_log'] = os.path.join(self.fdir_log, self.fnm_log)
                       
        return di
             
    def fpth_input_options(self):  
        patterns = ['*' + self.process_name + '*', '*' + self.script_name + '*']
        patterns = list(set(patterns))
        
        di = {
            'template':{
                'fdir': self.fdir_template_inputs,
                'fpths':[]
            },
            'project':{
                'fdir': self.fdir_inputs,
                'fpths':[]
            },
        }
        cnt = 0
        valid_exts = ['.csv','.json']
        for k,v in di.items():
            for pattern in patterns:
                fpths = recursive_glob(rootdir=v['fdir'],pattern=pattern,recursive=False)
                di[k]['fpths'] = fpths
                cnt += len(fpths)
                self.errors.append(['{0} not csv or json'.format(fpth) for fpth in fpths if os.path.splitext(fpth)[1] not in valid_exts])
        if cnt == 0:
            self.errors.append('couldnt find and input files within the templates folder or in the project folder')
        return di
    
    @property
    def fdir(self):
        '''check if fdir given, otherwise put it local to app'''
        if 'fdir' in self.user_keys:
            return self.config['fdir']
        else:
            return '.'
    
    @property
    def script_name(self):
        '''name of the script. used for checking if its different to the process name'''
        return os.path.splitext(os.path.split(self.config['fpth_script'])[1])[0]
    
    @property
    def process_name(self):
        '''add process name. defaults to name of the script with optional overide.
        the names of the inputs files and log file always match the process_name'''
        process_name = self.script_name
        if 'process_name' in self.user_keys:
            return self.config['process_name']
        else:
            return process_name
            
    @property
    def pretty_name(self):
        '''pretty name. opportunity to add user-friendly name.'''
        if 'pretty_name' in self.user_keys:
            return self.config['pretty_name']
        else:
            return self.process_name
    
    @property
    def fdir_inputs(self):
        # add inputs folder name
        if 'fdir_inputs' in self.user_keys:
            make_dir(self.config['fdir_inputs'])
            return self.config['fdir_inputs']
        else:
            make_dir(os.path.join(self.fdir,'inputs'))
            return os.path.join(self.fdir,'inputs')
        
    @property
    def fdir_template_inputs(self):
        return os.path.join(os.path.dirname(self.config['fpth_script']),r'template_inputs')
    
    @property
    def fpth_template_input(self):
        fpth = recursive_glob(rootdir=self.fdir_template_inputs,
                              pattern='*'+self.script_name+'.*',
                              recursive=False)
        if len(fpth)==0:
            self.errors.append('could not find template input: {0}'.format(os.path.join(self.fdir_inputs, self.process_name)))
        return fpth[0]
        
    @property
    def fpth_input(self):
        fpth = os.path.join(self.fdir_inputs, self.process_name)
        if not os.path.isfile(fpth):
            copyfile(self.fpth_template_input,fpth)
        return fpth

    @property
    def fdir_log(self):
        if 'fdir_log' in self.user_keys:
            return self.config['fdir_log']
        else:
            return os.path.join(self.fdir,'log')
        
    @property
    def fnm_log(self):
        if 'fnm_log' in self.user_keys:
            return self.config['fnm_log']
        else:
            return self.fnm_log+self.process_name+'.csv'
    
    def _fpths_out_template(self):
        spec = importlib.util.spec_from_file_location(self.script_name, self.config['fpth_script'])
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        return foo.FPTHS_OUT
        
    def _update_fpths_out(self):
        """overwrites the template fpth outputs with the user defined ones"""
        if 'fpths_out' not in self.user_keys:
            return self.fpths_out_template
        else:
            di = {}
            for k, v in self.fpths_out_template.items():
                di[k] = v
                for _k,_v in v.items():
                    di[k][_k] = self.config['fpths_out'][k][_k]
            return di
                


# -

fdir= os.path.join(os.path.dirname(di['fpth_script']),r'template_inputs')
script_name = os.path.splitext(os.path.basename(di['fpth_script']))[0]
fpth = recursive_glob(rootdir=fdir,
                      pattern='.',
                      recursive=False)
print(fdir)

# +
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    } 

ManageInputConfig(di)
# -

print(os.path.join(FDIR,r'data'))

print(os.path.join(FDIR,r'data'))

c = ManageInputConfigs(di)

# +
from mf_modules.pydtype_operations import read_yaml
#help(read_yaml)
di = read_yaml(r'default_config.yaml')
for k,v in di.items():
    display(Markdown('#### {0}'.format(k)))
    if type(v) == dict:
        for _k,_v in v.items():
            display(Markdown('{0}: {1}'.format(_k,_v)))
    if type(v)==list:
        for l in v:
            for _k,_v in l.items():
                display(Markdown('{0}: {1}'.format(_k,_v)))
        
#JSON(read_yaml(r'default_config.yaml'))
# -







c.config







from mf_modules.file_operations import make_dirs_from_dict
help(make_dirs_from_dict)

import mf_modules.file_operations as file_operations
from _ipydisplayfile import PreviewPy
#PreviewPy(file_operations)

di = 
make_dirs_from_dict

fdir_test = r'C:\engDev\git_mf\datadriven'
di = {
    'notebooks':{'_config':'_archive'},
    'reports':'figures'
}
make_dirs_from_dict(di,current_dir=fdir_test)

from shutil import copyfile

help(copyfile)


def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables 
        of the app. e.g filepaths for the script path, user inputs template file etc. 
        where explicit inputs are not given this function updates the config dict with 
        default values, flagging any errors that are spotted on the way.
        """
        di = self.config
        li = di.keys()
        process_name = os.path.splitext(os.path.split(di['fpth_script'])[1])[0]
        fdir_local = os.path.join(self.fdir,'_configs')
        make_dir(fdir_local)
        
        # find config file next to app
        self.local_template = True
        #file = _find_template_configs(self)
        
        config_local = os.path.join(fdir_local,process_name+'.csv')
        config_remote = os.path.join(os.path.split(di['fpth_script'])[0],'configs',process_name+'.csv')
        
        # add process name
        if 'process_name' in li:
            pass
        else:
            di['process_name'] = process_name
            
        # pretty name
        if 'pretty_name' in li:
            pass
        else:
            di['pretty_name'] = process_name
        
        # config dict passed explicitly to the script
        if 'fpth_inputs' in li:
            pass
        elif os.path.isfile(config_local):
            di['fpth_inputs'] = config_local
        elif os.path.isfile(config_remote):
            copyfile(config_remote,config_local)
            di['fpth_inputs'] = config_local #  look for template config file relative to script file
        else:
            di['fpth_inputs'] = 'ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'
            with self.out:
                clear_output()
                display(Markdown('### ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'))
        
        # folder to put the outputs
        if 'fdir_outputs' not in li:
            di['fdir_outputs'] = di['fdir']
        
        # folder to put the outputs
        if 'fdir_log' not in li:
            di['fdir_log'] = di['fdir']
       
        # get a list of fpth outputs
        di['fpths_outputs'] = self._fpths_out()
        
        # fpth log
        di['fpth_log'] = os.path.join(self.config['fdir_log'],'log.csv')
                       
        return di


c = ManageInputConfigs(r.config)
c.config_ext

# +
from mf_modules.datamine_functions import recursive_glob

def find_configs(self)
    pattern = '*' + r.config['process_name'] + '*'
    files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)
    if len(files) == 0:
        file = 'could not find a template config file'
    elif len(files) > 0:
        file = [file for file in files if os.path.splitext(os.path.basename(r.config['fpth_script']))[0] == r.config['process_name']][0]
    else:
        file = files[0]


# -



file







# +


class EditUserInputs():
    
    def __init__(self, fpth_csv, fdir='.', local_fol='.mfengdev'):
        self.fpth_csv = fpth_csv
        self.fdir = fdir
        self.local_fol = local_fol
        self.fpth_out = self._fpth_out()
        self.sheet = self._sheet()
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self._init_controls()
        self.layout = widgets.VBox([self.save_changes,self.sheet])
        self.out = widgets.Output()
        
    def _fpth_out(self):
        fol = os.path.join(self.fdir, self.local_fol)
        make_dir(fol)
        return os.path.join(fol,os.path.basename(self.fpth_csv))
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet(self):
        df=pd.read_csv(self.fpth_csv)
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        tmp = to_dataframe(self.sheet)
        tmp.to_csv(self.fpth_out)
        
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display() 
        

class RunApp(RunForm):
    """
    app for managing the execution of python scripts using an ipywidgets user interface
    """
    def __init__(self,config):
        
        self.out = widgets.Output()
        self.config = config
        self.fdir = config['fdir']
        self._update_config()
        self.select_li = [self.config['process_name']]
        self.value = self.config['process_name']
        self.form()
        self.fpths_out = self._fpths_out()
        self.fpth_log = os.path.join(self.config['fdir_log'],'log.csv')
        self.show_me_the_code = widgets.Button(description='show source code',
                      tooltip='shows the raw python code in the preview window below',
                      button_style='info')
        self._init_controls()
        
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.edit_config.on_click(self._edit_config)
        self.show_docstring.on_click(self._show_docstring)
        self.run_script.on_click(self._run_script)
        self.run_script.on_click(self._log)
        self.show_me_the_code.on_click(self._show_me_the_code)
        self.preview_outputs.on_click(self._preview_outputs)
        self.show_log.on_click(self._show_log)
        self.acc.observe(self._close_acc, names='selected_index')
        
    def _close_acc(self, change):
        if self.acc.selected_index!=0:
            self._reset(None)
            
    def _find_template_configs(self):
        self.template_configs = {}
        if self.local_template:
            # local (i.e. next to the notebook)
            rootdir = os.path.join(self.fdir,r'configs')
        else:
            # remote (i.e. next to the script)
            rootdir = os.path.join(os.path.dirname(self.config['fpth_script']),r'configs')
        pattern = '*' + os.path.splitext(os.path.basename(self.config['fpth_script']))[0] + '*'
        files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)
        
        # catch error
        if len(files) > 1:
            file = 'ERROR: too many template config files found'
        elif len(files) == 0
            file = 'ERROR: no template config files found'
            self.local_template = False
        else:
            file = files[0] 
        return file

    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables 
        of the app. e.g filepaths for the script path, user inputs template file etc. 
        where explicit inputs are not given this function updates the config dict with 
        default values, flagging any errors that are spotted on the way.
        """
        di = self.config
        li = di.keys()
        process_name = os.path.splitext(os.path.split(di['fpth_script'])[1])[0]
        fdir_local = os.path.join(self.fdir,'_configs')
        make_dir(fdir_local)
        
        # find config file next to app
        self.local_template = True
        file = _find_template_configs(self)
        
        #config_local = os.path.join(fdir_local,process_name+'.csv')
        #config_remote = os.path.join(os.path.split(di['fpth_script'])[0],'configs',process_name+'.csv')
        
        # add process name
        if 'process_name' in li:
            pass
        else:
            di['process_name'] = process_name
        
        # config dict passed explicitly to the script
        if 'fpth_inputs' in li:
            pass
        elif os.path.isfile(file):
            di['fpth_inputs'] = file
        elif os.path.isfile(config_remote):
            copyfile(config_remote,config_local)
            di['fpth_inputs'] = config_local #  look for template config file relative to script file
        else:
            di['fpth_inputs'] = 'ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'
            with self.out:
                clear_output()
                display(Markdown('### ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'))
        
        # folder to put the outputs
        if 'fdir_outputs' not in li:
            di['fdir_outputs'] = di['fdir']
        
        # folder to put the outputs
        if 'fdir_log' not in li:
            di['fdir_log'] = di['fdir']
                       
        self.config = di
          
    def _fpths_out(self):

        spec = importlib.util.spec_from_file_location(self.config['process_name'], self.config['fpth_script'])
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        try:
            li_out = foo.PROCESS_OUTPUTS
            fpths_out = [os.path.join(self.config['fdir_outputs'],l['fnm']) for l in li_out];
        except:
            fpths_out = ['no output files found']
        self.outputsfpth.options = fpths_out      
        #self.outputsfpth.value = (fpths_out[0],)
        return fpths_out
        
    def _show_me_the_code(self, sender):
        with self.out:
            clear_output()
            display(display_python_file(self.config['fpth_script']))
            
    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\user_guides\RunApp.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
    
    def _edit_config(self, sender):
        with self.out:
            clear_output()
            display(EditUserInputs(self.config['fpth_inputs'], self.config['fdir']))

    def _show_docstring(self, sender):
        with self.out:
            clear_output()
            display(self.show_me_the_code)
            display_module_docstring(self.config['fpth_script'])
            #%load C:\engDev\git_mf\MF_Toolbox\dev\mf_modules\mydocstring_example.py
        
    def _run_script(self, sender):
        with self.out:
            clear_output()
            display(self.config['process_name'])
            display(subprocess.check_output(['python','-O',self.config['fpth_script'], self.config['fdir_outputs'], self.config['fpth_inputs']]))
            #run_py_script(self.config['fpth_script'],self.config['fpth_inputs'])
            
    def _log(self,sender):
        
        if os.path.isfile(self.fpth_log):
            self.df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
        else:
            di = {
                'user':[],
                'datetime':[],
                'formalIssue':[],
                'tags':[]
            }
            self.df_log = pd.DataFrame(di).rename_axis("index")
        
        user = getpass.getuser()
        timestamp = str(pd.to_datetime('today'))
        timestamp = timestamp[:-7]
        
        tmp = pd.DataFrame({
            'user':[user],
            'datetime':[timestamp],
            'formalIssue':[''],
            'tags':['']
        })
        self.df_log = self.df_log.append(tmp).reset_index(drop=True)
        self.df_log.to_csv(self.fpth_log)
            
    def _preview_outputs(self, sender):
        with self.out:
            clear_output()
            #fpths = self.outputsfpth.options
            fpths = self.outputsfpth.value
            for fpth in fpths:
                display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(fpth))[0])))
                display(Markdown('`{0}`'.format(fpth)))
                d = DisplayFile(fpth)
                d.preview_fpth()
            if len(fpths)==0:
                display(Markdown('select the file(s) that you would like to display from the "outputs" list above '))
            
            
    def _show_log(self, sender):
        with self.out:
            clear_output()
            if os.path.isfile(self.fpth_log):
                d = DisplayFile(self.fpth_log)
                d.preview_fpth()
            else:  
                display(Markdown('### A log file does not yet exist.'))
                display(Markdown('### This indicates that the script has not yet been run. '))
             
    def display(self):
        display(self.layout, self.out)
        
    def _ipython_display_(self):
        self.display()     
        
def run_py_script(fpth,arg):
    """
    run a script using python magic
    """
    if os.path.isfile(fpth):
        print('run {0}'.format(fpth))
        %run -i $fpth $arg #-i
    elif fpth == 'READ PROCESSED DATA ONLY':
        pass
    else:
        print("{0} doesn't exist".format(fpth))
        
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    }  

# dumb form
#form = RunForm()
#form

r = RunApp(di)  
r
# -



# +
def _find_template_configs(self):
    self.template_configs = {}
    if self.local_template:
        # local (i.e. next to the notebook)
        rootdir = os.path.join(self.fdir,r'configs')
    else:
        # remote (i.e. next to the script)
        rootdir = os.path.join(os.path.dirname(self.config['fpth_script']),r'configs')
    pattern = '*' + os.path.splitext(os.path.basename(self.config['fpth_script']))[0] + '*'
    files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)

    # catch error
    if len(files) > 1:
        file = 'ERROR: too many template config files found'
    elif len(files) == 0
        file = 'ERROR: no template config files found'
        self.local_template = False
    else:
        file = files[0] 
    return file

def _update_config(self):
    """
    a configuration dict is passed to the app that defines the configuration variables 
    of the app. e.g filepaths for the script path, user inputs template file etc. 
    where explicit inputs are not given this function updates the config dict with 
    default values, flagging any errors that are spotted on the way.
    """
    di = self.config
    li = di.keys()
    process_name = os.path.splitext(os.path.split(di['fpth_script'])[1])[0]
    fdir_local = os.path.join(self.fdir,'_configs')
    make_dir(fdir_local)

    # find config file next to app
    self.local_template = True
    file = _find_template_configs(self)

    #config_local = os.path.join(fdir_local,process_name+'.csv')
    #config_remote = os.path.join(os.path.split(di['fpth_script'])[0],'configs',process_name+'.csv')

    # add process name
    if 'process_name' in li:
        pass
    else:
        di['process_name'] = process_name

    # config dict passed explicitly to the script
    if 'fpth_inputs' in li:
        pass
    elif os.path.isfile(file):
        di['fpth_inputs'] = file
    elif os.path.isfile(config_remote):
        copyfile(config_remote,config_local)
        di['fpth_inputs'] = config_local #  look for template config file relative to script file
    else:
        di['fpth_inputs'] = 'ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'
        with self.out:
            clear_output()
            display(Markdown('### ERROR: CANNOT FIND A TEMPLATE CONFIG FILE'))

    # folder to put the outputs
    if 'fdir_outputs' not in li:
        di['fdir_outputs'] = di['fdir']

    # folder to put the outputs
    if 'fdir_log' not in li:
        di['fdir_log'] = di['fdir']

    self.config = di
# -













r.config

from mf_modules.datamine_functions import recursive_glob
#help(recursive_glob)
rootdir = os.path.join(os.path.dirname(r.config['fpth_script']),r'configs')
pattern = '*' + os.path.splitext(os.path.basename(r.config['fpth_script']))[0] + '*' 
files = recursive_glob(rootdir=rootdir,pattern=pattern,recursive=False)
files




# +
class RunApp_edit(RunApp):
    
    def __init__(self,config):
        super().__init__(config)
        
    def _help(self, sender):
        with self.out:
            clear_output()
            #fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\user_guides\RunApp.png')
            #display(Image(fpth))
            #di['RunApp_help']()
            print('it is easy to extend the class by inheriting it and then changing on the buttons youd like to change')
            
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    #'fpth_log':os.path.join(FDIR,'notebooks',config),
    #'fdir_outputs':os.path.join(FDIR,'notebooks')
    #'RunApp_help':RunApp_help
    }  

r = RunApp_edit(di)  
r
# +
# RunApp_help
# RunApp_show_guide
# RunApp_edit_inputs
# RunApp_run
# RunApp_preview_outputs

# +
# option 1: preferred, but an annoying amount of space between tabs...
class RunApps():
    
    def __init__(self,configs):
        self.configs = configs
        
        self.li = []
        self._form()
        self._init_controls()
        for config in configs:
            self.li.append(RunApp(config))   
        self.out = widgets.Output()
        
        
    def _form(self):
        
        self.reset = widgets.Button(icon='fa-eye-slash',#'fa-repeat'
                                tooltip='removes temporary output view',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.help = widgets.Button(icon='fa-question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.run_batch = widgets.Button(description='run batch',
                                tooltip='execute checked processes below',
                                button_style='success',
                                style={'font_weight':'bold'})
        self.form = widgets.HBox([self.reset, self.help, self.run_batch],
                        layout=widgets.Layout(width='100%',align_items='stretch'))   
    
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.run_batch.on_click(self._run_batch)
        
    def _help(self, sender):
        
        with self.out:
            display('sadf')
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\user_guides\RunBatch.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
        for l in self.li:
            l._reset(sender)
    
    def _run_batch(self, sender):
        cnt = 0
        ttl = 0
        for l in self.li:
            ttl = ttl + 1
            if l.check.value:
                cnt = cnt + 1
        
        with self.out:
            clear_output()
            display(Markdown('{0} out of {1} scripts selected to be run'.format(cnt,ttl)))
            for l in self.li:
                if l.check.value:
                    display(Markdown('running: {0}'.format(l.config['process_name'])))
                    l._run_script('sender')
                    l._log('sender')

    def display(self):
        display(self.form)
        display(self.out)
        [display(l) for l in self.li]; 
        
    def _ipython_display_(self):
        self.display()   
        
di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    'fdir_outputs':os.path.join(FDIR,'notebooks')
    }  

# IT WOULD BE GOOD TO ADD A PROGRESS BAR
# i think this would require us to time how long it takes for the scripts to execute and use that 
# as a first estimate. this could be within the runapp itself rather than individual scripts.

# E.G. 
# fpth = r'C:\engDev\git_mf\MF_Toolbox\dev\mf_modules\progress_bar.py'
# # %run $fpth

configs = [di,di,di]
r = RunApps(configs)  
r
# -














# +
# option 2: looks better but the outputs appear at the bottom instead of in-line
class RunApps_SS():
    
    def __init__(self,configs):
        self.out = widgets.Output()
        self.configs = configs
        self.li = []
        for config in configs:
            self.li.append(RunApp(config))
        self.display()
            
    def display(self):
        
        out = [l.layout for l in self.li]
        self.applayout = widgets.VBox(out)
        display(self.applayout)
        for l in self.li:
            display(l.out)

di={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
    #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
    'fdir':os.path.join(FDIR,'notebooks'),
    'fdir_outputs':os.path.join(FDIR,'notebooks')
    }  

#configs = [di,di,di]
#r = RunApps_SS(configs)
#r;
# -


