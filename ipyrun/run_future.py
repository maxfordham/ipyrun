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
#     display_name: Python [conda env:mf_base1] *
#     language: python
#     name: conda-env-mf_base1-py
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
sys.path.append('/mnt/c/engDev/git_mf/ipyautoui/src')

from ipyautoui.autoui import AutoUi,display_template_ui_model


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
from ipyrun.constants import BUTTON_WIDTH_MIN, \
    BUTTON_WIDTH_MEDIUM, \
    FDIR_ROOT_EXAMPLE, \
    FPTH_SCRIPT_EXAMPLE, \
    FDIR_APP_EXAMPLE, \
    FPTH_SCRIPT_EXAMPLE_CSV, \
    FPTH_RUNAPP_HELP, \
    FPTH_RUNAPPS_HELP, \
    FPTH_SCRIPT_EXAMPLE_1
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
    check: typing.Optional[typing.Callable] = (lambda : display('check'))
    uncheck: typing.Optional[typing.Callable] = (lambda : display('uncheck'))
    help_ui_show: typing.Optional[typing.Callable] = (lambda : display(Image(FPTH_RUNAPP_HELP)))
    help_ui_hide: typing.Optional[typing.Callable] = (lambda : display('help_ui_hide'))
    help_run_show: typing.Optional[typing.Callable] = (lambda : display('help_run_show'))#None
    help_run_hide: typing.Optional[typing.Callable] = (lambda : display('help_run_hide'))
    help_config_show: typing.Optional[typing.Callable] = (lambda : display('help_run_show'))
    help_config_hide: typing.Optional[typing.Callable] = (lambda : display('help_run_hide'))
    inputs_show: typing.Optional[typing.Callable] = (lambda : display('inputs_show'))
    inputs_hide: typing.Optional[typing.Callable] = (lambda : display('inputs_hide'))
    outputs_show: typing.Optional[typing.Callable] = (lambda : display('outputs_show'))
    outputs_hide: typing.Optional[typing.Callable] = (lambda : display('outputs_hide'))
    log_show: typing.Optional[typing.Callable] = (lambda : display('log_show'))
    log_hide: typing.Optional[typing.Callable] = (lambda : display('log_hide'))
    run: typing.Optional[typing.Callable] = (lambda : display('run'))
    run_hide: typing.Optional[typing.Callable] = (lambda : display('console_hide'))
    activate: typing.Optional[typing.Callable] = (lambda : display('activate'))
    deactivate: typing.Optional[typing.Callable] = (lambda : display('deactivate'))
#     show: typing.Optional[typing.Callable] = (lambda : display('show'))
#     hide: typing.Optional[typing.Callable] = (lambda : display('hide'))

# +
class RunActionsUi:
    minwidth=BUTTON_WIDTH_MIN
    medwidth=BUTTON_WIDTH_MEDIUM
    
    def __init__(self, run_actions:RunActions=RunActions(), run_id:RunId=RunId()):
        self.run_actions = run_actions
        self.run_id = run_id
        self._init_objects()
        self._init_controls()
        
    def _init_objects(self):
#         button list:
#         ---------------
#         self.in_batch
#         self.help_ui
#         self.help_run
#         self.help_config
#         self.inputs
#         self.outputs
#         self.log
#         self.in_batch
#         self.run
#         self.show
#         self.hide
        self.in_batch = widgets.Checkbox(
                                value=self.run_id.in_batch,
                                disabled=False,
                                indent=False,
                                layout=widgets.Layout(max_width='30px',height='30px', padding='3px')
                                )
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
        self.help_config.observe(self._help_run, names='value')
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
        with self.out_console: 
            clear_output()
        
    def _in_batch(self, on_change):
        self.run_id.in_batch = self.in_batch.value
        
    def _show_hide_output(self, widgets_output, widget_button, show_action, hide_action):
        with widgets_output:
            if widget_button.value:
                show_action()
            else:
                hide_action()
                clear_output()
            
