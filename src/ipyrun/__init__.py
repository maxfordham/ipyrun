"""Top-level package for ipyrun.

Overview:

    - basemodel.py : extended functionality of pydantic.BaseModel
    - constants.py : any package constants. widget styling saved here.
    - schema_core.py : defines the actions (callables) that are accessible through the RunUi
    - schema_runshell.py : defines a config schema for ConfigRunShell(ConfigBatchShell) 
        and extends ActionsRun(ActiomsBatch) to ActionsRunShell(ActionsBatchShell) based on config
    - schema_runsnake.py : doesn't exist yet - but a new config could be added to re-use the same UI 
        to run snakemake commands rather than subprocess ones. 
    - run_ui.py : builds the generic UI classes. the actions associated to the buttons are programable. 
        the intention is that the classes in here are generic, the UI can be easily reprommaned to different 
        uses without editing these base classes. 
    - run.py
    - utils.py : helper functions.

"""
import sys
#sys.path.append('/mnt/c/engDev/git_mf/ipypdt')
sys.path.append('/mnt/c/engDev/git_mf/mfom')
#sys.path.append('/mnt/c/engDev/git_mf/ipyword')
sys.path.append('/mnt/c/engDev/git_mf/ipyrun/src')
sys.path.append("/mnt/c/engDev/git_mf/ipyautoui/src")
sys.path.append('/mnt/c/engDev/git_mf/MFFileUtilities')
# ^ not working for some reason... hence hack below
# for dev only. delete in production.

__author__ = """John Gunstone"""
__email__ = 'gunstone.john@gmail.com'

from ipyrun._version import get_versions
__version__ = get_versions()['version']
del get_versions


