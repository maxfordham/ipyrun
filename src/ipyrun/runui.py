# ---
# jupyter:
#   jupytext:
#     formats: py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
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
from ipyrun.actions import RunActions, BatchActions, DefaultRunActions
from ipyrun._utils import make_dir, del_matching, validate
from ipyrun.constants import (
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    DI_STATUS_MAP,
    DEFAULT_BUTTON_STYLES,
)
from ipyrun.constants import ADD, REMOVE, WIZARD
from ipyautoui.custom import FileChooser


# +
class UiComponents:
    def __init__(
        self,
        di_button_styles=DEFAULT_BUTTON_STYLES,
        container=widgets.Accordion,
        select=FileChooser,
    ):
        self._init_UiButtons(
            di_button_styles=di_button_styles, container=container, select=select
        )

    @property
    def di_button_styles(self):
        return self._di_button_styles

    @di_button_styles.setter
    def di_button_styles(self, value):
        for k, v in value.items():
            [
                setattr(getattr(self, k), k_, v_)
                for k_, v_ in v.items()
                if k_ in getattr(self, k).traits()
            ]
        self._di_button_styles = value

    def _init_UiButtons(
        self,
        di_button_styles=DEFAULT_BUTTON_STYLES,
        container=widgets.Accordion,
        select=FileChooser,
    ):
        self.check = widgets.Checkbox()
        self.status_indicator = widgets.Button(disabled=True)
        self.help_ui = widgets.ToggleButton()
        self.help_run = widgets.ToggleButton()
        self.help_config = widgets.ToggleButton()
        self.inputs = widgets.ToggleButton()
        self.outputs = widgets.ToggleButton()
        self.runlog = widgets.ToggleButton()
        self.run = widgets.Button()
        self.show = widgets.Button()
        self.hide = widgets.Button()
        self.load = widgets.Button()
        self.container = container([widgets.HTML("container")])
        if select is not None:
            self.select = select()

        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_runlog = widgets.Output()
        self.out_console = widgets.Output()

        self.di_button_styles = di_button_styles

        # self.selector = File


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
# -

if __name__ == "__main__":
    from ipyrun._utils import display_ui_tooltips

    uiobj = UiComponents()
    display(display_ui_tooltips(uiobj))


# +
class RunUiConfig(BaseModel):
    include_show_hide = True


class RunActionsUi(UiComponents):
    """maps the RunActions onto buttons. doesn't put them in a container.
    this is always used by the RunUi. the objects created here can then be placed
    appropriated in the RunUi container

    Returns:
        display: of buttons for testing
    """

    minwidth = BUTTON_WIDTH_MIN
    medwidth = BUTTON_WIDTH_MEDIUM


    def __init__(
        self, actions: RunActions = RunActions(), di_button_styles=DEFAULT_BUTTON_STYLES
    ):
        self._init_RunActionsUi(actions)

    def _init_RunActionsUi(self, actions, di_button_styles=DEFAULT_BUTTON_STYLES):
        self._init_UiButtons(di_button_styles)
        # self.status = "no_outputs"
        self.actions = actions
        self._init_controls()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        cl = type(value)
        di = value.dict()
        di["app"] = self
        self._actions = cl(**di)

        # value.app = self
        # self._actions = value
        # validate(self._actions)
        # ^ this not working
        # ^ TODO: https://github.com/samuelcolvin/pydantic/issues/1864#issuecomment-679044432

    def _status_indicator(self, onclick):
        self.actions.get_status()

    def _init_controls(self):
        self.help_ui.observe(self._help_ui, names="value")
        self.help_run.observe(self._help_run, names="value")
        self.help_config.observe(self._help_config, names="value")
        self.inputs.observe(self._inputs, names="value")
        self.outputs.observe(self._outputs, names="value")
        self.runlog.observe(self._runlog, names="value")
        if "selected_index" in self.container.traits():
            self.container.observe(self._container, names="selected_index")
        self.run.on_click(self._run)
        self.check.observe(self._check, names="value")
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)
        self.status_indicator.on_click(self._status_indicator)
        if self.load is not None:
            self.load.on_click(self._load)

    def _load(self, on_click):
        """default show run data. TODO - move to actions"""
        try:
            v = self.select.value
        except:
            ValueError(
                "a select widget with a value trait must be passed for actions.load to work"
            )
        self.actions.load(v)

    def _container(self, on_change):
        if self.container.selected_index is None:
            self.actions.deactivate()
        else:
            self.actions.activate()

    def _show(self, on_click):
        """default show run data. TODO - move to actions"""
        self.actions.show()

    def _hide(self, on_click):
        """default hide run data. TODO - move to actions"""
        self.actions.hide()

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

                if show_action is not None:
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

    @property
    def map_actions(self):
        return {
            self.check: self.actions.check,
            self.status_indicator: self.actions.get_status,
            self.help_ui: self.actions.help_ui_show,
            self.help_run: self.actions.help_run_show,
            self.help_config: self.actions.help_config_show,
            self.inputs: self.actions.inputs_show,
            self.outputs: self.actions.outputs_show,
            self.runlog: self.actions.runlog_show,
            self.run: self.actions.run,
            self.show: self.actions.show,
            self.hide: self.actions.hide,
            self.load: self.actions.load,
        }

    def get_buttons(self, li_buttons):
        return [
            getattr(self, l)
            for l in li_buttons
            if self.map_actions[getattr(self, l)] is not None
        ]

    def _run_hide(self, click):
        with self.out_console:
            clear_output()


