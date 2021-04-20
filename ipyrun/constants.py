import os
# from ipyrun.constants import BUTTON_WIDTH_MIN, BUTTON_WIDTH_MEDIUM, FDIR_ROOT_EXAMPLE, FPTH_SCRIPT_EXAMPLE, FDIR_EXAMPLE
FDIR_PACKAGE = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
FDIR_ROOT_EXAMPLE = os.path.join(FDIR_PACKAGE,'examples','J0000')
FDIR_EXAMPLE = os.path.join(FDIR_ROOT_EXAMPLE,'Automation','ExampleApp')
FPTH_SCRIPT_EXAMPLE = os.path.join(FDIR_PACKAGE,'examples','scripts','expansion_vessel_sizing.py')

BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM='90px'
BUTTON_HEIGHT_MIN = '25px'
