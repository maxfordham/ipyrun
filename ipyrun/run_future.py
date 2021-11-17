# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %load_ext dotenv
# %dotenv ../.vscode/dev.env -o

# ^ not working for some reason... hence hack below
# for dev only. delete in production.
import sys
#sys.path.append('/mnt/c/engDev/git_mf/ipypdt')
#sys.path.append('/mnt/c/engDev/git_mf/mfom')
#sys.path.append('/mnt/c/engDev/git_mf/ipyword')
sys.path.append('/mnt/c/engDev/git_mf/ipyrun')

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

import plotly.io as pio
import plotly.graph_objects as go

from dataclasses import  field, asdict #dataclass,
from dacite import from_dict
from typing import Optional, List, Dict, Type
from pydantic.dataclasses import dataclass

# widget stuff
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet

# core mf_modules
from mfom.directories import ProjectDirs

# from this repo
from ipyrun._runconfig import RunConfig, AppConfig, Output, Outputs

from ipyrun._ipyeditcsv import EditCsv
from ipyrun._ipyeditjson import EditJson
from ipyrun._ipydisplayfile import DisplayFile, PreviewOutputs
from ipyrun.utils import make_dir, del_matching, display_python_file, make_dir, read_json, write_json
from ipyrun.constants import BUTTON_WIDTH_MIN, BUTTON_WIDTH_MEDIUM, FDIR_ROOT_EXAMPLE, FPTH_SCRIPT_EXAMPLE, FDIR_APP_EXAMPLE, FPTH_SCRIPT_EXAMPLE_CSV, FPTH_RUNAPP_HELP, FPTH_RUNAPPS_HELP
from ipyrun.mydocstring_display import display_module_docstring

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0]+user[2]

@dataclass
class RunFormTestInput:
    fpth_script: str = 'fpth_script'
    fpth_inputs: str = 'fpth_inputs' 
    process_name: str = 'process_name' 
    pretty_name: str = 'pretty_name'
# +
# RUN __FUTURE__
from pydantic import BaseModel
import typing

class RunId(BaseModel):
    process_name: str = 'process_name'
    pretty_name: str = 'pretty_name'
    run_index: int = 0
    in_batch: bool = True
            
        
class RunActions(BaseModel):
    check: typing.Callable = (lambda : display('check'))
    uncheck: typing.Callable = (lambda : display('uncheck'))
    help_ui_show: typing.Callable = (lambda : display(Image(FPTH_RUNAPP_HELP)))
    help_ui_hide: typing.Callable = (lambda : display('help_ui_hide'))
    help_run_show: typing.Callable = (lambda : display('help_run_show'))
    help_run_hide: typing.Callable = (lambda : display('help_run_hide'))
    inputs_show: typing.Callable = (lambda : display('inputs_show'))
    inputs_hide: typing.Callable = (lambda : display('inputs_hide'))
    outputs_show: typing.Callable = (lambda : display('outputs_show'))
    outputs_hide: typing.Callable = (lambda : display('outputs_hide'))
    log_show: typing.Callable = (lambda : display('log_show'))
    log_hide: typing.Callable = (lambda : display('log_hide'))
    run: typing.Callable = (lambda : display('run'))
    run_hide: typing.Callable = (lambda : display('console_hide'))
    activate: typing.Callable = (lambda : display('activate'))
    deactivate: typing.Callable = (lambda : display('deactivate'))
        


# -

