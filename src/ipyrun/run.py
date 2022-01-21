# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %%
"""
A configuration of the ipyrun App for running shell python scripts. 
"""
# %run __init__.py
# %load_ext lab_black

import io
import shutil
import pandas as pd
from IPython.display import (
    # update_display,
    display,
    Image,
    # JSON,
    Markdown,
    # HTML,
    clear_output,
)
import subprocess
import functools
from shutil import copyfile
import getpass
import importlib.util
from halo import HaloNotebook
import pathlib
import typing
from typing import Optional, List, Dict, Type, Optional, Union
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, validator, Field
from ipyrun.basemodel import BaseModel
from jinja2 import Template
from enum import Enum, IntEnum

import plotly.io as pio
import plotly.graph_objects as go

# widget stuff
import ipywidgets as widgets

# core mf_modules
from ipyautoui import AutoUi, DisplayFiles, AutoUiConfig
from ipyautoui.autoui import display_template_ui_model
from ipyautoui._utils import display_pydantic_json
from pprint import pprint
import importlib.util
import inspect

# display_template_ui_model()

# from this repo
from ipyrun.utils import make_dir, del_matching, get_status
from ipyrun.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    JOBNO_DEFAULT,
    PATH_RUNAPP_HELP,
    PATH_RUNAPPS_HELP,
    DI_STATUS_MAP,
    load_test_constants
)
test_constants = load_test_constants()

from ipyrun.ui_run import *
from ipyrun.ui_run import RunActionsUi, RunUi, RunUiConfig
from ipyrun.ui_add import AddRun
from ipyrun.schema_actions import RunActions, BatchActions
from ipyrun.schema_config_runshell import ConfigActionsShell, DefaultConfigActionsShell, DisplayfileDefinition, FiletypeEnum, create_displayfile_renderer

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]


# %%
def check(config: ConfigActionsShell):
    config.in_batch = True

def uncheck(config: ConfigActionsShell):
    config.in_batch = False

def show_files(fpths, class_displayfiles=DisplayFiles, kwargs_displayfiles={}):
    return class_displayfiles([f for f in fpths], **kwargs_displayfiles)

def update_DisplayFiles(config, app):
    # user_file_renderers = {}
    # for d in config.displayfile_definitions: 
    #     user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=app._update_status))  

    user_file_renderers = {}
    for d in config.displayfile_definitions: 
        user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=app._update_status)) 
    return functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)

def run_shell( app=None): #
    """
    cmd: str, cls=None
    """
    if app.config.update_config_at_runtime:
        app.config = app.config #  this updates config and remakes run actions. useful if, for example, output fpths dependent on contents of input files
    shell = app.config.shell.split(" ")
    pr = """  
    """.join(shell)
    display(Markdown(f"{pr}"))
    spinner = HaloNotebook(animation="marquee", text="Running", spinner="dots")
    try:
        spinner.start()
        save = sys.stdout
        sys.stdout = io.StringIO()
        proc = subprocess.Popen(shell)
        proc.wait()
        in_stdout = sys.stdout.getvalue()
        sys.stdout = save
        display(in_stdout)
        spinner.succeed("Finished")
    except subprocess.CalledProcessError as e:
        spinner.fail("Error with Process")
    app._update_status()
    
class RunShellActions(RunActions):
    """extends RunActions by creating Callables based on data within the app or the config objects"""
    
    @validator("check", always=True)
    def _check(cls, v, values):
        return functools.partial(check, values["config"])
    
    @validator("uncheck", always=True)
    def _uncheck(cls, v, values):
        return functools.partial(uncheck, values["config"])
    
    @validator("get_status", always=True)
    def _get_status(cls, v, values):
        return values["app"]._update_status
    
    @validator("help_run_show", always=True)
    def _help_run_show(cls, v, values):
        return functools.partial(DisplayFiles, 
                               [values["config"].fpth_script],
                               auto_open=True)
    
    @validator("help_config_show", always=True)
    def _help_config_show(cls, v, values):
        return functools.partial(display_pydantic_json, values["config"], as_yaml=True)
    
    @validator("inputs_show", always=True)
    def _inputs_show(cls, v, values):
        return functools.partial(update_DisplayFiles(values["config"], values["app"]), 
                               values["config"].fpths_inputs,
                               **values["config"].displayfile_inputs_kwargs)
    
    @validator("outputs_show", always=True)
    def _outputs_show(cls, v, values):
        return functools.partial(update_DisplayFiles(values["config"], values["app"]), 
                               values["config"].fpths_outputs,
                               **values["config"].displayfile_outputs_kwargs)
    
    @validator("run", always=True)
    def _run(cls, v, values):
        return functools.partial(run_shell, app=values["app"])



