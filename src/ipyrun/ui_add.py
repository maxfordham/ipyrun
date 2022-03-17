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
generic Add run dialogue
"""
# %run __init__.py
# %load_ext lab_black

# +
import typing
import ipywidgets as widgets
from ipyautoui.custom import RunName
from ipyrun.constants import BUTTON_MIN_SIZE
from markdown import markdown


class RunApps:
    None


def create_runapp(cls=None, name="name"):
    return print(name)


class AddModelRun:
    def __init__(
        self,
        app: typing.Type[RunApps] = None,
        fn_add: typing.Callable = create_runapp,
        run_name_kwargs: typing.Dict = None,
    ):
        """
        a ui element for adding new runs to RunApps
        
        Args:
            app (RunApps): the app that will be modified by this class
            fn_add (typing.Callable): a function that is executed to add a new run to the "app"
                on_click of a button. the main app is passed to the function using functools:
        
        Code:
            ```
            def _init_controls(self):
                self.add.on_click(self._add)

            def _add(self, click):
                return functools.partial(self.fn_add, cls=self.app)()
            ```
        """
        self.run_name_kwargs = run_name_kwargs
        if self.run_name_kwargs is None:
            self.run_name_kwargs = {}
        self.app = app
        self.fn_add = fn_add
        self._init_form()
        self._init_controls()

    def _init_form(self):
        self.add = widgets.Button(
            icon="check", button_style="success", layout=dict(BUTTON_MIN_SIZE)
        )
        self.run_name = RunName(**self.run_name_kwargs)
        self.question = widgets.HTML(self.question_value)
        self.form = widgets.VBox(
            [widgets.HBox([self.add, self.question]), self.run_name]
        )

    @property
    def question_value(self):
        return markdown(f"would you like to add new a run? `{self.run_name.value}`")

    def _init_controls(self):
        self.add.on_click(self._add)
        self.run_name.observe(self._question, names="_value")

    def _question(self, on_change):
        self.question.value = self.question_value

    def _add(self, click):
        return self.fn_add(cls=self.app, name=self.run_name.value)

    def display(self):
        display(self.form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":

    add = AddModelRun(app=RunApps())
    display(add)
# +
class AddRun:
    def __init__(
        self,
        app: typing.Type[RunApps] = None,
        fn_add: typing.Callable = create_runapp,
        run_name_kwargs: typing.Dict = None,
    ):
        """
        a ui element for adding new runs to RunApps
        
        Args:
            app (RunApps): the app that will be modified by this class
            fn_add (typing.Callable): a function that is executed to add a new run to the "app"
                on_click of a button. the main app is passed to the function using functools:
        
        Code:
            ```
            def _init_controls(self):
                self.add.on_click(self._add)

            def _add(self, click):
                return functools.partial(self.fn_add, cls=self.app)()
            ```
        """
        self.run_name_kwargs = run_name_kwargs
        if self.run_name_kwargs is None:
            self.run_name_kwargs = {}
        self.app = app
        self.fn_add = fn_add
        self._init_form()
        self._init_controls()

    def _init_form(self):
        self.add = widgets.Button(
            icon="check", button_style="success", layout=dict(BUTTON_MIN_SIZE)
        )
        self.question = widgets.HTML(markdown(f"would you like to add new a run?"))
        self.form = widgets.HBox([self.add, self.question])

    def _init_controls(self):
        self.add.on_click(self._add)

    def _add(self, click):
        return self.fn_add(cls=self.app)

    def display(self):
        display(self.form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":

    add = AddRun(app=RunApps())
    display(add)
