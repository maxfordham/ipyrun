# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.3
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
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
from markdown import markdown
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

def _markdown(value='_Markdown_',
              **kwargs):
    """
    a simple template for markdown text input that templates required input
    fields. additional user defined fields can be added as kwargs
    """
    _kwargs = {}
    _kwargs['value'] = markdown(value)  # required field
    _kwargs.update(kwargs)  # user overides
    return widgets.HTML(**_kwargs)


# +
# RUN __FUTURE__
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
    get_status: typing.Optional[typing.Callable] = lambda: display("get_status")
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
    runlog_show: typing.Optional[typing.Callable] = lambda: display("runlog_show")
    runlog_hide: typing.Optional[typing.Callable] = lambda: display("runlog_hide")
    run: typing.Optional[typing.Callable] = lambda: display("run")
    run_hide: typing.Optional[typing.Callable] = lambda: display("console_hide")
    activate: typing.Optional[typing.Callable] = lambda: display("activate")
    deactivate: typing.Optional[typing.Callable] = lambda: display("deactivate")


#     show: typing.Optional[typing.Callable] = (lambda : display('show'))
#     hide: typing.Optional[typing.Callable] = (lambda : display('hide'))


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





if __name__ == "__main__":
    display(
        Markdown(
            """
### RunAppConfig

This is everything that will be passed to the RunApp on initialisation
    """
        )
    )
    #display(Markdown("`>>> display(RunAppConfig().dict())`"))
    #display(RunAppConfig().dict())
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
    #display(Markdown("`>>> display(BatchAppConfig().dict())`"))
    #display(BatchAppConfig().dict())
    display(Markdown("`>>> display(BatchActions().dict())`"))
    display(BatchActions().dict())


# +
import traitlets
from ipyrun.constants import STATUS_BUTTON_NEEDSRERUN, STATUS_BUTTON_NOOUTPUTS, STATUS_BUTTON_UPTODATE, DI_STATUS_MAP
#from traitelt