# %%
class RunApp(widgets.HBox):
    def __init__(self,
                 config: typing.Any,
                 cls_ui: typing.Type[widgets.Box] = RunUi,
                 cls_actions: typing.Type[BaseModel] = RunShellActions
                ):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 

        Args:
            config: typing.Any
            cls_ui
            fn_buildactions
        """
        super().__init__(layout=widgets.Layout(flex="100%"))
        self.children = [cls_ui(run_actions=RunActions(), name=config.pretty_name)]
        self.ui = self.children[0].ui
        #self.ui_box = cls_ui(run_actions=RunActions(), name=config.pretty_name) # init with defaults
        self.cls_actions = cls_actions
        self.config = config  # the setter updates the ui.actions using fn_buildactions. can be updated on the fly
        self._update_status()

    @property
    def config(self):
        return self.ui.actions.config

    @config.setter
    def config(self, value):
        self.ui.actions = self.cls_actions(config=value, app=self)
        self.config.file(self.config.fpth_config)

    @property
    def actions(self):
        return self.ui.actions

    def _update_status(self):
        st = get_status(self.config.fpths_inputs, self.config.fpths_outputs)
        self.ui.status = st
        self.config.status = st

#     def display(self):
#         display(self.ui_box)

#     def _ipython_display_(self):
#         self.display()

class MyConfigActionsShell(DefaultConfigActionsShell):
    @validator("fpths_outputs", always=True)
    def _fpths_outputs(cls, v, values):
        fdir = values['fdir_appdata']
        nm = values['process_name']
        paths = [fdir / ('output-'+nm+'.csv'), fdir / ('out-' + nm + '.plotly.json')]
        return paths

if __name__ == "__main__":
    PATH_EXAMPLE_SCRIPT = list(test_constants.DIR_EXAMPLE_PROCESS.glob('script*'))[0]
    MyConfigActionsShell = functools.partial(MyConfigActionsShell, fpth_script=PATH_EXAMPLE_SCRIPT, 
                                displayfile_definitions=[
                                    DisplayfileDefinition(
                                        path=PATH_EXAMPLE_SCRIPT.parent / 'schemas.py',
                                        obj_name='LineGraph',
                                        ext='.lg.json',
                                        ftype=FiletypeEnum.input
                                    )])

    config = MyConfigActionsShell()
    run_app = RunApp(config)
    display(run_app)

# %%
from ipyrun.constants import FNM_CONFIG_FILE
from ipyrun.basemodel import BaseModel
class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    fpth_config: pathlib.Path = Field(default=FNM_CONFIG_FILE, description='name of config file for batch app')
    title: str = Field(default='', description='markdown description of BatchApp')
    cls_ui: Callable = Field(default=RunUi, description="the class that defines the RunUi widget container", exclude=True)
    cls_actions: Callable = Field(default=RunShellActions, description="the class that defines the RunActions (extended with validators based on use case)", exclude=True)
    cls_app: Union[Type, Callable] = Field(default=RunApp, description="the class that defines the RunApp.", exclude=True) # functools.partial used to define the cls_ui and cls_actions beofre passing here
    cls_config: Union[Type, Callable] = Field(default=DefaultConfigActionsShell, description="the class that defines the config of a RunApp. this has can have fpth_script baked in", exclude=True)
    configs: List[Type[BaseModel]] = []
    runs: List[Callable] = Field(default=lambda: [], description="a list of RunApps", exclude=True)

    @validator("fpth_config", always=True, pre=True)
    def _fpth_config(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return values['fdir_root'] / v

    @validator("cls_app", always=True, pre=True)
    def _cls_app(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return functools.partial(v, cls_ui=values['cls_ui'], cls_actions=values['cls_actions'])



# %%
from ipyrun.ui_remove import RemoveRun

def fn_add(app, cls_runapp, cls_config, **kwargs):
    if "index" not in kwargs:
        kwargs['index'] = app.runs.length
    kwargs['fdir_appdata'] = app.config.fdir_root
    config = cls_config(**kwargs)
    app.configs_append(config)
    newapp = cls_runapp(config)
    app.runs.add_row(new_key=config.key, item=newapp)

def fn_add_show(app):
    return AddRun(fn_add=app.ui.actions.add)

def fn_remove(app=None, key=None):
    if key is None:
        print('key is None')
        key = app.runs.iterable[-1].key
    fdir = [i.fdir_appdata for i in app.config.configs if i.key==key][0]
    app.configs_remove(key)
    shutil.rmtree(fdir)

def fn_remove_show(app=None):
    app.runs.add_remove_controls = 'remove_only'
    return RemoveRun(app=app)

def fn_remove_hide(app=None):
    app.runs.add_remove_controls = None


class BatchShellActions(BatchActions):
    @validator("add", always=True)
    def _add(cls, v, values):
        return functools.partial(fn_add, values["app"], values["config"].cls_app, values["config"].cls_config)
    
    @validator("add_show", always=True)
    def _add_show(cls, v, values):
        return functools.partial(fn_add_show, values["app"])

    @validator("remove", always=True)
    def _remove(cls, v, values):
        values["app"].runs.fn_remove = functools.partial(fn_remove, app=values["app"])
        return values["app"].runs.remove_row
    
    @validator("remove_show", always=True)
    def _remove_show(cls, v, values):
        return functools.partial(fn_remove_show, values["app"])
    
    @validator("remove_hide", always=True)
    def _remove_hide(cls, v, values):
        return functools.partial(fn_remove_hide, values["app"])
    
    @validator("help_config_show", always=True)
    def _help_config_show(cls, v, values):
        return functools.partial(display_pydantic_json, values["config"], as_yaml=True)


# %%
class BatchApp(widgets.HBox):
    def __init__(self,
                 config: typing.Any,
                 cls_ui: typing.Type[widgets.Box] = BatchUi,
                 cls_actions: typing.Type[BaseModel] = BatchShellActions):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 

        Args:
            config: typing.Type[BaseModel]
        """
        super().__init__(layout=widgets.Layout(flex="100%")) #, flex="flex-grow"display="flex", 
        self.children = [cls_ui(batch_actions=BatchActions(), title=config.title)]
        self.ui = self.children[0].ui
        self.cls_actions = cls_actions
        self.config = config  # the setter updates the ui.actions using fn_buildactions. can be updated on the fly

    @property
    def runs(self):
        return self.children[0].runs

    @property
    def config(self):
        return self.ui.actions.config

    @config.setter
    def config(self, value):
        self.ui.actions = self.cls_actions(config=value, app=self)
        self.config.file(self.config.fpth_config)

    def configs_append(self, config):
        self.ui.actions.config.configs.append(config)
        self.config.file(self.config.fpth_config)

    def configs_remove(self, key):
        self.config.configs = [c for c in self.config.configs if c.key != key]
        self.config.file(self.config.fpth_config)

    @property
    def actions(self):
        return self.ui.actions

    def _update_status(self):
        st = get_status(self.config.fpths_inputs, self.config.fpths_outputs)
        self.ui.status = st
        self.config.status = st
