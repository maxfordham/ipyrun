#!/usr/bin/env python

"""Tests for `ipyrun` package."""

import unittest
import ipyrun

#from .constants import DIR_EXAMPLE_APP

import subprocess


class TestIpyrun(unittest.TestCase):
    """Tests for `ipyrun` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        print('sdf')
        #pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass
        
    def test_running_app(self):
        """Test something."""
        pass
        #try: 
        #    subprocess.run('python {}'.format(DIR_EXAMPLE_APP))
        #except:
        #    ValueError('failed to run')