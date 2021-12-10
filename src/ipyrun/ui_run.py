# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python [conda env:mf_base1] *
#     language: python
#     name: conda-env-mf_base1-py
# ---

"""
contains core UI elements and dummy definitions for RunActions and BatchActions. 
The Actions need to be re-defined to create anytype of functionality. 
"""
# %run __init__.py
# %load_ext lab_black

# +
import pandas as pd
from IPython.display import (
    # update_display,
    display,
    Image,
    # JSON,
    Markdown,
    # HTML,
    clear_output,
)
import subprocess
import functools
from shutil import copyfile
import getpass
import importlib.util
from halo import HaloNotebook
import pathlib
import typing
from typing import Optional, List, Dict, Type
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, validator, Field
from jinja2 import Template

import plotly.io as pio
import plotly.graph_objects as go

# widget stuff
import ipywidgets as widgets

# core mf_modules
from ipyautoui import AutoUi, DisplayFiles
from ipyautoui.autoui import display_template_ui_model

import inspect

# display_template_ui_model()

# from this repo
from ipyrun.utils import make_dir, del_matching
from ipyrun.constants import load_test_constants
from ipyrun.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    JOBNO_DEFAULT,
    PATH_RUNAPP_HELP,
    PATH_RUNAPPS_HELP,
)


def get_mfuser_initials():
    user = getpass.getuser()
    return user[0] + user[2]

# +
# RUN __FUTURE__


class RunId(BaseModel):
    """run identifier

    Args:
        BaseModel (pydantic.BaseModel): inherits pydantic

    Returns:
        RunId: RunId object
    """

    index: int = 0
    process_name: str = "process_name"
    pretty_name: str = None
    check: bool = True

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return str(values["index"]) + " - " + values["process_name"]
        else:
            return v


class RunUiConfig(BaseModel):
    include_show_hide = True


class RunActions(BaseModel):
    """map containing callables that are called when buttons in the RunApp are
    activated. Default values contain dummy calls. setting the values to "None"
    hides the button in the App. The actions here are used to show / hide another
    UI element that the user can edit.

    Args:
        BaseModel (pydantic.BaseModel):
    """

    check: typing.Optional[typing.Callable] = lambda: display("check")
    uncheck: typing.Optional[typing.Callable] = lambda: display("uncheck")
    help_ui_show: typing.Optional[typing.Callable] = lambda: display(
        Image(PATH_RUNAPP_HELP)
    )
    help_ui_hide: typing.Optional[typing.Callable] = lambda: display("help_ui_hide")
    help_run_show: typing.Optional[typing.Callable] = lambda: display(
        "help_run_show"
    )  # None
    help_run_hide: typing.Optional[typing.Callable] = lambda: display("help_run_hide")
    help_config_show: typing.Optional[typing.Callable] = lambda: display(
        "help_run_show"
    )
    help_config_hide: typing.Optional[typing.Callable] = lambda: display(
        "help_run_hide"
    )
    inputs_show: typing.Optional[typing.Callable] = lambda: display("inputs_show")
    inputs_hide: typing.Optional[typing.Callable] = lambda: display("inputs_hide")
    outputs_show: typing.Optional[typing.Callable] = lambda: display("outputs_show")
    outputs_hide: typing.Optional[typing.Callable] = lambda: display("outputs_hide")
    log_show: typing.Optional[typing.Callable] = lambda: display("log_show")
    log_hide: typing.Optional[typing.Callable] = lambda: display("log_hide")
    run: typing.Optional[typing.Callable] = lambda: display("run")
    run_hide: typing.Optional[typing.Callable] = lambda: display("console_hide")
    activate: typing.Optional[typing.Callable] = lambda: display("activate")
    deactivate: typing.Optional[typing.Callable] = lambda: display("deactivate")


#     show: typing.Optional[typing.Callable] = (lambda : display('show'))
#     hide: typing.Optional[typing.Callable] = (lambda : display('hide'))


