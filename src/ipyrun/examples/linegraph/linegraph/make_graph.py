import pandas as pd
import numpy as np
import plotly.express as px

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