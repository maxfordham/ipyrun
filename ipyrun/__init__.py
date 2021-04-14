"""Top-level package for ipyrun."""

__author__ = """John Gunstone"""
__email__ = 'gunstone.john@gmail.com'

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

#  https://stackoverflow.com/Questions/16981921/relative-imports-in-python-3
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))