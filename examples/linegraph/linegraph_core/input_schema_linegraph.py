from pydantic import BaseModel , Field, conint
import typing
import pathlib

class LineGraph(BaseModel):
    """parameters to define a simple `y=m*x + c` line graph"""
    title: str = Field(default='line equation', description='add chart title here')
    m: float = Field(default=2, description='gradient')
    c: float = Field(default=5, description='intercept')
    x_range: tuple[int, int] = Field(default=(0,5), ge=0, le=50, description='x-range for chart')
    y_range: tuple[int, int] = Field(default=(0,5), ge=0, le=50, description='y-range for chart')
        
if __name__ == "__main__":
    lg = LineGraph()