#         self.run_actions.uncheck
#         self.run_actions.help_ui_hide
#         self.run_actions.help_run_hide
#         self.run_actions.inputs_hide
#         self.run_actions.outputs_hide
#         self.run_actions.log_hide
#         self.run_actions.run_hide
#         self.run_actions.deactivate
        
    def _help_ui(self, on_change):
        self._show_hide_output(self.out_help_ui, 
                               self.help_ui, 
                               self.run_actions.help_ui_show, 
                               self.run_actions.help_ui_hide)

    def _help_run(self, on_change):
        self._show_hide_output(self.out_help_run, 
                               self.help_run, 
                               self.run_actions.help_run_show, 
                               self.run_actions.help_run_hide)
        
    def _help_config(self, on_change):
        self._show_hide_output(self.out_help_run, 
                               self.help_run, 
                               self.run_actions.help_config_show, 
                               self.run_actions.help_config_hide)
        
    def _inputs(self, on_change):
        self._show_hide_output(self.out_inputs, 
                               self.inputs, 
                               self.run_actions.inputs_show, 
                               self.run_actions.inputs_hide)
                
    def _outputs(self, on_change):
        self._show_hide_output(self.out_outputs, 
                               self.outputs, 
                               self.run_actions.outputs_show, 
                               self.run_actions.outputs_hide)
                
    def _log(self, on_change):
        self._show_hide_output(self.out_log, 
                               self.log, 
                               self.run_actions.log_show, 
                               self.run_actions.log_hide)
                
    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_actions.run()
            
    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form 
        where the display method is overwritten"""
        out= widgets.VBox([
            widgets.HBox([self.help_ui, self.out_help_ui]),
            widgets.HBox([self.help_run, self.out_help_run]),
            widgets.HBox([self.help_config, self.out_help_config ]),
            widgets.HBox([self.inputs, self.out_inputs]),
            widgets.HBox([self.outputs, self.out_outputs]),
            widgets.HBox([self.log, self.out_log]),
            widgets.HBox([self.in_batch]),
            widgets.HBox([self.run, self.out_console]),
            widgets.HBox([self.show]),
            widgets.HBox([self.hide])
        ])
        display(widgets.HTML('<b>Buttons to be programmed from `RunActions`</b> '))
        display(out)

    def _ipython_display_(self):
        self.display()
        
if __name__ == "__main__":
    actions = RunActionsUi()
    display(actions)


# +
class RunUiConfig(BaseModel):
    include_show_hide = True
    
def build_button_bar(button_map: typing.Dict, ui_config: RunUiConfig):
    button_bar = widgets.HBox(layout=widgets.Layout(width='100%',justify_content='space-between'))
    left = widgets.HBox(layout=widgets.Layout(align_items='stretch'))
    left.children = [k for k, v in button_map['left'].items() if v is not None]
    button_bar.children = [left]
    if ui_config.include_show_hide:
        right = widgets.HBox(button_map['right'], layout=widgets.Layout(align_items='stretch'))
        button_bar.children = [left, right]
    return button_bar

class RunApp(RunActionsUi):
    """wrapper that extends RunActionsUi to create UI form"""
    def __init__(self, run_actions:RunActions=RunActions(), run_id:RunId=RunId(), ui_config:RunUiConfig=RunUiConfig()):
        super().__init__(run_actions=run_actions,run_id=run_id)
        self.ui_config = ui_config
        self._layout_out()
        self._run_form()
        
    @property
    def _button_map(self):
        return {
            'outside': {self.in_batch: self.run_actions.check},
            'left': {
                    self.help_ui: self.run_actions.help_ui_show,
                    self.help_run: self.run_actions.help_run_show,
                    self.help_config: self.run_actions.help_config_show,
                    self.inputs: self.run_actions.inputs_show,
                    self.outputs: self.run_actions.outputs_show,
                    self.log: self.run_actions.log_show,
                    self.run: self.run_actions.run,
            },
            'right': [self.show, self.hide]
        } 
        
    def _layout_out(self):
        self.layout_out = widgets.VBox([
            widgets.HBox([self.out_console]),
            widgets.HBox([self.out_help_ui], 
                         layout=widgets.Layout(width='100%',align_items='stretch',justify_content='space-between',align_content='stretch')),
            widgets.HBox([self.out_help_run, self.out_help_config], 
                         layout=widgets.Layout(width='100%',align_items='stretch',justify_content='space-between',align_content='stretch')),
            widgets.HBox([self.out_inputs, self.out_outputs, self.out_log], 
                         layout=widgets.Layout(width='100%',align_items='stretch',justify_content='space-between',align_content='stretch'))
        ], layout=widgets.Layout(width='100%',align_items='stretch',align_content='stretch', display='flex', flex='flex-grow'))
        
    def _run_form(self):
        self.button_bar = build_button_bar(self._button_map, self.ui_config)
        self.layout = widgets.VBox([
            self.button_bar,
            self.layout_out
        ])
        self.acc = widgets.Accordion(children=[self.layout], selected_index=None, layout=widgets.Layout(width='100%'))
        self.acc.set_title(0, self.run_id.pretty_name)
        self.run_form = widgets.HBox([self.in_batch, self.acc],layout=widgets.Layout(margin='0px',padding='0px',border='0px'))#'3px solid red'
        
    def display(self):
        display(self.run_form)

    def _ipython_display_(self):
        self.display()
    
if __name__ == "__main__":
    run = RunApp()
    display(run)
# -


# +
import pathlib
from pydantic import validator
from ipyrun._ipydisplayfile import DisplayFiles
from ipyrun._ipyeditcsv import EditCsv
from ipyrun._runconfig import Output
from ipyrun._ipydisplayfile import DisplayFile, PreviewOutputs
from jinja2 import Template

class ShellHandler(BaseModel):
    call: str = "python -O"
    fpth_script: pathlib.Path
    fdir_appdata: pathlib.Path
    fpths_inputs: List[pathlib.Path]
    fpths_outputs: List[pathlib.Path]
    params: typing.Dict = {}
    fpth_config: pathlib.Path = 'config-shell_handler.json'
    cmd_template: str = """\