class RunAppConfig(BaseModel):
    """generic RunApp configurator definition. this will be serialised to JSON and remade
    for storing the Apps state. it will also be used to generate a RunApp when using the
    "add" button.

    Args:
        BaseModel ([type]): [description]
    """

    # run_actions: RunActions = RunActions() # TODO: add this back in once pydantic has updated such that it can be excluded from the json output. and remade by a validator.
    run_id: RunId = RunId()
    config_ui: RunUiConfig = RunUiConfig()
    config_actions: typing.Any = None  # this one might get overwritten


class BatchId(RunId):
    description: str = Field(
        "",
        description="a description of the batch of RunApps. Displayed as a header to the UI",
    )

    @validator("pretty_name", always=True)
    def _pretty_name(cls, v, values):
        if v is None:
            return values["process_name"]
        else:
            return v


#  as the RunActions are so generic, the same actions can be applied to Batch operations
#  with the addition of some batch specific operations
class BatchActions(RunActions):
    """actions associated within managing a batch of RunApps. As with the RunActions,
    these actions just call in another UI element that does the actual work. See
    ui_add.py, ui_remove.py, ui_wizard.py

    Args:
        RunActions ([type]): [description]
    """

    add_show: typing.Optional[typing.Callable] = lambda: display("add_show")
    add_hide: typing.Optional[typing.Callable] = lambda: display("add_hide")
    remove_show: typing.Optional[typing.Callable] = lambda: display("remove_show")
    remove_hide: typing.Optional[typing.Callable] = lambda: display("remove_hide")
    wizard_show: typing.Optional[typing.Callable] = lambda: display("wizard_show")
    wizard_hide: typing.Optional[typing.Callable] = lambda: display("wizard_hide")
    review_show: typing.Optional[typing.Callable] = lambda: display("review_show")
    review_hide: typing.Optional[typing.Callable] = lambda: display("review_hide")


class BatchAppConfig(BaseModel):
    # batch_actions: BatchActions = BatchActions() # TODO: add this back in once pydantic has updated such that it can be excluded from the json output. and remade by a validator.
    batch_ui: BatchId = BatchId()
    config_ui: RunUiConfig = RunUiConfig()
    config_actions: typing.Any = None  # this one might get overwritten


if __name__ == "__main__":
    display(
        Markdown(
            """
### RunAppConfig

This is everything that will be passed to the RunApp on initialisation
    """
        )
    )
    display(Markdown("`>>> display(RunAppConfig().dict())`"))
    display(RunAppConfig().dict())
    display(Markdown("`>>> display(RunActions().dict())`"))
    display(RunActions().dict())

    display(
        Markdown(
            """
--- 

### BatchAppConfig

This is everything that will be passed to the RunApp on initialisation
    """
        )
    )
    display(Markdown("`>>> display(BatchAppConfig().dict())`"))
    display(BatchAppConfig().dict())
    display(Markdown("`>>> display(BatchActions().dict())`"))
    display(BatchActions().dict())