# ----------------------------------------



# %%
config_batch = ConfigBatch(fdir_root=test_constants.DIR_EXAMPLE_BATCH, 
                           cls_config=MyConfigActionsShell,
                           title="""# Plot Straight Lines\n### example RunApp"""
                          )
app = BatchApp(config_batch)
app

# %%
from ipyautoui.constants import BUTTON_MIN_SIZE
BUTTON_MIN_SIZE

# %%
if __name__ == "__main__":
    display(Markdown('change add remove to ToggleButtons?'))
    display(widgets.HBox([
        widgets.ToggleButtons(options = [('', 0), (' ', 1), ('  ', 2)], value=1,
                  icons=['plus','','minus'],
                  tooltips=['add a process','hide add / remove dialogue','remove a process'],
                  style=widgets.ToggleButtonsStyle(button_width='20px'),
                  layout=widgets.Layout(border='solid yellow')),
        widgets.Button()]))

# %%

# %%

# %%

# %%

# %%

# %%

# %%

# %%

# %%
from typing import Union

class Run(BaseModel):
    fdir_root: pathlib.Path
    process_name: str
    pretty_name: str = None
    fdir_appdata: pathlib.Path = None
    fpth_config: pathlib.Path = None
    
    @validator("fdir_appdata", always=True, pre=True)
    def _fdir_appdata(cls, v, values):
        return values['fdir_root'] / values['process_name']
    
    @validator("fpth_config", always=True, pre=True)
    def _fpth_config(cls, v, values):
        return values['fdir_root'] / FNM_CONFIG_FILE
    
