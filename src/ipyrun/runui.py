# ---
# jupyter:
#   jupytext:
#     formats: py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.6
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
from markdown import markdown

# object models
from typing import Dict, Type, Any
from pydantic import BaseModel

# widget stuff
import traitlets
from IPython.display import display, Markdown, clear_output
import ipywidgets as widgets

# core mf_modules
from ipyautoui.constants import TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT
from ipyautoui.custom import Dictionary, LoadProject

# from this repo
from ipyrun.actions import RunActions, BatchActions
from ipyrun.utils import make_dir, del_matching
from ipyrun.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    DI_STATUS_MAP,
    DEFAULT_BUTTON_STYLES,
)

# +
class UiComponents:
    def __init__(self, di_button_styles=DEFAULT_BUTTON_STYLES):
        self._init_UiButtons(di_button_styles)

    @property
    def di_button_styles(self):
        return self._di_button_styles

    @di_button_styles.setter
    def di_button_styles(self, value):
        for k, v in value.items():
            [setattr(getattr(self, k), k_, v_) for k_, v_ in v.items()]
        self._di_button_styles = value

    def _init_UiButtons(self, di_button_styles=DEFAULT_BUTTON_STYLES):
        self.check = widgets.Checkbox()
        self.status_indicator = widgets.Button()
        self.help_ui = widgets.ToggleButton()
        self.help_run = widgets.ToggleButton()
        self.help_config = widgets.ToggleButton()
        self.inputs = widgets.ToggleButton()
        self.outputs = widgets.ToggleButton()
        self.runlog = widgets.ToggleButton()
        self.run = widgets.Button()
        self.show = widgets.Button()
        self.hide = widgets.Button()

        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_runlog = widgets.Output()
        self.out_console = widgets.Output()

        self.di_button_styles = di_button_styles


if __name__ == "__main__":
    display(
        widgets.VBox(
            [
                widgets.HBox(
                    [widgets.HTML(f"<b>{k}</b>", layout={"width": "120px"}), v]
                )
                for k, v in UiComponents().__dict__.items()
                if k != "_di_button_styles"
            ]
        )
    )


# +
class RunUiConfig(BaseModel):
    include_show_hide = True


