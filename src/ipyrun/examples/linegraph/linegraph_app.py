from pydantic import field_validator, ValidationInfo
from ipyrun.runshell import (
    ConfigBatch,
    DefaultConfigShell,
    AutoDisplayDefinition,
    FiletypeEnum,
    RunShellActions,
    BatchShellActions
)
import pathlib
PATH_RUN = pathlib.Path(__file__).parent / "linegraph"
PATH_INPUTSCHEMA = PATH_RUN / "input_schema_linegraph.py"

class LineGraphConfigShell(DefaultConfigShell):
    @field_validator("path_run")
    def _set_path_run(cls, v, info: ValidationInfo):
        return PATH_RUN

    @field_validator("fpths_outputs")
    def _fpths_outputs(cls, v, info: ValidationInfo):
        fdir = info.data["fdir_appdata"]
        nm = info.data["name"]
        paths = [
            fdir / pathlib.Path("out-" + nm + ".csv"),
            fdir / pathlib.Path("out-" + nm + ".plotly.json"),
        ]
        return paths

    @field_validator("autodisplay_definitions")
    def _autodisplay_definitions(cls, v, info: ValidationInfo):
        return [
            AutoDisplayDefinition(
                path=PATH_INPUTSCHEMA,
                obj_name="LineGraph",
                ext=".lg.json",
                ftype=FiletypeEnum.input,
            )
        ]

    @field_validator("autodisplay_inputs_kwargs")
    def _autodisplay_inputs_kwargs(cls, v, info: ValidationInfo):
        return dict(patterns="*")

    @field_validator("autodisplay_outputs_kwargs")
    def _autodisplay_outputs_kwargs(cls, v, info: ValidationInfo):
        return dict(patterns="*.plotly.json")


class LineGraphConfigBatch(ConfigBatch):
    @field_validator("cls_actions")
    def _cls_actions(cls, v, info: ValidationInfo):
        """bundles RunApp up as a single argument callable"""
        return RunShellActions

    @field_validator("cls_config")
    def _cls_config(cls, v, info: ValidationInfo):
        """bundles RunApp up as a single argument callable"""
        return LineGraphConfigShell


def fn_loaddir_handler(value, app=None):
    fdir_root = value["fdir"] / "06_Models"
    app.actions.load(fdir_root=fdir_root)


class LineGraphBatchActions(BatchShellActions):
    @field_validator("runlog_show")
    def _runlog_show(cls, v, info: ValidationInfo):
        return None

    @field_validator("load_show")
    def _load_show(cls, v, info: ValidationInfo):
        return lambda: WorkingDirsUi(
            fn_onload=wrapped_partial(fn_loaddir_handler, app=info.data["app"])
        )
