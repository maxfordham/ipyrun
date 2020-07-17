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



# +
class RunForm():
    """
    simple user input form for running scripts. 
    the buttons are not connected to actions in this class. 
    """
    def __init__(self):
        """
        to inputs required. this class is intended to be inherited by RunApp
        """
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
        self.edit_inputs = widgets.Button(description='edit inputs',
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
        self.form = widgets.HBox([self.reset, self.help, self.show_docstring, self.edit_inputs, self.run_script, self.preview_outputs, self.show_log],
                    layout=widgets.Layout(width='100%',align_items='stretch'))
        self.paths = widgets.VBox([self.configfpth,self.scriptfpth,self.outputsfpth],
                    layout=widgets.Layout(width='100%',align_items='stretch')) 
        self.acc = widgets.Accordion(children=[widgets.VBox([widgets.Box([self.form]),self.paths])],selected_index=None,layout=widgets.Layout(width='100%'))
        self.acc.set_title(0,self.config['process_name'])
        self.layout = widgets.HBox([self.check,self.acc],layout=widgets.Layout(margin='0px',padding='0px',border='0px'))
    
#RunForm()
# +
class RunApp(RunForm, RunConfig):
    """
    app for managing the execution of python scripts using an ipywidgets user interface
    """
    def __init__(self,config):
        """
        class that builds a user interface for:
        - editing inputs, 
        - running a script, 
        - reviewing the files output by the script
        - maintaining a log of when the script was last run, by who, and what the inputs were
        - allows users to reload previous input runs. 
        
        Args:
            config (dict): a dict that defines the script path, inputs path, archive inputs path, 
                log file path, output paths etc. this class inherits the RunConfig class which 
                has a default configuration for all of these things allowing the user to pass minimal 
                amounts of information to setup. 
                
        Example:
            ```
            config={
                'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
                'fdir':NBFDIR,
                }    

            r = RunApp(config) 
            from ipyrun._ipyeditjson import 
            
            ui = EditListOfDicts(li)
            ui
            ```
        """
        self.out = widgets.Output()
        self.config = config
        self.user_keys = list(config.keys())
        self.errors = []
        self._update_config()
        self.form()
        self.outputsfpth.options = list(self.fpths_outputs.values())
        self.show_me_the_code = widgets.Button(description='show source code',
                      tooltip='shows the raw python code in the preview window below',
                      button_style='info')
        self._init_controls()

    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.edit_inputs.on_click(self._edit_inputs)
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
            fpth = os.path.join(os.environ['mf_root'],r'ipyrun\docs\images\RunApp.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
    
    def _edit_inputs(self, sender):
        with self.out:
            clear_output()
            #display(EditCsv(self.config))
            display(EditJson(self.config))

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
                #display(subprocess.check_output(['conda', 'run', '-n', 'mf_main', 'python','-O', self.config['fpth_script'], self.config['fpth_config'], self.config['fpth_inputs']]))
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
            #for fpth in fpths:
             #   display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(fpth))[0])))
            #    display(Markdown('`{0}`'.format(fpth)))
            #    d = DisplayFile(fpth)
            #    d.preview_fpth()
                
            fpths = [v for k,v in self.fpths_outputs.items()]
            if len(fpths)==0:
                display(Markdown('select the file(s) that you would like to display from the "outputs" list above '))
            else:

                display(DisplayFiles(fpths))
                
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
    
# IT WOULD BE GOOD TO ADD A PROGRESS BAR
# i think this would require us to time how long it takes for a script to execute and use that 
# as a first estimate. we could also then keep an ongoing record of time-taken to run a script within
# the log file which could be used to keep the assumed time up-to-date / more accurate.
# E.G. owen's example:
# (but there is a fancy looking ipywidget we could use...)
# fpth = r'C:\engDev\git_mf\MF_Toolbox\dev\mf_modules\progress_bar.py'
# # %run $fpth

class RunApps():
    
    def __init__(self,configs):
        """
        Args:
            configs (list): list of RunApp input configs. 
                can explicitly specify a different RunApp to be used when passing 
                the list 
        """
        self.inputconfigs = configs
        self.processes = self._update_configs()
        self.li = []
        self._form()
        self._init_controls()
        for process in self.processes:
            self.li.append(process['app'](process['config']))   
        self.out = widgets.Output()
    
    def _update_configs(self):
        newconfigs = []
        for config in self.inputconfigs:
            if list(config.keys()) == ['app','config']:
                # app to use already explicitly specified
                newconfigs.append(config)     
            else:
                # assume the config got passed without the associated app
                newconfigs.append({'app': RunApp, 'config': config})     
        return newconfigs
        
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
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'ipyrun\docs\images\RunBatch.png')
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
                    l._log() # 'sender'

    def display(self):
        display(self.form)
        display(self.out)
        [display(l) for l in self.li]; 
        
    def _ipython_display_(self):
        self.display() 

class RunAppsMruns():
    
    def __init__(self, di, fdir_input, fdir_output):
        """
        Args:
            configs (list): list of RunApp input configs. 
                can explicitly specify a different RunApp to be used when passing 
                the list 
        """
        
        di_config = RunConfig(di).config
        self.batch = []
        self.fdir_input = os.path.join(di_config['fdir_inputs'], r'modelruninputs')
        self.fdir_output = fdir_output
        
        if not os.path.exists(self.fdir_input):
            os.makedirs(self.fdir_input)

        for filename in os.listdir(self.fdir_input):
            if filename.endswith(".json"):
                self.batch.append(self._create_process(process_name=os.path.splitext(filename)[0], di=di)) 

        filename = os.path.basename(fpth_script)
        process_name = '{0}_{1}'.format(os.path.splitext(filename)[0],'000')
        
        if not self.batch:
            self.batch.append(self._create_process(process_name=process_name, di=di))
        
        self.inputconfigs = self.batch
       
        self.processes = self._update_configs()
        self.li = []
        self._form()
        self._init_controls()
        
        for process in self.processes:
            self.li.append(process['app'](process['config']))   
        self.out = widgets.Output()

    def _create_process(self, process_name, di):
        tmp = copy.deepcopy(di)
        fpth_input = os.path.join(self.fdir_input, process_name + '.json')
        tmp['script_outputs']['0']['fnm'] = os.path.join(self.fdir_output, process_name)
        tmp['fpth_inputs'] = fpth_input
        tmp['fdir_inputs'] = self.fdir_input
        tmp.update({'process_name':process_name})
        
        return {'app':RunApp,'config':tmp}

    def _update_configs(self):
        newconfigs = []
        for config in self.inputconfigs:
            newconfigs.append(self._create_config(config))
        return newconfigs

    def _create_config(self, config):
        if list(config.keys()) == ['app','config']:
            # app to use already explicitly specified
            return config  
        else:
            # assume the config got passed without the associated app
            return{'app': RunApp, 'config': config}

        
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
                                style={'font_weight':'add'})
        self.add_run = widgets.Button(description='add run',
                                tooltip='add new run, based on another run',
                                button_style='warning',
                                style={'font_weight':'bold'})
        self.compare_runs = widgets.Button(description='compare run',
                                tooltip='Compare multiple runs',
                                button_style='info',
                                style={'font_weight':'bold'})
        self.form = widgets.HBox([self.reset, self.help, self.run_batch, self.add_run, self.compare_runs],
                        layout=widgets.Layout(width='100%',align_items='stretch'))   
    
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.run_batch.on_click(self._run_batch)
        self.compare_runs.on_click(self._compare_runs)
        self.add_run.on_click(self._add_run)
        
    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'ipyrun\docs\images\RunBatch.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
        for l in self.li:
            l._reset(sender)

    def _get_process_names(self):
        return [process['config']['process_name'] for process in self.processes]
    
    def _get_apps_layout(self):
        return [widgets.VBox([l.layout, l.out]) for l in self.li]
        
    def _add_run(self, sender):
        
        # Create Dropdown & Run Button
        self.add_run_dd = widgets.Dropdown(
                options=self._get_process_names(),
                description='Run to Copy:',
                disabled=False)
        self.add_run_btn = widgets.Button(description='add chosen run',
                    tooltip='add chosen run',
                    button_style='primary',
                    style={'font_weight':'bold'})
        
        self.add_run_btn.on_click(self._run_add_run) # OnClick method
        with self.out:
            clear_output()
            display(self.add_run_dd)
            display(self.add_run_btn)
    
    def _run_add_run(self,sender):
        
        # Pull selected process from dropdown
        dd_val = self.add_run_dd.value
        dd_split = str(self.add_run_dd.value).split('_')
        
        # Get basename of selected process
        if(dd_split[-1].isdigit()):
            dd_process_name_base = "_".join(dd_split[:-1])
        else:
            dd_process_name_base = dd_val
            
        # Create new process name, by
        # appending the next number to the basename
        current_num = 0
        num_exists = True
        new_process_name = ""
        while (num_exists):
            new_process_name = '{0}_{1}'.format(dd_process_name_base,str(current_num).zfill(3))
            if new_process_name in self._get_process_names():
                current_num = current_num + 1   
            else:
                num_exists = False

        # Copy the selected process to the new process
        new_process = None
        old_process = None
        for process in self.processes:
            if(process['config']['process_name'] == dd_val):
                old_process = copy.deepcopy(process['config'])
        
        # Copy old inputs file, to create new inputs file
        src = old_process['fpth_inputs']
        fdir_inputs = old_process['fdir_inputs']
        dst = os.path.join(fdir_inputs, '{0}{1}'.format(new_process_name,os.path.splitext(src)[1]))
        copyfile(src,dst)
        
        new_process = self._create_process(new_process_name, old_process)
        new_process = self._create_config(new_process)
        
        # Add new process to data within RunApps 
        self.inputconfigs.append(new_process)
        self.processes.append(new_process)
        self.li.append(new_process['app'](new_process['config']))
        self.add_run_dd.options=self._get_process_names() # Update Dropdown
        
        # Display new process
        self.apps_layout.children = self._get_apps_layout()
        '''with self.out:
            display(self.li[-1])'''

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
                    l._log() # 'sender'
                    
    def _compare_runs(self, sender):
        cnt = 0
        ttl = 0
        for l in self.li:
            ttl = ttl + 1
            if l.check.value:
                cnt = cnt + 1
        with self.out:
            clear_output()
            display(Markdown('{0} out of {1} scripts selected to be run'.format(cnt,ttl)))

            self.compare_run_dd = widgets.Dropdown(
                    options=self._update_compare_dd(),
                    description='Pick graph:',
                    disabled=False)
            self.compare_run_btn = widgets.Button(description='Compare',
                        tooltip='Compare',
                        button_style='primary',
                        style={'font_weight':'bold'})

            self.compare_run_btn.on_click(self._run_compare_runs) # OnClick method
            display(self.compare_run_dd)
            display(self.compare_run_btn)
    
    def _update_compare_dd(self):
        self.l_checked = []
        graphs_count = {}
        graphs_tocompare = []
        for l in self.li:
            if l.check.value:
                out_dir = l.config['fpths_outputs']['0']
                self.l_checked.append(out_dir)
                for file in os.listdir(out_dir):
                    if file.endswith(".plotly"):
                        if file in graphs_count:
                            graphs_count[file] += 1
                        else:
                            graphs_count[file] = 1
        for graph in graphs_count:
            if graphs_count[graph] == len(self.l_checked):
                graphs_tocompare.append(graph)
        return graphs_tocompare
    
    def _run_compare_runs(self, sender):
        
        with self.out:
            
            self.compare_run_dd.options = self._update_compare_dd()
            filename = self.compare_run_dd.value

            data_raw = []
            for l in self.l_checked:
                data_raw.append((l,pio.read_json(os.path.join(l, filename))))
                
            layout = data_raw[0][1]['layout']
            data_interim = [(x[0], x[1]['data']) for x in data_raw]
            
            clear_output()
            legend_names = []
            data_out = []
            
            colors = ["lightskyblue",
                    "mediumseagreen",
                    "goldenrod",
                    "deeppink",
                    "LightGray",
                    "mediumspringgreen",
                     "darksalmon"]
            color_index = 0
            
            for dataset in data_interim:
                for scatter in dataset[1]:
                    if scatter['name'] not in legend_names:
                        plot = scatter
                        if scatter['name'] != "External temperature":
                            plot['name'] = scatter['name'] + ' - ' + os.path.basename(dataset[0])
                            plot['line']['color'] = colors[color_index]
                            color_index += 1
                        data_out.append(plot)
                        legend_names.append(plot['name'])

            fig = go.Figure(
                data=tuple(data_out),
                layout=layout
            )
            
            display(self.compare_run_dd)
            display(self.compare_run_btn)
            fig.show()
            
        
    def display(self):
        display(self.form)
        display(self.out)
        self.apps_layout = widgets.VBox(self._get_apps_layout())
        display(self.apps_layout)
        
    def _ipython_display_(self):
        self.display() 
        

