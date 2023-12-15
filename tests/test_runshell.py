#!/usr/bin/env python

"""Tests for `ipyrun` package."""

# TODO: sort out the way packaged demos and tests work. c.f. ipyrun

import unittest

from .constants import (
    DIR_EXAMPLE_APP,
    DIR_EXAMPLE_APPDATA,
    DIR_EXAMPLE_PROCESS,
    FDIR_APPDATA,
)
from datetime import datetime
import subprocess

# TODO: add tests!
import pathlib
from pydantic import BaseModel, ValidationInfo, field_validator
from ipyrun.runshell import (
    DefaultConfigShell,
    ConfigShell,
    run,
    AutoDisplayDefinition,
    FPTH_EXAMPLE_INPUTSCHEMA,
    FiletypeEnum,
)
from ipyrun.examples.linegraph.linegraph_app import (
    LineGraphConfigShell,
    LineGraphConfigBatch,
    LineGraphBatchActions,
)
from ipyrun.constants import FPTH_EXAMPLE_SCRIPT
import uuid
from dirty_equals import IsNow

### ----------------------------
### ----------------------------
### ----------------------------
from ipyrun.constants import load_test_constants
from ipyrun.runshell import (
    ConfigBatch,
    BatchShellActions,
    BatchApp,
    RunShellActions,
)
from ipyautoui.custom.workingdir import WorkingDirsUi
import json

test_constants = load_test_constants()


# class LineGraphConfigShell(DefaultConfigShell):
#     @field_validator("path_run")
#     def _set_path_run(cls, v):
#         return FPTH_EXAMPLE_SCRIPT

#     @field_validator("fpths_outputs")
#     def _fpths_outputs(cls, v, info: ValidationInfo):
#         fdir = info.data["fdir_appdata"]
#         nm = info.data["name"]
#         paths = [
#             fdir / pathlib.Path("out-" + nm + ".csv"),
#             fdir / pathlib.Path("out-" + nm + ".plotly.json"),
#         ]
#         return paths

#     @field_validator("autodisplay_definitions")
#     def _autodisplay_definitions(cls, v):
#         return [
#             AutoDisplayDefinition(
#                 path=FPTH_EXAMPLE_INPUTSCHEMA,
#                 obj_name="LineGraph",
#                 ext=".lg.json",
#                 ftype=FiletypeEnum.input,
#             )
#         ]


# class LineGraphConfigBatch(ConfigBatch):
#     @field_validator("cls_config")
#     def _cls_config(cls, v, info: ValidationInfo):
#         """bundles RunApp up as a single argument callable"""
#         return LineGraphConfigShell

#     @field_validator("cls_actions")
#     def _cls_actions(cls, v, info: ValidationInfo):
#         """bundles RunApp up as a single argument callable"""
#         return RunShellActions


# def fn_loaddir_handler(value, app=None):
#     fdir_root = value["fdir"] / "06_Models"
#     app.actions.load(fdir_root=fdir_root)


# class LineGraphBatchActions(BatchShellActions):
#     @field_validator("runlog_show")
#     def _runlog_show(cls, v, info: ValidationInfo):
#         return None

#     @field_validator("load_show")
#     def _load_show(cls, v, info: ValidationInfo):
#         return lambda: WorkingDirsUi(
#             fn_onload=wrapped_partial(fn_loaddir_handler, app=info.data["app"])
#         )


### ----------------------------
### ----------------------------
### ----------------------------


def test_runapp():
    """Test something."""

    config = LineGraphConfigShell(
        path_run=FPTH_EXAMPLE_SCRIPT,
        fdir_root=FDIR_APPDATA,
        shell="python -O -m",
    )
    pr = run(config)
    print("config")
    assert isinstance(config, ConfigShell)


# TODO: update example to this: https://examples.pyviz.org/attractors/attractors.html
# TODO: configure so that the value of the RunApp is the config?


def test_run_config():
    config = LineGraphConfigShell()
    assert isinstance(config, ConfigShell)
    config = LineGraphConfigShell(index=1)
    assert isinstance(config, ConfigShell)


def change_input(path):
    """change the input"""
    di_in = json.loads(path.read_text())
    di_in["title"] = "test" + " - " + str(uuid.uuid4())
    json.dump(di_in, path.open("w"))


def test_run_batch():
    config_batch = LineGraphConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        # cls_config=MyConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    if config_batch.fpth_config.is_file():
        config_batch = LineGraphConfigBatch(
            **json.loads(config_batch.fpth_config.read_text())
        )
    app = BatchApp(config_batch, cls_actions=LineGraphBatchActions)
    p_in = app.config.configs[0].fpths_inputs[0]
    p_out = app.config.configs[0].fpths_outputs[0]

    # assert app.actions.get_status() == "up_to_date"
    change_input(p_in)
    app.actions.update_status()
    assert app.actions.get_status() == "outputs_need_updating"

    app.actions.run()
    assert datetime.fromtimestamp(p_out.stat().st_mtime) == IsNow(delta=3)


def test_batch_add_run():
    config_batch = LineGraphConfigBatch(
        fdir_root=test_constants.DIR_EXAMPLE_BATCH,
        # cls_config=MyConfigShell,
        title="""# Plot Straight Lines\n### example RunApp""",
    )
    if config_batch.fpth_config.is_file():
        config_batch = LineGraphConfigBatch(
            **json.loads(config_batch.fpth_config.read_text())
        )
    app = BatchApp(config_batch, cls_actions=LineGraphBatchActions)
    n = len(app.config.configs)
    app.actions.add()
    assert len(app.config.configs) == n + 1