def test_display_runapp(app):
    """note. this is for dev only. this class is designed to be inherited into a form
    where the display method is overwritten"""
    app.out = widgets.VBox(
        [
            widgets.HBox([app.help_ui, app.out_help_ui]),
            widgets.HBox([app.help_run, app.out_help_run]),
            widgets.HBox([app.help_config, app.out_help_config]),
            widgets.HBox([app.inputs, app.out_inputs]),
            widgets.HBox([app.outputs, app.out_outputs]),
            widgets.HBox([app.runlog, app.out_runlog]),
            widgets.HBox([app.check]),
            widgets.HBox([app.status_indicator]),
            widgets.HBox([app.run, app.out_console]),
            widgets.HBox([app.show]),
            widgets.HBox([app.hide]),
            widgets.HBox([app.container]),
            widgets.HBox([app.load, app.select]),
        ]
    )
    display(widgets.HTML("<b>Buttons to be programmed from `RunActions`</b> "))
    display(app.out)

    # ------------------------------------


# ui_controller
# ui_output
# actions
# action_type

if __name__ == "__main__":

    display(
        Markdown(
            """
### RunActionsUi

These are all of the buttons that will be linked to callables in RunActions
    """
        )
    )
    from ipyrun.actions import DefaultRunActions
    from pydantic import validator
    import functools

    display(Markdown("`>>> display(RunActionsUi())`"))
    actions = DefaultRunActions(check=None)
    run_actions_ui = RunActionsUi(actions)
    test_display_runapp(run_actions_ui)
# -

if __name__ == "__main__":
    actions = RunActions()
    actions.inputs_show = lambda: "asdfasfdasdfasdf"
    run_actions_ui.actions = actions
    run_actions_ui.status = "up_to_date"


