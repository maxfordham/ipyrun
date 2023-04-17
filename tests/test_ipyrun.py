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

import subprocess

# TODO: add tests!
import pathlib
from pydantic import BaseModel, validator
from ipyrun.runshell import (
    DefaultConfigShell,
    ConfigShell,
    run,
    AutoDisplayDefinition,
    FPTH_EXAMPLE_INPUTSCHEMA,
    FiletypeEnum,
)
from ipyrun.constants import FPTH_EXAMPLE_SCRIPT


class TestIpyrun(unittest.TestCase):
    """Tests for `ipyrun` package."""

    def test_running_app(self):
        """Test something."""
        class LineGraphConfigShell(DefaultConfigShell):
            @validator("path_run", always=True, pre=True)
            def _set_path_run(cls, v, values):
                return FPTH_EXAMPLE_SCRIPT

            @validator("fpths_outputs", always=True)
            def _fpths_outputs(cls, v, values):
                fdir = values["fdir_appdata"]
                nm = values["name"]
                paths = [
                    fdir / pathlib.Path("out-" + nm + ".csv"),
                    fdir / pathlib.Path("out-" + nm + ".plotly.json"),
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

        config = LineGraphConfigShell(
            path_run=FPTH_EXAMPLE_SCRIPT,
            fdir_root=FDIR_APPDATA,
            shell="python -O -m",
        )
        pr = run(config)
        print("config")
        assert isinstance(config, ConfigShell)
