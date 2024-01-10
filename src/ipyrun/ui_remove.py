# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %%
"""
generic Add run dialogue
"""
# %run _dev_sys_path_append.py
# %run __init__.py
# %load_ext lab_black

# %%
import typing
import ipywidgets as widgets


class RunApps:
    None


def fn_remove(cls=None, delete_data=True):
    return print(f"remove runapp = {delete_data}")


class RemoveRun:
    def __init__(
        self,
        app: typing.Type[RunApps] = None,
        fn_remove: typing.Callable = fn_remove,
        md_question: str = "delete all files associated with selected runs (_recommended_, ***note.*** _this requires all active files to be closed_)",
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
        self.fn_remove = fn_remove
        self.md_question = md_question
        self._init_form()
        self._init_controls()

    def _init_form(self):
        self.delete_data = widgets.Checkbox(
            value=True,  # self.checked
            disabled=False,
            indent=False,
            layout=widgets.Layout(
                max_width="20px",
                height="40px",
                padding="3px",
                # border='3px solid green'
            ),
        )
        self.form = widgets.HBox(
            [
                self.delete_data,
                widgets.HTML(self.md_question),
            ]
        )

    def _init_controls(self):
        self.delete_data.observe(self._delete_data, names="value")

    def _delete_data(self, on_change):
        self.fn_remove(cls=self.app, delete_data=self.delete_data.value)

    def display(self):
        display(self.form)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":

    def remove_run_dialogue(cls=None):
        display(RemoveRunDialogue(cls))

    display(RemoveRun(app=RunApps()))

# %%
