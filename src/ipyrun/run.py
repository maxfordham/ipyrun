# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.3
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %%
"""
attaches genuine functionality onto the datastructures / UI elements defined in ui_*.py
"""
# %run __init__.py
# %load_ext lab_black

# %%
import io
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
from typing import Optional, List, Dict, Type
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, validator, Field
from jinja2 import Template

import plotly.io as pio
import plotly.graph_objects as go

# widget stuff
import ipywidgets as widgets

# core mf_modules
from ipyautoui import AutoUi, DisplayFiles, AutoUiConfig
from ipyautoui.autoui import display_template_ui_model
from ipyautoui.autoui import AutoUiConfig
from pprint import pprint
import importlib.util
import inspect

# display_template_ui_model()

# from this repo
from ipyrun.utils import make_dir, del_matching
from ipyrun.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    JOBNO_DEFAULT,
    PATH_RUNAPP_HELP,
    PATH_RUNAPPS_HELP,
    DI_STATUS_MAP,
    load_test_constants
)
#from ipyrun.run_config import *
from ipyrun.ui_run import *
def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]

# %%



# %%
class PyObj(BaseModel):
    path: pathlib.Path
    obj_name: str
    module_name: str = None
    
    @validator("module_name", always=True)
    def _module_name(cls, v, values):
        if v is None:
            return values["path"].stem
        else:
            return v
        
class DisplayfileDefinition(PyObj):
    ext: str
    