# +
class RunUi(RunActionsUi):
    """takes run_actions object as an argument and initiates UI objects using
    RunActionsUi. This class places these objects in containers to create a
    more readable interface"""

    def __init__(self, run_actions=RunActions(), name="name"):
        self._init_RunUi(name, run_actions)

    def _init_RunUi(self, name, run_actions):
        self.name = name
        self._init_form()
        self._init_RunActionsUi(run_actions)

    #         self._update_controls()

    #     def _update_controls(self):
    #         self.out_inputs.observe(self._update_out, names='outputs')
    #         self.out_outputs.observe(self._update_out, names='outputs')
    #         self.out_runlog.observe(self._update_out, names='outputs')

    #     def _update_out(self, on_change): # TODO: this isnt working properly
    #         out = [self.out_inputs, self.out_outputs, self.out_runlog]
    #         self.out_box_main.children = [o for o in out if len(o.outputs) > 0]
    # TODO: make something like this ^ work.
    #     : use ipyflex !!!
    # ^ the goal is to let the inputs or outputs take full width if only 1 is selected...

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        cl = type(value)
        di = value.dict()
        di["app"] = self
        self._actions = cl(**di)
        self.update_form()

        # value.app = self
        # self._actions = value
        # validate(self._actions)
        # ^ this not working
        # ^ TODO: https://github.com/samuelcolvin/pydantic/issues/1864#issuecomment-679044432

    def update_form(self):
        """update the form if the actions have changed"""
        # self._layout_out()
        self.layout_out.children = [
            self.out_console,
            self.out_help_ui,
            self.out_box_help,
            self.out_box_main,
        ]
        self.out_box_help.children = [self.out_help_run, self.out_help_config]
        self.out_box_main.children = [
            self.out_inputs,
            self.out_outputs,
            self.out_runlog,
        ]

        self.container.children = [widgets.VBox([self.button_bar, self.layout_out])]
        self.button_bar_left.children = self.get_buttons(
            [
                "help_ui",
                "help_run",
                "help_config",
                "show",
                "inputs",
                "outputs",
                "runlog",
                "run",
            ]
        )
        self.button_bar_right.children = self.get_buttons(["load"])  # , 'select'
        self.run_form.children = self.get_buttons(["check", "status_indicator"]) + [
            self.container
        ]
        try:
            self.container.set_title(0, self.name)
        except:
            pass

    def _init_form(self):
        # buttons
        self.run_form = widgets.HBox(layout=widgets.Layout(width="100%"))
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

        # out # update the output to use ipyflex
        self.layout_out = widgets.VBox(
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                align_content="stretch",
                display="flex",
                flex="flex-grow",
            ),
        )
        self.out_box_help = widgets.HBox(
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                justify_content="space-between",
                align_content="stretch",
            ),
        )
        self.out_box_main = widgets.HBox(
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                justify_content="space-between",
                align_content="stretch",
            ),
        )


if __name__ == "__main__":
    run_actions = RunActions()
    run_ui = RunUi(run_actions=run_actions)
    display(run_ui.run_form)

    run_actions1 = DefaultRunActions(check=None)
    run_ui1 = RunUi(run_actions=run_actions1)
    display(run_ui1.run_form)
# -

if __name__ == "__main__":
    # actions can be changed on the fly and the form will update
    # but the whole actions object must be updated rather than component parts
    actions = run_ui.actions
    actions.help_ui_show = None
    run_ui.actions = actions



class RunApp(widgets.HBox, RunUi):
    """
    The goal of RunApp is to simplify the process of making a functional UI that interacts
    with remote data for use in a Jupyter Notebook or Voila App. 
    
    Any RunApp needs 3 core components: 
    - RunUi (inherited) : contains definitions for UI elements
    - config (arg) : see args in __init__ docstring
    - cls_actions (arg) : see args in __init__ docstring

    """
    status = traitlets.Unicode(default_value="no_outputs")  #

    @traitlets.validate("status")
    def valid_status(self, proposal):
        if proposal["value"] not in list(DI_STATUS_MAP.keys()):
            raise ValueError(
                f"{proposal} must be one of: {str(list(DI_STATUS_MAP.keys()))}"
            )
        return proposal["value"]

    @traitlets.observe("status")
    def _observe_status(self, change):
        self._style_status()

    def _style_status(self):
        style = dict(DI_STATUS_MAP[self.status])
        [
            setattr(self.status_indicator, k, v)
            for k, v in style.items()
            if k != "layout"
        ]

    def __init__(
        self, config: Any, cls_actions: Type[RunActions] = DefaultRunActions,
    ):
        """
        The RunApp is defined by config and cls_actions. In this way the UI can be re-purposed to the needs of the user
        and how they choose to configure thir application. 
        
        The default configuration is the use a config object of type `DefaultConfigShell` and `DefaultRunActions`. 
        These defaults assume the following: 
            - a script is executed on run
            - input files and passed to the script
            - output files are generated by the script

        Args:
            config: Any, suggested = DefaultConfigShell. defines where data is cached to / loaded from. 
            cls_actions: a RunActions class, default = DefaultRunActions. uses `config` to build zero-argument callable 
                functions that get associated to buttons in the RunUi interface and are activated on_click.
                validators are used to build the cls_actions functions based on data in the `config` and `app`.
        """
        super().__init__(layout={"width": "100%"})  # init HBox
        try:
            name = config.long_name
        except:
            name = None
        self._init_RunUi(run_actions=RunActions(), name=name)  # init default actions
        self.children = [self.run_form]
        self.cls_actions = cls_actions
        self.config = config  # the setter updates the ui.actions using fn_buildactions. can be updated on the fly

    @property
    def config(self):
        return self.actions.config

    @config.setter
    def config(self, value):
        actions = self.cls_actions(config=value, app=self)
        self.actions = actions
        self.actions.save_config()
        self.actions.update_status()