class RunActionsUi(traitlets.HasTraits, UiComponents):
    """maps the RunActions onto buttons. doesn't put them in a container.
    this is always used by the RunUi. the objects created here can then be placed
    appropriated in the RunUi container

    Returns:
        display: of buttons for testing
    """

    # TODO: make value == RunActions
    minwidth = BUTTON_WIDTH_MIN
    medwidth = BUTTON_WIDTH_MEDIUM
    _status = traitlets.Unicode()

    @traitlets.default("_status")
    def _default_status(self):
        return "no_outputs"

    @traitlets.validate("_status")
    def _validate_status(self, proposal):
        if proposal.value not in [
            "up_to_date",
            "no_outputs",
            "outputs_need_updating",
            "error",
        ]:
            raise ValueError(
                f'{proposal} given. allowed values of "status" are: "up_to_date", "no_outputs", "outputs_need_updating", "error" only'
            )
        return proposal

    def __init__(
        self, actions: RunActions = RunActions(), di_button_styles=DEFAULT_BUTTON_STYLES
    ):
        self._init_RunActionsUi(actions)

    def _init_RunActionsUi(self, actions, di_button_styles=DEFAULT_BUTTON_STYLES):
        self._init_UiButtons(di_button_styles)
        self.status = "no_outputs"
        self._actions = actions
        self._init_controls()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        self._actions = value

    @property
    def status(self):
        return self._status.value

    @status.setter
    def status(self, value):
        self._status = value
        self._style_status("click")

    # def _init_show_hide_functions(self): # TODO: decide what to do with the show hide buttons
    #     show_hide_buttons = ['help_ui', 'help_run', 'help_config', 'inputs', 'outputs', 'runlog']
    #     for b in show_hide_buttons:
    #         f = lambda self, on_change: self._show_hide_output(
    #             getattr(self, 'out_'+b),
    #             getattr(self, b),
    #             getattr(self.actions, b+'_show'),
    #             getattr(self.actions, b+'_hide')
    #         )
    #         setattr(self, '_'+b, f)

    def _init_controls(self):
        # show hide toggle widgets
        # self._init_show_hide_functions()
        self.help_ui.observe(self._help_ui, names="value")
        self.help_run.observe(self._help_run, names="value")
        self.help_config.observe(self._help_config, names="value")
        self.inputs.observe(self._inputs, names="value")
        self.outputs.observe(self._outputs, names="value")
        self.runlog.observe(self._runlog, names="value")

        self.run.on_click(self._run)
        self.check.observe(self._check, names="value")
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)
        self.observe(self._status, names="status")
        self.status_indicator.on_click(self._status_indicator)

    def _style_status(self, change):
        style = dict(DI_STATUS_MAP[self.status])
        [setattr(self.status_indicator, k, v) for k, v in style.items()]

    def _status_indicator(self, onclick):
        self.actions.get_status()

    def _show(self, on_click):
        """default show run data. TODO - move to actions"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = True
        self.outputs.value = True
        self.runlog.value = True

    def _hide(self, on_click):
        """default hide run data. TODO - move to actions"""
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

    # show_hide toggle buttons --------------
    def _show_hide_output(
        self, widgets_output, widget_button, show_action, hide_action
    ):
        with widgets_output:
            if widget_button.value:
                widget_button.layout.border = (
                    TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT  # 'solid yellow 2px'
                )
                show = show_action()
                if show is not None:
                    display(show)
            else:
                widget_button.layout.border = ""
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
            self.out_help_config,
            self.help_config,
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
            self.out_runlog,
            self.runlog,
            self.actions.runlog_show,
            self.actions.runlog_hide,
        )

    # ------------------------------------

    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_hide = widgets.Button(
                layout={"width": BUTTON_WIDTH_MIN},
                icon="fa-times",
                button_style="danger",
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

    # for testing / explanation only -----
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

    # ------------------------------------


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
    run_actions_ui = RunActionsUi()
    display(run_actions_ui)

# -

if __name__ == "__main__":
    actions = RunActions()
    actions.inputs_show = lambda: "asdfasfdasdfasdf"
    run_actions_ui.actions = actions
    run_actions_ui.status = "up_to_date"


# +
class RunUi(RunActionsUi):  # widgets.HBox
    """takes run_actions object as an argument and initiates UI objects using 
    RunActionsUi. This class places these objects in containers to create a 
    more readable interface"""

    def __init__(self, run_actions=RunActions(), name="name", include_show_hide=True):
        self._init_UiButtons()
        self._init_RunActionsUi(run_actions)
        self.name = name
        self._init_show_hide(include_show_hide)
        self._layout_out()
        self._run_form()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        self._actions = value
        self.update_form()

    def _init_show_hide(self, include_show_hide):
        if not include_show_hide:
            self.include_show_hide = None
        else:
            self.include_show_hide = include_show_hide

    def _layout_out(self):  # TODO: update this so boxes empty
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

    @property
    def button_map(self):
        return {
            "outside": {
                self.check: self.actions.check,
                self.status_indicator: self.actions.get_status,
            },
            "left": {
                self.help_ui: self.actions.help_ui_show,
                self.help_run: self.actions.help_run_show,
                self.help_config: self.actions.help_config_show,
                self.show_hide_box: self.include_show_hide,
                self.inputs: self.actions.inputs_show,
                self.outputs: self.actions.outputs_show,
                self.runlog: self.actions.runlog_show,
                self.run: self.actions.run,
            },
            # "right": {self.show: self.include_show_hide,
            #           self.hide: self.include_show_hide},
        }

    def update_form(self):
        """update the form if the actions have changed"""
        self.button_bar_left.children = [
            k for k, v in self.button_map["left"].items() if v is not None
        ]
        # self.button_bar_right.children = [k for k, v in self.button_map["right"].items() if v is not None]
        check = [k for k, v in self.button_map["outside"].items() if v is not None]
        self.run_form.children = check + [self.acc]
        self.acc.set_title(0, self.name)

    def _run_form(self):
        self.run_form = widgets.HBox(layout=widgets.Layout(width="100%"))
        self.show_hide_box = widgets.HBox(
            [self.show, self.hide],
            layout=widgets.Layout(align_items="stretch", border="solid LightSeaGreen"),
        )  # fcec90
        self.button_bar = widgets.HBox(
            layout=widgets.Layout(width="100%", justify_content="space-between")
        )
        self.button_bar_left = widgets.HBox(
            layout=widgets.Layout(align_items="stretch")
        )
        self.button_bar_right = widgets.HBox(
            layout=widgets.Layout(align_items="stretch")
        )
        self.button_bar.children = [self.button_bar_left, self.button_bar_right]
        self.acc = widgets.Accordion(
            children=[widgets.VBox([self.button_bar, self.layout_out])],
            selected_index=None,
            layout=widgets.Layout(width="100%"),
        )
        self.update_form()


if __name__ == "__main__":
    run_actions = RunActions()
    run_ui = RunUi(run_actions=run_actions)
    display(run_ui.run_form)

    run_actions1 = RunActions()
    run_ui1 = RunUi(run_actions=run_actions1)
    display(run_ui1.run_form)
# -

if __name__ == "__main__":
    # actions can be changed on the fly and the form will update
    # but the whole actions object must be updated rather than component parts
    actions = run_ui.actions
    actions.help_ui_show = None
    run_ui.actions = actions


# +
class RunApp(widgets.HBox):
    def __init__(
        self,
        config: Any,
        cls_ui: Type[widgets.Box] = RunUi,
        cls_actions: Type[BaseModel] = RunActions,
    ):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 

        Args:
            config: Any
            cls_ui: 
            cls_actions: a RunActions class. can be extended with validators for but names must remain
        """
        super().__init__(layout=widgets.Layout(flex="100%"))
        try:
            name = config.pretty_name
        except:
            name = None
        self.ui = cls_ui(run_actions=RunActions(), name=name)
        self.children = [self.ui.run_form]
        # self.ui_box = cls_ui(run_actions=RunActions(), name=config.pretty_name) # init with defaults
        self.cls_actions = cls_actions
        self.config = config  # the setter updates the ui.actions using fn_buildactions. can be updated on the fly
        self.update_status()

    @property
    def config(self):
        return self.ui.actions.config

    @config.setter
    def config(self, value):
        self.ui.actions = self.cls_actions(config=value, app=self)
        self.ui.actions.save_config()

    @property
    def actions(self):
        return self.ui.actions

    @actions.setter
    def actions(self, value):
        self.ui.actions = value

    def update_status(self):
        self.actions.update_status()


