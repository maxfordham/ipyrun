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
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""
A configuration of the ipyrun App for running shell commands scripts. 
By default it is used for running python scripts on the command line.
"""
# %run _dev_sys_path_append.py
# %run __init__.py
# %load_ext lab_black

if __name__ == "__main__":
    FDIR_TEST_EXAMPLES = (
        pathlib.Path("__init__.py").absolute().parent.parent.parent
        / "tests"
        / "examples"
    )
    FDIR_APPDATA = FDIR_TEST_EXAMPLES / "fdir_appdata"

# +
# core libs
import os
import sys
import io
import typing as ty
import shutil
import pathlib
import functools
import subprocess
import stringcase
from jinja2 import Template
from markdown import markdown
import json
import logging
import importlib

# object models
from pydantic import (
    validator,
    Field,
    field_validator,
    ValidationInfo,
    ValidationError,
    BaseModel,
    ConfigDict,
)
from typing import Optional, List, Dict, Type, Callable, Union
from enum import Enum

# widget stuff
from IPython.display import Markdown, clear_output, display
import ipywidgets as widgets
from halo import HaloNotebook

from ipyautoui import AutoUi, AutoDisplay
from ipyautoui._utils import (
    display_pydantic_json,
    check_installed,
    open_path,
    # get_user
)

# ---------------------------------------------------
# load pydantic object:
# TODO: update this!!!
# ---------------------------------------------------
from ipyrun.basemodel import file


class SerializableCallable(BaseModel):  # NOT IN USE
    callable_str: ty.Union[ty.Callable, str] = Field(
        ...,
        validate_default=True,
        description="import string that can use importlib\
                    to create a python obj. Note. if a Callable object\
                    is given it will be converted into a string",
    )
    callable_obj: ty.Union[ty.Callable, ty.Type] = Field(
        None, exclude=True, validate_default=True
    )

    @field_validator("callable_str")
    def _callable_str(cls, v):
        if type(v) != str:
            return obj_to_importstr(v)
        invalid = [i for i in "!@#£[]()<>|¬$%^&*,?''- "]
        for i in invalid:
            if i in v:
                raise ValueError(
                    f"callable_str = {v}. import_str must not contain spaces {i}"
                )
        return v

    @field_validator("callable_obj")
    def _callable_obj(cls, v, info: ValidationInfo):
        return obj_from_importstr(info.data["callable_str"])


class PyObj(BaseModel):
    """a definition of a python object"""

    path: pathlib.Path
    obj_name: str
    module_name: ty.Optional[str] = Field(
        None,
        description="ignore, this is overwritten by a validator",
        validate_default=True,
    )

    @field_validator("module_name")
    def _module_name(cls, v, info: ValidationInfo):
        return info.data["path"].stem


def load_PyObj(obj: PyObj):
    submodule_search_locations = None
    p = obj.path
    if obj.path.is_dir():
        p = p / "__main__.py"
        submodule_search_locations = []
    spec = importlib.util.spec_from_file_location(
        obj.module_name, p, submodule_search_locations=submodule_search_locations
    )
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return getattr(foo, obj.obj_name)


def create_pydantic_json_file(
    pyobj: ty.Union[str, PyObj], path: pathlib.Path, **kwargs
):
    """
    loads a pyobj (which must be a pydantic model) and then saves the default Json to file.
    this requires defaults for all pydantic attributes.

    Todo:
        could extend the functionality to cover models that don't have defaults
        using [pydantic-factories](https://github.com/Goldziher/pydantic-factories)

    Args:
        pyobj (SerializableCallable): definition of where to get a pydantic model
        path (pathlib.Path): where to save the pydantic json
        **kwargs : passed to the pydantic model upon initiation

    Returns:
        path
    """
    if type(pyobj) == str:
        obj = SerializableCallable(pyobj).callable_obj
    else:
        obj = load_PyObj(pyobj)
    assert "ModelMetaclass" in str(
        type(obj)
    ), "the python object must be a pydantic model"
    file(obj(), path)
    return path


# ---------------------------------------------------
# ---------------------------------------------------

# from this repo
from ipyrun.runui import RunApp, BatchApp
from ipyrun.constants import BUTTON_WIDTH_MIN
from ipyrun.actions import (
    # RunActions,
    # BatchActions,
    DefaultRunActions,
    DefaultBatchActions,
)
from ipyrun.basemodel import BaseModel
from ipyrun._utils import get_status
from ipyrun.constants import (
    PATH_CONFIG,
    PATH_RUNHISTORY,
    PATH_LOG,
    FPTH_EXAMPLE_INPUTSCHEMA,
    DI_STATUS_MAP,
)

if check_installed("mf_file_utilities"):
    from mf_file_utilities.applauncher_wrapper import get_fpth_win
else:
    get_fpth_win = lambda v: v


def wrapped_partial(func, *args, **kwargs):
    # http://louistiao.me/posts/adding-__name__-and-__doc__-attributes-to-functoolspartial-objects/
    partial_func = functools.partial(func, *args, **kwargs)
    functools.update_wrapper(partial_func, func)
    return partial_func


# +
class FiletypeEnum(str, Enum):
    input = "in"
    output = "out"
    wip = "wip"


# class JsonablePyObject(BaseModel):
#     """a definition of a python object"""
#     pyobject: str
#     object: ty.Callable = Field(None, exclude=True)
#     @field_validator("object")
#     def _object(cls, v, info: ValidationInfo):
#         return obj_from_importstr(info.data["pyobject"])


# TODO:
# if we make a rule that is the input schema must be imported into `path_run`
# then all we need is the class name (e.g. InputSchema) and we can import the
# object from path_run
class AutoDisplayDefinition(PyObj):
    ftype: FiletypeEnum = Field(
        None, description='valid inputs are: "in", "out", "wip"'
    )
    ext: str


from ipyautoui.autoui import get_autodisplay_map


def create_autodisplay_map(ddf: AutoDisplayDefinition, **kwargs):
    model = load_PyObj(ddf)
    kwargs = kwargs | dict(show_savebuttonbar=True)
    return get_autodisplay_map(schema=model, ext=ddf.ext, **kwargs)


# class BaseConfigShell(BaseModel):
#     fdir_root: pathlib.Path = Field(
#         default=None,
#         description=(
#             "root folder. same as fdir_root within batch config."
#             " facilitates running many processes. this is the working dir."
#         ),
#     )
#     fpths_inputs: Optional[List[pathlib.Path]] = None
#     fpths_outputs: Optional[List[pathlib.Path]] = None
#     path_run: pathlib.Path = pathlib.Path("script.py")
#     pythonpath: pathlib.Path = None
#     run: str = None
#     call: str = "python -O"
#     params: Dict = {}
#     shell_template: str = """\
# {{ call }} {{ run }}\
# {% for f in fpths_inputs %} {{f}}{% endfor %}\
# {% for f in fpths_outputs %} {{f}}{% endfor %}\
# {% for k,v in params.items()%} --{{k}} {{v}}{% endfor %}
# """
#     shell: str = ""


class ConfigShell(BaseModel):

    """a config object. all the definitions required to create the RunActions for a shell running tools are here.
    it is anticipated that this class will be inherited and validators added to create application specific relationships between variables.
    """

    index: int = 0
    path_run: pathlib.Path = "script.py"
    pythonpath: ty.Optional[pathlib.Path] = None
    run: ty.Optional[str] = None
    name: ty.Optional[str] = None
    long_name: ty.Optional[str] = None
    key: ty.Optional[str] = None
    fdir_root: ty.Optional[pathlib.Path] = Field(
        default=None,
        description=(
            "root folder. same as fdir_root within batch config."
            " facilitates running many processes. this is the working dir."
        ),
    )
    fdir_appdata: ty.Optional[pathlib.Path] = Field(default=None)
    in_batch: bool = False
    status: ty.Optional[str] = None
    update_config_at_runtime: bool = Field(
        default=False,
        description=(
            "updates config before running shell command. useful if for example outputs"
            " filepaths defined within the input filepaths"
        ),
    )
    autodisplay_definitions: List[AutoDisplayDefinition] = Field(
        default_factory=list,
        description="autoui definitions for displaying files. see ipyautoui",
        validate_default=True,
    )
    autodisplay_inputs_kwargs: Dict = Field(default_factory=dict)
    autodisplay_outputs_kwargs: Dict = Field(default_factory=dict)
    fpths_inputs: Optional[List[pathlib.Path]] = None
    fpths_outputs: Optional[List[pathlib.Path]] = None
    fpth_params: ty.Optional[pathlib.Path] = None
    fpth_config: ty.Optional[pathlib.Path] = Field(
        None,
        description=(
            "there is a single unique folder and config file for each RunApp."
            f" the config filename is fixed as {str(PATH_CONFIG)}"
        ),
        # const=True
    )
    fpth_runhistory: pathlib.Path = Field(PATH_RUNHISTORY)  # ,const=True
    fpth_log: ty.Optional[pathlib.Path] = Field(None)  # ,const=True
    call: str = Field("python -O", validate_default=True)
    params: Dict = {}
    shell_template: str = """\
{{ call }} {{ run }}\
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
        path_run (pathlib.Path):
        fdir_root (pathlib.Path): defaults to cwd
        autodisplay_definitions (List[AutoDisplayDefinition]): used to generate custom input and output forms
            using ipyautoui

    Example:
        ::

            class LineGraphConfigShell(DefaultConfigShell):
                # script specific outputs defined by custom ConfigShell class
                @field_validator("fpths_outputs")
                def _fpths_outputs(cls, v, info: ValidationInfo):
                    fdir = info.data['fdir_appdata']
                    nm = info.data['name']
                    paths = [fdir / ('out-'+nm+'.csv'), fdir / ('out-' + nm + '.plotly.json')]
                    return paths
    """

    model_config = ConfigDict(validate_default=True)

    @field_validator("status")
    @classmethod
    def _status(cls, v):
        li = list(DI_STATUS_MAP.keys()) + [None]
        if v not in li:
            ValidationError(f"status must be in {str(li)}")
        return v

    @field_validator("path_run")
    def validate_path_run(cls, v):
        assert " " not in str(v.stem), "must be alphanumeric"
        return v

    @field_validator("pythonpath")
    def _pythonpath(cls, v, info: ValidationInfo):
        # then we are executing a package rather than a script
        # so we need to add the package to the PYTHONPATH
        # TODO: Tasks pending completion -@jovyan at 9/29/2022, 9:31:39 AM
        #       this should append the parent to allow users to also specify
        #       a PYTHONPATH
        v = info.data["path_run"].parent
        return v

    @field_validator("run")
    def _run(cls, v, info: ValidationInfo):
        prun = pathlib.Path(info.data["path_run"])
        if prun.is_dir() or prun.is_file():
            # then we are executing a package rather than a script
            # and we just assigned the PYTHONPATH
            # so no we remove the parent to create the shell cmd
            v = prun.stem
        else:
            raise ValidationError(
                f"{str(prun)} must be python package dir or python script"
            )
        return v

    @field_validator("name")
    def _name(cls, v, info: ValidationInfo):
        if v is None:
            return info.data["path_run"].stem.replace("script_", "")
        else:
            if " " in v:
                raise ValidationError("the name must not contain any spaces")
            return v

    @field_validator("long_name")
    def _long_name(cls, v, info: ValidationInfo):
        if v is None:
            return (
                str(info.data["index"]).zfill(2)
                + " - "
                + stringcase.titlecase(info.data["name"])
            )
        else:
            return v

    @field_validator("key")
    def _key(cls, v, info: ValidationInfo):
        if v is None:
            return str(info.data["index"]).zfill(2) + "-" + info.data["name"]
        else:
            return v

    @field_validator("fdir_root")
    def _fdir_root(cls, v, info: ValidationInfo):
        if v is None:
            v = pathlib.Path(".")
        os.chdir(str(v))  # TODO: this will fail if the code is run twice...?
        return v
        # TODO: Tasks pending completion -@jovyan at 9/29/2022, 11:51:24 AM
        #       rename to `cwd`

    @field_validator("fdir_appdata")
    def _fdir_appdata(cls, v, info: ValidationInfo):
        v = info.data["fdir_root"] / info.data["key"]
        v.mkdir(exist_ok=True)
        return pathlib.Path(info.data["key"])

    @field_validator("fpths_inputs")
    def _fpths_inputs(cls, v, info: ValidationInfo):
        if v is None:
            v = []
            if info.data["autodisplay_definitions"] is not None:
                ddfs = [
                    v_
                    for v_ in info.data["autodisplay_definitions"]
                    if v_.ftype.value == "in"
                ]
                paths = [
                    info.data["fdir_root"]
                    / info.data["fdir_appdata"]
                    / ("in-" + info.data["key"] + ddf.ext)
                    for ddf in ddfs
                ]
                for ddf, path in zip(ddfs, paths):
                    if not path.is_file():
                        create_pydantic_json_file(ddf, path)  # TODO: remove from here?
                v = [p.relative_to(info.data["fdir_root"]) for p in paths]

            # ^ NOTE: while generic-ish, this code is probs not generic enough to be in the
            #   root default definition
        assert type(v) == list, "type(v) != list"
        return v

    @field_validator("fpths_outputs")
    def _fpths_outputs(cls, v, info: ValidationInfo):
        if v is None:
            v = []
        return v

    @field_validator("fpth_config")
    def _fpth_config(cls, v, info: ValidationInfo):
        v = info.data["fdir_root"] / info.data["fdir_appdata"] / PATH_CONFIG
        return v.relative_to(info.data["fdir_root"])

    @field_validator("fpth_runhistory")
    def _fpth_runhistory(cls, v, info: ValidationInfo):
        v = info.data["fdir_root"] / info.data["fdir_appdata"] / PATH_RUNHISTORY
        return v.relative_to(info.data["fdir_root"])

    @field_validator("fpth_log")
    def _fpth_log(cls, v, info: ValidationInfo):
        v = info.data["fdir_root"] / info.data["fdir_appdata"] / PATH_LOG
        return v.relative_to(info.data["fdir_root"])

    @field_validator("params")
    def _params(cls, v, info: ValidationInfo):
        if info.data["fpth_params"] is not None:
            with open(info.data["fpth_params"], "r") as f:
                v = json.load(f)
        return v

    @field_validator("call")
    def _call(cls, v, info: ValidationInfo):
        if "-m" not in str(v):
            v = v + " -m"
        if "python " in v and "/python " not in v:
            import sys

            v = v.replace("python ", f"{sys.executable} ")
        return v

    @field_validator("shell")
    def _shell(cls, v, info: ValidationInfo):
        return Template(info.data["shell_template"]).render(**info.data)


def udpate_env(append_to_pythonpath: str):
    env = os.environ.copy()
    if not "PYTHONPATH" in env.keys():
        env["PYTHONPATH"] = str(append_to_pythonpath)
    else:
        env["PYTHONPATH"] = (
            env["PYTHONPATH"] + f"{os.pathsep}{str(append_to_pythonpath)}"
        )
    return env


def run(config: Type[ConfigShell]):
    save = sys.stdout
    sys.stdout = io.StringIO()
    env = udpate_env(config.pythonpath)
    proc = subprocess.check_output(config.shell, env=env, shell=True)
    in_stdout = sys.stdout.getvalue()
    sys.stdout = save
    return proc


if __name__ == "__main__":
    from ipyrun.constants import FPTH_EXAMPLE_RUN

    config = DefaultConfigShell(path_run=FPTH_EXAMPLE_RUN, fdir_root=FDIR_APPDATA)
    display(config.model_dump())


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
    logging.info("update_status")
    if app is None:
        print("update status requires an app object to update the UI")
    st = app.actions.get_status()
    app.status = st  # .ui
    app.config.status = st
    fn_saveconfig()


def make_run_hide(fn_on_click):
    run_hide = widgets.Button(
        layout={"width": BUTTON_WIDTH_MIN},
        icon="times",
        button_style="danger",
    )
    run_hide.on_click(fn_on_click)
    return run_hide


def run_shell(app=None, display_hide_btn=True):
    """
    app=None
    """
    if app.config.update_config_at_runtime:
        app.config = app.config
        # ^  this updates config and remakes run actions using the setter.
        #    useful if, for example, output fpths dependent on contents of input files
    if display_hide_btn:
        run_hide = make_run_hide(app._run_hide)  # button to hide the run console
        display(run_hide)
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
    env = None
    if app.config.pythonpath is not None:
        env = udpate_env(app.config.pythonpath)
    try:
        spinner.start()
        save = sys.stdout
        sys.stdout = io.StringIO()
        proc = subprocess.Popen(shell, env=env)
        proc.wait()
        in_stdout = sys.stdout.getvalue()
        sys.stdout = save
        display(in_stdout)
        spinner.succeed("Finished")
    except subprocess.CalledProcessError as e:
        spinner.fail("Error with Process")
    app.actions.update_status()


class BaseShell(BaseModel):
    config: ty.Optional[ty.Type[DefaultConfigShell]] = Field(
        None,
        validate_default=True,  # not a config type is defined - get pydantic to validate it
    )


class RunShellActions(DefaultRunActions, BaseShell):
    """extends RunActions by creating Callables based on data within the app or the config objects."""

    @field_validator("renderers")
    def _renderers(cls, v, info: ValidationInfo):
        renderers = {}
        for d in info.data["config"].autodisplay_definitions:
            renderers = renderers | create_autodisplay_map(
                d, fns_onsave=[info.data["update_status"]]
            )
        return renderers

    @field_validator("hide")
    def _hide(cls, v, info: ValidationInfo):
        return None

    @field_validator("save_config")
    def _save_config(cls, v, info: ValidationInfo):
        if info.data["config"] is not None:
            return wrapped_partial(
                info.data["config"].file, info.data["config"].fpth_config
            )

    @field_validator("check")
    def _check(cls, v, info: ValidationInfo):
        return wrapped_partial(check, info.data["config"], info.data["save_config"])

    @field_validator("uncheck")
    def _uncheck(cls, v, info: ValidationInfo):
        return wrapped_partial(uncheck, info.data["config"], info.data["save_config"])

    @field_validator("get_status")
    def _get_status(cls, v, info: ValidationInfo):
        return wrapped_partial(
            get_status,
            info.data["config"].fpths_inputs,
            info.data["config"].fpths_outputs,
        )

    @field_validator("update_status")
    def _update_status(cls, v, info: ValidationInfo):
        return wrapped_partial(
            update_status, info.data["app"], info.data["save_config"]
        )

    @field_validator("help_run_show")
    def _help_run_show(cls, v, info: ValidationInfo):
        return wrapped_partial(
            AutoDisplay.from_paths, [info.data["config"].path_run], patterns="*"
        )

    @field_validator("help_config_show")
    def _help_config_show(cls, v, info: ValidationInfo):
        return wrapped_partial(
            display_pydantic_json, info.data["config"], as_yaml=False
        )

    @field_validator("inputs_show")
    def _inputs_show(cls, v, info: ValidationInfo):
        if info.data["config"] is not None:
            if info.data["update_status"].__name__ != "update_status":
                raise ValidationError("update_status error")
            paths = [f for f in info.data["config"].fpths_inputs]
            return wrapped_partial(
                AutoDisplay.from_paths,
                paths,
                renderers=info.data["renderers"],
                **info.data["config"].autodisplay_inputs_kwargs,
            )
        else:
            return None

    @field_validator("outputs_show")
    def _outputs_show(cls, v, info: ValidationInfo):
        if info.data["config"] is not None and info.data["app"] is not None:
            paths = [f for f in info.data["config"].fpths_outputs]
            return wrapped_partial(
                AutoDisplay.from_paths,
                paths,
                renderers=info.data["renderers"],
                **info.data["config"].autodisplay_inputs_kwargs,
            )
        else:
            return None

    @field_validator("run")
    def _run(cls, v, info: ValidationInfo):
        return wrapped_partial(run_shell, app=info.data["app"])

    @field_validator("runlog_show")
    def _runlog_show(cls, v, info: ValidationInfo):
        return None  # TODO: add logging!

    @field_validator("load_show")
    def _load_show(cls, v, info: ValidationInfo):
        return None


# extend RunApp to make a default RunShell
# -
if __name__ == "__main__":
    from ipyrun.constants import FPTH_EXAMPLE_RUN

    config = DefaultConfigShell(path_run=FPTH_EXAMPLE_RUN, fdir_root=FDIR_APPDATA)
    display(config.model_dump())

if __name__ == "__main__":
    config = DefaultConfigShell(path_run=FPTH_EXAMPLE_RUN, fdir_root=FDIR_APPDATA)
    actions = RunShellActions(config=config)
    display(actions)

if __name__ == "__main__":
    from ipyrun.examples.linegraph.linegraph_app import LineGraphConfigShell

    config = LineGraphConfigShell(fdir_root=FDIR_APPDATA)
    run_app = RunApp(config, cls_actions=RunShellActions)  # cls_ui=RunUi,
    display(run_app)

if __name__ == "__main__":
    pr = run(config)


class ConfigBatch(BaseModel):
    fdir_root: pathlib.Path
    fpth_config: pathlib.Path = Field(
        default=PATH_CONFIG, description="name of config file for batch app"
    )
    title: str = Field(default="", description="markdown description of BatchApp")
    status: ty.Optional[str] = None
    cls_actions: Callable = Field(
        default=RunShellActions,
        description=(
            "the class that defines the RunActions (extended with validators based on"
            " use case)"
        ),
        exclude=True,
        validate_default=True,
    )
    cls_app: Union[Type, Callable] = Field(
        default=RunApp,
        description="the class that defines the RunApp.",
        exclude=True,
        validate_default=True,
    )
    cls_config: Union[Type, Callable] = Field(
        default=DefaultConfigShell,
        description=(
            "the class that defines the config of a RunApp. this has can have path_run"
            " baked in"
        ),
        exclude=True,
        validate_default=True,
    )
    configs: List = []
    # runs: List[Callable] = Field(default=lambda: [], description="a list of RunApps", exclude=True)

    # @field_validator("fpth_config")
    # def _fpth_config(cls, v, info: ValidationInfo):
    #     """bundles RunApp up as a single argument callable"""
    #     return info.data["fdir_root"] / v

    @field_validator("fdir_root")
    def _fdir_root(cls, v, info: ValidationInfo):
        if v is None:
            v = pathlib.Path(".")
        os.chdir(str(v))  # TODO: this will fail if the code is run twice...?
        return v

    @field_validator("cls_app")
    def _cls_app(cls, v, info: ValidationInfo):
        """bundles RunApp up as a single argument callable"""
        return wrapped_partial(
            v, cls_actions=info.data["cls_actions"]  # cls_ui=info.data["cls_ui"],
        )

    @field_validator("configs")
    def _configs(cls, v, info: ValidationInfo):
        """bundles RunApp up as a single argument callable"""
        return [info.data["cls_config"](**v_) for v_ in v]

    @field_validator("status")
    def _status(cls, v, info: ValidationInfo):
        li = list(DI_STATUS_MAP.keys()) + [None]
        if v not in li:
            ValidationError(f"status must be in {str(li)}")
        return v


if __name__ == "__main__":
    DIR_EXAMPLE_BATCH = FDIR_TEST_EXAMPLES / "line_graph_batch"
    config_batch = ConfigBatch(
        fdir_root=DIR_EXAMPLE_BATCH,
        cls_config=ConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    display(config_batch.model_dump())


# +
def fn_add(app, **kwargs):
    cls_config = app.config.cls_config
    if "index" not in kwargs:
        if len(app.config.configs) == 0:
            kwargs["index"] = 0
        else:
            kwargs["index"] = app.config.configs[-1].index + 1
    kwargs["fdir_root"] = app.config.fdir_root
    print(kwargs)
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


def fn_remove(arg, app=None):
    key = arg.key
    if key is None:
        print("key is None")
        key = app.runs.iterable[-1].key
    fdir = [i.fdir_appdata for i in app.config.configs if i.key == key][0]
    app.configs_remove(key)
    app.watch_run_statuses()
    app.actions.update_status()
    shutil.rmtree(fdir)


def fn_remove_show(app=None):
    app.runs.add_remove_controls = "remove_only"
    return widgets.HTML(markdown("### 🗑️ select runs below to delete 🗑️"))


def fn_remove_hide(app=None):
    app.runs.add_remove_controls = "none"


def check_batch(app, fn_saveconfig, bool_=True):
    [setattr(v.check, "value", bool_) for k, v in app.di_runs.items()]
    [setattr(c, "in_batch", bool_) for c in app.config.configs]
    fn_saveconfig()


def run_batch(app=None):
    run_hide = make_run_hide(app._run_hide)  # button to hide the run console
    display(run_hide)
    # TODO: add remove run button
    sel = {c.key: c.in_batch for c in app.config.configs}
    if True not in sel.values():
        print("no runs selected")
    else:
        print("run the following:")
        [print(k) for k, v in sel.items() if v is True]
    [
        v.run() for v in app.run_actions if v.config.in_batch  # display_hide_btn=False
    ]  # TODO add "hide_button" arg


def batch_get_status(app=None):
    st = [a.get_status() for a in app.run_actions]
    if st is None:
        st = "error"
    if len(st) == 0:
        bst = "no_outputs"
    else:
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
        config_batch = cl(**json.loads(config_batch.fpth_config.read_text()))
    print("loading")
    app.config = config_batch
    app.loaded.value = f"{str(get_fpth_win(fdir_root))}"
    app.load.value = False


def set_loaded(app=None, value=""):
    app.loaded.value = value
    return value


def open_loaded(app=None, fdir_root=None):
    with app.out_load:
        open_path(fdir_root)
        clear_output()


class BatchShellActions(DefaultBatchActions):
    @field_validator("load")
    def _load(cls, v, info: ValidationInfo):
        fn = lambda: None
        if info.data["app"] is not None:
            cl = type(info.data["app"].config)
            fn = wrapped_partial(load_dir, app=info.data["app"])
        return fn

    @field_validator("get_loaded")
    def _get_loaded(cls, v, info: ValidationInfo):
        fn = lambda: None
        if info.data["app"] is not None and info.data["config"] is not None:
            fdir_root = info.data["config"].fdir_root
            fn = wrapped_partial(
                set_loaded,
                app=info.data["app"],
                value=f"<code>{str(get_fpth_win(fdir_root))}</code>",
            )
        return fn


    @field_validator("save_config")
    def _save_config(cls, v, info: ValidationInfo):
        return wrapped_partial(
            info.data["config"].file, info.data["config"].fpth_config
        )

    @field_validator("wizard_show")
    def _wizard_show(cls, v, info: ValidationInfo):
        return None

    @field_validator("check")
    def _check(cls, v, info: ValidationInfo):
        return wrapped_partial(
            check_batch, info.data["app"], info.data["save_config"], bool_=True
        )

    @field_validator("uncheck")
    def _uncheck(cls, v, info: ValidationInfo):
        return wrapped_partial(
            check_batch, info.data["app"], info.data["save_config"], bool_=False
        )

    @field_validator("add")
    def _add(cls, v, info: ValidationInfo):
        return wrapped_partial(fn_add, info.data["app"])

    @field_validator("add_show")
    def _add_show(cls, v, info: ValidationInfo):
        return wrapped_partial(fn_add_show, info.data["app"])

    @field_validator("add_hide")
    def _add_hide(cls, v, info: ValidationInfo):
        return wrapped_partial(fn_add_hide, info.data["app"])

    @field_validator("remove")
    def _remove(cls, v, info: ValidationInfo):
        info.data["app"].runs.fn_remove = functools.partial(
            fn_remove, app=info.data["app"]
        )
        return info.data["app"].runs.remove_row

    @field_validator("remove_show")
    def _remove_show(cls, v, info: ValidationInfo):
        return wrapped_partial(fn_remove_show, app=info.data["app"])

    @field_validator("remove_hide")
    def _remove_hide(cls, v, info: ValidationInfo):
        return wrapped_partial(fn_remove_hide, info.data["app"])

    @field_validator("help_config_show")
    def _help_config_show(cls, v, info: ValidationInfo):
        return wrapped_partial(
            display_pydantic_json, info.data["config"], as_yaml=False
        )  # TODO: revert to as_yaml=True when tested as working in Voila

    @field_validator("run")
    def _run(cls, v, info: ValidationInfo):
        return wrapped_partial(run_batch, app=info.data["app"])

    @field_validator("inputs_show")
    def _inputs_show(cls, v, info: ValidationInfo):
        return None

    @field_validator("outputs_show")
    def _outputs_show(cls, v, info: ValidationInfo):
        return None

    @field_validator("get_status")
    def _get_status(cls, v, info: ValidationInfo):
        return wrapped_partial(batch_get_status, app=info.data["app"])

    @field_validator("update_status")
    def _update_status(cls, v, info: ValidationInfo):
        return wrapped_partial(batch_update_status, app=info.data["app"])


# -

if __name__ == "__main__":
    # TODO: update example to this: https://examples.pyviz.org/attractors/attractors.html
    # TODO: configure so that the value of the RunApp is the config?
    from ipyrun.examples.linegraph.linegraph_app import (
        LineGraphConfigShell,
        LineGraphConfigBatch,
        LineGraphBatchActions,
    )

    config_batch = LineGraphConfigBatch(
        fdir_root=DIR_EXAMPLE_BATCH,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    if config_batch.fpth_config.is_file():
        config_batch = LineGraphConfigBatch(
            **json.loads(config_batch.fpth_config.read_text())
        )
    app = BatchApp(config_batch, cls_actions=LineGraphBatchActions)
    display(app)

# +

# TODO: use computed fields in the future...
# from pydantic import BaseModel, computed_field

# class My(BaseModel, validate_assignment=True):
#     fdir: pathlib.Path = pathlib.Path(".")

#     @computed_field
#     @property
#     def fdirs(self) -> pathlib.Path:
#         return [
#             f
#             for f in self.fdir.glob("*")
#             if f.is_dir() and len(list(f.glob("config-shell_handler.json"))) > 0
#         ]


# my = My()
# my