# +
class RunActionsUi:
    """maps the RunActions onto buttons. doesn't put them in a container.

    Returns:
        display: of buttons for testing
    """

    minwidth = BUTTON_WIDTH_MIN
    medwidth = BUTTON_WIDTH_MEDIUM

    def __init__(self, run_actions: RunActions = RunActions(), run_id: RunId = RunId()):
        self.run_actions = self._init_run_actions(run_actions)
        self.run_id = run_id
        self._init_objects()
        self._init_controls()

    def _init_run_action(self, action):
        if action is not None:
            try:
                if "cls" in inspect.getfullargspec(action).args:
                    return functools.partial(action, cls=self)
                else:
                    return action
            except:
                print("error inspecting the following:")
                print(action)
                print(type(action))
                print("cls" in inspect.getfullargspec(action).args)
                action()
        else:
            return action

    def _init_run_actions(
        self, run_actions: typing.Type[RunActions]
    ) -> typing.Type[RunActions]:
        return type(run_actions)(
            **{k: self._init_run_action(v) for k, v in run_actions.dict().items()}
        )

    def _init_objects(self):
        """initiates UI objects
        #         button list:
        #         ---------------
        #         self.check
        #         self.help_ui
        #         self.help_run
        #         self.help_config
        #         self.inputs
        #         self.outputs
        #         self.log
        #         self.check
        #         self.run
        #         self.show
        #         self.hide
        """

        self.check = widgets.Checkbox(
            value=self.run_id.check,
            disabled=False,
            indent=False,
            layout=widgets.Layout(max_width="30px", height="30px", padding="3px"),
        )
        self.help_ui = widgets.ToggleButton(
            icon="question-circle",
            tooltip="describes the functionality of elements in the RunApp interface",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.minwidth),
        )
        self.help_run = widgets.ToggleButton(
            icon="book",
            tooltip="describes the functionality of elements in the RunApp interface",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.minwidth),
        )
        self.help_config = widgets.ToggleButton(
            icon="cog",
            tooltip="the config of the task",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.minwidth),
        )
        self.inputs = widgets.ToggleButton(
            description="inputs",
            tooltip="edit the user input information that is used when the script is executed",
            button_style="warning",
            icon="edit",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.medwidth),
        )
        self.outputs = widgets.ToggleButton(
            description="outputs",
            icon="search",
            tooltip="show a preview of the output files generated when the script runs",
            button_style="info",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.medwidth),
        )
        self.log = widgets.ToggleButton(
            description="log",
            tooltip="show a log of when the script was executed to generate the outputs, and by who",
            button_style="info",
            icon="scroll",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.medwidth),
        )
        self.run = widgets.Button(
            description=" run",
            icon="fa-play",
            tooltip="execute the script based on the user inputs",
            button_style="success",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.medwidth),
        )
        self.show = widgets.Button(
            icon="fa-eye",
            tooltips="default show",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.minwidth),
        )
        self.hide = widgets.Button(
            icon="fa-eye-slash",
            tooltips="default show",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=self.minwidth),
        )

        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_log = widgets.Output()
        self.out_console = widgets.Output()

    def _init_controls(self):
        self.help_ui.observe(self._help_ui, names="value")
        self.help_run.observe(self._help_run, names="value")
        self.help_config.observe(self._help_run, names="value")
        self.inputs.observe(self._inputs, names="value")
        self.outputs.observe(self._outputs, names="value")
        self.log.observe(self._log, names="value")
        self.run.on_click(self._run)
        self.check.observe(self._check, names="value")
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)

    @property
    def get_show_hide_value(self):
        return [
            self.help_ui.value,
            self.help_run.value,
            self.help_config.value,
            self.inputs.value,
            self.outputs.value,
            self.log.value,
        ]

    def _show(self, on_click):
        """default show run data"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = True
        self.outputs.value = True
        self.log.value = True

    def _hide(self, on_click):
        """default hide run data"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = False
        self.outputs.value = False
        self.log.value = False
        with self.out_console:
            clear_output()

    def _check(self, on_change):
        self.run_id.check = self.check.value

    def _show_hide_output(
        self, widgets_output, widget_button, show_action, hide_action
    ):
        with widgets_output:
            if widget_button.value:
                show_action()
            else:
                hide_action()
                clear_output()

    def _help_ui(self, on_change):
        self._show_hide_output(
            self.out_help_ui,
            self.help_ui,
            self.run_actions.help_ui_show,
            self.run_actions.help_ui_hide,
        )

    def _help_run(self, on_change):
        self._show_hide_output(
            self.out_help_run,
            self.help_run,
            self.run_actions.help_run_show,
            self.run_actions.help_run_hide,
        )

    def _help_config(self, on_change):
        self._show_hide_output(
            self.out_help_run,
            self.help_run,
            self.run_actions.help_config_show,
            self.run_actions.help_config_hide,
        )

    def _inputs(self, on_change):
        self._show_hide_output(
            self.out_inputs,
            self.inputs,
            self.run_actions.inputs_show,
            self.run_actions.inputs_hide,
        )

    def _outputs(self, on_change):
        self._show_hide_output(
            self.out_outputs,
            self.outputs,
            self.run_actions.outputs_show,
            self.run_actions.outputs_hide,
        )

    def _log(self, on_change):
        self._show_hide_output(
            self.out_log, self.log, self.run_actions.log_show, self.run_actions.log_hide
        )

    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_actions.run()
            # reload outputs
            self.outputs.value = False
            self.outputs.value = True

    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form
        where the display method is overwritten"""
        self.out = widgets.VBox(
            [
                widgets.HBox([self.help_ui, self.out_help_ui]),
                widgets.HBox([self.help_run, self.out_help_run]),
                widgets.HBox([self.help_config, self.out_help_config]),
                widgets.HBox([self.inputs, self.out_inputs]),
                widgets.HBox([self.outputs, self.out_outputs]),
                widgets.HBox([self.log, self.out_log]),
                widgets.HBox([self.check]),
                widgets.HBox([self.run, self.out_console]),
                widgets.HBox([self.show]),
                widgets.HBox([self.hide]),
            ]
        )
        display(widgets.HTML("<b>Buttons to be programmed from `RunActions`</b> "))
        display(self.out)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":

    display(
        Markdown(
            """
