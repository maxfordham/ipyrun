import pathlib
import immutables
frozenmap = (
    immutables.Map
)  # https://www.python.org/dev/peps/pep-0603/, https://github.com/MagicStack/immutables

PATH_PACKAGE = pathlib.Path(__file__).parent
PATH_RUNAPP_HELP = PATH_PACKAGE / 'images' / 'RunApp.png'
PATH_RUNAPPS_HELP = PATH_PACKAGE / 'images' / 'RunBatch.png'

JOBNO_DEFAULT = 'J5001' #  testing job

BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM = '90px'
BUTTON_HEIGHT_MIN = '25px'
BUTTON_MIN_SIZE = frozenmap(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN)

FPTH_MXF_ICON = PATH_PACKAGE / 'images' / 'mxf-icon.png'
FPTH_USER_ICON = PATH_PACKAGE / 'images' / 'user-icon.png'
FNM_CONFIG_FILE = pathlib.Path("config-shell_handler.json")

# RunApp status button styles ------------------------
STATUS_BUTTON_UPTODATE = frozenmap(
    icon="fa-check",
    style={},
    button_style="success",
    tooltip="up-to-date",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

STATUS_BUTTON_NOOUTPUTS = frozenmap(
    icon="fa-circle",
    style={'button_color':'LightYellow'},
    button_style="",
    tooltip="no-outputs",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

STATUS_BUTTON_NEEDSRERUN = frozenmap(
    icon="fa-refresh",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)
STATUS_BUTTON_ERROR = frozenmap(
    icon="fa-exclamation-triangle",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

DI_STATUS_MAP = frozenmap(
    up_to_date=STATUS_BUTTON_UPTODATE,
    no_outputs=STATUS_BUTTON_NOOUTPUTS,
    outputs_need_updating=STATUS_BUTTON_NEEDSRERUN,
    error=STATUS_BUTTON_ERROR
)
# ------------------------------------------------

# RunApp buttons widget styling ------------------
CHECK = dict(
    value=False, # self.checked
    disabled=False,
    indent=False,
    layout=dict(max_width="20px", 
                          height="40px", 
                          padding="3px", 
                         )
)
HELP_UI = dict(
    icon="question-circle",
    tooltip="describes the functionality of elements in the RunApp interface",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MIN}
)
HELP_RUN = dict(
    icon="book",
    tooltip="describes the functionality of elements in the RunApp interface",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MIN},
)
HELP_CONFIG = dict(
    icon="cog",
    tooltip="the config of the task",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MIN},
)
INPUTS = dict(
    description="inputs",
    tooltip="edit the user input information that is used when the script is executed",
    button_style="warning",
    icon="edit",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MEDIUM},
)
OUTPUTS = dict(
    description="outputs",
    icon="search",
    tooltip="show a preview of the output files generated when the script runs",
    button_style="info",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MEDIUM},
)
RUNLOG = dict(
    description="runlog",
    tooltip="show a runlog of when the script was executed to generate the outputs, and by who",
    button_style="info",
    icon="scroll",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MEDIUM},
)
RUN = dict(
    description=" run",
    icon="fa-play",
    tooltip="execute the script based on the user inputs",
    button_style="success",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MEDIUM},
)
SHOW = dict(
    icon="fa-eye",
    tooltips="default show",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MIN},
)
HIDE = dict(
    icon="fa-eye-slash",
    tooltips="default show",
    style={"font_weight": "bold"},
    layout={"width":BUTTON_WIDTH_MIN},
)

DEFAULT_BUTTON_STYLES = frozenmap(
    check = CHECK,
    status_indicator = STATUS_BUTTON_NOOUTPUTS,
    help_ui = HELP_UI,
    help_run = HELP_RUN,
    help_config = HELP_CONFIG,
    inputs = INPUTS,
    outputs = OUTPUTS,
    runlog = RUNLOG,
    run = RUN,
    show = SHOW,
    hide = HIDE,
)
# ------------------------------------------------

def load_test_constants():
    """only in use for debugging within the package. not used in production code.

    Returns:
        module: test_constants object
        
    Example:
        DIR_TESTS
        DIR_EXAMPLE_PROCESS
        DIR_EXAMPLE_BATCH
    """
    from importlib.machinery import SourceFileLoader
    path_testing_constants = PATH_PACKAGE.parents[1] / 'tests' / 'constants.py'
    test_constants = SourceFileLoader("constants", str(path_testing_constants)).load_module()
    return test_constants