if __name__ == "__main__":
    from ipyrun.runshell import ConfigActionsShell

    config = ConfigActionsShell(fpth_script="script.py", pretty_name="pretty name")
    app = RunApp(config)
    display(app)

# + tags=[]
class BatchActionsUi(RunActionsUi):
    """maps actions to buttons

    Args:
        RunActionsUi ([type]): inherits majority of definitions from RunActionsUi
    """

    def __init__(
        self,
        batch_actions: BatchActions = BatchActions(),
        di_button_styles=DEFAULT_BUTTON_STYLES,
    ):
        self._init_BatchActionsUi(batch_actions, di_button_styles=di_button_styles)

    def _init_BatchActionsUi(self, actions, di_button_styles=DEFAULT_BUTTON_STYLES):
        self._init_RunActionsUi(actions, di_button_styles=DEFAULT_BUTTON_STYLES)
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
            icon="exchange-alt",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="warning",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.load_project = LoadProject()
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
                self.load_project,
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


# -

class BatchUi(BatchActionsUi):
    """Manage an array of RunApps

    Args:
        BatchActionsUi ([type]): [description]
    """

    def __init__(
        self,
        batch_actions: BatchActions(wizard_show=None),
        title: str = "# markdown batch title",
        include_show_hide=True,
        runs: Dict[str, Type[RunUi]] = None,
        fn_add=None,
        cls_runs_box=Dictionary,
    ):
        self._init_BatchActionsUi(batch_actions)
        self.cls_runs_box = cls_runs_box
        self.fn_add = fn_add
        self._init_show_hide(include_show_hide)
        self.title = widgets.HTML(markdown(title))
        self._layout_out()
        self._run_form()
        self._update_batch_controls()
        if runs is None:
            runs = {}
        self.runs.items = runs

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        self._actions = value
        self.update_form()

    def _init_show_hide(self, include_show_hide):
        if not include_show_hide:
            self.include_show_hide = None
        else:
            self.include_show_hide = include_show_hide

    def _update_batch_controls(self):
        self.check.observe(self.check_all, names="value")

    def check_all(self, onchange):
        for k, v in self.apps.items():
            v.check.value = self.check.value

    @property
    def button_map(self):
        return {
            "outside": {self.check: self.actions.check},
            "left": {
                self.help_ui: self.actions.help_ui_show,
                self.help_run: self.actions.help_run_show,
                self.help_config: self.actions.help_config_show,
                self.show_hide_box: self.include_show_hide,
                self.inputs: self.actions.inputs_show,
                self.outputs: self.actions.outputs_show,
                self.runlog: self.actions.runlog_show,
                self.run: self.actions.run,
                self.add: self.actions.add_show,
                self.remove: self.actions.remove_show,
                self.wizard: self.actions.wizard_show,
            },
            # "right": {self.show: self.include_show_hide,
            #           self.hide: self.include_show_hide},
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
                widgets.HBox([self.out_add, self.out_remove, self.out_wizard],),
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

    def update_form(self):
        """update the form if the actions have changed"""
        self.button_bar_left.children = [
            k for k, v in self.button_map["left"].items() if v is not None
        ]
        # self.button_bar_right.children = [k for k, v in self.button_map["right"].items() if v is not None]
        check = [k for k, v in self.button_map["outside"].items() if v is not None]
        self.top_bar.children = check + [self.button_bar]
        self.batch_form.children = [
            self.title,
            self.top_bar,
            self.layout_out,
            self.runs,
        ]

    def _run_form(self):
        self.batch_form = widgets.VBox()
        self.show_hide_box = widgets.HBox(
            [self.show, self.hide],
            layout=widgets.Layout(align_items="stretch", border="solid LightSeaGreen"),
        )
        self.button_bar = widgets.HBox(
            layout=widgets.Layout(width="100%", justify_content="space-between")
        )
        self.button_bar_left = widgets.HBox(
            layout=widgets.Layout(align_items="stretch")
        )
        self.button_bar_right = widgets.HBox(
            layout=widgets.Layout(align_items="stretch")
        )
        self.button_bar.children = (
            [self.button_bar_left] + [self.button_bar_right] + [self.load_project]
        )
        self.top_bar = widgets.HBox(
            layout=widgets.Layout(width="100%", justify_content="space-between")
        )
        self.runs = self.cls_runs_box(
            toggle=False,
            watch_value=False,
            add_remove_controls=None,
            fn_add=self.fn_add,
            show_hash=None,
        )
        self.update_form()


if __name__ == "__main__":
    config = ConfigActionsShell(
        fpth_script="script.py", pretty_name="00-lean-description"
    )
    config = ConfigActionsShell(
        fpth_script="script.py", pretty_name="01-lean-description"
    )
    run0 = RunApp(config)
    run1 = RunApp(config)

    def add_show(cls=None):
        return "add"

    batch_actions = BatchActions(  # add_show=add_show,
        inputs_show=None, outputs_show=None, runlog_show=None, wizard_show=None
    )
    ui_actions = BatchActionsUi(batch_actions=batch_actions)
    run_batch = BatchUi(
        runs={"01-lean-description": run0, "02-lean-description": run1},
        batch_actions=batch_actions,
    )
    display(run_batch.batch_form)


# +
class BatchApp(widgets.VBox):
    def __init__(
        self,
        config: Any,
        cls_ui: Type[widgets.Box] = BatchUi,
        cls_actions: Type[BaseModel] = BatchActions,
    ):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 

        Args:
            config: Type[BaseModel]
        """
        super().__init__(
            layout=widgets.Layout(flex="100%")
        )  # , flex="flex-grow"display="flex",
        try:
            title = config.pretty_name
        except:
            title = ""
        self.ui = cls_ui(batch_actions=BatchActions(), title=title)
        self.children = [self.ui.batch_form]
        self.cls_actions = cls_actions
        self.config = config  # the setter updates the ui.actions

    @property
    def run_actions(self):
        return [v.ui.actions for k, v in self.runs.items.items()]

    @property
    def runs(self):
        return self.ui.runs

    @property
    def config(self):
        return self.ui.actions.config

    @config.setter
    def config(self, value):
        self.ui.actions = self.cls_actions(config=value, app=self)
        self.ui.actions.save_config()
        try:
            self.runs.items = {
                c.key: self.make_run(c) for c in self.config.configs
            }  # TODO: this code isn't generic!
        except:
            print("error building runs fron config")
            print(f"self.config == {str(self.config)}")
        self.update_in_batch()
 
    def update_in_batch(self): # TODO: remove config dependent code? 
        for k, v in self.runs.items.items():
            v.ui.check.value = v.config.in_batch
            
    def check_all(self, onchange):
        for k, v in self.apps.items():
            v.check.value = self.check.value
        
    def update_status(self):
        self.ui.actions.update_status()
        
    def make_run(self, config):
        """builds RunApp from config"""
        return self.config.cls_app(config)

    def configs_append(self, config):  # TODO: remove config dependent code? 
        self.ui.actions.config.configs.append(config)
        self.ui.actions.save_config()
        newapp = self.make_run(config)
        self.runs.add_row(new_key=config.key, item=newapp)
        self.update_in_batch()

    def configs_remove(self, key):  # TODO: remove config dependent code? 
        self.config.configs = [c for c in self.config.configs if c.key != key]
        self.update_in_batch()

    @property
    def actions(self):
        return self.ui.actions


# -


if __name__ == "__main__":
    from ipyrun.runshell import ConfigBatch
    config_batch = ConfigBatch(fdir_root='.', fpth_script='script.py', configs=[config.dict()]) # create simple example... 
    batch_app = BatchApp(None)
    display(batch_app)

# +
import pandas as pd
import getpass
import pathlib


def runlog(path_runlog):  # TODO: do runlogging!
    if type(path_runlog) == str:
        path_runlog = pathlib.Path(path_runlog)
    if path_runlog.is_file:
        self.df_runlog = del_matching(pd.read_csv(self.fpth_runlog), "Unnamed")
    else:
        di = {
            "processName": [],
            "user": [],
            "datetime": [],
            "formalIssue": [],
            "tags": [],
            "fpthInputs": [],
        }
        self.df_runlog = pd.DataFrame(di).rename_axis("index")

    user = getpass.getuser()
    timestamp = str(pd.to_datetime("today"))
    timestamp = timestamp[:-7]

    tmp = pd.DataFrame(
        {
            "processName": [self.process_name],
            "user": [user],
            "datetime": [timestamp],
            "formalIssue": [""],
            "tags": [""],
            "fpthInputs": [self.fpth_inputs_archive],
        }
    )
    self.df_runlog = self.df_runlog.append(tmp).reset_index(drop=True)
    make_dir(self.fdir_runlog)
    self.df_runlog.to_csv(self.fpth_runlog)
    return


# path_runlog = '/mnt/c/engDev/git_mf/ipyrun/examples/J0000/test_appdir/appdata/runlog/runlog-expansion_vessel_sizing.csv'


# -
if __name__ == "__main__":
    display(Markdown("change add remove to ToggleButtons? (probs not)"))
    display(
        widgets.HBox(
            [
                widgets.ToggleButtons(
                    options=[("", 0), (" ", 1), ("  ", 2)],
                    value=1,
                    icons=["plus", "", "minus"],
                    tooltips=[
                        "add a process",
                        "hide add / remove dialogue",
                        "remove a process",
                    ],
                    style=widgets.ToggleButtonsStyle(button_width="20px"),
                    layout=widgets.Layout(border="solid yellow"),
                ),
            ]
        )
    )

