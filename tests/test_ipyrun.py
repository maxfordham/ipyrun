#!/usr/bin/env python

"""Tests for `ipyrun` package."""

import unittest

from .constants import DIR_EXAMPLE_APP, DIR_EXAMPLE_APPDATA

import subprocess

# TODO: add tests!
from ipyrun.runshell import DefaultConfigShell, ConfigShell, run


class TestIpyrun(unittest.TestCase):
    """Tests for `ipyrun` package."""

    def test_running_app(self):
        """Test something."""
        config = ConfigShell(
            path_run=DIR_EXAMPLE_APP,
            fdir_root=DIR_EXAMPLE_APPDATA,
            fpths_inputs=["in-linegraph.lg.json"],
            fpths_outputs=["out-linegraph.csv", "out-linegraph.plotly.json"],
            shell='python -O -m',
            pythonpath=DIR_EXAMPLE_APP,
        )
        pr = run(config)
        print("config")
        assert isinstance(config, ConfigShell)