python -O {{ fpth_script }}\
{% for f in fpths_inputs %} {{f}}{% endfor %}\
{% for f in fpths_outputs %} {{f}}{% endfor %}\
{% for k,v in params.items()%} --{{k}} {{v}}{% endfor %}
"""
    cmd: str = ""
    fpth_runhistory: str = 'runhistory.csv'
    #fpth_log: pathlib.Path
    
    @validator("fpth_config", always=True)
    def _fpth_config(cls, v, values):
        return values['fdir_appdata'] / v
    
    @validator("fpth_runhistory", always=True)
    def _fpth_runhistory(cls, v, values):
        return values['fdir_appdata'] / v
    
    @validator("cmd", always=True)
    def _cmd(cls, v, values):
        return Template(values['cmd_template']).render(fpth_script=values['fpth_script'], 
            fpths_inputs=values['fpths_inputs'], 
            fpths_outputs=values['fpths_outputs'], 
            params=values['params'])
    
class RunId(BaseModel):
    project_number: str = 'J5001'
    process_name: str = 'process_name'
    pretty_name: str = 'pretty_name'
    run_index: int = 0
    in_batch: bool=True
              
def execute(cmd):
    print(cmd)
    cmd = run_script.cmd.split(' ')
    spinner = HaloNotebook(animation='marquee', text='Running', spinner='dots')
    try:
        spinner.start()
        subprocess.check_output(cmd)
        spinner.succeed('Finished')
    except subprocess.CalledProcessError as e:
        spinner.fail('Error with Process')
        
    # reload outputs
    run_app.outputs.value = False
    run_app.outputs.value = True

# +
import sys
sys.path.append('../test_scripts/line_graph')
from ipyautoui.autoui import AutoUi, AutoUiConfig
from ipyautoui.displayfile import DisplayFiles
from schemas import LineGraph
import functools

config_autoui = AutoUiConfig(pydantic_model=LineGraph)
line_graph_ui = AutoUi.create_displayfile(config_autoui)

def line_graph_prev(path):
    display(line_graph_ui(path))
    
user_file_renderers = {'.lg.json': line_graph_prev}
DisplayFiles = functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)
FPTH_SCRIPT_EXAMPLE_1
# -



pathlib.Path(FPTH_SCRIPT_EXAMPLE_1).parent / 


# +
class ShellHandlerConfig(BaseModel):
    run_id: RunId = RunId()
    command_handler: ShellHandler
    #run_actions: RunActions
    ui_config: RunUiConfig =RunUiConfig(include_show_hide=True)

run_id = RunId(
    process_name = 'line_graph',
    in_batch=False
)
run_script = ShellHandler(
    fpth_script=pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV),
    fdir_appdata=pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent,
    fpths_inputs=[pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'inputs-{run_id.process_name}.lg.json'],
    fpths_outputs=[
        pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'outputs-{run_id.process_name}.csv',
        pathlib.Path(FPTH_SCRIPT_EXAMPLE_CSV).parent/f'outputs-{run_id.process_name}.plotly.json'
    ],
    #params={'k':'v'}
)
run_actions = RunActions(
    #help_config_show=None,
    #help_ui_show=None,
    help_run_show=(lambda: display(DisplayFile(str(run_script.fpth_script)))),
    inputs_show=(lambda: [display(EditCsv(f)) for f in run_script.fpths_inputs]),
    outputs_show=(lambda: display(DisplayFiles([f for f in run_script.fpths_outputs], auto_open=True))),
    run=(lambda: execute(run_script.cmd))
)

app_config = ShellHandlerConfig(run_id= RunId(),
    command_handler=run_script,
    run_actions=run_actions)
        
def create_RunApp(app_config: ShellHandlerConfig) -> RunApp:
    run_actions = RunActions(
        #help_config_show=None,
        #help_ui_show=None,
        help_run_show=(lambda: display(DisplayFile(str(app_config.command_handler.fpth_script)))),
        inputs_show=(lambda: [display(EditCsv(f)) for f in app_config.command_handler.fpths_inputs]),
        outputs_show=(lambda: display(DisplayFiles([f for f in app_config.command_handler.fpths_outputs], auto_open=True))),
        run=(lambda: execute(app_config.command_handler.cmd))
    )
    return RunApp(run_actions=run_actions)

#  TODO: @output_widget.capture() could be used to interact with the outputs on RunApp...? 
#def create_AppConfig
# -



inputs-line_graph

LineGraph().file()

# +
from ipyautoui.test_schema import TestAutoLogic

display_template_ui_model()
# -



# +
from pydantic import BaseModel , Field, conint
import typing

class LineGraph(BaseModel):
    """parameters to define a simple `y=m*x + c` line graph"""
    title: str = Field(default='line equation', description='add chart title here')
    m: float = Field(default=2, description='gradient')
    c: float = Field(default=5, description='intercept')
    x_range: tuple[int, int] = Field(default=(0,5), ge=0, le=50, description='x-range for chart')
    y_range: tuple[int, int] = Field(default=(0,5), ge=0, le=50, description='y-range for chart')

LineGraph()
# -





# +
from ipyautoui.autoui import AutoUiConfig 

config_autoui = AutoUiConfig(pydantic_model=LineGraph)


# -

ui = AutoUi(LineGraph())

ui#.title.value

run_app = RunApp(run_actions=run_actions, ui_config=RunUiConfig(include_show_hide=True))
run_app

create_RunApp(app_config)

from myst_parser.main import to_html
s = """
__some__ *text*
> This is a block quote. This
> paragraph has two lines.
>
> 1. This is a list inside a block quote.
> 2. Second item.