class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    #fpth_script: pathlib.Path
    batch_desccription: str = ''
    run_config_model_definition: PyObj = None
    run_config_model: Union[Type[BaseModel], Callable] = Field(None, exclude=True)
    run_app_model_definition: PyObj = None
    run_app_model: Callable = Field(RunApp, exclude=True)
    runs: List[Run] = []
    
    @validator("run_config_model", always=True)
    def _run_config_model(cls, v, values):
        obj_def = values['run_config_model_definition']
        if obj_def is not None and v is None:
            v = _get_PyObj(obj_def)
        return v
    
    @validator("run_app_model", always=True)
    def _run_app_model(cls, v, values):
        obj_def = values['run_app_model_definition']
        if obj_def is not None and v is None:
            v = _get_PyObj(obj_def)
        return v
    
def add(name='name', cls=None):
    fdir_root = cls.config.fdir_root
    Config_ = cls.config.run_config_model
    RunApp_ = cls.config.run_app_model
    run = Run(fdir_root=fdir_root, process_name=name)
    print(run)
    batchconfig = cls.config.copy()
    batchconfig.runs.append(run)
    cls.config = batchconfig
    runconfig = Config_(process_name=run.process_name, pretty_name=run.pretty_name, fdir_appdata=run.fdir_appdata)
    app = RunApp_(runconfig)
    cls.ui_box.runs.add_row(new_key=name, item=app.ui_box)
    
def add_show(cls=None):
    fn_add_show = functools.partial(AddRun, app=cls, fn_add=cls.ui.actions.add, run_name_kwargs={'index': len(cls.config.runs)+1})
    return fn_add_show()


# %%
type(MyConfigActionsShell)

# %%
config = ConfigBatch(fdir_root=TEST_CONSTANTS.DIR_EXAMPLE_BATCH, run_config_model=MyConfigActionsShell, fpth_script=TEST_CONSTANTS.PATH_EXAMPLE_SCRIPT)
config.run_config_model

# %%
add(cls=batch)

# %%
AddRun()


# %%
def fn_buildbatchactions(config: ConfigBatch, cls=None) -> BatchActions: 
    return BatchActions(add=add, add_show=add_show)
    #pass


