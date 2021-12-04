"""Top-level package for ipyrun."""
import sys
#sys.path.append('/mnt/c/engDev/git_mf/ipypdt')
sys.path.append('/mnt/c/engDev/git_mf/mfom')
#sys.path.append('/mnt/c/engDev/git_mf/ipyword')
sys.path.append('/mnt/c/engDev/git_mf/ipyrun')
sys.path.append('/mnt/c/engDev/git_mf/MFFileUtilities')
# ^ not working for some reason... hence hack below
# for dev only. delete in production.

__author__ = """John Gunstone"""
__email__ = 'gunstone.john@gmail.com'

from ipyrun._version import get_versions
__version__ = get_versions()['version']
del get_versions