class RunActionsUi(traitlets.HasTraits):
    """maps the RunActions onto buttons. doesn't put them in a container.

    Returns:
        display: of buttons for testing
    """
    # TODO: make value == RunActions
    minwidth = BUTTON_WIDTH_MIN
    medwidth = BUTTON_WIDTH_MEDIUM
    status = traitlets.Unicode()
    
    @traitlets.validate("status")
    def _status(self, proposal):
        if proposal.value not in ["up_to_date", "no_outputs", "outputs_need_updating"]:
            raise ValueError(
                f'{proposal} given. allowed values of "status" are: "up_to_date", "no_outputs", "outputs_need_updating" only'
            )
        return proposal

    def __init__(self, actions: RunActions = RunActions()): #, checked=True
        #self.checked = checked
        self._init_RunActionsUi(actions)
        self.status = 'no_outputs'
        
    def _init_RunActionsUi(self, actions):
        
        self.actions = self._init_actions(actions)
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

    def _init_actions(
        self, actions: typing.Type[RunActions]
    ) -> typing.Type[RunActions]:
        """this allows us to pass the RunApp object to the Run Actions. TODO: describe better! """
        return type(actions)(
            **{k: self._init_run_action(v) for k, v in actions.dict().items()}
        )
    
    def _init_actions(self, actions):
        return actions

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
        #         self.runlog
        #         self.check
        #         self.run
        #         self.show
        #         self.hide
        """
    
        self.check = widgets.Checkbox(
            value=False, # self.checked
            disabled=False,
            indent=False,
            layout=widgets.Layout(max_width="20px", 
                                  height="40px", 
                                  padding="3px", 
                                  #border='3px solid green'
                                 ),
        )
        #self.check_uptodate = widgets.HBox(layout={'border':'3px solid green'})
        self.status_indicator = widgets.Button(**STATUS_BUTTON_NOOUTPUTS)
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
        self.runlog = widgets.ToggleButton(
            description="runlog",
            tooltip="show a runlog of when the script was executed to generate the outputs, and by who",
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
        self.out_runlog = widgets.Output()
        self.out_console = widgets.Output()

    def _init_controls(self):
        self.help_ui.observe(self._help_ui, names="value")
        self.help_run.observe(self._help_run, names="value")
        self.help_config.observe(self._help_run, names="value")
        self.inputs.observe(self._inputs, names="value")
        self.outputs.observe(self._outputs, names="value")
        self.runlog.observe(self._runlog, names="value")
        self.run.on_click(self._run)
        self.check.observe(self._check, names="value")
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)
        self.observe(self._status, names="status")
        self.status_indicator.on_click(self._status_indicator)
        
    def _status(self, change):
        style = DI_STATUS_MAP[self.status]
        [setattr(self.status_indicator, k, v) for k, v in style.items()];
        #
    def _status_indicator(self, onclick):
        self.actions.get_status()

    @property
    def get_show_hide_value(self):
        return [
            self.help_ui.value,
            self.help_run.value,
            self.help_config.value,
            self.inputs.value,
            self.outputs.value,
            self.runlog.value,
        ]
    
    def _show(self, on_click):
        """default show run data"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = True
        self.outputs.value = True
        self.runlog.value = True

    def _hide(self, on_click):
        """default hide run data"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = False
        self.outputs.value = False
        self.runlog.value = False
        with self.out_console:
            clear_output()

    def _check(self, on_change):
        if self.check.value:
            self.actions.check()
        else:
            self.actions.uncheck()

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
            self.actions.help_ui_show,
            self.actions.help_ui_hide,
        )

    def _help_run(self, on_change):
        self._show_hide_output(
            self.out_help_run,
            self.help_run,
            self.actions.help_run_show,
            self.actions.help_run_hide,
        )

    def _help_config(self, on_change):
        self._show_hide_output(
            self.out_help_run,
            self.help_run,
            self.actions.help_config_show,
            self.actions.help_config_hide,
        )

    def _inputs(self, on_change):
        self._show_hide_output(
            self.out_inputs,
            self.inputs,
            self.actions.inputs_show,
            self.actions.inputs_hide,
        )

    def _outputs(self, on_change):
        self._show_hide_output(
            self.out_outputs,
            self.outputs,
            self.actions.outputs_show,
            self.actions.outputs_hide,
        )

    def _runlog(self, on_change):
        self._show_hide_output(
            self.out_runlog, self.runlog, self.actions.runlog_show, self.actions.runlog_hide
        )

    def _run(self, on_change):
        with self.out_console:
            self.run_hide = widgets.Button(
                layout={"width": BUTTON_WIDTH_MIN}, icon="fa-times", button_style="danger"
            )
            self.run_hide.on_click(self._run_hide)
            display(self.run_hide)
            self.actions.run()
            # reload outputs
            self.outputs.value = False
            self.outputs.value = True
            
    def _run_hide(self, click):
        with self.out_console:
            clear_output()

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
                widgets.HBox([self.runlog, self.out_runlog]),
                widgets.HBox([self.check]),
                widgets.HBox([self.status_indicator]),
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
    ui_actions = RunActionsUi()
    display(ui_actions)


# +
def build_button_bar(button_map: typing.Dict, config_ui: RunUiConfig):
    button_bar = widgets.HBox(
        layout=widgets.Layout(width="100%", justify_content="space-between")
    )
    left = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
    left.children = [k for k, v in button_map["left"].items() if v is not None]
    button_bar.children = [left]

    # outside = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
    # outside.children = [k for k, v in button_map["outside"].items() if v is not None]
    # button_bar.children = [outside, left]
    
    if config_ui.include_show_hide:
        right = widgets.HBox(
            button_map["right"], layout=widgets.Layout(align_items="stretch")
        )
        button_bar.children = [left, right]
    return button_bar


class RunUi(RunActionsUi):#widgets.HBox, 
    """wrapper that extends RunActionsUi to create UI form. config data that defines
    the functionality of the App are passed as arguments that give the App its
    functionality."""

    def __init__(
        self,
        actions: RunActions = RunActions(),
        #checked: bool = True,
        name: str ='run name',
        config_ui: RunUiConfig = RunUiConfig(),
        #config_actions: typing.Any = None,
    ):
        #self.checked = checked
        self._init_RunActionsUi(actions)
        self.name = name
        self.config_ui = config_ui
        #self.config_actions = config_actions
        self._layout_out()
        self._run_form()


    @property
    def _button_map(self):
        return {
            "outside": {self.check: self.actions.check},
            "left": {
                self.help_ui: self.actions.help_ui_show,
                self.help_run: self.actions.help_run_show,
                self.help_config: self.actions.help_config_show,
                self.inputs: self.actions.inputs_show,
                self.outputs: self.actions.outputs_show,
                self.runlog: self.actions.runlog_show,
                self.run: self.actions.run,
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
                    [self.out_inputs, self.out_outputs, self.out_runlog],
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
        #self.layout = 
        self.acc = widgets.Accordion(
            children=[widgets.VBox([self.button_bar, self.layout_out])],
            selected_index=None,
            layout=widgets.Layout(width="100%"),
        )
        self.acc.set_title(0, self.name)
        #self.check_uptodate.children = [self.check]
        self.run_form = widgets.HBox([self.check, self.status_indicator, self.acc])
        # super().__init__(
        #     [self.check, self.acc],
        #     #layout=widgets.Layout(margin="0px", padding="0px", border="0px"),
        # ) 

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
    run = RunUi()
    display(run)


# +
class BatchActionsUi(RunActionsUi):
    """maps actions to buttons

    Args:
        RunActionsUi ([type]): inherits majority of definitions from RunActionsUi
    """

    def __init__(
        self, actions: BatchActions = BatchActions()):
        self._init_BatchActionsUi(actions)
        
    def _init_BatchActionsUi(self, actions):
        super().__init__(actions=actions)
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
            self.out_add, self.add, self.actions.add_show, self.actions.add_hide
        )

    def _remove(self, on_change):
        self._show_hide_output(
            self.out_remove,
            self.remove,
            self.actions.remove_show,
            self.actions.remove_hide,
        )

    def _wizard(self, on_change):
        self._show_hide_output(
            self.out_wizard,
            self.wizard,
            self.actions.wizard_show,
            self.actions.wizard_hide,
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
                widgets.HBox([self.runlog, self.out_runlog]),
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
class BatchUi(BatchActionsUi):
    """Manage an array of RunApps

    Args:
        BatchActionsUi ([type]): [description]
    """

    def __init__(
        self,
        actions: BatchActions = BatchActions(),
        title: str = 'batch title',
        config_ui: RunUiConfig = RunUiConfig(),
        apps: typing.List[typing.Type[RunUi]] = None,
    ):
        self._init_BatchActionsUi(actions) # super().__init__(actions=actions)
        self.config_ui = config_ui
        self.apps = apps
        self.title=_markdown(title)
        if self.apps is None:
            self.apps = []
        self._layout_out()
        self._run_form()
        self._update_controls()
        
    def _update_controls(self):
        self.check.observe(self.check_all, names='value')
        
    def check_all(self, onchange):
        for a in self.apps:
            a.check.value = self.check.value

    @property
    def _button_map(self):
        return {
            #"outside": {self.check: self.actions.check},
            "left": {
                self.help_ui: self.actions.help_ui_show,
                self.help_run: self.actions.help_run_show,
                self.help_config: self.actions.help_config_show,
                self.inputs: self.actions.inputs_show,
                self.outputs: self.actions.outputs_show,
                self.runlog: self.actions.runlog_show,
                self.run: self.actions.run,
                self.add: self.actions.add_show,
                self.remove: self.actions.remove_show,
                self.wizard: self.actions.wizard_show,
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
                    [self.out_inputs, self.out_outputs, self.out_runlog],
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
        self.top_bar = widgets.HBox([self.check, self.button_bar])
        self.apps_box = widgets.VBox([app.run_form for app in self.apps]) #.run_form
        self.batch_form = widgets.VBox(
            [self.title, self.top_bar, self.layout_out, self.apps_box]
        )
        # super().__init__(
        #     [self.top_bar, self.layout_out, self.apps_box],
        #     #layout=widgets.Layout(margin="0px", padding="0px", border="0px"),
        # ) 
    def display(self):
        display(self.batch_form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":

    run0 = RunUi()
    run1 = RunUi(name='asdf')
    run_batch = BatchUi(apps=[run0, run1], title='# a batch process')
    display(run_batch)
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
# +
def runlog(path_runlog): # TODO: do runlogging! 
    if type(path_runlog) == str:
        path_runlog = pathlib.Path(path_runlog)
    if path_runlog.is_file:
        self.df_runlog = del_matching(pd.read_csv(self.fpth_runlog),'Unnamed')
    else:
        di = {
            'processName':[],
            'user':[],
            'datetime':[],
            'formalIssue':[],
            'tags':[],
            'fpthInputs':[]
        }
        self.df_runlog = pd.DataFrame(di).rename_axis("index")

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
    self.df_runlog = self.df_runlog.append(tmp).reset_index(drop=True)
    make_dir(self.fdir_runlog)
    self.df_runlog.to_csv(self.fpth_runlog)
    return 
    
#path_runlog = '/mnt/c/engDev/git_mf/ipyrun/examples/J0000/test_appdir/appdata/runlog/runlog-expansion_vessel_sizing.csv'
# -




