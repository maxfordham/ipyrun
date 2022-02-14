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
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

"""
A configuration of the ipyrun App for running shell commands scripts. 
By default it is used for running python scripts on the command line.
"""
# %run __init__.py
#  ^ this means that the local imports still work when running as a notebook
# %load_ext lab_black

# +
# core libs
import io
import shutil
import pathlib
import functools
import subprocess
import getpass
import stringcase
from jinja2 import Template
from markdown import markdown

# object models
from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Type, Callable, Union
from enum import Enum

# widget stuff
from IPython.display import Markdown, clear_output, display
import ipywidgets as widgets
from halo import HaloNotebook

# core mf_modules
from ipyautoui import AutoUi, DisplayFiles, AutoUiConfig
from ipyautoui._utils import (
    PyObj,
    load_PyObj,
    create_pydantic_json_file,
    display_pydantic_json,
)
from ipyautoui.basemodel import BaseModel

# from this repo
from ipyrun.runui import RunUi, RunApp, BatchApp
from ipyrun.actions import RunActions, BatchActions
from ipyrun.basemodel import BaseModel
from ipyrun.utils import get_status
from ipyrun.constants import FNM_CONFIG_FILE

# display_template_ui_model()  # TODO: add this to docs


def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]


# +
class FiletypeEnum(str, Enum):
    input = "in"
    output = "out"
    wip = "wip"


class DisplayfileDefinition(PyObj):
    ftype: FiletypeEnum = None
    ext: str


def create_displayfile_renderer(
    ddf: DisplayfileDefinition, fn_onsave: Callable = lambda: None
):
    model = load_PyObj(ddf)
    config_ui = AutoUiConfig(ext=ddf.ext, pydantic_model=model)
    return AutoUi.create_displayfile_renderer(
        config_autoui=config_ui, fn_onsave=fn_onsave
    )


class ConfigShell(BaseModel):
    """a config object. all the definitions required to create the RunActions for a shell running tools are here.
    it is anticipated that this class will be inherited and validators added to create application specific relationships between variables."""

    index: int = 0
    fpth_script: pathlib.Path
    process_name: str = None  # change to name?
    pretty_name: str = None  # change to title?
    key: str = None
    fdir_appdata: pathlib.Path = Field(
        default=None,
        description="working dir for process execution. defaults to script folder if folder not given.",
    )
    in_batch: bool = False
    status: str = None
    update_config_at_runtime: bool = Field(
        default=False,
        description="updates config before running shell command. useful if for example outputs filepaths defined within the input filepaths",
    )
    displayfile_definitions: List[DisplayfileDefinition] = Field(
        default_factory=list,
        description="autoui definitions for displaying files. see ipyautui",
    )
    displayfile_inputs_kwargs: Dict = Field(default_factory=dict)
    displayfile_outputs_kwargs: Dict = Field(default_factory=dict)
    fpths_inputs: Optional[List[pathlib.Path]] = None
    fpths_outputs: Optional[List[pathlib.Path]] = None
    fpth_params: pathlib.Path = None
    fpth_config: pathlib.Path = Field(
        FNM_CONFIG_FILE,
        description=f"there is a single unique folder and config file for each RunApp. the config filename is fixed as {str(FNM_CONFIG_FILE)}",
    )
    fpth_runhistory: pathlib.Path = "runhistory.csv"
    fpth_log: pathlib.Path = "log.csv"
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
    """extends ConfigShell with validators only. 
    this creates opinionated relationships between the variables that dont necessarily have to exist.
    
    A likely way that this would need extending is to generate fpth_outputs based on other fields here. 
    This is very application specific, but could be done like this:
    
    Example:
        ::
        
            class LineGraphConfigShell(DefaultConfigShell):
                @validator("fpths_outputs", always=True)
                def _fpths_outputs(cls, v, values):
                    fdir = values['fdir_appdata']
                    nm = values['process_name']
                    paths = [fdir / ('output-'+nm+'.csv'), fdir / ('out-' + nm + '.plotly.json')]
                    return paths
    """

    @validator("fpth_script")
    def validate_fpth_script(cls, v):
        assert " " not in str(v.stem), "must be alphanumeric"
        return v

    @validator("process_name", always=True)
    def _process_name(cls, v, values):
        if v is None:
            return values["fpth_script"].stem.replace("script_", "")
        else:
            if " " in v:
                raise ValueError("the process_name must not contain any spaces")
            return v

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return (
                str(values["index"]).zfill(2)
                + " - "
                + stringcase.titlecase(values["process_name"])
            )
        else:
            return v

    @validator("key", always=True)
    def _key(cls, v, values):
        if v is None:
            return str(values["index"]).zfill(2) + "-" + values["process_name"]
        else:
            return v

    @validator("fdir_appdata", always=True)
    def _fdir_appdata(cls, v, values):
        if v is None:
            v = values["fpth_script"].parent  # put next to script
        else:
            if v.stem == values["key"]:  # folder with key name alread exists
                return v
            else:  # create a folder with key name for run
                v = v / values["key"]
                v.mkdir(exist_ok=True)
        return v

    @validator("fpths_inputs", always=True)
    def _fpths_inputs(cls, v, values):
        if v is None:
            v = []
            if values["displayfile_definitions"] is not None:
                ddfs = [
                    v_
                    for v_ in values["displayfile_definitions"]
                    if v_.ftype.value == "in"
                ]
                paths = [
                    values["fdir_appdata"] / ("in-" + values["key"] + ddf.ext)
                    for ddf in ddfs
                ]  # +str(values['index']).zfill(2)+'-'
                for ddf, path in zip(ddfs, paths):
                    if not path.is_file():
                        create_pydantic_json_file(ddf, path)
                v = paths
        assert type(v) == list, "type(v)!=list"
        return v

    @validator("fpths_outputs", always=True)
    def _fpths_outputs(cls, v, values):
        if v is None:
            v = []
        return v

    @validator("fpth_config", always=True)
    def _fpth_config(cls, v, values):
        return values["fdir_appdata"] / v

    @validator("fpth_runhistory", always=True)
    def _fpth_runhistory(cls, v, values):
        return values["fdir_appdata"] / v

    @validator("params", always=True)
    def _params(cls, v, values):
        if values["fpth_params"] is not None:
            with open(values["fpth_params"], "r") as f:
                v = json.load(f)
        return v

    @validator("shell", always=True)
    def _shell(cls, v, values):
        return Template(values["shell_template"]).render(**values)