if __name__ == "__main__":
    from ipyrun.runshell import ConfigShell

    config = ConfigShell(fpth_script="script.py", long_name="pretty name")
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
        self._update_objects()
        self._init_RunActionsUi(actions, di_button_styles=DEFAULT_BUTTON_STYLES)
        self._update_controls()

    def _update_objects(self):  # TODO: define updated batch objects better...
        self.add = widgets.ToggleButton(**ADD)
        self.remove = widgets.ToggleButton(**REMOVE)
        self.wizard = widgets.ToggleButton(**WIZARD)
        self.load_project = LoadProject()
        self.out_add = widgets.Output()
        self.out_remove = widgets.Output()
        self.out_wizard = widgets.Output()

    def _update_controls(self):
        self.add.observe(self._add, names="value")
        self.remove.observe(self._remove, names="value")
        self.wizard.observe(self._wizard, names="value")

        self.out_inputs.observe(self._update_out, names="outputs")
        self.out_outputs.observe(self._update_out, names="outputs")
        self.out_runlog.observe(self._update_out, names="outputs")

    def _update_out(self, on_change):
        out = [self.out_inputs, self.out_outputs, self.out_runlog]
        self.out_box_main.children = [o for o in out if len(o.outputs) > 0]

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

    @property
    def map_actions(self):
        return {
            self.check: self.actions.check,
            self.status_indicator: self.actions.get_status,
            self.help_ui: self.actions.help_ui_show,
            self.help_run: self.actions.help_run_show,
            self.help_config: self.actions.help_config_show,
            self.inputs: self.actions.inputs_show,
            self.outputs: self.actions.outputs_show,
            self.runlog: self.actions.runlog_show,
            self.run: self.actions.run,
            self.show: self.actions.show,
            self.hide: self.actions.hide,
            self.add: self.actions.add_show,
            self.remove: self.actions.remove_show,
            self.wizard: self.actions.wizard_show,
        }


def test_display_batchactionsui(self: BatchActionsUi):

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


if __name__ == "__main__":
    batch = BatchActionsUi()
    test_display_batchactionsui(batch)

# +
KWARGS_OUT_WIDGET_LAYOUT = dict(
    width="100%",
    align_items="stretch",
    # justify_content="space-between",
    align_content="stretch",
)