# %%
class BatchApp():
    def __init__(self,
                 config: typing.Type[BaseModel],
                 cls_ui: typing.Type[widgets.Box] = BatchUi,
                 fn_buildactions: typing.Callable[[typing.Type[BaseModel]], BatchActions]=fn_buildbatchactions
                ):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 
        
        Args:
            config: typing.Type[BaseModel]
        """
        self.fn_buildactions = fn_buildactions
        self.ui = BatchActionsUi() # init with defaults
        self.ui_box = cls_ui(ui_actions=self.ui)
        self.config = config # the setter updates the ui.actions using fn_buildactions. can be updated on the fly
        #self._update_status()
        
    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, value):
        actions = self.fn_buildactions(value, cls=self)
        self.ui.actions = self._init_actions(actions)
        self._config = value
        
    def _update_status(self):
        st = get_status(self.config.fpths_inputs, self.config.fpths_outputs)
        self.ui.status = st
        self.config.status = st
    
    def _init_run_action(self, action):
        if action is not None:
            try:
                if "cls" in inspect.getfullargspec(action).args:
                    return functools.partial(action, cls=self)
                else:
                    return action
            except:
                print("error inspecting the following:")
                print(action)
                print(type(action))
                print("cls" in inspect.getfullargspec(action).args)
                action()
        else:
            return action

    def _init_actions(
        self, actions: typing.Type[BatchActions]
    ) -> typing.Type[BatchActions]:
        """this allows us to pass the RunApp object to the Run Actions. TODO: describe better! """
        return type(actions)(
            **{k: self._init_run_action(v) for k, v in actions.dict().items()}
        )
    
    def display(self):
        display(self.ui_box)

    def _ipython_display_(self):
        self.display()
        
TEST_CONSTANTS = load_test_constants()

config = ConfigBatch(fdir_root=TEST_CONSTANTS.DIR_EXAMPLE_BATCH, run_config_model=MyConfigActionsShell, fpth_script=TEST_CONSTANTS.PATH_EXAMPLE_SCRIPT)
batch = BatchApp(config)
batch

# %%
batch.config

# %%
batch.ui_box.runs.items

# %%
batch.ui.actions.add('01-lean-description')

# %%
# ?TEST_CONSTANTS

# %%
# ?Run

# %%
FiletypeEnum.input.value

# %%
from ipyrun.ui_add import AddRun
from ipyrun.ui_remove import RemoveRun
# ?AddRun

# %%

# %%
from ipyrun.ui_run import RunActionsUi, RunUi, RunUiConfig, BatchActions, BatchActionsUi, BatchUi

def _fn_addshow(cls=None, name='name'):
    print(f'_fn_add: name={name}')
    print(f'str(cls)={str(cls)}')
    ui_actions = RunActionsUi()
    keys = cls.apps_box.iterable_keys
    if len(keys) == 0:
        key = 0
    else:
        nums = [int(s.split('-')[0]) for s in keys]
        index = max(nums)
        
    def add_run(cls, name='name'):
        cls.apps_box.add_row(new_key=name)
    #display()    
    return AddRun(app=cls, fn_add=add_run)
    

b_actions = BatchActions(
                         #help_ui_show=None, 
                         #help_ui_hide=None,
                         help_config_show=None,
                         help_config_hide=None,
                         help_run_show=None,
                         help_run_hide=None,
                         inputs_show=None,
                         inputs_hide=None,
                         wizard_show=None,
                         runlog_show=None,
                         run_hide=None, 
                         add_show=_fn_addshow
            )

ui_actions = BatchActionsUi(b_actions)
ui_batch = BatchUi(ui_actions=ui_actions)
ui_batch


# %%
def fn_buildbatchactions(config: ConfigActionsShell, cls=None) -> RunActions:  # fn_onsave
    # create custom Displayfile 
    user_file_renderers = {}
    for d in config.displayfile_definitions: 
        user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=fn_onsave))    
    cls_display = functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)
    
    run_actions = BatchActions(check=functools.partial(check, config),
                             uncheck=functools.partial(uncheck, config),
                             get_status=cls._update_status,
                             help_run_show=functools.partial(show_files, 
                                                           [config.fpth_script],
                                                           class_displayfiles=cls_display,
                                                           kwargs_displayfiles={'auto_open':True}),
                             help_config_show=help_config_show,
                             inputs_show=functools.partial(show_files, 
                                                           config.fpths_inputs,
                                                           class_displayfiles=cls_display,
                                                           kwargs_displayfiles=config.displayfile_inputs_kwargs),
                             outputs_show=functools.partial(show_files, 
                                                           config.fpths_outputs,
                                                           class_displayfiles=cls_display,
                                                           kwargs_displayfiles=config.displayfile_outputs_kwargs),
                             run=functools.partial(run_shell,config.shell)
                            )
    return run_actions


# %%

# %%

# %%
AddRun()

# %%
max([])

# %%

# %%
from ipyautoui.custom import Dictionary, Array
#run_app.ui.run_form

# %%
items = {'test': run_app.ui_box}
d = Dictionary(items, watch_value=False, toggle=False, add_remove_controls='append_only', show_hash=None)
d#.iterable[0].item

# %%
run_app1 = RunApp(config)
d.add_row(new_key='test1', item=run_app1.ui_box)

# %%
items =[run_app.ui.run_form]
d = Array(items, watch_value=False)
d

# %%
if __name__ == "__main__":
    display(
        widgets.HBox([
            widgets.HBox(
                [
                    widgets.Accordion(
                        [widgets.Button()], layout=widgets.Layout(width='100%'))]
            ,layout=widgets.Layout(width='100%'))
        ])
    )     

# %%
DisplayFiles(config.fpths_outputs)

# %%
from ipyrun.utils import write_yaml
import yaml
import json
#write_yaml(config.json())

with open('data.yaml', 'w') as outfile:
    yaml.dump(json.loads(config.json()), outfile, default_flow_style=False)

# %%
widgets.Button(tooltip='afds', disabled=True)

# %%
from pprint import pprint
s = "python -O /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/script_line_graph.py /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/input-line_graph.lg.json /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.csv /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.plotly.json"
pprint(s)


# %%

class RunId(BaseModel):
    """run identifier

    Args:
        BaseModel (pydantic.BaseModel): inherits pydantic

    Returns:
        RunId: RunId object
    """

    index: int = 0
    process_name: str = "process_name"
    pretty_name: str = None
    check: bool = True

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return str(values["index"]) + " - " + values["process_name"]
        else:
            return v


class BatchId(RunId):
    description: str = Field(
        "",
        description="a description of the batch of RunApps. Displayed as a header to the UI",
    )

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return values["process_name"]
        else:
            return v
    
    
class BaseConfig(BaseModel):
    run_id: RunId = RunId()
    config_ui: RunUiConfig = RunUiConfig()
    config_actions: typing.Any = None  # this one might get overwritten


# %%
class BatchAppConfig(BaseModel):
    # actions: BatchActions = BatchActions() # TODO: add this back in once pydantic has updated such that it can be excluded from the json output. and remade by a validator.
    batch_id: BatchId = BatchId()
    config_ui: RunUiConfig = RunUiConfig()
    config_actions: typing.Any = None  # this one might get overwritten


# %%
class RunAppConfig(BaseConfig):
    """generic RunApp configurator definition. this will be serialised to JSON and remade
    for storing the Apps state. it will also be used to generate a RunApp when using the
    "add" button.

    Args:
        BaseModel ([type]): [description]
        
    
    """
    
    actions: RunActions = RunActions() # TODO: add this back in once pydantic has updated such that it can be excluded from the json output. and remade by a validator.


# %%

# %%

# %%

# %%

# %%

# %%

# %%

# %%

# %%
if __name__ == "__main__":
    # ?AddRunDialogue

    def add_run_dialogue(cls=None):
        display(AddRunDialogue(cls))

    batch_actions = BatchActions(
        inputs_show=None,
        inputs_hide=None,
        outputs_show=None,
        outputs_hide=None,
        add_show=add_run_dialogue,
    )

    display(RunApps(batch_actions=batch_actions))


# %%
def default_runapp_config(
    path_script: pathlib.Path,
    index: int,
    input_models: typing.List[typing.Type[BaseModel]],
    process_name: str = None,
    fdir_appdata: pathlib.Path = None,
    class_displayfiles: typing.Type[DisplayFiles] = DisplayFiles,
) -> typing.Tuple[RunAppConfigShell, RunActions]:

    if fdir_appdata is None:
        fdir_appdata = path_script.parent

    if process_name is None:
        process_name = path_script.stem.replace("script_", "")

    run_id = RunId(process_name=process_name, check=True, index=index)
    paths_inputs = [
        create_inputs_file(model, index, fdir_appdata, process_name=process_name)
        for model in input_models
    ]

    config_actions = ShellHandler(
        fpth_script=path_script,
        fpths_inputs=paths_inputs,
        fpths_outputs=[
            fdir_appdata / f"outputs-{run_id.process_name}-{run_id.index}.csv",
            fdir_appdata / f"outputs-{run_id.process_name}-{run_id.index}.plotly.json",
        ],
        # params={'k':'v'}
    )
    config_runapp = RunAppConfigShell(run_id=run_id, config_actions=config_actions)
    run_actions = RunActions(
        help_config_show=None,
        # help_ui_show=None,
        help_run_show=(
            lambda: display(class_displayfiles([config_actions.fpth_script]))
        ),
        inputs_show=(
            lambda: display(
                class_displayfiles(
                    [f for f in config_actions.fpths_inputs], auto_open=True
                )
            )
        ),
        outputs_show=(
            lambda: display(
                class_displayfiles(
                    [f for f in config_actions.fpths_outputs], auto_open=True
                )
            )
        ),
        run=functools.partial(execute, config_actions.cmd),
    )
    return config_runapp, run_actions


# %%

# %%

# %%
config.dict()

# %%

# %%
fn_buildoutputs(**config.dict())


# %%
def fn_updateoutputs(**kwargs):
    fdir = kwargs['fdir_appdata']
    nm_in = kwargs['fpths_inputs'][0].with_suffix('').stem
    outputs = [
        fdir / (nm_in.replace('input', 'output') + '.csv'),
        fdir / (nm_in.replace('input', 'output') + '.plotly.json')
    ]
    return outputs


# %%



# %%
# /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.csv
# C:\engDev\git_mf\ipyrun\tests\examples\line_graph\output-line_graph.plotly.json

# %%
#config.dict()

# %%
#fn_updateoutputs(config).dict()

# %%
def fn_updateoutputs(config):
    kwargs = config.dict()
    fdir = kwargs['fdir_appdata']
    nm_in = kwargs['fpths_inputs'][0].with_suffix('').stem
    outputs = [
        fdir / (nm_in.replace('input', 'output') + '.plotly.json'),
        fdir / (nm_in.replace('input', 'output') + '.csv')
    ]
    kwargs['fpths_outputs'] = outputs
    #pprint(kwargs)
    newconfig = type(config)(**kwargs)
    return newconfig


# %%

# %%
run_app.__dict__.keys()

# %%
from ipyautoui.constants import BUTTON_HEIGHT_MIN
widgets.Checkbox(icon='fa-add')

# %%
flag = widgets.Button(layout={'width':'10px','height':'20px'}, button_style='danger')
check_w = widgets.Checkbox(indent=False)
widgets.HBox([flag, run_app.ui.run_form])

# %%

# %%
subprocess.run("python -O /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/script_line_graph.py /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/input-line_graph.lg.json /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.plotly.json /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.csv", shell=True)

# %%
s = "python -O /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/script_line_graph.py /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/input-line_graph.lg.json /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.csv /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.plotly.json"
subprocess.run(s.split(" "))

# %%
run_app.config.dict()

# %%
subprocess.run("python -O /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/script_line_graph.py /mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/input-line_graph.lg.json", shell=True)

# %%
run_app.ui.actions.run()

# %%
config.fpths_inputs


# %%
config.fpths_outputs[1]


# %%

# %%
def create_ShellAppConfig(fpth_script, fdir_appdata=None, run_index=0, process_name=None, pretty_name=None, check=True):
    
    if process_name is None:
        process_name = f"{fpth_script.stem}-{run_index}"

    return ShellAppConfig(run_id=RunId(index=run_index, process_name=process_name, pretty_name=pretty_name, check=check), 
                          run_actions=
                         )


# %%
obj = PyObj(path='/mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/schemas.py',obj_name='LineGraph')
_get_PyObj(obj)

# %%
import re

re.match('[A-Z]{2,6}-[1-9][0-9]*', 'AHU-1023234234')


# %%
spec

# %%
f = lambda:['output-*']
f()

# %%
from ipyautoui.test_schema import TestAutoLogic

# %%
from ipyautoui.displayfile import DisplayFile

DisplayFile('/mnt/c/engDev/git_mf/ipyrun/tests/constants.py')

# %%
list(test_constants.DIR_EXAMPLE_PROCESS.glob('*inputs*'))[0]


# %%

# %%
class RunAppConfigShell(RunAppConfig):
    config_actions: ShellHandler = None

    @validator("config_actions", always=True)
    def _config_actions(cls, v, values):
        run_id = values["config_actions"] 
        config_actions = values["config_actions"] 

ShellHandler(
        fpth_script=path_script,
        fdir_appdata=path_script.parent,
        fpths_inputs=paths_inputs,
        fpths_outputs=[
            fdir_appdata / f"outputs-{run_id.process_name}-{run_id.index}.csv",
            fdir_appdata / f"outputs-{run_id.process_name}-{run_id.index}.plotly.json",
        ],
        # params={'k':'v'}
    )
        #return values["fdir_appdata"] / v


if __name__ == "__main__":
    display(
        Markdown(
            """
