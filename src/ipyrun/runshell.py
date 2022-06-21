# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""
A configuration of the ipyrun App for running shell commands scripts. 
By default it is used for running python scripts on the command line.
"""
# %run __init__.py
#  ^ this means that the local imports still work when running as a notebook
# #%load_ext lab_black

# +
#  TODO: make the config shell commands relative rather than absolute (improves readability)

# +
# core libs
import os
import sys
import io
import shutil
import pathlib
import functools
import subprocess
import getpass
import stringcase
from jinja2 import Template
from markdown import markdown
import json

# object models
from pydantic import validator, Field
from typing import Optional, List, Dict, Type, Callable, Union, Any
from enum import Enum

# widget stuff
from IPython.display import Markdown, clear_output, display
import ipywidgets as widgets
from halo import HaloNotebook
from markdown import markdown

# core mf_modules
from ipyautoui import AutoUi, AutoDisplay
from ipyautoui._utils import (
    PyObj,
    load_PyObj,
    create_pydantic_json_file,
    display_pydantic_json,
    check_installed
)


# from this repo
from ipyrun.runui import RunUi, RunApp, BatchApp
from ipyrun.actions import (
    RunActions,
    BatchActions,
    DefaultRunActions,
    DefaultBatchActions,
)
from ipyrun.basemodel import BaseModel
from ipyrun._utils import get_status, open_file
from ipyrun.constants import PATH_CONFIG, PATH_RUNHISTORY, PATH_LOG, FPTH_EXAMPLE_INPUTSCHEMA, DI_STATUS_MAP

if check_installed('mf_file_utilities'):
    from mf_file_utilities.applauncher_wrapper import get_fpth_win
else:
    get_fpth_win = lambda v: v

# display_template_ui_model()  # TODO: add this to docs

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]


# +
class FiletypeEnum(str, Enum):
    input = "in"
    output = "out"
    wip = "wip"


class AutoDisplayDefinition(PyObj):
    ftype: FiletypeEnum = Field(
        None, description='valid inputs are: "in", "out", "wip"'
    )
    ext: str


def create_autodisplay_map(
    ddf: AutoDisplayDefinition, fn_onsave: Callable = lambda: None
):
    model = load_PyObj(ddf)
    return AutoUi.create_autodisplay_map(schema=model, ext=ddf.ext, fn_onsave=fn_onsave)


class ConfigShell(BaseModel):

    """a config object. all the definitions required to create the RunActions for a shell running tools are here.
    it is anticipated that this class will be inherited and validators added to create application specific relationships between variables."""

    index: int = 0
    fpth_script: pathlib.Path = "script.py" # TODO: refactor --> path_run
    name: str = None
    long_name: str = None
    key: str = None
    fdir_root: pathlib.Path = Field(
        default=None,
        description="root folder. same as fdir_root within batch config. facilitates running many processes. this is the working dir.",
    )
    fdir_appdata: pathlib.Path = Field(
        default=None,
    )
    in_batch: bool = False
    status: str = None
    update_config_at_runtime: bool = Field(
        default=False,
        description="updates config before running shell command. useful if for example outputs filepaths defined within the input filepaths",
    )
    autodisplay_definitions: List[AutoDisplayDefinition] = Field(
        default_factory=list,
        description="autoui definitions for displaying files. see ipyautoui",
    )
    autodisplay_inputs_kwargs: Dict = Field(default_factory=dict)
    autodisplay_outputs_kwargs: Dict = Field(default_factory=dict)
    fpths_inputs: Optional[List[pathlib.Path]] = None
    fpths_outputs: Optional[List[pathlib.Path]] = None
    fpth_params: pathlib.Path = None
    fpth_config: pathlib.Path = Field(
        None,
        description=f"there is a single unique folder and config file for each RunApp. the config filename is fixed as {str(PATH_CONFIG)}",
        #const=True
    )
    fpth_runhistory: pathlib.Path = Field(PATH_RUNHISTORY)#,const=True
    fpth_log: pathlib.Path = Field(None)#,const=True
    call: str = "python -O"
    params: Dict = {}
    shell_template: str = """\
{{ call }} {{ fpth_script }}\
{% for f in fpths_inputs %} {{f}}{% endfor %}\
{% for f in fpths_outputs %} {{f}}{% endfor %}\
{% for k,v in params.items()%} --{{k}} {{v}}{% endfor %}
"""
    shell: str = ""


# -

class DefaultConfigShell(ConfigShell):
    """
    a config object. all the definitions required to create the RunActions for a shell running tools are here.
    
    extends ConfigShell with validators only. 
    this creates opinionated relationships between the variables that dont necessarily have to exist.
    
    A likely way that this would need extending is to generate fpth_outputs based on other fields here. 
    This is very application specific, but could be done as shown in the Example.
    
    The validators, in some cases overwrite the parameters based on other parameters (so they are effectively
    no longer user editable), or they default to something sensible. This reduces the amount of inputs that 
    need providing by the User. 
    
    Notes:
        - validators can be overwritten, allowing users to keep the majority of default behaviour but overwrite 
        some of it. 
        - in Args below the minimum number of input vars are given
    
    Args: 
        index (int):
        fpth_script (pathlib.Path): 
        fdir_root (pathlib.Path): defaults to cwd
        autodisplay_definitions (List[AutoDisplayDefinition]): used to generate custom input and output forms
            using ipyautoui
            
    Example:
        ::

            class LineGraphConfigShell(DefaultConfigShell):
                # script specific outputs defined by custom ConfigShell class
                @validator("fpths_outputs", always=True)
                def _fpths_outputs(cls, v, values):
                    fdir = values['fdir_appdata']
                    nm = values['name']
                    paths = [fdir / ('out-'+nm+'.csv'), fdir / ('out-' + nm + '.plotly.json')]
                    return paths
    """

    @validator("status")
    def _status(cls, v, values):
        li = list(DI_STATUS_MAP.keys()) + [None]
        if v not in li:
            ValueError(f"status must be in {str(li)}")
        return v

    @validator("fpth_script")
    def validate_fpth_script(cls, v):
        assert " " not in str(v.stem), "must be alphanumeric"
        return v

    @validator("name", always=True)
    def _name(cls, v, values):
        if v is None:
            return values["fpth_script"].stem.replace("script_", "")
        else:
            if " " in v:
                raise ValueError("the name must not contain any spaces")
            return v

    @validator("long_name", always=True)
    def _long_name(cls, v, values):
        if v is None:
            return (
                str(values["index"]).zfill(2)
                + " - "
                + stringcase.titlecase(values["name"])
            )
        else:
            return v

    @validator("key", always=True)
    def _key(cls, v, values):
        if v is None:
            return str(values["index"]).zfill(2) + "-" + values["name"]
        else:
            return v

    @validator("fdir_root", always=True)
    def _fdir_root(cls, v, values):
        if v is None:
            v = pathlib.Path('.')
        os.chdir(str(v))
        return v

    @validator("fdir_appdata", always=True)
    def _fdir_appdata(cls, v, values):
        v = values['fdir_root'] / values["key"]
        v.mkdir(exist_ok=True)
        return pathlib.Path(values["key"])

    @validator("fpths_inputs", always=True)
    def _fpths_inputs(cls, v, values):
        if v is None:
            v = []
            if values["autodisplay_definitions"] is not None:
                ddfs = [
                    v_
                    for v_ in values["autodisplay_definitions"]
                    if v_.ftype.value == "in"
                ]
                paths = [
                    values["fdir_root"] / values["fdir_appdata"] / ("in-" + values["key"] + ddf.ext)
                    for ddf in ddfs
                ]  
                for ddf, path in zip(ddfs, paths):
                    if not path.is_file():
                        create_pydantic_json_file(ddf, path) # TODO: remove from here? 
                        
                v = [p.relative_to(values["fdir_root"]) for p in paths]
        assert type(v) == list, "type(v)!=list"
        return v

    @validator("fpths_outputs", always=True)
    def _fpths_outputs(cls, v, values):
        if v is None:
            v = []
        return v

    @validator("fpth_config", always=True)
    def _fpth_config(cls, v, values):
        v = values["fdir_root"] / values["fdir_appdata"] / PATH_CONFIG 
        return v.relative_to(values["fdir_root"])


    @validator("fpth_runhistory", always=True)
    def _fpth_runhistory(cls, v, values):
        v = values["fdir_root"] / values["fdir_appdata"] / PATH_RUNHISTORY
        return v.relative_to(values["fdir_root"])
    
    @validator("fpth_log", always=True)
    def _fpth_log(cls, v, values):
        v = values["fdir_root"] / values["fdir_appdata"] / PATH_LOG
        return v.relative_to(values["fdir_root"])

    @validator("params", always=True)
    def _params(cls, v, values):
        if values["fpth_params"] is not None:
            with open(values["fpth_params"], "r") as f:
                v = json.load(f)
        return v

    @validator("shell", always=True)
    def _shell(cls, v, values):
        return Template(values["shell_template"]).render(**values)

if __name__ == "__main__":
    from ipyrun.constants import FPTH_EXAMPLE_SCRIPT, load_test_constants

    test_constants = load_test_constants()
    config = DefaultConfigShell(
        fpth_script=FPTH_EXAMPLE_SCRIPT, fdir_root=test_constants.FDIR_APPDATA
    )
    display(config.dict())


# +
def check(config: ConfigShell, fn_saveconfig):
    config.in_batch = True
    fn_saveconfig()


def uncheck(config: ConfigShell, fn_saveconfig):
    config.in_batch = False
    fn_saveconfig()


def show_files(fpths, class_autodisplay=AutoDisplay.from_paths, kwargs_autodisplay={}):
    return class_autodisplay([f for f in fpths], **kwargs_autodisplay)


def update_status(app, fn_saveconfig):
    if app is None:
        print("update status requires an app object to update the UI")
    st = app.actions.get_status()
    app.status = st  # .ui
    app.config.status = st
    fn_saveconfig()


def update_AutoDisplay(config, fn_onsave=None):
    file_renderers = {}
    for d in config.autodisplay_definitions:
        file_renderers.update(create_autodisplay_map(d, fn_onsave=fn_onsave))
    return functools.partial(AutoDisplay.from_paths, file_renderers=file_renderers)


def run_shell(app=None):
    """
    app=None
    """
    if app.config.update_config_at_runtime:
        app.config = (
            app.config
        )  #  this updates config and remakes run actions. useful if, for example, output fpths dependent on contents of input files
    print(f"run { app.config.key}")
    if app.status == "up_to_date":
        print(f"already up-to-date")
        # clear_output()
        return
    shell = app.config.shell.split(" ")
    pr = """
    """.join(
        shell
    )
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
    app.actions.update_status()
    


class RunShellActions(DefaultRunActions):
    """extends RunActions by creating Callables based on data within the app or the config objects. 
    TODO: currently this full filepaths and does not work with relative paths. make it work with relative paths! 
    """

    config: DefaultConfigShell = None  # not a config type is defined - get pydantic to validate it
    
    @validator("hide", always=True)
    def _hide(cls, v, values):
        return None

    @validator("save_config", always=True)
    def _save_config(cls, v, values):
        if values["config"] is not None:
            return functools.partial(values["config"].file, values["config"].fpth_config)

    @validator("check", always=True)
    def _check(cls, v, values):
        return functools.partial(check, values["config"], values["save_config"])

    @validator("uncheck", always=True)
    def _uncheck(cls, v, values):
        return functools.partial(uncheck, values["config"], values["save_config"])

    @validator("get_status", always=True)
    def _get_status(cls, v, values):
        return functools.partial(
            get_status, values["config"].fpths_inputs, values["config"].fpths_outputs
        )

    @validator("update_status", always=True)
    def _update_status(cls, v, values):
        return functools.partial(update_status, values["app"], values["save_config"])

    @validator("help_run_show", always=True)
    def _help_run_show(cls, v, values):
        return functools.partial(
            AutoDisplay.from_paths, [values["config"].fpth_script], patterns="*"
        )

    @validator("help_config_show", always=True)
    def _help_config_show(cls, v, values):
        return functools.partial(display_pydantic_json, values["config"], as_yaml=False)

    @validator("inputs_show", always=True)
    def _inputs_show(cls, v, values):
        if values["config"] is not None:
            AutoDisplayInputs = update_AutoDisplay(
                values["config"], fn_onsave=values["update_status"] 
            )
            paths = [values["config"].fdir_root / f for f in values["config"].fpths_inputs]
            return functools.partial(
                AutoDisplayInputs,
                paths,
                **values["config"].autodisplay_inputs_kwargs,
            )
        else:
            return None

    @validator("outputs_show", always=True)
    def _outputs_show(cls, v, values):
        if values["config"] is not None and values["app"] is not None:
            AutoDisplayOutputs = update_AutoDisplay(values["config"]) 
            return functools.partial(
                AutoDisplayOutputs,
                values["config"].fpths_outputs,
                **values["config"].autodisplay_outputs_kwargs,
            )
        else:
            return None

    @validator("run", always=True)
    def _run(cls, v, values):
        return functools.partial(run_shell, app=values["app"])

    @validator("runlog_show", always=True)
    def _runlog_show(cls, v, values):
        return None  # TODO: add logging!
    
    @validator("load_show", always=True)
    def _load_show(cls, v, values):
        return None  


# extend RunApp to make a default RunShell
# -
if __name__ == "__main__":
    from ipyrun.constants import FPTH_EXAMPLE_SCRIPT, load_test_constants

    test_constants = load_test_constants()
    config = DefaultConfigShell(
        fpth_script=FPTH_EXAMPLE_SCRIPT, fdir_root=test_constants.FDIR_APPDATA
    )
    display(config.dict())

if __name__ == "__main__":

    class LineGraphConfigShell(DefaultConfigShell):
        @validator("fpth_script", always=True, pre=True)
        def _set_fpth_script(cls, v, values):
            return FPTH_EXAMPLE_SCRIPT

        @validator("fpths_outputs", always=True)
        def _fpths_outputs(cls, v, values):
            fdir = values["fdir_appdata"]
            nm = values["name"]
            paths = [
                fdir / pathlib.Path("out-" + nm + ".csv"),
                fdir / pathlib.Path("out-" + nm + ".plotly.json")
            ]
            return paths

        @validator("autodisplay_definitions", always=True)
        def _autodisplay_definitions(cls, v, values):
            return [
                AutoDisplayDefinition(
                    path=FPTH_EXAMPLE_INPUTSCHEMA,
                    obj_name="LineGraph",
                    ext=".lg.json",
                    ftype=FiletypeEnum.input,
                )
            ]

        @validator("autodisplay_inputs_kwargs", always=True)
        def _autodisplay_inputs_kwargs(cls, v, values):
            return dict(patterns="*")

        @validator("autodisplay_outputs_kwargs", always=True)
        def _autodisplay_outputs_kwargs(cls, v, values):
            return dict(patterns="*.plotly.json")

    config = LineGraphConfigShell(fdir_root=test_constants.FDIR_APPDATA)
    run_app = RunApp(config, cls_actions=RunShellActions)  # cls_ui=RunUi,
    display(run_app)


class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    fpth_config: pathlib.Path = Field(
        default=PATH_CONFIG, description="name of config file for batch app"
    )
    title: str = Field(default="", description="markdown description of BatchApp")
    status: str = None
    cls_actions: Callable = Field(
        default=RunShellActions,
        description="the class that defines the RunActions (extended with validators based on use case)",
        exclude=True,
    )
    cls_app: Union[Type, Callable] = Field(
        default=RunApp, description="the class that defines the RunApp.", exclude=True
    )
    cls_config: Union[Type, Callable] = Field(
        default=DefaultConfigShell,
        description="the class that defines the config of a RunApp. this has can have fpth_script baked in",
        exclude=True,
    )
    configs: List = []
    # runs: List[Callable] = Field(default=lambda: [], description="a list of RunApps", exclude=True)

    # @validator("fpth_config", always=True, pre=True)
    # def _fpth_config(cls, v, values):
    #     """bundles RunApp up as a single argument callable"""
    #     return values["fdir_root"] / v
    
    @validator("fdir_root", always=True)
    def _fdir_root(cls, v, values):
        if v is None:
            v = pathlib.Path('.')
        os.chdir(str(v))
        return v

    @validator("cls_app", always=True, pre=True)
    def _cls_app(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return functools.partial(
            v, cls_actions=values["cls_actions"]  # cls_ui=values["cls_ui"],
        )

    @validator("configs", always=True)
    def _configs(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return [values["cls_config"](**v_) for v_ in v]

    @validator("status")
    def _status(cls, v, values):
        li = list(DI_STATUS_MAP.keys()) + [None]
        if v not in li:
            ValueError(f"status must be in {str(li)}")
        return v


if __name__ == "__main__":
    from ipyrun.constants import load_test_constants

    test_constants = load_test_constants()
    config_batch = ConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        cls_config=ConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    display(config_batch.dict())


# +
def fn_add(app, **kwargs):
    cls_config = app.config.cls_config
    if "index" not in kwargs:
        if len(app.config.configs) == 0:
            kwargs["index"] = 0
        else:
            kwargs["index"] = app.config.configs[-1].index + 1
    kwargs["fdir_root"] = app.config.fdir_root
    config = cls_config(**kwargs)
    app.configs_append(config)
    app.add.value = False
    app.watch_run_statuses()
    app.actions.update_status()

def fn_add_show(app):
    clear_output()
    app.actions.add()

def fn_add_hide(app):
    return "add hide"

def fn_remove(app=None, key=None):
    if key is None:
        print("key is None")
        key = app.runs.iterable[-1].key
    fdir = [i.fdir_appdata for i in app.config.configs if i.key == key][0]
    app.configs_remove(key)
    shutil.rmtree(fdir)
    app.watch_run_statuses()
    app.actions.update_status()


def fn_remove_show(app=None):
    app.runs.add_remove_controls = "remove_only"
    return widgets.HTML(
        markdown("### 🗑️ select runs below to delete 🗑️")
    )

def fn_remove_hide(app=None):
    app.runs.add_remove_controls = None

def check_batch(app, fn_saveconfig, bool_=True):
    [setattr(v.check, "value", bool_) for k, v in app.runs.items.items()]
    [setattr(c, "in_batch", bool_) for c in app.config.configs]
    fn_saveconfig()

def run_batch(app=None):
    sel = {c.key: c.in_batch for c in app.config.configs}
    if True not in sel.values():
        print("no runs selected")
    else:
        print("run the following:")
        [print(k) for k, v in sel.items() if v is True]
    [v.run() for v in app.run_actions if v.config.in_batch]

def batch_get_status(app=None):
    st = [a.get_status() for a in app.run_actions]
    if st is None:
        st = "error"
    bst = "error"
    for s in ["up_to_date", "no_outputs", "outputs_need_updating", "error"]:
        if s in st:
            bst = s
    return bst


def batch_update_status(app=None):
    [a.update_status() for a in app.run_actions]
    app.status = app.actions.get_status()

    
def load_dir(app=None, fdir_root=None):
    cl = type(app.config)
    config_batch = cl(fdir_root=fdir_root)
    if config_batch.fpth_config.is_file():
        config_batch = cl.parse_file(config_batch.fpth_config)
    print('loading')
    app.config = config_batch
    app.loaded.value = f"{str(get_fpth_win(fdir_root))}"
    app.load.value = False
    
def set_loaded(app=None, value=""):
    app.loaded.value = value
    return value

def open_loaded(app=None, fdir_root=None):
    with app.out_load:
        open_file(fdir_root)
        clear_output()

class BatchShellActions(DefaultBatchActions):
    
    @validator("load", always=True)
    def _load(cls, v, values):
        fn = lambda: None
        if values["app"] is not None:
            cl = type(values["app"].config)
            fn = functools.partial(load_dir, app=values["app"])
        return fn
    
    @validator("get_loaded", always=True)
    def _get_loaded(cls, v, values):
        fn = lambda: None
        if values["app"] is not None and values["config"] is not None:
            fdir_root = values["config"].fdir_root
            fn = functools.partial(set_loaded, app=values["app"], value=markdown(f'`{str(get_fpth_win(fdir_root))}`'))
        return fn
    
    @validator("open_loaded", always=True)
    def _open_loaded(cls, v, values):
        fn = lambda: None
        if values["app"] is not None and values["config"] is not None:
            fn = functools.partial(open_loaded, app=values["app"], fdir_root=values["config"].fdir_root)
        return fn
    
    @validator("save_config", always=True)
    def _save_config(cls, v, values):
        return functools.partial(values["config"].file, values["config"].fpth_config)

    @validator("wizard_show", always=True)
    def _wizard_show(cls, v, values):
        return None

    @validator("check", always=True)
    def _check(cls, v, values):
        return functools.partial(
            check_batch, values["app"], values["save_config"], bool_=True
        )

    @validator("uncheck", always=True)
    def _uncheck(cls, v, values):
        return functools.partial(
            check_batch, values["app"], values["save_config"], bool_=False
        )

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
        return functools.partial(display_pydantic_json, values["config"], as_yaml=False) # TODO: revert to as_yaml=True when tested as working in Voila

    @validator("run", always=True)
    def _run(cls, v, values):
        return functools.partial(run_batch, app=values["app"])

    @validator("inputs_show", always=True)
    def _inputs_show(cls, v, values):
        return None

    @validator("outputs_show", always=True)
    def _outputs_show(cls, v, values):
        return None

    @validator("get_status", always=True)
    def _get_status(cls, v, values):
        return functools.partial(batch_get_status, app=values["app"])

    @validator("update_status", always=True)
    def _update_status(cls, v, values):
        return functools.partial(batch_update_status, app=values["app"])
    


# -

if __name__ == "__main__":
    # TODO: update example to this: https://examples.pyviz.org/attractors/attractors.html
    # TODO: configure so that the value of the RunApp is the config
    
    from ipyrun.constants import load_test_constants
    from ipyautoui.custom.workingdir import WorkingDirsUi

    test_constants = load_test_constants()

    class LineGraphConfigBatch(ConfigBatch):
        @validator("cls_actions", always=True)
        def _cls_actions(cls, v, values):
            """bundles RunApp up as a single argument callable"""
            return RunShellActions

        @validator("cls_config", always=True)
        def _cls_config(cls, v, values):
            """bundles RunApp up as a single argument callable"""
            return LineGraphConfigShell
        
    def fn_loaddir_handler(value, app=None):
        fdir_root = value["fdir"] / "06_Models"
        app.actions.load(fdir_root=fdir_root)
        
    class LineGraphBatchActions(BatchShellActions):
        @validator("config", always=True)
        def _config(cls, v, values):
            """bundles RunApp up as a single argument callable"""
            if type(v) == dict:
                v = LineGraphConfigBatch(**v)
            return v

        @validator("runlog_show", always=True)
        def _runlog_show(cls, v, values):
            return None
        
        @validator("load_show", always=True)
        def _load_show(cls, v, values):
            return lambda: WorkingDirsUi(fn_onload=functools.partial(fn_loaddir_handler, app=values["app"]))

    config_batch = LineGraphConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        # cls_config=MyConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    if config_batch.fpth_config.is_file():
        config_batch = LineGraphConfigBatch.parse_file(config_batch.fpth_config)
    app = BatchApp(config_batch, cls_actions=LineGraphBatchActions)
    display(app)