[Jupyter Book](https://jupyterbook.org "JB Homepage")
"""
widgets.HTML(to_html(s))


# +
import subprocess

cmd = f'echo """{s}""" | pandoc --from markdown --to html'
out = subprocess.run(cmd, shell=True, check=True, capture_output=True)
widgets.HTML(out.stdout)
# -

out.stdout

# +
from myst_parser.main import to_docutils
print(to_docutils("some *text*").pformat())

from myst_parser.main import default_parser, MdParserConfig
config = MdParserConfig(renderer="html")
parser = default_parser(config)
widgets.HTML(parser.render("""
__some__ *text* 
```python
def python(asdf):
    print('asdf')
```
"""))
# -



# +
#  as the RunActions are so generic, the same actions can be applied to Batch operations 
#  with the addition of some batch specific operations

class BatchActions(RunActions):
    add_show: typing.Callable = (lambda : display('add_show'))
    add_hide: typing.Callable = (lambda : display('add_hide'))
    remove_show: typing.Callable = (lambda : display('remove_show'))
    remove_hide: typing.Callable = (lambda : display('remove_hide'))
    wizard_show: typing.Callable = (lambda : display('wizard_show'))
    wizard_hide: typing.Callable = (lambda : display('wizard_hide'))


# -

class BatchActionsUi(RunActionsUi):
    
    def __init__(self, batch_actions:BatchActions=BatchActions(), run_id:RunId=RunId()):
        self.run_actions = batch_actions
        self.run_id = run_id
        
        self._init_objects()
        self._init_controls()
        self._update_objects()
        self._update_controls()

    def _update_objects(self):
        self.add = widgets.ToggleButton(icon='plus',
                                tooltip='add a run',
                                style={'font_weight':'bold'},
                                button_style='primary',
                                layout=widgets.Layout(width=self.minwidth))
        self.remove = widgets.ToggleButton(icon='minus',
                                tooltip='add a run',
                                style={'font_weight':'bold'},
                                button_style='danger',
                                layout=widgets.Layout(width=self.minwidth))
        self.wizard = widgets.ToggleButton(icon='magic',
                                tooltip='add a run',
                                style={'font_weight':'bold'},
                                button_style='warning',
                                layout=widgets.Layout(width=self.minwidth))
        
        self.out_add = widgets.Output()
        self.out_remove = widgets.Output()
        self.out_wizard = widgets.Output()

    def _update_controls(self):
        self.add.observe(self._add, names='value')
        self.remove.observe(self._remove, names='value')
        self.wizard.observe(self._wizard, names='value')
    
    def _add(self, on_change):
        self._show_hide_output(self.out_add, 
                               self.add, 
                               self.run_actions.add_show, 
                               self.run_actions.add_hide)
        
    def _remove(self, on_change):
        self._show_hide_output(self.out_remove, 
                               self.remove, 
                               self.run_actions.remove_show, 
                               self.run_actions.remove_hide)
        
    def _wizard(self, on_change):
        self._show_hide_output(self.out_wizard, 
                               self.wizard, 
                               self.run_actions.wizard_show, 
                               self.run_actions.wizard_hide)
        
    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form 
        where the display method is overwritten"""
        out = widgets.VBox([
            widgets.HBox([self.help_ui, self.out_help_ui]),
            widgets.HBox([self.help_run, self.out_help_run]),
            widgets.HBox([self.help_config, self.out_help_config]),
            widgets.HBox([self.inputs, self.out_inputs]),
            widgets.HBox([self.outputs, self.out_outputs]),
            widgets.HBox([self.log, self.out_log]),
            widgets.HBox([self.in_batch]),
            widgets.HBox([self.run, self.out_console]),
            widgets.HBox([self.show]),
            widgets.HBox([self.hide])
        ])
        display(widgets.HTML("""
Buttons to be programmed from `RunActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """))
        display(out)
        
        out_batch_only = widgets.VBox([
            widgets.HBox([self.add, self.out_add]),
            widgets.HBox([self.remove, self.out_remove]),
            widgets.HBox([self.wizard, self.out_wizard ])])
        display(widgets.HTML("""
Buttons to be programmed from `BatchActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """))
        display(out_batch_only)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    batch = BatchActionsUi()
    display(batch)


class RunApps(BatchActionsUi):
    def __init__(self, batch_actions:BatchActions=BatchActions(), run_id:RunId=RunId(), ui_config:RunUiConfig=RunUiConfig()):
        super().__init__(batch_actions=batch_actions, run_id=run_id)
        self.ui_config = ui_config
        self._run_form()
        
    @property
    def _button_map(self):
        return {
            'outside': {self.in_batch: self.run_actions.check},
            'left': {
                    self.help_ui: self.run_actions.help_ui_show,
                    self.help_run: self.run_actions.help_run_show,
                    self.help_config: self.run_actions.help_config_show,
                    self.inputs: self.run_actions.inputs_show,
                    self.outputs: self.run_actions.outputs_show,
                    self.log: self.run_actions.log_show,
                    self.run: self.run_actions.run,
                    self.add: self.run_actions.add_show,
                    self.remove: self.run_actions.remove_show,
                    self.wizard: self.run_actions.wizard_show,
            },
            'right': [self.show, self.hide]
        } 
    
    def _run_form(self):
        self.button_bar = build_button_bar(self._button_map, self.ui_config)


    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form 
        where the display method is overwritten"""
        display(self.button_bar)

    def _ipython_display_(self):
        self.display()
if __name__ == '__main__':
    RunApps()

# +
# Default commands:
# -----------------
# RunShell
#   RunScript
#   RunSnake
# -





# +

t = Template("Hello {{ something }}!")
t.render(something="World")
# -

t = Template("My favorite numbers: {% for n in range(1,10) %} {{n}} {% endfor %}")
t.render()

# +

# ?EditCsv
# -

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
    add_show: typing.Callable = (lambda : display('add_show'))
    add_hide: typing.Callable = (lambda : display('add_hide'))
    remove_show: typing.Callable = (lambda : display('remove_show'))
    remove_hide: typing.Callable = (lambda : display('remove_hide'))
    wizard_show: typing.Callable = (lambda : display('wizard_show'))
    wizard_hide: typing.Callable = (lambda : display('wizard_hide'))
        
class BatchActionsUi():
    minwidth=BUTTON_WIDTH_MIN
    medwidth=BUTTON_WIDTH_MEDIUM
    
    def __init__(self, batch_actions: BatchActions=BatchActions()):
        self.batch_actions = batch_actions
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
        self.help_config = widgets.ToggleButton(icon='book',
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

    def _help_ui(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_help_ui:
            if self.help_ui.value:
                self.batch_actions.help_ui_show()
            else:
                self.batch_actions.help_ui_hide()
                clear_output()
        
    def _help_run(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_help_run:
            if self.help_run.value:
                self.batch_actions.help_run_show()
            else:
                self.batch_actions.help_run_hide()
                clear_output()
                
    def _help_config(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_help_run:
            if self.help_run.value:
                self.batch_actions.help_config_show()
            else:
                self.batch_actions.help_config_hide()
                clear_output()
        
    def _inputs(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_inputs:
            if self.inputs.value:
                self.batch_actions.inputs_show()
            else:
                self.batch_actions.inputs_hide()
                clear_output()
                
    def _outputs(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_outputs:
            if self.outputs.value:
                self.batch_actions.outputs_show()
            else:
                self.batch_actions.outputs_hide()
                clear_output()
                
    def _log(self, on_change):
        #self.show_hide.value = self.set_show_hide_value()
        with self.out_log:
            if self.log.value:
                self.batch_actions.log_show()
            else:
                self.batch_actions.log_hide()
                clear_output()
                
    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_actions.run()
            
    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form 
        where the display method is overwritten"""
        out= widgets.VBox([
            widgets.HBox([self.help_ui, self.out_help_ui]),
            widgets.HBox([self.help_run, self.out_help_run]),
            widgets.HBox([self.help_config, self.out_help_config ]),
            widgets.HBox([self.inputs, self.out_inputs]),
            widgets.HBox([self.outputs, self.out_outputs]),
            widgets.HBox([self.log, self.out_log]),
            widgets.HBox([self.in_batch]),
            widgets.HBox([self.run, self.out_console]),
            widgets.HBox([self.show]),
            widgets.HBox([self.hide])
        ])
        display(out)


    def _ipython_display_(self):
        self.display()
        
BatchActionsUi()
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


