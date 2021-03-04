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
#     display_name: mf_base
#     language: python
#     name: mf_base
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
from halo import HaloNotebook
import traceback
import sys

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
                                layout=widgets.Layout(width='50px'))
        self.help = widgets.Button(icon='fa-question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='50px'))
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
    def __init__(self,config,lkup_outputs_from_script=True):
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
                'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
                'fdir':NBFDIR,
                }

            r = RunApp(config)
            from ipyrun._ipyeditjson import

            ui = EditListOfDicts(li)
            ui
            ```
        """
        self._init_RunApp(config,lkup_outputs_from_script=lkup_outputs_from_script)


    def _init_RunApp(self,config,lkup_outputs_from_script=True):
        self.out = widgets.Output()
        self.errors = []
        self._init_RunConfig(config, lkup_outputs_from_script=lkup_outputs_from_script)
        self.form()
        self.outputsfpth.options = self.fpths_outputs
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
            fpth = os.path.join(os.environ['MF_ROOT'],r'ipyrun\docs\images\RunApp.png')
            display(Image(fpth))

    def _reset(self, sender):
        with self.out:
            clear_output()

    def _edit_inputs(self, sender):
        with self.out:
            clear_output()
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

    def _cache(self):
        self.config_to_json()
        self.archive_inputs()
        self._log()

    def pre_script_func(self):
        pass

    def post_script_func(self):
        pass

    def execute_subproces(self):
        subprocess.check_output(['python','-O', self.config['fpth_script'], self.config['fpth_config'], self.config['fpth_inputs']])

    def _run_script(self, sender):
        self.pre_script_func()
        self._cache()
        with self.out:
            clear_output()
            if os.path.isfile(self.config['fpth_inputs']):
                spinner = HaloNotebook(animation='marquee', text='Running', spinner='dots')
                try:
                    spinner.start()
                    self.execute_subproces()
                    spinner.succeed('Finished')
                except subprocess.CalledProcessError as e:
                    spinner.fail('Error with Process')

                #display(subprocess.check_output(['conda', 'run', '-n', 'mf_main', 'python','-O', self.config['fpth_script'], self.config['fpth_config'], self.config['fpth_inputs']]))
            else:
                display(Markdown("## inputs have not been saved"))
                display(Markdown('click on the "edit inputs" button to edit inputs and hit save when done'))
                display(Markdown('this will save a datafile that is passed to the script when you press run'))
                display(Markdown('the input datafile should be saved here:'))
                display(Markdown('`{0}`'.format(self.config['fpth_inputs'])))

        self.post_script_func()

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

            fpths = self.fpths_outputs

            if 'display_ignore' in self.config:
                display_ignore = self.config['display_ignore']
            else:
                display_ignore = []

            if 'display_prefix' in self.config:
                display_prefix = self.config['display_prefix']
            else:
                display_prefix = ''

            if len(fpths)==0:
                display(Markdown('select the file(s) that you would like to display from the "outputs" list above '))
            else:
                for f in fpths:
                    if not os.path.isfile(f) and not os.path.isdir(f):
                        fpths.remove(f)
                display(DisplayFiles(fpths, fpths_ignore=display_ignore, fpth_prefix=display_prefix))

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


config={
    'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
    'fdir':NBFDIR,
    'script_outputs': [
        {
                'fdir_rel':r'..\reports',
                'fnm': r'JupyterReportDemo.pdf',
                'description': "a pdf report from word"
        },
    ]
}

rjson = RunApp(config)
rjson

# +


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
            fpth = os.path.join(os.environ['MF_ROOT'],r'ipyrun\docs\images\RunBatch.png')
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
# +
class RunConfigTemplated(RunConfig):
    # DEPRECATED #
    def _fdir_inputs(self, folder_name=None):
        # add inputs folder name
        if 'fdir_inputs' in self.user_keys:
            make_dir(self.config['fdir_inputs'])
            return self.config['fdir_inputs']
        elif 'fdir_inputs_foldername' in self.user_keys:
            make_dir(os.path.join(self.fdir,r'appdata\inputs',self.config['fdir_inputs_foldername']))
            return os.path.join(self.fdir,r'appdata\inputs',self.config['fdir_inputs_foldername'])
        else:
            make_dir(os.path.join(self.fdir,r'appdata\inputs\batchinputs'))
            return os.path.join(self.fdir,r'appdata\inputs\batchinputs')

    def _fpth_inputs(self, process_name=None, template_process=None):

        if process_name:
            name = process_name + '.json'
        else:
            name = 'TEMPLATE.json'

        if template_process:
            src = template_process
        else:
            src = self.fpth_template_input

        dstn = os.path.join(self.fdir_inputs, name)
        if not os.path.isfile(dstn) or not process_name:
            copyfile(src, dstn)

        return dstn

class RunAppsTemplated():

    def __init__(self, di, app=RunApp, folder_name=None):
        """
        Args:
            di (object): list of RunApp input configs.
                can explicitly specify a different RunApp to be used when passing
                the list
        """

        self.app = app
        self.configapp = RunConfig#Templated
        self.di = di
        #self._fdir_inputs = self.configapp(di)._fdir_inputs(folder_name=folder_name)
        #self.processes = self._update_processes(self._fdir_inputs)
        self.runconfig = self.configapp(self.di)
        
        self.processes = self._update_processes(self.runconfig.fdir_inputs)
        
        self.li = []
        self._form()
        self._init_controls()
        for process in self.processes:
            self.li.append(process['app'](process['config']))
        self.out = widgets.Output()

    def _create_process(self, process_name='TEMPLATE', template_process=None):
        process_di = copy.deepcopy(self.di)
        process_di['process_name'] = process_name
        process_di['pretty_name'] = process_name
        process = self.configapp(process_di)
        process.config['fpth_inputs'] = process.fpth_inputs#(process_name=process_name,template_process=template_process) #process._fpth_inputs(process_name=process_name,template_process=template_process)
        return {'app':self.app,'config':process.config}

    def _update_processes(self, fdir_inputs):
        configs = []

        # Add processes to batch, from existing JSON files
        for filename in os.listdir(fdir_inputs):
            if filename.endswith(".json"):
                process_name = os.path.splitext(filename)[0]
                process = self._create_process(process_name=process_name)
                if process_name == 'TEMPLATE':
                    # Add JSON template to beginning of the batch
                    configs.insert(0, process)
                else:
                    configs.append(process)

        # If no JSON files exist, create a Template File
        if not configs:
            configs.append(self._create_process())

        return configs


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
                                button_style='primary',
                                style={'font_weight':'bold'})
        self.del_run = widgets.Button(description='delete run',
                                tooltip='delete a run',
                                button_style='danger',
                                style={'font_weight':'bold'})
        self.form = widgets.HBox([self.reset, self.help, self.run_batch, self.add_run, self.del_run],
                        layout=widgets.Layout(width='100%',align_items='stretch'))

    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.run_batch.on_click(self._run_batch)
        self.add_run.on_click(self._add_run)
        self.del_run.on_click(self._del_run)

    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['MF_ROOT'],r'ipyrun\docs\images\RunBatch.png')
            display(Image(fpth))

    def _reset(self, sender):
        with self.out:
            clear_output()
        for l in self.li:
            l._reset(sender)

    def _get_process_names(self):
        return [process['config']['process_name'] for process in self.processes]

    def _get_apps_layout(self):
        return [widgets.VBox([l.layout, l.out]) for l in self.li[1:]]

    def _add_run(self, sender):
        # Create Dropdown, Run Button, and Name field
        self.add_run_dd = widgets.Dropdown(
                options=self._get_process_names(),
                description='Run to Copy:',
                disabled=False)

        self.add_run_btn = widgets.Button(description='Add Chosen Run',
                    tooltip='add chosen run',
                    button_style='primary',
                    style={'font_weight':'bold'})

        self.add_run_name = widgets.Text(
                                value='',
                                placeholder='New Process Name',
                                description='Name:',
                                disabled=False)

        self.add_run_btn.on_click(self._run_add_run) # Onclick method
        with self.out:
            clear_output()
            display(self.add_run_dd)
            display(self.add_run_name)
            display(self.add_run_btn)

    def _del_run(self, sender):
        # Create Dropdown & Run Button
        self.del_run_dd = widgets.Dropdown(
                options=self._get_process_names()[1:],
                description='Run:',
                disabled=False)
        self.del_run_btn = widgets.Button(description='Delete Chosen Run',
                    tooltip='delete chosen run',
                    button_style='danger',
                    style={'font_weight':'bold'})
        self.del_run_btn.on_click(self._run_del_run) # Onlick method
        with self.out:
            clear_output()
            display(self.del_run_dd)
            display(self.del_run_btn)

    def _run_del_run(self, sender):
        dd_val = self.del_run_dd.value
        for process in self.processes:
            if(process['config']['process_name'] == dd_val):
                self.processes.remove(process)

        for l in self.li:
            if(l.config['process_name'] == dd_val):
                os.remove(l.config['fpth_inputs'])
                self.li.remove(l)

        self.del_run_dd.options=self._get_process_names()[1:] # Update Dropdown
        self.apps_layout.children = self._get_apps_layout()

    def _run_add_run(self,sender):

        # Pull info from widgets
        dd_val = self.add_run_dd.value
        dd_split = str(self.add_run_dd.value).split('_')
        process_name_base = self.add_run_name.value
        if not process_name_base:
            process_name_base = dd_split[-1]

        # Get next highest number from processes
        basenumbers = [process.split('_')[0] for process in self._get_process_names()]
        current_num = 0
        num_exists = True
        new_process_name = ""
        while (num_exists):
            if str(current_num).zfill(3) in basenumbers:
                current_num = current_num + 1
            else:
                new_process_name = '{0}_{1}'.format(str(current_num).zfill(3),process_name_base)
                num_exists = False

        old_process = None
        for process in self.processes:
            if(process['config']['process_name'] == dd_val):
                old_process = copy.deepcopy(process['config'])

        new_process = self._create_process(process_name=new_process_name,template_process=old_process['fpth_inputs'])

        # Add new process to data within RunApps
        self.processes.append(new_process)
        self.li.append(new_process['app'](new_process['config']))

        self.add_run_dd.options=self._get_process_names() # Update Dropdown

        # Display new process
        self.apps_layout.children = self._get_apps_layout()

    def _run_batch(self, sender):
        cnt = 0
        ttl = 0
        for l in self.li:
            ttl = ttl + 1
            if l.check.value:
                cnt = cnt + 1

        with self.out:
            clear_output()
            display(Markdown('{0} out of {1} scripts selected to be run'.format(cnt,ttl-1)))
            for l in self.li:
                if l.check.value:
                    spinner = HaloNotebook(
                                animation='marquee',
                                text='Running {0}'.format(l.config['process_name']),
                                spinner={
                                    'interval': 100,
                                    'frames': ['-']
                                })
                    spinner.start()
                    l._run_script('sender')
                    l._log() # 'sender'
                    spinner.succeed('Finished {0}'.format(l.config['process_name']))
                    #display(Markdown('Running: {0}'.format(l.config['process_name'])))


    def display(self):
        display(self.form)
        display(self.out)
        self.apps_layout = widgets.VBox(self._get_apps_layout())
        display(self.apps_layout)

    def _ipython_display_(self):
        self.display()
# -

if __name__ == '__main__':
    display(Markdown('### Example5'))
    display(Markdown('''
    Demonstrates how multiple RunApp's can be ran as a batch, with templating. If not explicitly defined, the app assumes the default
    RunApp is used. But, if definied, a variant of RunApp can be used for the whole batch. New runs can be added, based on other runs or based on the template. Runs can also be deleted.
    '''))

    di={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py')
    }
    runappstemplated = RunAppsTemplated(di)
    display(runappstemplated)
    display(Markdown('---'))
    display(Markdown(''))

if __name__ == '__main__':

    # Example1 --------------------------
    # RunApp example, using a default JSON file
    # EDIT JSON FILE with custom config and file management

    config={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': [
            {
                    'fdir':r'..\reports',
                    'fnm': r'JupyterReportDemo.pdf',
                    'description': "a pdf report from word"
            }
        ]
    }


    rjson = RunApp(config)
    display(Markdown('### Example1'))
    display(Markdown('''default RunApp.'''))
    display(rjson)

    # Example2 --------------------------
    class RunAppEditCsv(RunApp):

        def __init__(self, config):
            super().__init__(config)

        def _edit_inputs(self, sender):
            with self.out:
                clear_output()
                display(EditCsv(self.config))

    di={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
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
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
        'fdir':os.path.join(NBFDIR,'notebooks'),
        'fdir_outputs':os.path.join(NBFDIR,'notebooks')
        }

    defaultrunapp={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': [
                {
                'fdir':r'..\reports',
                'fnm': r'JupyterReportDemo.pdf',
                'description': "a pdf report from word"
                }
            ]
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
            'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
            #'process_name':os.path.basename(os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
            #'fpth_inputs':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
            'fdir':os.path.join(NBFDIR,'notebooks'),
            'fdir_outputs':os.path.join(NBFDIR,'notebooks')
            }

        defaultrunapp={
            'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
            'fdir':NBFDIR,
            'script_outputs': [
                    {
                        'fdir':r'..\reports',
                        'fnm': r'JupyterReportDemo.pdf',
                        'description': "a pdf report from word"
                    }
                ]
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
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        #'process_name':os.path.basename(os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')),
        #'fpth_inputs':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv'),
        'fdir':os.path.join(NBFDIR,'notebooks'),
        'fdir_outputs':os.path.join(NBFDIR,'notebooks')
        }

if __name__ == '__main__':
    defaultrunapp={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':NBFDIR,
        'script_outputs': [
                {
                    'fdir':r'..\reports',
                    'fnm': r'JupyterReportDemo.pdf',
                    'description': "a pdf report from word"
                }
            ]
        }

    runappcsv = {'app':RunAppEditCsv,'config':di}
    configs = [runappcsv,defaultrunapp,runappcsv]
    runapps = RunApps(configs)

    display(Markdown('### Example5'))
    display(Markdown('''
    Demonstrates how multiple RunApp's can be ran as a batch, with templating. If not explicitly defined, the app assumes the default
    RunApp is used. But, if definied, a variant of RunApp can be used for the whole batch. New runs can be added, based on other runs or based on the template. Runs can also be deleted.
    '''))

    di={
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py')
    }
    runappstemplated = RunAppsTemplated(di)
    display(runappstemplated)
    display(Markdown('---'))
    display(Markdown(''))