# +
def check(config: ConfigShell, fn_saveconfig):
    config.in_batch = True
    fn_saveconfig()


def uncheck(config: ConfigShell, fn_saveconfig):
    config.in_batch = False
    fn_saveconfig()


def show_files(fpths, class_displayfiles=DisplayFiles, kwargs_displayfiles={}):
    return class_displayfiles([f for f in fpths], **kwargs_displayfiles)


def update_status(app, fn_saveconfig):
    if app is None:
        print("update status requires an app object to update the UI")
    print(type(app))
    st = app.actions.get_status()
    app.status = st #.ui
    app.config.status = st
    fn_saveconfig()


def update_DisplayFiles(config, fn_onsave=None):
    user_file_renderers = {}
    for d in config.displayfile_definitions:
        user_file_renderers.update(create_displayfile_renderer(d, fn_onsave=fn_onsave))
    return functools.partial(DisplayFiles, user_file_renderers=user_file_renderers)


def run_shell(app=None):
    """
    app=None
    """
    if app.config.update_config_at_runtime:
        app.config = (
            app.config
        )  #  this updates config and remakes run actions. useful if, for example, output fpths dependent on contents of input files
    print(f'run { app.config.key}')
    if app.status == "up_to_date":
        print(f"already up-to-date")
        #clear_output()
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


class RunShellActions(RunActions):
    """extends RunActions by creating Callables based on data within the app or the config objects"""
    config: DefaultConfigShell = None  # not a config type is defined - get pydantic to validate it

    @validator("save_config", always=True)
    def _save_config(cls, v, values):
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
            DisplayFiles, [values["config"].fpth_script], auto_open=True
        )

    @validator("help_config_show", always=True)
    def _help_config_show(cls, v, values):
        return functools.partial(display_pydantic_json, values["config"], as_yaml=True)

    @validator("inputs_show", always=True)
    def _inputs_show(cls, v, values):
        if values["config"] is not None:
            DisplayFilesInputs = update_DisplayFiles(values["config"], fn_onsave=values['update_status'])
            return functools.partial(
                DisplayFilesInputs,
                values["config"].fpths_inputs,
                **values["config"].displayfile_inputs_kwargs,
            )
        else:
            return None

    @validator("outputs_show", always=True)
    def _outputs_show(cls, v, values):
        if values["config"] is not None and values["app"] is not None:
            DisplayFilesOutputs = update_DisplayFiles(values["config"])#, values["app"]
            return functools.partial(
                DisplayFilesOutputs,
                values["config"].fpths_outputs,
                **values["config"].displayfile_outputs_kwargs,
            )
        else:
            return None

    @validator("run", always=True)
    def _run(cls, v, values):
        return functools.partial(run_shell, app=values["app"])


