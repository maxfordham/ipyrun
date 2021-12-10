"""a test script for ipyrun that plots a line graph based on inputs

Returns:
    fpth_csv (str): csv file with plot data
    fpth_plotly (str): plotly json of plot
"""
import pandas as pd
import numpy as np
import plotly.express as px
import json
from schemas import LineGraph


def fpth_chg_extension(fpth, new_ext="plotly"):
    return os.path.splitext(fpth)[0] + "." + new_ext


def write_json(data, fpth="data.json", indent=4):
    """
    write output to json file
    Args:
        data
        ** indent=4
        ** fpth='data.json'

    Code:
        out=json.dumps(data, sort_keys=sort_keys, indent=indent)
        f = open(fpth,"w")
        f.write(out)
        f.close()
        if print_fpth ==True:
            print(fpth)
        if openFile==True:
            open_file(fpth)
        return fpth
    """
    out = json.dumps(data, indent=indent)
    f = open(fpth, "w")
    f.write(out)
    f.close()
    return fpth


def graph(
    formula, x_range, title="", display_plot=False, fpth_save_plot=None, returndf=True
):
    """
    generic graph plotter.
    pass a  and a range to plot over
    and returns a dataframe.
    Args:
        formula(str): formula as a string
        x_range(np.arange): formula as a string
        **plot(booll:
        **returndf(bool)
    Returns:
        df(pd.DataFrame):
    """
    try:
        x = np.array(x_range)
        y = eval(formula)
    except:
        li = []
        y = [li.append(eval(formula)) for x in x_range]
        x = x_range
        y = np.array(li)
    if len(title) > 0:
        title = title + "<br>" + "y = " + formula
    else:
        title = "y = " + formula
    try:
        df = pd.DataFrame({"x": x, "y": y}, columns=["x", "y"])
    except:
        df = {"x": x, "y": y}
    if display_plot:
        fig = px.line(df, x="x", y="y", title=title, template="plotly_white")
        fig.show()
    if fpth_save_plot is not None:
        fig = px.line(df, x="x", y="y", title=title, template="plotly_white")
        data = fig.write_json(fpth_save_plot)
    if returndf:
        return df


def main(fpth_in, fpth_out_csv, fpth_out_plotly):
    inputs = pd.read_csv(fpth_in).set_index("name")["value"]
    formula = "{} * x + {}".format(inputs.m, inputs.c)
    x_range = np.arange(inputs.x_range_min, inputs.x_range_max)
    df = graph(
        formula,
        x_range,
        fpth_save_plot=fpth_out_plotly,
        returndf=True,
        title=inputs.title,
    )
    df.to_csv(fpth_out_csv)
    return df


def main(fpth_in, fpth_out_csv, fpth_out_plotly):
    inputs = LineGraph.parse_file(fpth_in)
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
    print("asdfasdf")
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