### RunActionsUi

These are all of the buttons that will be linked to callables in RunActions
    """
        )
    )
    display(Markdown("`>>> display(RunActionsUi())`"))
    actions = RunActionsUi()
    display(RunActionsUi())


# +
def build_button_bar(button_map: typing.Dict, config_ui: RunUiConfig):
    button_bar = widgets.HBox(
        layout=widgets.Layout(width="100%", justify_content="space-between")
    )
    left = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
    left.children = [k for k, v in button_map["left"].items() if v is not None]
    button_bar.children = [left]
    if config_ui.include_show_hide:
        right = widgets.HBox(
            button_map["right"], layout=widgets.Layout(align_items="stretch")
        )
        button_bar.children = [left, right]
    return button_bar


class RunApp(RunActionsUi):
    """wrapper that extends RunActionsUi to create UI form. config data that defines
    the functionality of the App are passed as arguments that give the App its
    functionality."""

    def __init__(
        self,
        run_actions: RunActions = RunActions(),
        run_id: RunId = RunId(),
        config_ui: RunUiConfig = RunUiConfig(),
        config_actions: typing.Any = None,
    ):
        super().__init__(run_actions=run_actions, run_id=run_id)
        self.config_ui = config_ui
        self.config_actions = config_actions
        self._layout_out()
        self._run_form()

    @classmethod
    def from_config(
        cls, config_runapp: typing.Type[RunAppConfig], run_actions: RunActions
    ):  # TODO: put run_actions in config_runapp when pydantic updates
        return RunApp(
            run_actions=run_actions,
            run_id=config_runapp.run_id,
            config_ui=config_runapp.config_ui,
            config_actions=config_runapp.config_actions,
        )

    @property
    def _button_map(self):
        return {
            "outside": {self.check: self.run_actions.check},
            "left": {
                self.help_ui: self.run_actions.help_ui_show,
                self.help_run: self.run_actions.help_run_show,
                self.help_config: self.run_actions.help_config_show,
                self.inputs: self.run_actions.inputs_show,
                self.outputs: self.run_actions.outputs_show,
                self.log: self.run_actions.log_show,
                self.run: self.run_actions.run,
            },
            "right": [self.show, self.hide],
        }

    def _layout_out(self):
        self.layout_out = widgets.VBox(
            [
                widgets.HBox([self.out_console]),
                widgets.HBox(
                    [self.out_help_ui],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.out_help_run, self.out_help_config],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.out_inputs, self.out_outputs, self.out_log],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
            ],
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                align_content="stretch",
                display="flex",
                flex="flex-grow",
            ),
        )

    def _run_form(self):
        self.button_bar = build_button_bar(self._button_map, self.config_ui)
        self.layout = widgets.VBox([self.button_bar, self.layout_out])
        self.acc = widgets.Accordion(
            children=[self.layout],
            selected_index=None,
            layout=widgets.Layout(width="100%"),
        )
        self.acc.set_title(0, self.run_id.pretty_name)
        self.run_form = widgets.HBox(
            [self.check, self.acc],
            layout=widgets.Layout(margin="0px", padding="0px", border="0px"),
        )  #'3px solid red'

    def display(self):
        display(self.run_form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    display(
        Markdown(
            """
### RunApp

