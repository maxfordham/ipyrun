import pathlib
import immutables
from ipyautoui.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    # BUTTON_HEIGHT_MIN,
    # BUTTON_MIN_SIZE,
)

frozenmap = (
    immutables.Map
)  # https://www.python.org/dev/peps/pep-0603/, https://github.com/MagicStack/immutables

PATH_PACKAGE = pathlib.Path(__file__).parent
PATH_RUNAPP_HELP = PATH_PACKAGE / "images" / "RunApp.png"
PATH_RUNAPPS_HELP = PATH_PACKAGE / "images" / "RunBatch.png"
FPTH_MXF_ICON = PATH_PACKAGE / "images" / "mxf-icon.png"
FPTH_USER_ICON = PATH_PACKAGE / "images" / "user-icon.png"
FPTH_EXAMPLE_SCRIPT = PATH_PACKAGE / "examplerun"
FPTH_EXAMPLE_INPUTSCHEMA = PATH_PACKAGE / "examplerun" / "input_schema_linegraph.py"

FPTH_EXAMPLE_RUN = PATH_PACKAGE / "examples" / "linegraph" / "linegraph"

# default names of files in RunShell
PATH_CONFIG = pathlib.Path("config-shell_handler.json")
PATH_RUNHISTORY = pathlib.Path("runhistory.csv")
PATH_LOG = pathlib.Path("log.csv")

FILENAME_FORBIDDEN_CHARACTERS = {"<", ">", ":", '"', "/", "\\", "|", "?", "*"}
# [naming-a-file](https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file)

JOBNO_DEFAULT = "J5001"  #  testing job


# RunApp status button styles ------------------------
STATUS_BUTTON_UPTODATE = frozenmap(
    icon="check",
    style={},
    button_style="success",
    tooltip="up-to-date",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    # disabled=True,
)

STATUS_BUTTON_NOOUTPUTS = frozenmap(
    icon="circle",
    style={"button_color": "LightYellow"},
    button_style="",
    tooltip="no-outputs",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    # disabled=True,
)

STATUS_BUTTON_NEEDSRERUN = frozenmap(
    icon="refresh",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    # disabled=True,
)
STATUS_BUTTON_ERROR = frozenmap(
    icon="exclamation-triangle",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    # disabled=True,
)

DI_STATUS_MAP = frozenmap(
    up_to_date=STATUS_BUTTON_UPTODATE,
    no_outputs=STATUS_BUTTON_NOOUTPUTS,
    outputs_need_updating=STATUS_BUTTON_NEEDSRERUN,
    error=STATUS_BUTTON_ERROR,
)
# ------------------------------------------------

# RunApp buttons widget styling ------------------
CHECK = dict(
    value=False,  # self.checked
    disabled=False,
    indent=False,
    layout=dict(
        max_width="20px",
        height="40px",
        padding="3px",
    ),
)
HELP_UI = dict(
    icon="question-circle",
    tooltip="describes the functionality of elements in the RunApp interface",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MIN},
)
HELP_RUN = dict(
    icon="book",
    tooltip="describes what the Run process is actually doing. whats it for...?",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MIN},
)
HELP_CONFIG = dict(
    icon="cog",
    tooltip=(
        "the config of the Run. i.e. where is the process getting data from and saving"
        " results to?"
    ),
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MIN},
)
INPUTS = dict(
    description="inputs",
    tooltip="edit the user input information that is used when the process is executed",
    button_style="warning",
    icon="edit",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MEDIUM},
)
OUTPUTS = dict(
    description="outputs",
    icon="search",
    tooltip="show a preview of the output files generated when the script runs",
    button_style="info",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MEDIUM},
)
RUNLOG = dict(
    description="runlog",
    tooltip=(
        "show a runlog of when the script was executed to generate the outputs, and"
        " by who"
    ),
    button_style="info",
    icon="scroll",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MEDIUM},
)
RUN = dict(
    description=" run",
    icon="play",
    tooltip="execute the process based on the defined user inputs",
    button_style="success",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MEDIUM},
)
SHOW = dict(
    icon="eye",
    tooltip="default show",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MIN},
)
HIDE = dict(
    icon="eye-slash",
    tooltip="default show",
    style={"font_weight": "bold"},
    layout={"width": BUTTON_WIDTH_MIN},
)

LOAD = dict(
    icon="ellipsis-v",
    tooltip="load selected",
    style={"font_weight": "bold"},
    button_style="info",
    layout={"width": BUTTON_WIDTH_MIN},
)
UPLOAD = dict(
    icon="upload",
    tooltip="upload data",
    style={"font_weight": "bold"},
    button_style="info",
    layout={"width": BUTTON_WIDTH_MIN},
)

BUTTONBAR_LAYOUT_KWARGS = {
    "display": "flex",
    "flex_flow": "row",
    "justify_content": "space-between",
}

DEFAULT_BUTTON_STYLES = frozenmap(
    check=CHECK,
    status_indicator=STATUS_BUTTON_NOOUTPUTS,
    help_ui=HELP_UI,
    help_run=HELP_RUN,
    help_config=HELP_CONFIG,
    inputs=INPUTS,
    outputs=OUTPUTS,
    upload=UPLOAD,
    runlog=RUNLOG,
    run=RUN,
    show=SHOW,
    hide=HIDE,
    load=LOAD,
    container=dict(layout={"width": "100%"}, selected_index=None),
)

ADD = dict(
    icon="plus",
    tooltip="add a run",
    style={"font_weight": "bold"},
    button_style="primary",
    layout={"width": BUTTON_WIDTH_MIN},
)
REMOVE = dict(
    icon="minus",
    tooltip="remove a run",
    style={"font_weight": "bold"},
    button_style="danger",
    layout={"width": BUTTON_WIDTH_MIN},
)
WIZARD = dict(
    icon="exchange-alt",
    tooltip="add remove wizard",
    style={"font_weight": "bold"},
    button_style="warning",
    layout={"width": BUTTON_WIDTH_MIN},
)

# ------------------------------------------------


# TODO: delete
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

    path_testing_constants = PATH_PACKAGE.parents[1] / "tests" / "constants.py"
    test_constants = SourceFileLoader(
        "constants", str(path_testing_constants)
    ).load_module()
    return test_constants
