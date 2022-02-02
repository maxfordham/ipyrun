# -*- coding: utf-8 -*-
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
    BUTTON_MIN_SIZE,
    JOBNO_DEFAULT,
    PATH_RUNAPP_HELP,
    PATH_RUNAPPS_HELP,
    DI_STATUS_MAP,
    FNM_CONFIG_FILE,
    load_test_constants
)
test_constants = load_test_constants()

from ipyrun.ui_run import *
from ipyrun.ui_run import RunActionsUi, RunUi, RunUiConfig
from ipyrun.ui_add import AddRun
from ipyrun.schema_actions import RunActions, BatchActions
from ipyrun.schema_config_runshell import ConfigActionsShell, DefaultConfigActionsShell, DisplayfileDefinition, FiletypeEnum, create_displayfile_renderer
from ipyrun.basemodel import BaseModel

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]


# %%
def check(config: ConfigActionsShell):
    config.in_batch = True
    config.file(config.fpth_config)

def uncheck(config: ConfigActionsShell):
    config.in_batch = False
    config.file(config.fpth_config)

def show_files(fpths, class_displayfiles=DisplayFiles, kwargs_displayfiles={}):
    return class_displayfiles([f for f in fpths], **kwargs_displayfiles)

def update_DisplayFiles(config, app):
    user_file_renderers = {}
    for d in config.displayfile_definitions: 
        user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=app._update_status)) 
    return functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)