# -
if __name__ == "__main__":
    from ipyrun.constants import FPTH_EXAMPLE_SCRIPT, load_test_constants

    test_constants = load_test_constants()
    config = DefaultConfigShell(
        fpth_script=FPTH_EXAMPLE_SCRIPT, fdir_appdata=test_constants.FDIR_APPDATA
    )
    display(config.dict())

if __name__ == "__main__":

    # example run app

    from ipyrun.constants import (
        FPTH_EXAMPLE_SCRIPT,
        FPTH_EXAMPLE_INPUTSCHEMA,
        load_test_constants,
    )

    class LineGraphConfigShell(DefaultConfigShell):
        @validator("fpths_outputs", always=True)
        def _fpths_outputs(cls, v, values):
            fdir = values["fdir_appdata"]
            nm = values["process_name"]
            paths = [
                fdir / ("output-" + nm + ".csv"),
                fdir / ("out-" + nm + ".plotly.json"),
            ]
            return paths

    LineGraphConfigShell = functools.partial(
        LineGraphConfigShell,
        fpth_script=FPTH_EXAMPLE_SCRIPT,
        displayfile_definitions=[
            DisplayfileDefinition(
                path=FPTH_EXAMPLE_INPUTSCHEMA,
                obj_name="LineGraph",
                ext=".lg.json",
                ftype=FiletypeEnum.input,
            )
        ],
    )

    config = LineGraphConfigShell(fdir_appdata=test_constants.FDIR_APPDATA)
    run_app = RunApp(config, cls_actions=RunShellActions) #cls_ui=RunUi, 
    display(run_app)


class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    fpth_config: pathlib.Path = Field(
        default=FNM_CONFIG_FILE, description="name of config file for batch app"
    )
    title: str = Field(default="", description="markdown description of BatchApp")
    cls_ui: Callable = Field(
        default=RunUi,
        description="the class that defines the RunUi widget container",
        exclude=True,
    )
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

    @validator("fpth_config", always=True, pre=True)
    def _fpth_config(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return values["fdir_root"] / v

    @validator("cls_app", always=True, pre=True)
    def _cls_app(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return functools.partial(
            v, cls_ui=values["cls_ui"], cls_actions=values["cls_actions"]
        )

    @validator("configs", always=True)
    def _configs(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return [values["cls_config"](**v_) for v_ in v]


if __name__ == "__main__":
    from ipyrun.constants import load_test_constants

    test_constants = load_test_constants()
    config_batch = ConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        cls_config=ConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    from devtools import debug

    debug(config_batch)

# +


def fn_add(app, **kwargs):
    cls_config = app.config.cls_config
    if "index" not in kwargs:
        kwargs["index"] = app.config.configs[-1].index + 1
    kwargs["fdir_appdata"] = app.config.fdir_root
    config = cls_config(**kwargs)
    app.configs_append(config)
    app.ui.add.value = False


def fn_add_show(app):
    app.ui.actions.add()


def fn_add_hide(app):
    return "add hide"


def fn_remove(app=None, key=None):
    if key is None:
        print("key is None")
        key = app.runs.iterable[-1].key
    fdir = [i.fdir_appdata for i in app.config.configs if i.key == key][0]
    app.configs_remove(key)
    shutil.rmtree(fdir)


def fn_remove_show(app=None):
    app.runs.add_remove_controls = "remove_only"
    return widgets.HTML(
        markdown("# 🗑️ select runs below to delete 🗑️")
    )  # RemoveRun(app=app)


def fn_remove_hide(app=None):
    app.runs.add_remove_controls = None


def check_batch(app, fn_saveconfig, bool_=True):
    [setattr(v.ui.check, "value", bool_) for k, v in app.runs.items.items()]
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


class BatchShellActions(BatchActions):
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


# -

if __name__ == "__main__":
    from ipyrun.constants import load_test_constants

    test_constants = load_test_constants()

    class LineGraphConfigBatch(ConfigBatch):
        @validator("cls_config", always=True)
        def _cls_config(cls, v, values):
            """bundles RunApp up as a single argument callable"""
            return LineGraphConfigShell

    config_batch = LineGraphConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        # cls_config=MyConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    if config_batch.fpth_config.is_file():
        config_batch = LineGraphConfigBatch.parse_file(config_batch.fpth_config)
    app = BatchApp(config_batch, cls_actions=BatchShellActions)
    display(app)