class BatchUi(BatchActionsUi):
    """takes run_actions object as an argument and initiates UI objects using 
    RunActionsUi. This class places these objects in containers to create a 
    more readable interface"""

    def __init__(
        self,
        batch_actions: BatchActions(wizard_show=None),
        title: str = "# markdown batch title",
        runs: Dict[str, Type[RunUi]] = None,
        fn_add=None,
        cls_runs_box=Dictionary,
    ):
        self._init_BatchUi(batch_actions, title, runs, fn_add, cls_runs_box)

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        cl = type(value)
        di = value.dict()
        di["app"] = self
        self._actions = cl(**di)
        self.update_form()

    def _init_BatchUi(
        self,
        batch_actions: BatchActions(wizard_show=None),
        title: str = "# markdown batch title",
        runs: Dict[str, Type[RunUi]] = None,
        fn_add=None,
        cls_runs_box=Dictionary,
    ):
        self.title = widgets.HTML(markdown(title))
        self.cls_runs_box = cls_runs_box
        self.fn_add = fn_add
        self._init_UiButtons()
        self._init_form()
        self._init_BatchActionsUi(batch_actions)
        self._update_batch_controls()
        if runs is None:
            runs = {}
        self.runs.items = runs

    def _update_batch_controls(self):
        self.check.observe(self.check_all, names="value")
        

    def check_all(self, onchange):
        for k, v in self.runs.items.items():
            v.check.value = self.check.value



    def update_form(self):
        """update the form if the actions have changed"""
        self.status_indicator.layout = {"width": BUTTON_WIDTH_MIN}
        self.button_bar_left.children = self.get_buttons(
            [
                "help_ui",
                "help_run",
                "help_config",
                "show",
                "inputs",
                "outputs",
                "runlog",
                "run",
                "add",
                "remove",
            ]
        )  # , 'add', 'remove'
        self.top_bar.children = self.get_buttons(["check", "status_indicator"]) + [
            self.button_bar
        ]
        self.batch_form.children = [
            self.title,
            self.top_bar,
            self.layout_out,
            self.runs,
        ]

        self.layout_out.children = [
            self.out_box_addremove,
            self.out_console,
            self.out_help_ui,
            self.out_box_help,
            self.out_box_main,
        ]
        self.out_box_help.children = [self.out_help_run, self.out_help_config]
        self.out_box_addremove.children = [
            self.out_add,
            self.out_remove,
            self.out_wizard,
        ]
        self.out_box_main.children = [
            self.out_inputs,
            self.out_outputs,
            self.out_runlog,
        ]

    def _init_form(self):
        # buttons
        self.batch_form = widgets.VBox()
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

        # out
        self.layout_out = widgets.VBox(layout=KWARGS_OUT_WIDGET_LAYOUT)
        self.out_box_help = widgets.HBox(layout=KWARGS_OUT_WIDGET_LAYOUT)
        self.out_box_addremove = widgets.HBox(layout=KWARGS_OUT_WIDGET_LAYOUT)
        self.out_box_main = widgets.HBox(layout=KWARGS_OUT_WIDGET_LAYOUT)
# -
if __name__ == "__main__":
    config = ConfigShell(fpth_script="script.py", long_name="00-lean-description")
    config = ConfigShell(fpth_script="script.py", long_name="01-lean-description")
    run0 = RunApp(config)
    run1 = RunApp(config)

    def add_show(cls=None):
        return "add"

    batch_actions = BatchActions(  # add_show=add_show,
        inputs_show=None,
        outputs_show=None,
        runlog_show=None,
        wizard_show=None,
        show=None,
    )
    ui_actions = BatchActionsUi(batch_actions=batch_actions)
    run_batch = BatchUi(
        runs={"01-lean-description": run0, "02-lean-description": run1},
        batch_actions=batch_actions,
    )
    display(run_batch.batch_form)



