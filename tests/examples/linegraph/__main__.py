"""a test script for ipyrun that plots a line graph based on inputs

Returns:
    fpth_csv (str): csv file with plot data
    fpth_plotly (str): plotly json of plot
"""
from .make_graph import graph_filehandler

if __debug__:
    import os
    import pathlib
    os.chdir(pathlib.Path(__file__).parent)
    fpth_in = "inputs-line_graph.lg.json"
    fpth_out_csv = "line_graph-output.csv"
    fpth_out_plotly = "line_graph-output.plotly.json"
    graph_filehandler(fpth_in, fpth_out_csv, fpth_out_plotly)
else:
    import sys
    fpth_in = sys.argv[1]
    fpth_out_csv = sys.argv[2]
    fpth_out_plotly = sys.argv[3]
    print(f"fpth_in = {fpth_in}")
    print(f"fpth_out_csv = {fpth_out_csv}")
    print(f"fpth_out_plotly = {fpth_out_plotly}")
    graph_filehandler(fpth_in, fpth_out_csv, fpth_out_plotly)