### RunAppConfigShell

Extend the `RunAppConfig`
    """
        )
    )
    display(Markdown("`>>> display(RunAppConfigShell())`"))
    config_runapp = RunAppConfigShell()
    display(RunAppConfigShell().dict())

# %%
path =pathlib.Path('.')
list(path.glob('inputs-*'))

# %%
if __name__ == "__main__":
    from ipyrun.constants import load_test_constants
    from ipyautoui.autoui import AutoUi, AutoUiConfig
    from ipyautoui.displayfile import DisplayFiles, DisplayFile

    test_constants = load_test_constants()
    sys.path.append(str(test_constants.DIR_EXAMPLE_PROCESS))
    from schemas import LineGraph
    import functools
    import sys

    config_autoui = AutoUiConfig(pydantic_model=LineGraph, ext=".lg.json")
    LineGraphUi = AutoUi.create_displayfile(config_autoui)

    def line_graph_prev(path):
        display(LineGraphUi(path))

    user_file_renderers = {".lg.json": line_graph_prev}
    DisplayFiles = functools.partial(
        DisplayFiles, user_file_renderers=user_file_renderers
    )  # overwrite the DisplayFiles class with the .lg.json file renderer baked in
    test_constants = load_test_constants()

    PATH_SCRIPT = list(test_constants.DIR_EXAMPLE_PROCESS.glob(pattern="script*"))[0]
    tu = default_runapp_config(
        PATH_SCRIPT, 1, input_models=[LineGraph], class_displayfiles=DisplayFiles
    )
    run = RunApp.from_config(*tu)
    display(run)

# %%
tu[0].dict()

# %%
from io import StringIO


def create_runapp_linegraph(
    path_script=PATH_SCRIPT,
    input_models=[LineGraph],
    class_displayfiles=DisplayFiles,
    cls=None,
):
    if cls is not None:
        index = len(cls.apps)
    else:
        index = 0
    return RunApp.from_config(
        *default_runapp_config(
            path_script,
            index,
            input_models,
            class_displayfiles=class_displayfiles,
        )
    )


def add_linegraph_dialogue(cls=None):
    display(AddRunDialogue(cls, add_cmd=create_runapp_linegraph))


batch_actions = BatchActions(
    inputs_show=None,
    inputs_hide=None,
    outputs_show=None,
    outputs_hide=None,
    add_show=add_linegraph_dialogue,
)
batch = RunApps(batch_actions=batch_actions, apps=[create_runapp_linegraph()])
display(batch)
# create_runapp_linegraph(2)