def run_shell(app=None):
    """
    app=None
    """
    if app.config.update_config_at_runtime:
        app.config = app.config #  this updates config and remakes run actions. useful if, for example, output fpths dependent on contents of input files
    if app.ui.status == 'up_to_date':
        display(Markdown(f"already up-to-date"))
        clear_output()
        return 
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
        self.ui_form = cls_ui(run_actions=RunActions(), name=config.pretty_name)
        self.children = [self.ui_form]
        self.ui = self.ui_form.ui
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
class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    fpth_config: pathlib.Path = Field(default=FNM_CONFIG_FILE, description='name of config file for batch app')
    title: str = Field(default='', description='markdown description of BatchApp')
    cls_ui: Callable = Field(default=RunUi, description="the class that defines the RunUi widget container", exclude=True)
    cls_actions: Callable = Field(default=RunShellActions, description="the class that defines the RunActions (extended with validators based on use case)", exclude=True)
    cls_app: Union[Type, Callable] = Field(default=RunApp, description="the class that defines the RunApp.", exclude=True) # functools.partial used to define the cls_ui and cls_actions beofre passing here
    cls_config: Union[Type, Callable] = Field(default=DefaultConfigActionsShell, description="the class that defines the config of a RunApp. this has can have fpth_script baked in", exclude=True)
    configs: List = []
    #runs: List[Callable] = Field(default=lambda: [], description="a list of RunApps", exclude=True)

    @validator("fpth_config", always=True, pre=True)
    def _fpth_config(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return values['fdir_root'] / v

    @validator("cls_app", always=True, pre=True)
    def _cls_app(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return functools.partial(v, cls_ui=values['cls_ui'], cls_actions=values['cls_actions'])

    @validator("configs", always=True)
    def _configs(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return [values['cls_config'](**v_) for v_ in v]
    
if __name__ == "__main__":
    config_batch = ConfigBatch(fdir_root=test_constants.DIR_EXAMPLE_BATCH,
                                   cls_config=MyConfigActionsShell,
                                   title="""# Plot Straight Lines\n### example RunApp""")
    from devtools import debug
    debug(config_batch)

# %%
from ipyrun.ui_remove import RemoveRun

def fn_add(app, **kwargs):
    cls_runapp = app.config.cls_app
    cls_config = app.config.cls_config
    if "index" not in kwargs:
        kwargs['index'] = app.config.configs[-1].index + 1
    kwargs['fdir_appdata'] = app.config.fdir_root
    config = cls_config(**kwargs)
    app.configs_append(config)
    app.ui.add.value=False

def fn_add_show(app):
    app.ui.actions.add()

def fn_add_hide(app):
    return 'add hide'
    # with app.ui.out_add:
    #     clear_output()

def fn_remove(app=None, key=None):
    if key is None:
        print('key is None')
        key = app.runs.iterable[-1].key
    fdir = [i.fdir_appdata for i in app.config.configs if i.key==key][0]
    app.configs_remove(key)
    shutil.rmtree(fdir)

def fn_remove_show(app=None):
    app.runs.add_remove_controls = 'remove_only'
    return widgets.HTML(markdown("# 🗑️ select runs below to delete 🗑️")) # RemoveRun(app=app)

def fn_remove_hide(app=None):
    app.runs.add_remove_controls = None

def check_batch(app=None, bool_=True):
    [setattr(v.ui.check, 'value', bool_) for k, v in app.runs.items.items()]
    [setattr(c, 'in_batch', bool_) for c in app.config.configs]
    app.config.file(app.config.fpth_config)

def run_batch(app=None):
    [v.run() for v in app.run_actions];

class BatchShellActions(BatchActions):
    @validator("check", always=True)
    def _check(cls, v, values):
        return functools.partial(check_batch, app=values["app"], bool_=True)
    
    @validator("uncheck", always=True)
    def _uncheck(cls, v, values):
        return functools.partial(check_batch, app=values["app"], bool_=False)

    @validator("add", always=True)
    def _add(cls, v, values):
        return functools.partial(fn_add, values["app"])
    
    @validator("add_show", always=True)
    def _add_show(cls, v, values):
        return functools.partial(fn_add_show, values["app"])
    
    @validator("add_hide", always=True)
    def _add_hide(cls, v, values):
        return functools.partial(fn_add_hide, values["app"])

    @validator("remove", always=True)
    def _remove(cls, v, values):
        values["app"].runs.fn_remove = functools.partial(fn_remove, app=values["app"])
        return values["app"].runs.remove_row
    
    @validator("remove_show", always=True)
    def _remove_show(cls, v, values):
        return functools.partial(fn_remove_show, app=values["app"])
    
    @validator("remove_hide", always=True)
    def _remove_hide(cls, v, values):
        return functools.partial(fn_remove_hide, values["app"])
    
    @validator("help_config_show", always=True)
    def _help_config_show(cls, v, values):
        return functools.partial(display_pydantic_json, values["config"], as_yaml=True)
    
    @validator("run", always=True)
    def _run(cls, v, values):
        return functools.partial(run_batch, app=values["app"])
    
    @validator("inputs_show", always=True)
    def _inputs_show(cls, v, values):
        return None
    
    @validator("outputs_show", always=True)
    def _outputs_show(cls, v, values):
        return None


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
    def run_actions(self):
        return [v.ui.actions for k, v in self.runs.items.items()]

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
        self.runs.items = {c.key: self.make_run(c) for c in self.config.configs}

    def make_run(self, config):
        """builds RunApp from config"""
        return self.config.cls_app(config)

    def configs_append(self, config):
        self.ui.actions.config.configs.append(config)
        self.config.file(self.config.fpth_config)
        newapp = self.make_run(config)
        self.runs.add_row(new_key=config.key, item=newapp)

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
class MyConfigBatch(ConfigBatch):
    @validator("cls_config", always=True)
    def _cls_config(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return MyConfigActionsShell


# %%
if __name__ == "__main__":
    #MyConfigBatch = functools.partial(ConfigBatch, cls_config=MyConfigActionsShell)
    config_batch = MyConfigBatch(fdir_root=test_constants.DIR_EXAMPLE_BATCH,
                               #cls_config=MyConfigActionsShell,
                               title="""# Plot Straight Lines\n### example RunApp""")
    if config_batch.fpth_config.is_file():
        config_batch = MyConfigBatch.parse_file(config_batch.fpth_config)
    app = BatchApp(config_batch)
    display(app)

# %%
# ?object

# %%
