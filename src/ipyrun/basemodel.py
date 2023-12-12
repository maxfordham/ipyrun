"""Added functionality to default pydantic.BaseModel (mostly for reading and
writing to file)
"""
from pydantic import ConfigDict, BaseModel
import stringcase
import pathlib
import subprocess
from typing import Type


def file(self: Type[BaseModel], path: pathlib.Path):
    """
    this is a method that is added to the pydantic BaseModel within AutoUi using
    "setattr".

    Example:
        ```setattr(model, 'file', file)```

    Args:
        self (pydantic.BaseModel): instance
        path (pathlib.Path): to write file to
    """
    if type(path) == str:
        path = pathlib.Path(path)
    path.write_text(self.model_dump_json(indent=4), encoding="utf-8")


def file_schema(self: Type[BaseModel], path: pathlib.Path, **json_kwargs):
    if type(path) == str:
        path = pathlib.Path(path)
    path = path.with_suffix(".schema.json")
    if "indent" not in json_kwargs.keys():
        json_kwargs.update({"indent": 4})
    path.write_text(self.schema(**{"indent": 4}), encoding="utf-8")


def file_mdschema(self: Type[BaseModel], path: pathlib.Path, **json_kwargs):
    """creates markdown file from jsonschema using

    Reference:
        https://github.com/RalfG/jsonschema2md

    Args:
        path (pathlib.Path): output path of md-schema
    """
    if type(path) == str:
        path = pathlib.Path(path)
    path_schema = path.with_suffix(".schema.json")
    self.file_schema(path_schema, **json_kwargs)
    subprocess.run(["jsonschema2md", str(path_schema), str(path)])


def check_validators(self: Type[BaseModel]):
    model = self.model_validate(self.model_dump())
    self = model
    # try:
    #     setattr(self, "__dict__", model.model_dump())
    # except TypeError as e:
    #     raise TypeError(
    #         "Model values must be a dict; you may not have returned "
    #         + "a dictionary from a root validator"
    #     ) from e


class BaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


setattr(BaseModel, "file", file)
setattr(BaseModel, "file_schema", file_schema)
setattr(BaseModel, "file_mdschema", file_mdschema)
setattr(BaseModel, "check_validators", check_validators)