# SUPERCEDED

#def run_py_script(fpth,arg):
#    """
#    NOT IN USE
#    run a script using python magic
#    (% means it can't be imported as a script)
#    """
#    if os.path.isfile(fpth):
#        print('run {0}'.format(fpth))
#        %run -i $fpth $arg #-i
#    elif fpth == 'READ PROCESSED DATA ONLY':
#        pass
#    else:
#        print("{0} doesn't exist".format(fpth))

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


# -
if __name__ =='__main__':

    
    
    # dumb form
    #form = RunForm()
    #form


    # Example1 --------------------------
    # RunApp example, using a default JSON file
    # EDIT JSON FILE with custom config and file management

    config={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': {
            '0': {
                    'fdir':r'..\reports',
                    'fnm': r'JupyterReportDemo.pdf',
                    'description': "a pdf report from word"
            }
        }
    }    

    rjson = RunApp(config)  
    display(Markdown('### Example1'))
    display(Markdown('''default RunApp.'''))
    display(rjson)

    display(Markdown('---'))  
    display(Markdown(''))  

    # Example2 --------------------------
    class RunAppEditCsv(RunApp):

        def __init__(self, config):
            super().__init__(config)

        def _edit_inputs(self, sender):
            with self.out:
                clear_output()
                display(EditCsv(self.config))

    di={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
        'fdir':NBFDIR,
        #'fpth_log':os.path.join(NBFDIR,'notebooks',config),
        #'fdir_outputs':os.path.join(NBFDIR,'notebooks')
        #'RunApp_help':RunApp_help
        }  
    rcsv = RunAppEditCsv(di)  
    display(Markdown('### Example2'))
    display(Markdown('''example where the RunApp class has been extended by inheriting the 
    RunApp and overwriting the _edit_inputs
    take a simple csv file as an input instead of a JSON file...
    the main funtions that can be overwritten to extend the class in this way are:

    - _help
    - _show_guide
    - _edit_inputs
    - _run
    - _preview_outputs'''))
    display(rcsv)
    display(Markdown('---'))  
    display(Markdown(''))  

    # Example3 --------------------------
    di={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
        'fdir':os.path.join(NBFDIR,'notebooks'),
        'fdir_outputs':os.path.join(NBFDIR,'notebooks')
        }  

    defaultrunapp={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': {'0': {
            'fdir':r'..\reports',
            'fnm': r'JupyterReportDemo.pdf',
            'description': "a pdf report from word"
                }
            }
        }

    runappcsv = {'app':RunAppEditCsv,'config':di}
    configs = [runappcsv,defaultrunapp,runappcsv]
    runapps = RunApps(configs)  

    display(Markdown('### Example3'))
    display(Markdown('''
    demonstrates how multiple RunApp's can be ran as a batch. if not explicitly defined, the app assumes the default
    RunApp is used.<br> it is also possible to explictly pass a RunApp variant, and it will still be executed within the batch:  

    ```
        di={
            'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
            #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
            #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
            'fdir':os.path.join(NBFDIR,'notebooks'),
            'fdir_outputs':os.path.join(NBFDIR,'notebooks')
            }  

        defaultrunapp={
            'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
            'fdir':NBFDIR,
            'script_outputs': {'0': {
                'fdir':r'..\reports',
                'fnm': r'JupyterReportDemo.pdf',
                'description': "a pdf report from word"
                    }
                }
            }

        runappcsv = {'app':RunAppEditCsv,'config':di}
        configs = [runappcsv,defaultrunapp,runappcsv]
        runapps = RunApps(configs)  
        display(runapps)
    ```
    '''))
    display(runapps)
    display(Markdown('---'))  
    display(Markdown('')) 

    # Example4 --------------------------
    di={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
        'fdir':os.path.join(NBFDIR,'notebooks'),
        'fdir_outputs':os.path.join(NBFDIR,'notebooks')
        }  

    defaultrunapp={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': {'0': {
            'fdir':r'..\reports',
            'fnm': r'JupyterReportDemo.pdf',
            'description': "a pdf report from word"
                }
            }
        }

    runappcsv = {'app':RunAppEditCsv,'config':di}
    configs = [runappcsv,defaultrunapp,runappcsv]
    runapps = RunApps(configs)  

    display(Markdown('### Example4'))
    display(Markdown('''
    as above but with an add run feature added. 

    ```
        di={
            'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
            #'process_name':os.path.basename(os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
            #'fpth_inputs':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
            'fdir':os.path.join(NBFDIR,'notebooks'),
            'fdir_outputs':os.path.join(NBFDIR,'notebooks')
            }  

        defaultrunapp={
            'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
            'fdir':NBFDIR,
            'script_outputs': {'0': {
                'fdir':r'..\reports',
                'fnm': r'JupyterReportDemo.pdf',
                'description': "a pdf report from word"
                    }
                }
            }

        runappcsv = {'app':RunAppEditCsv,'config':di}
        configs = [runappcsv,defaultrunapp,runappcsv]
        runapps = RunApps(configs)  
        display(runapps)
    ```
    '''))
    display(runapps)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    
    fpth_script = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\gbxml.py')
    config={
        'fpth_script':os.path.realpath(fpth_script),
        'fdir':NBFDIR
        }  
    r = RunApp(config)
    r

   # Example5 --------------------------
    fpth_script = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\datadriven\src\create_model_run_file.py')
    fdir = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\datadriven\src')
    di={
        'fpth_script':os.path.realpath(fpth_script),
        'fdir':os.path.join(fdir),
        "script_outputs": {
            "0": {
                "description": "Creates model run file test",
                "fdir": '.',
                "fnm": ''
            }
        }
    } 

    fdir_modelrunoutput = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\datadriven\data\interim')
    fdir_modelruninput = os.path.join(os.environ['mf_root'],r'ipyrun\examples\testproject\05 Model Files') 

        
    runapps = RunAppsMruns(di=di, fdir_input=fdir_modelruninput, fdir_output=fdir_modelrunoutput)  
    display(Markdown('### Example5'))
    display(Markdown('''Batch Run of RunApps, for ModelRun'''))
    display(runapps, display_id=True)








