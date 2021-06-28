"""Top-level package for ipyrun."""
#import sys
#sys.path.append('/mnt/c/engDev/git_mf/ipyrun')
#sys.path.append('/mnt/c/engDev/git_mf/MFFileUtilities')

__author__ = """John Gunstone"""
__email__ = 'gunstone.john@gmail.com'

from mf_file_utilities._version import get_versions
__version__ = get_versions()['version']
del get_versions

