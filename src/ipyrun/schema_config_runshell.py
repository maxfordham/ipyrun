# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:light
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

# +
# %run __init__.py
# %load_ext lab_black

import pathlib
import functools
# object models
from typing import Optional, List, Dict, Type, Callable, Any
from pydantic.dataclasses import dataclass
from pydantic import validator, Field
from enum import Enum, IntEnum
from ipyrun.constants import FNM_CONFIG_FILE
from jinja2 import Template
import importlib.util
from ipyautoui import AutoUi, DisplayFiles, AutoUiConfig
from ipyautoui._utils import file
from ipyautoui.basemodel import BaseModel
import stringcase


# -

class FiletypeEnum(str, Enum):
    input = "in"
    output = "out"
    wip = "wip"

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
    ftype: FiletypeEnum = None
    ext: str

def _get_PyObj(obj: PyObj):
    spec = importlib.util.spec_from_file_location(obj.module_name, obj.path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return getattr(foo, obj.obj_name)

def create_pydantic_json_file(pyobj: PyObj, path: pathlib.Path):
    obj = _get_PyObj(pyobj)
    assert str(type(obj)) == "<class 'pydantic.main.ModelMetaclass'>", "the python object must be a pydantic model"
    if not hasattr(obj, "file"):
        setattr(obj, 'file', file) 
    assert hasattr(obj, "file"), "the pydantic BaseModel must be extended to have method 'file' for writing model to json"
    myobj = obj()
    myobj.file(path)
    return path

def create_displayfile_renderer(ddf: DisplayfileDefinition, fn_onsave: Callable = lambda: None):
    model = _get_PyObj(ddf)
    config_ui = AutoUiConfig(ext=ddf.ext, pydantic_model=model)
    return AutoUi.create_displayfile_renderer(config_autoui=config_ui, fn_onsave=fn_onsave)

class ConfigActionsShell(BaseModel):
    """a config object. all the definitions required to create the RunActions for a shell running tools are here.
    it is anticipated that this class will be inherited and validators added to create application specific relationships between variables."""
    index: int = 0
    fpth_script: pathlib.Path
    process_name: str = None
    pretty_name: str = None
    key: str = None
    fdir_appdata: pathlib.Path = Field(default=None, description='working dir for process execution. defaults to script folder if folder not given.')
    in_batch: bool = True
    status: str = None
    update_config_at_runtime: bool = Field(
        default=False, 
        description='updates config before running shell command. useful if for example outputs filepaths defined within the input filepaths')
    displayfile_definitions: List[DisplayfileDefinition] = Field(default=None, description='autoui definitions for displaying files. see ipyautui')
    displayfile_inputs_kwargs: Dict = Field(default_factory=lambda:{})
    displayfile_outputs_kwargs: Dict = Field(default_factory=lambda:{})
    fpths_inputs: Optional[List[pathlib.Path]] = None
    fpths_outputs: Optional[List[pathlib.Path]] = None
    fpth_config: pathlib.Path = Field(FNM_CONFIG_FILE, description=f"there is a single unique folder and config file for each RunApp. the config filename is fixed as {FNM_CONFIG_FILE}")
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



class DefaultConfigActionsShell(ConfigActionsShell):
    """extends ConfigActionsShell with validators only. this creates opinionated relationships between the variables that 
    dont necessarily have to exist."""

    @validator('fpth_script')
    def validate_fpth_script(cls, v):
        assert " " not in str(v.stem), 'must be alphanumeric'
        return v

    @validator("process_name", always=True)
    def _process_name(cls, v, values):
        if v is None:
            return values["fpth_script"].stem.replace('script_','')
        else:
            if " " in v:
                raise ValueError('the process_name must not contain any spaces')
            return v

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return str(values["index"]).zfill(2) + " - " + stringcase.titlecase(values["process_name"])
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
            v = values["fpth_script"].parent
        else:
            v = v / values["key"]
            v.mkdir()
        return v

    @validator("fpths_inputs", always=True)
    def _fpths_inputs(cls, v, values):
        if v is None:
            v = []
            if values['displayfile_definitions'] is not None:
                ddfs = [v_ for v_ in values['displayfile_definitions'] if v_.ftype.value == 'in']
                paths = [values['fdir_appdata'] / ('in-'+values['key']+ddf.ext) for ddf in ddfs] #+str(values['index']).zfill(2)+'-'
                for ddf, path in zip(ddfs, paths):
                    if not path.is_file():
                        create_pydantic_json_file(ddf, path)
                v = paths
        assert type(v)==list, 'type(v)!=list'
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

    @validator("shell", always=True)
    def _shell(cls, v, values):
        #pprint(values)
        return Template(values["shell_template"]).render(**values)


if __name__ == "__main__":
    config = DefaultConfigActionsShell(fpth_script='my_script.py')
    display(config.dict())

if __name__ == "__main__":
    from ipyrun.constants import load_test_constants
    test_constants = load_test_constants()
    config = DefaultConfigActionsShell(fpth_script='my_script.py', fdir_appdata=test_constants.DIR_EXAMPLE_PROCESS.parent / 'test_dir')
    display(config.dict())
    config1 = DefaultConfigActionsShell(fpth_script='my_script.py', fdir_appdata=test_constants.DIR_EXAMPLE_PROCESS.parent / 'test_dir', index=1)
    display(config1.dict())