class RunActionsUi:
    minwidth=BUTTON_WIDTH_MIN
    medwidth=BUTTON_WIDTH_MEDIUM
    
    def __init__(self, run_actions:RunActions=RunActions(), run_id:RunId=RunId()):
        self.run_actions = run_actions
        self.run_id = run_id
        self._init_objects()
        self._init_controls()
        
    def _init_objects(self):
        self.help_ui = widgets.ToggleButton(icon='question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.help_run = widgets.ToggleButton(icon='book',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.help_config = widgets.ToggleButton(icon='cog',
                                tooltip='the config of the task',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.inputs = widgets.ToggleButton(description='inputs',
                                tooltip='edit the user input information that is used when the script is executed',
                                button_style='warning',
                                icon = 'edit',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.outputs = widgets.ToggleButton(description='outputs',
                                icon='search',
                                tooltip='show a preview of the output files generated when the script runs',
                                button_style='info',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.log = widgets.ToggleButton(description='log',
                                tooltip='show a log of when the script was executed to generate the outputs, and by who',
                                button_style='info',
                                icon='scroll',
                                style={'font_weight': 'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.in_batch = widgets.Checkbox(
                                value=self.run_id.in_batch,
                                disabled=False,
                                indent=False,
                                layout=widgets.Layout(max_width='30px',height='30px', padding='3px')
                                )
        self.run = widgets.Button(description=' run',
                                icon = 'fa-play',
                                tooltip='execute the script based on the user inputs',
                                button_style='success',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.show = widgets.Button(
                                icon='fa-eye',
                                tooltips='default show',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.hide = widgets.Button(
                                icon='fa-eye-slash',
                                tooltips='default show',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_log = widgets.Output()
        self.out_console = widgets.Output()
        
    def _init_controls(self):
        self.help_ui.observe(self._help_ui, names='value')
        self.help_run.observe(self._help_run, names='value')
        self.inputs.observe(self._inputs, names='value')
        self.outputs.observe(self._outputs, names='value')
        self.log.observe(self._log, names='value')
        self.run.on_click(self._run)
        self.in_batch.observe(self._in_batch, names='value')
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)
        
    @property
    def get_show_hide_value(self):
        return [self.help_ui.value,
                self.help_run.value,
                self.help_config.value,
                self.inputs.value,
                self.outputs.value,
                self.log.value]
    
    def set_show_hide_value(self):
        if self.get_show_hide_value == self.default_show_hide[True]:
            return True
        elif self.get_show_hide_value == self.default_show_hide[False]:
            return False
        else:
            return None
        
    def _show(self, on_click):
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = True
        self.outputs.value = True
        self.log.value = True
        
    def _hide(self, on_click):
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = False
        self.outputs.value = False
        self.log.value = False
        
    def _in_batch(self, on_change):
        self.run_id.in_batch = self.in_batch.value
        
    def _help_ui(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_help_ui:
            if self.help_ui.value:
                self.run_actions.help_ui_show()
            else:
                self.run_actions.help_ui_hide()
                clear_output()
        
    def _help_run(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_help_run:
            if self.help_run.value:
                self.run_actions.help_run_show()
            else:
                self.run_actions.help_run_hide()
                clear_output()
        
    def _inputs(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_inputs:
            if self.inputs.value:
                self.run_actions.inputs_show()
            else:
                self.run_actions.inputs_hide()
                clear_output()
                
    def _outputs(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_outputs:
            if self.outputs.value:
                self.run_actions.outputs_show()
            else:
                self.run_actions.outputs_hide()
                clear_output()
                
    def _log(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_log:
            if self.log.value:
                self.run_actions.log_show()
            else:
                self.run_actions.log_hide()
                clear_output()
                
    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_actions.run()


# +
class RunApp(RunActionsUi):
    def __init__(self, run_actions:RunActions=RunActions(), run_id:RunId=RunId()):
        super().__init__(run_actions=run_actions,run_id=run_id)
        self._layout_out()
        self._run_form()
        
    def _layout_out(self):
        self.layout_out = widgets.VBox([
            widgets.HBox([self.out_console]),
            widgets.HBox([self.out_help_ui, self.out_help_run, self.out_help_config]),
            widgets.HBox([self.out_inputs, self.out_outputs, self.out_log])
        ])
        
    def _run_form(self):
        self.button_bar = widgets.HBox(
            [
                widgets.HBox(
                    [self.help_ui,self.help_run,self.help_config,self.inputs,self.outputs,self.run,self.log],
                    layout=widgets.Layout(align_items='stretch')),
                widgets.HBox([self.show, self.hide])
            ],layout=widgets.Layout(width='100%',justify_content='space-between'))
        self.layout = widgets.VBox([
            self.button_bar,
            self.layout_out
        ])
        self.acc = widgets.Accordion(children=[self.layout], selected_index=None, layout=widgets.Layout(width='100%'))
        self.run_form = widgets.HBox([self.in_batch, self.acc],layout=widgets.Layout(margin='0px',padding='0px',border='0px'))
        self.acc.set_title(0, self.run_id.pretty_name)
        
    def display(self):
        display(self.run_form)

    def _ipython_display_(self):
        self.display()
        
run = RunApp()
run

# +
import pathlib

class RunId(BaseModel):
    #script_name: str
    project_number: str = 'J5001'
    process_name: str = 'process_name'
    pretty_name: str = 'pretty_name'
    run_index: int = 0

class ScriptHandler(BaseModel):
    fpth_script: pathlib.Path
    fdir_appdata: pathlib.Path
    #fpth_config: pathlib.Path
    fpth_inputs: pathlib.Path
    fpths_outputs: List[pathlib.Path]
    #fpth_log: pathlib.Path
    
class AppConfig(BaseModel):
    run_id: RunId = RunId()
    paths: ScriptHandler
        


# +
def run(cmd):
    spinner = HaloNotebook(animation='marquee', text='Running', spinner='dots')
    print(' '.join([str(c) for c in cmd]))
    try:
        spinner.start()
        subprocess.check_output(cmd)
        spinner.succeed('Finished')
    except subprocess.CalledProcessError as e:
        spinner.fail('Error with Process')

run_id = RunId(
    process_name = 'line_graph',
)

run_script = ScriptHandler(
    fpth_script=pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV),
    fdir_appdata=pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent,
    fpth_inputs=pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'inputs-{run_id.process_name}.csv',
    fpths_outputs=[
        pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'outputs-{run_id.process_name}.csv',
        pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'outputs-{run_id.process_name}.plotly.json'
    ]
             )

cmd = ['python','-O', run_script.fpth_script, run_script.fpth_inputs, *run_script.fpths_outputs]

run_actions = RunActions(
    help_run_show=(lambda: display(DisplayFile(str(run_script.fpth_script)))),
    inputs_show=(lambda: display(EditCsv(run_script.fpth_inputs))),
    outputs_show=(lambda: display(PreviewOutputs([Output(str(f)) for f in run_script.fpths_outputs]))),
    run=(lambda: run(run_script(cmd)))
)

run_app = RunApp(run_actions=run_actions)
run_app
# -

cmd = ['python','-O', run_script.fpth_script, run_script.fpth_inputs, *run_script.fpths_outputs]

from jinja2 import Template
t = Template("Hello {{ something }}!")
t.render(something="World")

t = Template("My favorite numbers: {% for n in range(1,10) %}{{n}} " "{% endfor %}")
t.render()

t = Template("My favorite numbers: *")
t.render()

run_actions.help_run_show()



from ipyrun._ipyeditcsv import EditCsv
from ipyrun._runconfig import Output
from ipyrun._ipydisplayfile import DisplayFile, PreviewOutputs
# ?EditCsv



PreviewOutputs()

if __name__ == '__main__':
    from ipyrun._ipyeditcsv import EditRunAppCsv # TODO: i think there is an issue with "EditRunAppCsv" that needs fixing
    # Example2 --------------------------
    class RunAppEditCsvLineGraph(RunApp):

        def __init__(self, config_app, app_config_revert_to_file=False):
            super().__init__(config_app,app_config_revert_to_file=app_config_revert_to_file)

        def _edit_inputs(self, sender):
            with self.out:
                clear_output()
                display(EditRunAppCsv(self.config_app))

        def execute(self):
            fpth_csv = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.csv')
            fpth_plotly = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.plotly.json')
            subprocess.check_output(['python','-O', self.config_app.fpth_script, self.config_app.fpth_inputs, fpth_csv, fpth_plotly])
            self.config_app.script_outputs = [Output(fpth_csv),Output(fpth_plotly)]


    config_app_line_graph=AppConfig(
            fpth_script=FPTH_SCRIPT_EXAMPLE_CSV,
            fdir=FDIR_APP_EXAMPLE,
            ftyp_inputs='csv'
        )
    
    rcsv = RunAppEditCsvLineGraph(config_app_line_graph)
    display(rcsv)


# +
class BatchActions(BaseModel):
    help_ui_show: typing.Callable = (lambda : display('help_ui_show'))
    help_ui_hide: typing.Callable = (lambda : display('help_ui_hide'))
    help_run_show: typing.Callable = (lambda : display('help_run_show'))
    help_run_hide: typing.Callable = (lambda : display('help_run_hide'))
    inputs_show: typing.Callable = (lambda : display('inputs_show'))
    inputs_hide: typing.Callable = (lambda : display('inputs_hide'))
    outputs_show: typing.Callable = (lambda : display('outputs_show'))
    outputs_hide: typing.Callable = (lambda : display('outputs_hide'))
    log_show: typing.Callable = (lambda : display('log_show'))
    log_hide: typing.Callable = (lambda : display('log_hide'))
    run: typing.Callable = (lambda : display('run'))
    activate: typing.Callable = (lambda : display('activate'))
    deactivate: typing.Callable = (lambda : display('deactivate'))
    add_run_show: typing.Callable = (lambda : display('add_run_show'))
    add_run_hide: typing.Callable = (lambda : display('add_run_hide'))
    remove_run_show: typing.Callable = (lambda : display('remove_run_show'))
    remove_run_hide: typing.Callable = (lambda : display('remove_run_hide'))
    wizard_show: typing.Callable = (lambda : display('wizard_show'))
    wizard_hide: typing.Callable = (lambda : display('wizard_hide'))
        
class BatchActionsUi():

    def __init__(batch_actions: BatchActions):
        self._init_objects()
        
    def _init_objects(self):
        self.check = widgets.Checkbox(
                        value=False,
                        disabled=False,
                        indent=False,
                        layout=widgets.Layout(max_width='30px',height='30px', padding='3px')
                        )
        self.reset = widgets.Button(icon='fa-eye-slash',#'fa-repeat'
                                tooltip='removes temporary output view',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.help_ui = widgets.ToggleButton(icon='question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.help_run = widgets.ToggleButton(icon='book',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.run_batch = widgets.Button(description=' run',
                                icon = 'fa-play',
                                tooltip='execute the script based on the user inputs',
                                button_style='success',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.inputs = widgets.ToggleButton(description=' inputs',
                                icon='edit',
                                tooltip='a preview of input data',
                                button_style='info',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.outputs = widgets.ToggleButton(description=' outputs',
                                icon='search',
                                tooltip='show a preview of the output files generated when the script runs',
                                button_style='info',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.medwidth))
        self.add = widgets.ToggleButton(
                                #description='add run',
                                tooltip='add new run, based on another run',
                                button_style='primary',
                                icon='plus',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.remove = widgets.ToggleButton(
                                #description='delete run',
                                tooltip='delete a run',
                                icon='minus',
                                button_style='danger',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.wizard = widgets.ToggleButton(
                                #description='delete run',
                                tooltip='manage runs wizard',
                                icon='wizard',
                                button_style='danger',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width=self.minwidth))
        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_log = widgets.Output()

        
# -

        self.form = widgets.HBox([self.check, self.reset, self.help,  self.run_batch, self.preview_outputs],
                        layout=widgets.Layout(width='100%',align_items='stretch'))




# +
def log(path_log):
    if type(path_log) == str:
        path_log = pathlib.Path(path_log)
    if path_log.is_file:
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
    return 
    
path_log = '/mnt/c/engDev/git_mf/ipyrun/examples/J0000/test_appdir/appdata/log/log-expansion_vessel_sizing.csv'

# -





widgets.ToggleButton(layout=widgets.Layout(border='5px'))

RunConfig(config_app=AppConfig())

# +
#AppConfig()
# -

asdict(AppConfig(**{'process_name': 'asdf'}))


