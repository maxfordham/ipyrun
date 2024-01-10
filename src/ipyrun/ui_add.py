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

# +
"""
generic Add run dialogue
"""
# %run _dev_sys_path_append.py
# %run __init__.py
# %load_ext lab_black

import typing
import ipywidgets as widgets
from IPython.display import display
from ipyautoui.custom.modelrun import RunName
from ipyautoui.constants import BUTTON_MIN_SIZE
from ipyrun.constants import FILENAME_FORBIDDEN_CHARACTERS
import traitlets
import stringcase


# +
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
        return f"would you like to add new a run? `{self.run_name.value}`"

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
def modify_string(
    s,
    remove_forbidden_chars=True,
    remove_spaces=True,
    fn_on_string=stringcase.pascalcase,
):
    if remove_spaces:
        s = stringcase.titlecase(s)
        s = s.replace(" ", "")
    if remove_forbidden_chars:
        for c in FILENAME_FORBIDDEN_CHARACTERS:
            s = s.replace(c, "")
    if fn_on_string is not None:
        s = fn_on_string(s)
    return s


class AddNamedRun(traitlets.HasTraits):
    value = traitlets.Unicode()

    def __init__(
        self,
        app: typing.Type[RunApps] = None,
        fn_add: typing.Callable = create_runapp,
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
                return self.fn_add(cls=self.app, name=self.value)
            ```
        """
        self.app = app
        self.fn_add = fn_add
        self._init_form()
        self._init_controls()

    def _init_form(self):
        self.add = widgets.Button(
            icon="check", button_style="success", layout=dict(BUTTON_MIN_SIZE)
        )
        self.run_name = widgets.Text()
        self.question = widgets.HTML(self.question_value)
        self.form = widgets.VBox(
            [widgets.HBox([self.add, self.question]), self.run_name]
        )

    @property
    def question_value(self):
        return f"Would you like to add new a run? `{self.value}`"

    def _init_controls(self):
        self.add.on_click(self._add)
        self.run_name.observe(self._run_name, names=["_value", "value"])
        self.run_name.observe(self._question, names=["_value", "value"])

    def _run_name(self, on_change):
        self.value = modify_string(self.run_name.value)

    def _question(self, on_change):
        self.question.value = self.question_value

    def _add(self, click):
        return self.fn_add(name=self.value)

    def display(self):
        display(self.form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    add = AddNamedRun(app=RunApps())
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
        self.question = widgets.HTML(f"would you like to add new a run?")
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
# -