The actions are pulled together in a container
    """
        )
    )
    display(Markdown("`>>> display(RunApp())`"))
    run = RunApp()
    display(run)


# +
class BatchActionsUi(RunActionsUi):
    """maps actions to buttons

    Args:
        RunActionsUi ([type]): inherits majority of definitions from RunActionsUi
    """

    def __init__(
        self, batch_actions: BatchActions = BatchActions(), run_id: RunId = RunId()
    ):
        self.run_actions = self._init_run_actions(batch_actions)
        self.run_id = run_id

        self._init_objects()
        self._init_controls()
        self._update_objects()
        self._update_controls()

    def _update_objects(self):
        self.add = widgets.ToggleButton(
            icon="plus",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="primary",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.remove = widgets.ToggleButton(
            icon="minus",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="danger",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.wizard = widgets.ToggleButton(
            icon="magic",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="warning",
            layout=widgets.Layout(width=self.minwidth),
        )

        self.out_add = widgets.Output()
        self.out_remove = widgets.Output()
        self.out_wizard = widgets.Output()

    def _update_controls(self):
        self.add.observe(self._add, names="value")
        self.remove.observe(self._remove, names="value")
        self.wizard.observe(self._wizard, names="value")

    def _add(self, on_change):
        self._show_hide_output(
            self.out_add, self.add, self.run_actions.add_show, self.run_actions.add_hide
        )

    def _remove(self, on_change):
        self._show_hide_output(
            self.out_remove,
            self.remove,
            self.run_actions.remove_show,
            self.run_actions.remove_hide,
        )

    def _wizard(self, on_change):
        self._show_hide_output(
            self.out_wizard,
            self.wizard,
            self.run_actions.wizard_show,
            self.run_actions.wizard_hide,
        )

    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form
        where the display method is overwritten"""
        out = widgets.VBox(
            [
                widgets.HBox([self.help_ui, self.out_help_ui]),
                widgets.HBox([self.help_run, self.out_help_run]),
                widgets.HBox([self.help_config, self.out_help_config]),
                widgets.HBox([self.inputs, self.out_inputs]),
                widgets.HBox([self.outputs, self.out_outputs]),
                widgets.HBox([self.log, self.out_log]),
                widgets.HBox([self.check]),
                widgets.HBox([self.run, self.out_console]),
                widgets.HBox([self.show]),
                widgets.HBox([self.hide]),
            ]
        )
        display(
            widgets.HTML(
                """
Buttons to be programmed from `RunActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """
            )
        )
        display(out)

        out_batch_only = widgets.VBox(
            [
                widgets.HBox([self.add, self.out_add]),
                widgets.HBox([self.remove, self.out_remove]),
                widgets.HBox([self.wizard, self.out_wizard]),
            ]
        )
        display(
            widgets.HTML(
                """
Buttons to be programmed from `BatchActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """
            )
        )
        display(out_batch_only)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    batch = BatchActionsUi()
    display(batch)