# +
class BatchApp(widgets.VBox, BatchUi): 
    status = traitlets.Unicode(default_value="no_outputs")  #

    @traitlets.validate("status")
    def valid_status(self, proposal):
        if proposal["value"] not in list(DI_STATUS_MAP.keys()):
            raise ValueError(
                f"{proposal} must be one of: {str(list(DI_STATUS_MAP.keys()))}"
            )
        return proposal["value"]

    @traitlets.observe("status")
    def _observe_status(self, change):
        self._style_status()

    def _style_status(self):
        style = dict(DI_STATUS_MAP[self.status])
        [
            setattr(self.status_indicator, k, v)
            for k, v in style.items()
            if k != "layout"
        ]

    def __init__(
        self, config: Any, cls_actions: Type[BaseModel] = BatchActions,
    ):
        """
        The goal of RunApp is to simplify the process of making a functional UI that interacts
        with remote data for use in a Jupyter Notebook or Voila App. 

        Args:
            config: Type[BaseModel]
        """
        super().__init__(layout=widgets.Layout(flex="100%"))
        try:
            title = config.title
        except:
            title = ""
        self.cls_actions = cls_actions
        self._init_BatchUi(BatchActions(), title)  # runs , fn_add, cls_runs_box
        self.children = [self.batch_form]  # [self.ui.batch_form]
        self.config = config  # the setter updates the ui.actions
        self._init_controls()
        
    def _init_controls(self):
        self.watch_run_statuses()
        
    def _update_batch_status(self, onchange):
        self.actions.update_status()

    def watch_run_statuses(self):
        for k, v in self.runs.items.items():
            v.observe(self._update_batch_status, "status")

    @property
    def run_actions(self):
        return [v.actions for k, v in self.runs.items.items()]

    @property
    def config(self):
        return self.actions.config

    @config.setter
    def config(self, value):
        actions = self.cls_actions(config=value, app=self)
        self.actions = actions
        self.actions.save_config()
        try:
            self.runs.items = {
                c.key: self.make_run(c) for c in self.config.configs
            }  # TODO: this code isn't generic!
        except:
            print("error building runs fron config")
            print(f"self.config == {str(self.config)}")
        self.update_in_batch()
        self.actions.update_status()

    def update_in_batch(self):  # TODO: remove config dependent code?
        for k, v in self.runs.items.items():
            v.check.value = v.config.in_batch

    def make_run(self, config):
        """builds RunApp from config"""
        return self.config.cls_app(config)

    def configs_append(self, config):  # TODO: remove config dependent code?
        self.actions.config.configs.append(config)
        self.actions.save_config()
        newapp = self.make_run(config)
        self.runs.add_row(new_key=config.key, item=newapp)
        self.update_in_batch()

    def configs_remove(self, key):  # TODO: remove config dependent code?
        self.config.configs = [c for c in self.config.configs if c.key != key]
        self.update_in_batch()
        self.actions.save_config()


if __name__ == "__main__":
    from ipyrun.runshell import ConfigBatch

    config_batch = ConfigBatch(fdir_root=".", fpth_script="script.py", title="# title")
    batch_app = BatchApp(config_batch)
    display(batch_app)
# -

if __name__ == "__main__":
    from ipyrun.runshell import ConfigBatch

    config_batch = ConfigBatch(
        fdir_root=".", fpth_script="script.py", configs=[config.dict()], title="# title"
    )  # TODO: sort out "title" (and how its named in the back)
    batch_app = BatchApp(None)
    display(batch_app)

# +
# import pandas as pd
# import getpass
# import pathlib

# def runlog(path_runlog):  # TODO: do runlogging!
#     if type(path_runlog) == str:
#         path_runlog = pathlib.Path(path_runlog)
#     if path_runlog.is_file:
#         self.df_runlog = del_matching(pd.read_csv(self.fpth_runlog), "Unnamed")
#     else:
#         di = {
#             "processName": [],
#             "user": [],
#             "datetime": [],
#             "formalIssue": [],
#             "tags": [],
#             "fpthInputs": [],
#         }
#         self.df_runlog = pd.DataFrame(di).rename_axis("index")

#     user = getpass.getuser()
#     timestamp = str(pd.to_datetime("today"))
#     timestamp = timestamp[:-7]

#     tmp = pd.DataFrame(
#         {
#             "processName": [self.name],
#             "user": [user],
#             "datetime": [timestamp],
#             "formalIssue": [""],
#             "tags": [""],
#             "fpthInputs": [self.fpth_inputs_archive],
#         }
#     )
#     self.df_runlog = self.df_runlog.append(tmp).reset_index(drop=True)
#     make_dir(self.fdir_runlog)
#     self.df_runlog.to_csv(self.fpth_runlog)
#     return


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

#

#


