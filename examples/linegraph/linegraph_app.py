# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Linegraph - tutorial App

# +
import sys
import pathlib

sys.path.append(str(pathlib.Path('../../src').resolve())) # append ipyrun. TODO: for dev only. remove at build time.
#sys.path.append(str(pathlib.Path('../../../ipyautoui/src').resolve())) # append ipyautoui. TODO: for dev only. remove at build time.

import subprocess
from pydantic import validator

from ipyrun import RunApp, BatchApp, ConfigShell, DefaultConfigShell, RunShellActions 
from ipyrun.runshell import DisplayfileDefinition, create_displayfile_renderer, ConfigBatch, DefaultConfigShell, DefaultBatchActions, BatchShellActions

from ipyautoui import AutoUi, AutoUiConfig
from ipyautoui import DisplayFiles
from ipyautoui.displayfile import display_python_file

DIR_CORE = pathlib.Path('./linegraph_core').resolve()
FPTH_SCRIPT = DIR_CORE / 'script_linegraph.py'
FPTH_INPUTS_SCHEMA = DIR_CORE / 'input_schema_linegraph.py'
DIR_APPDATA = pathlib.Path('./linegraph_appdata').resolve()

# extend DefaultConfigShell to LineGraphConfigShell

class LineGraphConfigShell(DefaultConfigShell):
    @validator("fpth_script", always=True, pre=True)
    def _set_fpth_script(cls, v, values):
        return FPTH_SCRIPT

    @validator("fpths_outputs", always=True)
    def _fpths_outputs(cls, v, values):
        fdir = values["fdir_appdata"]
        key = values["key"]
        paths = [
            fdir / ("out-" + key + ".csv"),
            fdir / ("out-" + key + ".plotly.json"),
        ]
        return paths

    @validator("displayfile_definitions", always=True)
    def _displayfile_definitions(cls, v, values):
        return [
            DisplayfileDefinition(
                path=FPTH_INPUTS_SCHEMA,
                obj_name="LineGraph",
                ext=".lg.json",
                ftype='in',
            )
        ]

    @validator("displayfile_inputs_kwargs", always=True)
    def _displayfile_inputs_kwargs(cls, v, values):
        return dict(patterns="*")

    @validator("displayfile_outputs_kwargs", always=True)
    def _displayfile_outputs_kwargs(cls, v, values):
        return dict(patterns="*.plotly.json")
    
    
# extend ConfigBatch to LineGraphConfigBatch
    
class LineGraphConfigBatch(ConfigBatch):
    @validator("cls_config", always=True)
    def _cls_config(cls, v, values):
        """bundles RunApp up as a single argument callable"""
        return LineGraphConfigShell

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

config_batch = LineGraphConfigBatch(
    fdir_root=DIR_APPDATA,
    # cls_config=MyConfigShell,
    title="""# Plot Straight Lines\n### example RunApp""",
)
if config_batch.fpth_config.is_file():
    config_batch = LineGraphConfigBatch.parse_file(config_batch.fpth_config)
app = BatchApp(config_batch, cls_actions=LineGraphBatchActions)
display(app)

# -


