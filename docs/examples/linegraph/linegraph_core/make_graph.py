"""a test script for ipyrun that plots a line graph based on inputs

Returns:
    fpth_csv (str): csv file with plot data
    fpth_plotly (str): plotly json of plot
"""
import pandas as pd
import numpy as np
import plotly.express as px
from .input_schema_linegraph import LineGraph
import os

def fpth_chg_extension(fpth, new_ext="plotly"):
    return os.path.splitext(fpth)[0] + "." + new_ext

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

def graph_filehandler(fpth_in, fpth_out_csv, fpth_out_plotly):
    """
    Args:
        fpth_in (str)
        fpth_out_csv (str)
        fpth_out_plotly (str)
    Returns:
        fpth_out_csv
    """
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
    return df