# +
class RunApps(BatchActionsUi):
    """Manage an array of RunApps

    Args:
        BatchActionsUi ([type]): [description]
    """

    def __init__(
        self,
        batch_actions: BatchActions = BatchActions(),
        run_id: RunId = RunId(),
        config_ui: RunUiConfig = RunUiConfig(),
        apps: typing.List[typing.Type[RunApp]] = None,
    ):
        super().__init__(batch_actions=batch_actions, run_id=run_id)
        self.config_ui = config_ui
        self.apps = apps
        if self.apps is None:
            self.apps = []
        self._layout_out()
        self._run_form()

    #         self._update_actions()

    #     def _update_actions(self):
    #         self.run_actions.add_show = functools.partial(
    #             self.run_actions.add_show, cls=self
    #         )

    @property
    def _button_map(self):
        return {
            "outside": {self.check: self.run_actions.check},
            "left": {
                self.help_ui: self.run_actions.help_ui_show,
                self.help_run: self.run_actions.help_run_show,
                self.help_config: self.run_actions.help_config_show,
                self.inputs: self.run_actions.inputs_show,
                self.outputs: self.run_actions.outputs_show,
                self.log: self.run_actions.log_show,
                self.run: self.run_actions.run,
                self.add: self.run_actions.add_show,
                self.remove: self.run_actions.remove_show,
                self.wizard: self.run_actions.wizard_show,
            },
            "right": [self.show, self.hide],
        }

    def _layout_out(self):
        self.layout_out = widgets.VBox(
            [
                widgets.HBox([self.out_console]),
                widgets.HBox(
                    [self.out_help_ui],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.out_add, self.out_remove, self.out_wizard],
                    #                     layout=widgets.Layout(
                    #                         width="100%",
                    #                         align_items="stretch",
                    #                         justify_content="space-between",
                    #                         align_content="stretch",
                    #                     ),
                ),
                widgets.HBox(
                    [self.out_help_run, self.out_help_config],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.out_inputs, self.out_outputs, self.out_log],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
            ],
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                align_content="stretch",
                display="flex",
                flex="flex-grow",
            ),
        )

    def _run_form(self):
        self.button_bar = build_button_bar(self._button_map, self.config_ui)
        self.apps_box = widgets.VBox([app.run_form for app in self.apps])
        self.batch_form = widgets.VBox(
            [self.button_bar, self.layout_out, self.apps_box]
        )

    def display(self):
        display(self.batch_form)

    def _ipython_display_(self):
        self.display()
        
    @property
    def indices(self):
        return [r.run_id.index for r in self.apps]

    @property
    def checked(self):
        pass


if __name__ == "__main__":
    display(
        Markdown(
            """
Batch actions arranged in a container.
    """
        )
    )
    run0 = RunApp()
    run1 = RunApp(run_id=RunId(index=1))
    run_batch = RunApps(apps=[RunApp()])
    display(run_batch)
# -



run_batch.apps[0].__dict__.keys()

[r.run_id.index for r in run_batch.apps]

# +
# if __name__ == '__main__':
#     # from ipyrun._ipyeditcsv import EditRunAppCsv # TODO: i think there is an issue with "EditRunAppCsv" that needs fixing
#     # Example2 --------------------------
#     class RunAppEditCsvLineGraph(RunApp):

#         def __init__(self, config_app, app_config_revert_to_file=False):
#             super().__init__(config_app,app_config_revert_to_file=app_config_revert_to_file)

#         def _edit_inputs(self, sender):
#             with self.out:
#                 clear_output()
#                 display(EditRunAppCsv(self.config_app))

#         def execute(self):
#             fpth_csv = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.csv')
#             fpth_plotly = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.plotly.json')
#             subprocess.check_output(['python','-O', self.config_app.fpth_script, self.config_app.fpth_inputs, fpth_csv, fpth_plotly])
#             self.config_app.script_outputs = [Output(fpth_csv),Output(fpth_plotly)]


#     config_app_line_graph=AppConfig(
#             fpth_script=FPTH_SCRIPT_EXAMPLE_CSV,
#             fdir=FDIR_APP_EXAMPLE,
#             ftyp_inputs='csv'
#         )

#     rcsv = RunAppEditCsvLineGraph(config_app_line_graph)
#     display(rcsv)
# -




# +
def log(path_log): # TODO: do logging! 
    if type(path_log) == str:
        path_log = pathlib.Path(path_log)
    if path_log.is_file:
        self.df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
    else:
        di = {
            'processName':[],
            'user':[],
            'datetime':[],
            'formalIssue':[],
            'tags':[],
            'fpthInputs':[]
        }
        self.df_log = pd.DataFrame(di).rename_axis("index")

    user = getpass.getuser()
    timestamp = str(pd.to_datetime('today'))
    timestamp = timestamp[:-7]

    tmp = pd.DataFrame({
        'processName':[self.process_name],
        'user':[user],
        'datetime':[timestamp],
        'formalIssue':[''],
        'tags':[''],
        'fpthInputs':[self.fpth_inputs_archive]
    })
    self.df_log = self.df_log.append(tmp).reset_index(drop=True)
    make_dir(self.fdir_log)
    self.df_log.to_csv(self.fpth_log)
    return 
    
#path_log = '/mnt/c/engDev/git_mf/ipyrun/examples/J0000/test_appdir/appdata/log/log-expansion_vessel_sizing.csv'