def _get_PyObj(obj: PyObj):
    spec = importlib.util.spec_from_file_location(obj.module_name, obj.path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return getattr(foo, obj.obj_name)

def create_displayfile_renderer(ddf: DisplayfileDefinition, fn_onsave: typing.Callable = lambda: None):
    model = _get_PyObj(ddf)
    config_ui = AutoUiConfig(ext=ddf.ext, pydantic_model=model)
    return AutoUi.create_displayfile_renderer(config_autoui=config_ui, fn_onsave=fn_onsave)

class ConfigActionsShell(BaseModel):
    index: int = 0
    in_batch: bool = True 
    status: str = None
    fpth_script: pathlib.Path
    process_name: str = "process_name"
    pretty_name: str = None
    fdir_appdata: pathlib.Path = Field(default=None, description='working dir for process execution. defaults to script folder if folder not given.')
    displayfile_definitions: typing.List[DisplayfileDefinition] = Field(default=None, description='autoui definitions for displaying files. see ipyautui')
    displayfile_inputs_kwargs: typing.Dict = Field(default_factory=lambda:{})
    displayfile_outputs_kwargs: typing.Dict = Field(default_factory=lambda:{})
    fpths_inputs: List[pathlib.Path] = Field(default = None)# Field(default_factory = list)
    fpths_outputs: List[pathlib.Path] = Field(default_factory = list)
    fpth_config: pathlib.Path = "config-shell_handler.json"
    fpth_runhistory: pathlib.Path = "runhistory.csv"
    fpth_log: pathlib.Path = "log.csv"
    call: str = "python -O"
    params: typing.Dict = {}
    shell_template: str = """\
{{ call }} {{ fpth_script }}\
{% for f in fpths_inputs %} {{f}}{% endfor %}\
{% for f in fpths_outputs %} {{f}}{% endfor %}\
{% for k,v in params.items()%} --{{k}} {{v}}{% endfor %}
"""
    shell: str = ""
    
    @validator("process_name", always=True)
    def _process_name(cls, v, values):
        if v is None:
            return values["fpth_script"].stem
        else:
            return v
                       
    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return str(values["process_name"])
        else:
            return v

    @validator("fdir_appdata", always=True)
    def _fdir_appdata(cls, v, values):
        if v is None:
            v=values["fpth_script"].parent
        return v
    
    @validator("fpths_inputs", always=True)
    def _fpths_inputs(cls, v, values):
        if v is None:
            v=[]
        # find = []
        # if values['patterns_inputs'] is not None:
        #     for p in values['patterns_inputs']:
        #         find.extend(list(values["fdir_appdata"].glob(f"{p}")))
        v = v #+ find        
        assert type(v)==list, 'type(v)!=list'
        return v
    
    @validator("fpths_outputs", always=True)
    def _fpths_outputs(cls, v, values):
        if v is None:
            v=[]
        # find = []
        # if values['fn_buildoutputs'] is not None:    
        #     find = values['fn_buildoutputs'](**values)
        return v #+ find
        
    @validator("fpth_config", always=True)
    def _fpth_config(cls, v, values):
        return values["fdir_appdata"] / v

    @validator("fpth_runhistory", always=True)
    def _fpth_runhistory(cls, v, values):
        return values["fdir_appdata"] / v

    @validator("shell", always=True)
    def _shell(cls, v, values):
        #pprint(values)
        return Template(values["shell_template"]).render(**values)
    
# template run action callables
def get_status(fpths_inputs, fpths_outputs):
    #['no_outputs', 'up_to_date', 'outputs_need_updating']
    for f in fpths_outputs:
        if f.is_file() is False:
            return 'no_outputs'
    in_max = max([f.lstat().st_mtime for f in config.fpths_inputs])
    out_max = max([f.lstat().st_mtime for f in config.fpths_outputs])
    if in_max > out_max:
        return 'outputs_need_updating'
    else: 
        return 'up_to_date'
    
def update_cls_status(cls=None):
    cls._update_status()
    
def check(config: ConfigActionsShell):
    config.in_batch = True

def uncheck(config: ConfigActionsShell):
    config.in_batch = False
    
def show_files(fpths, class_displayfiles=DisplayFiles, kwargs_displayfiles={}):
    display(class_displayfiles([f for f in fpths], **kwargs_displayfiles))
    
def run_shell(shell: str, cls=None): #
    """
    cmd: str, cls=None
    """
   
    shell = shell.split(" ")
    pr = "\n".join(shell)
    pr = f"```{pr}```"
    display(Markdown(pr))
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
    
    cls._update_status()

    
def build_run_actions(config: ConfigActionsShell, cls=None) -> RunActions:  # fn_onsave
    # create custom Displayfile 
    user_file_renderers = {}
    fn_onsave = cls._update_status
    for d in config.displayfile_definitions: 
        user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=fn_onsave))    
    cls_display = functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)
    
    run_actions = RunActions(check=functools.partial(check, config),
                             uncheck=functools.partial(uncheck, config),
                             get_status=fn_onsave,
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
list(DI_STATUS_MAP.keys())

# %%
from ipyrun.ui_run import RunActionsUi, RunUi
class RunApp:
    def __init__(self,
                 config: typing.Type[BaseModel],
                 cls_ui: typing.Type[RunActionsUi] = RunUi,
                 fn_buildactions: typing.Callable[[typing.Type[BaseModel]], RunActions]=build_run_actions
                ):
        self.config = config
        self.fn_buildactions = fn_buildactions
        actions = fn_buildactions(self.config, cls=self)
        self.actions = self._init_actions(actions)
        self.ui = cls_ui(self.actions)
        self._update_status()
        
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
        self, actions: typing.Type[RunActions]
    ) -> typing.Type[RunActions]:
        """this allows us to pass the RunApp object to the Run Actions. TODO: describe better! """
        return type(actions)(
            **{k: self._init_run_action(v) for k, v in actions.dict().items()}
        )
    
    def display(self):
        display(self.ui)

    def _ipython_display_(self):
        self.display()
        

test_constants = load_test_constants()
PATH_EXAMPLE_SCRIPT = list(test_constants.DIR_EXAMPLE_PROCESS.glob('script*'))[0]
config = ConfigActionsShell(fpth_script=PATH_EXAMPLE_SCRIPT, 
                            fpths_inputs=['/mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/input-line_graph.lg.json'],
                            fpths_outputs=['/mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.csv',
                                           '/mnt/c/engDev/git_mf/ipyrun/tests/examples/line_graph/output-line_graph.plotly.json'],
                            displayfile_definitions=[DisplayfileDefinition(path=PATH_EXAMPLE_SCRIPT.parent / 'schemas.py',
                                obj_name='LineGraph',
                                ext='.lg.json')])#.dict()
run_app = RunApp(config)# fn_updateoutputs=fn_updateoutputs
run_app


# %%

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
