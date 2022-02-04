"""Added functionality to default pydantic.BaseModel (mostly for reading and
writing to file)
"""
from pydantic import BaseModel
import stringcase
import pathlib
import subprocess


class BaseModel(BaseModel):
    def file(self, path: pathlib.Path, **json_kwargs):
        if type(path) == str:
            path = pathlib.Path(path)
        if "indent" not in json_kwargs.keys():
            json_kwargs.update({"indent": 4})
        path.write_text(self.json(**json_kwargs), encoding="utf-8")

    def file_schema(self, path: pathlib.Path, **json_kwargs):
        if type(path) == str:
            path = pathlib.Path(path)
        path = path.with_suffix(".schema.json")
        if "indent" not in json_kwargs.keys():
            json_kwargs.update({"indent": 4})
        path.write_text(self.schema(**{"indent": 4}), encoding="utf-8")

    def file_mdschema(self, path: pathlib.Path, **json_kwargs):
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

    class Config:
        alias_generator = stringcase.titlecase
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
