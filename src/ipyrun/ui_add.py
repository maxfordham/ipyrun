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

# +
import typing
import ipywidgets as widgets
import functools

class RunApps:
    None

def create_runapp(cls=None):
    return print('create runapp')

class AddRunDialogue:
    def __init__(
        self, app: typing.Type[RunApps]=None, add_cmd: typing.Callable = create_runapp
    ):
        """
        a ui element for adding new runs to RunApps
        
        Args:
            app (RunApps): the app that will be modified by this class
            add_cmd (typing.Callable): a function that is executed to add a new run to the "app"
                on_click of a button. the main app is passed to the function using functools:
        
        Code:
            ```
            def _init_controls(self):
                self.add.on_click(self._add)

            def _add(self, click):
                return functools.partial(self.add_cmd, cls=self.app)()
            ```
        """
        self.app = app
        self.add_cmd = add_cmd
        self._init_form()
        self._init_controls()

    def _init_form(self):
        self.add = widgets.Button(icon="check", button_style="success")
        self.form = widgets.HBox(
            [
                self.add,
                widgets.HTML("would you like to add a run?"),
            ]
        )

    def _init_controls(self):
        self.add.on_click(self._add)
    
    def _add(self, click):
        return self.add_cmd(cls=self.app)

    def display(self):
        display(self.form)

    def _ipython_display_(self):
        self.display()

if __name__ == "__main__":

    def add_run_dialogue(cls=None):
        display(AddRunDialogue(cls))

    display(AddRunDialogue(app =RunApp()))
# -


