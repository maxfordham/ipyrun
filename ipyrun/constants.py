import os
# from ipyrun.constants import BUTTON_WIDTH_MIN, BUTTON_WIDTH_MEDIUM, FDIR_ROOT_EXAMPLE, FPTH_SCRIPT_EXAMPLE, FDIR_APP_EXAMPLE
FDIR_PACKAGE = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
FDIR_IPYRUN_MAIN = os.path.dirname(__file__)
FPTH_RUNAPP_HELP = os.path.join(FDIR_PACKAGE, 'images', 'RunApp.png')

FDIR_ROOT_EXAMPLE = os.path.join(FDIR_PACKAGE,'examples','J0000')
FDIR_APP_EXAMPLE = os.path.join(FDIR_ROOT_EXAMPLE,'test_appdir')
FPTH_SCRIPT_EXAMPLE = os.path.join(FDIR_PACKAGE,'test_scripts','expansion_vessel_sizing.py')
FPTH_SCRIPT_EXAMPLE_CSV = os.path.join(FDIR_PACKAGE,'test_scripts','line_graph.py')


BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM='90px'
BUTTON_HEIGHT_MIN = '25px'
