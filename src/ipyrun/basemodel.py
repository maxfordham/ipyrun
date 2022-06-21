"""Added functionality to default pydantic.BaseModel (mostly for reading and
writing to file)
"""
from pydantic import BaseModel, validate_model
import stringcase
import pathlib
import subprocess
from typing import Type

def file(self:Type[BaseModel], path: pathlib.Path, **json_kwargs):
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
    if "indent" not in json_kwargs.keys():
        json_kwargs.update({"indent": 4})
    path.write_text(self.json(**json_kwargs), encoding="utf-8")

def file_schema(self:Type[BaseModel], path: pathlib.Path, **json_kwargs):
    if type(path) == str:
        path = pathlib.Path(path)
    path = path.with_suffix(".schema.json")
    if "indent" not in json_kwargs.keys():
        json_kwargs.update({"indent": 4})
    path.write_text(self.schema(**{"indent": 4}), encoding="utf-8")

def file_mdschema(self:Type[BaseModel], path: pathlib.Path, **json_kwargs):
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
    
def check(self:Type[BaseModel]):
    values, fields_set, validation_error = validate_model(
        self.__class__, self.__dict__
    )
    if validation_error:
        raise validation_error
    try:
        object.__setattr__(self, "__dict__", values)
    except TypeError as e:
        raise TypeError(
            "Model values must be a dict; you may not have returned "
            + "a dictionary from a root validator"
        ) from e
    object.__setattr__(self, "__fields_set__", fields_set)

class BaseModel(BaseModel):

    class Config:
        #alias_generator = stringcase.titlecase
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


setattr(BaseModel, 'file', file)
setattr(BaseModel, 'file_schema', file_schema)
setattr(BaseModel, 'file_mdschema', file_mdschema)
setattr(BaseModel, 'check', check)