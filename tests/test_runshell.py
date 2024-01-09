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
import json

test_constants = load_test_constants()


import pytest
from ipyrun.basemodel import file


CONFIG_BATCH = {
    "fdir_root": "/home/jovyan/ipyrun/tests/examples/line_graph_batch",
    "fpth_config": "config-shell_handler.json",
    "title": "# Plot Straight Lines\n### example RunApp",
    "status": None,
    "configs": [
        {
            "index": 0,
            "path_run": "/home/jovyan/ipyrun/src/ipyrun/examples/linegraph/linegraph",
            "pythonpath": "/home/jovyan/ipyrun/src/ipyrun/examples/linegraph",
            "run": "linegraph",
            "name": "linegraph",
            "long_name": "00 - Linegraph",
            "key": "00-linegraph",
            "fdir_root": "/home/jovyan/ipyrun/tests/examples/line_graph_batch",
            "fdir_appdata": "00-linegraph",
            "in_batch": True,
            "status": "outputs_need_updating",
            "update_config_at_runtime": False,
            "autodisplay_definitions": [
                {
                    "path": "/home/jovyan/ipyrun/src/ipyrun/examples/linegraph/linegraph/input_schema_linegraph.py",
                    "obj_name": "LineGraph",
                    "module_name": "input_schema_linegraph",
                    "ftype": "in",
                    "ext": ".lg.json",
                }
            ],
            "autodisplay_inputs_kwargs": {"patterns": "*"},
            "autodisplay_outputs_kwargs": {"patterns": "*.plotly.json"},
            "fpths_inputs": ["00-linegraph/in-00-linegraph.lg.json"],
            "fpths_outputs": [
                "00-linegraph/out-linegraph.csv",
                "00-linegraph/out-linegraph.plotly.json",
            ],
            "fpth_params": None,
            "fpth_config": "00-linegraph/config-shell_handler.json",
            "fpth_runhistory": "00-linegraph/runhistory.csv",
            "fpth_log": "00-linegraph/log.csv",
            "call": "/home/jovyan/micromamba/envs/ipyrun-dev/bin/python -O -m",
            "params": {},
            "shell_template": "{{ call }} {{ run }}{% for f in fpths_inputs %} {{f}}{% endfor %}{% for f in fpths_outputs %} {{f}}{% endfor %}{% for k,v in params.items()%} --{{k}} {{v}}{% endfor %}\n",
            "shell": "/home/jovyan/micromamba/envs/ipyrun-dev/bin/python -O -m linegraph 00-linegraph/in-00-linegraph.lg.json 00-linegraph/out-linegraph.csv 00-linegraph/out-linegraph.plotly.json",
        }
    ],
}


@pytest.fixture
def remake_config():
    config_batch = LineGraphConfigBatch(**CONFIG_BATCH)
    file(config_batch, config_batch.fpth_config)


def test_runapp():
    """Test something."""

    config = LineGraphConfigShell(
        path_run=FPTH_EXAMPLE_SCRIPT,
        fdir_root=FDIR_APPDATA,
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


def test_run_batch(remake_config):
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


def test_batch_add_run(remake_config):
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
    assert len(app.runs.children) != 0
    assert n == 1
    app.actions.add()
    assert len(app.config.configs) == n + 1
    assert len(app.runs.children) != 0
