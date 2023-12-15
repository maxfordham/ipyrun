from pydantic import BaseModel, Field, conint

# from ipyautoui.custom.fileupload import File

# class BaseModel(BaseModel):
#     def file(self, path: pathlib.Path, **json_kwargs):
#         """
#         this is a method that is added to the pydantic BaseModel within AutoUi using
#         "setattr"
#         Args:
#             self (pydantic.BaseModel): instance
#             path (pathlib.Path): to write file to
#         """
#         if 'indent' not in json_kwargs.keys():
#             json_kwargs.update({'indent':4})
#         path.write_text(self.json(**json_kwargs), encoding='utf-8')


class LineGraph(BaseModel):
    """parameters to define a simple `y=m*x + c` line graph"""

    title: str = Field(default="line equation", description="add chart title here")
    m: float = Field(default=2, description="gradient")
    c: float = Field(default=5, description="intercept")
    x_range: tuple[conint(ge=0, le=50), conint(ge=0, le=50)] = Field(
        default=(0, 5), description="x-range for chart"
    )
    y_range: tuple[conint(ge=0, le=50), conint(ge=0, le=50)] = Field(
        default=(0, 5), description="y-range for chart"
    )
    # references: typing.Dict[str, File] = Field(default_factory=lambda: {},
    #             autoui="ipyautoui.custom.fileupload.FileUploadToDir", maximumItems=1, minimumItems=0
    #         )


if __name__ == "__main__":
    lg = LineGraph()
