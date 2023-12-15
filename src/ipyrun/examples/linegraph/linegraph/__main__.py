import json
import pathlib
import numpy as np
from .input_schema_linegraph import LineGraph
from .make_graph import graph

def main(fpth_in, fpth_out_csv, fpth_out_plotly):
    """
    Args:
        fpth_in (str)
        fpth_out_csv (str)
        fpth_out_plotly (str)
    Returns:
        fpth_out_csv
    """
    inputs = LineGraph(**json.loads(pathlib.Path(fpth_in).read_text()))
    formula = "{} * x + {}".format(inputs.m, inputs.c)
    x_range = np.arange(inputs.x_range[0], inputs.x_range[1], step=1)
    df = graph(
        formula,
        x_range,
        fpth_save_plot=fpth_out_plotly,
        returndf=True,
        title=inputs.title,
    )
    df.to_csv(fpth_out_csv)
    return df


if __name__ == "__main__":
    if __debug__:
        import os
        import pathlib
        os.chdir(pathlib.Path(__file__).parent)
        fpth_in = "inputs-line_graph.lg.json"
        fpth_out_csv = "line_graph-output.csv"
        fpth_out_plotly = "line_graph-output.plotly.json"
        main(fpth_in, fpth_out_csv, fpth_out_plotly)
    else:
        import sys
        fpth_in = sys.argv[1]
        fpth_out_csv = sys.argv[2]
        fpth_out_plotly = sys.argv[3]
        print(f"fpth_in = {fpth_in}")
        print(f"fpth_out_csv = {fpth_out_csv}")
        print(f"fpth_out_plotly = {fpth_out_plotly}")
        main(fpth_in, fpth_out_csv, fpth_out_plotly)
