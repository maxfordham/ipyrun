"""
this module contains utility functions. these are copied from the main mf library.
"""

import os
import pathlib
import re
import codecs
import glob
import pandas as pd
from IPython.display import Markdown
from markdown import markdown
import json
import yaml
import time
from datetime import datetime
import fnmatch


import ipywidgets as widgets
from ipyrun.constants import BUTTON_WIDTH_MIN
from ipyautoui._utils import open_path


#  from mf_modules.pandas_operations import del_matching
#  ------------------------------------------------------------------------------------------------
def del_cols(df, cols):
    """delete a pandas column if it is in
    the column index otherwise ignore it."""
    if type(cols) == str:
        try:
            del df[cols]
        except:
            print(cols + " is not in column index")
    else:
        for col in cols:
            try:
                del df[col]
            except:
                print(col + " is not in column index")
    return df


def del_matching(df, string):
    """
    deletes columns if col name matches string
    """
    matching = [s for s in list(df) if string in s]
    df = del_cols(df, matching)
    return df


def string_of_time(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def time_meta_data(fpth, as_DataFrame: bool = True, timeformat: str = "strftime"):
    """
    extract time based metadata about a file

    Name:
        20180916~3870~dev~pyfnctn~jg~get time based metadata for a file~A~0

    Args:
        fdir (string): file-directory
        as_DataFrame: bool =True
        timeformat: str = 'strftime' or 'datetime'


    See Also:
        list of metadata available from os.stat(fdir): https://docs.python.org/3/library/os.html
        write docstrings like google: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
        Google python code style guide: https://github.com/google/styleguide/blob/gh-pages/pyguide.md

    References:
        https://docs.python.org/3/library/os.html
            shows other info available from os.stat

    Returns:
        df (pd.DataFrame):
            time_of_file_creation (string):
            time_of_most_recent_access (string):
            time_of_most_recent_content_modification (string):

    To Do:
        add optionally extract other meta-data available from os.stat
        this should be *args inputs
    """

    di = {}
    try:
        meta = os.stat(fpth)
    except:
        return None
    di["fpth"] = fpth
    if timeformat == "strftime":
        di["time_of_file_creation"] = string_of_time(meta.st_ctime)
        di["time_of_most_recent_access"] = string_of_time(meta.st_atime)
        di["time_of_most_recent_content_modification"] = string_of_time(meta.st_mtime)
    else:
        di["time_of_file_creation"] = datetime.fromtimestamp(
            time.mktime(time.localtime(meta.st_ctime))
        )
        di["time_of_most_recent_access"] = datetime.fromtimestamp(
            time.mktime(time.localtime(meta.st_atime))
        )
        di["time_of_most_recent_content_modification"] = datetime.fromtimestamp(
            time.mktime(time.localtime(meta.st_mtime))
        )

    if as_DataFrame:
        return pd.DataFrame.from_dict(di, orient="index").T
    else:
        return di


def get_time_of_most_recent_content_modification(fpth):
    try:
        return time_meta_data(fpth, as_DataFrame=False, timeformat="datetime").get(
            "time_of_most_recent_content_modification"
        )
    except:
        return None


def make_dir(directory):
    """
    check if folder exists, if not, make a new folder using python
    """
    import os, errno

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


#  from mf_modules.pydtype_operations flatten_list, import read_json, read_txt, read_yaml
#  ------------------------------------------------------------------------------------------------
def flatten_list(list_of_lists: list) -> list:
    """Flatten a list of (lists of (lists of strings)) for any level
    of nesting

    Args:
        list_of_lists: with mix of lists and other
    Returns:
        rt: list with no nested lists

    """
    rt = []
    for i in list_of_lists:
        if isinstance(i, list):
            rt.extend(flatten_list(i))
        else:
            rt.append(i)
    return rt


def read_json(fpth, encoding="utf8"):
    """
    read info in a .json file
    """
    with open(fpth, "r", encoding=encoding) as f:
        json_file = json.load(f)
    return json_file


def read_txt(fpth, encoding="utf-8", delim=None, read_lines=True):
    """
    read a .txt file

    Args:
        fpth(string): filepath
        encoding(string): https://docs.python.org/3/library/codecs.html, examples:
            utf-16, utf-8, ascii
        delim(char): character to string split, examples:
            '\t', ','
        read_lines(bool): readlines or whole string (delim may not work if read_lines==False

    """
    with codecs.open(fpth, encoding=encoding) as f:
        if read_lines == True:
            content = f.readlines()
        else:
            content = f.read()
    f.close()
    if delim != None:
        li = []
        for n in range(0, len(content)):
            li.append(content[n].split(delim))
        return li
    else:
        return content


def read_yaml(fpth, encoding="utf8"):
    """
    read yaml file.

    Ref:
        https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python
    """
    with open(fpth, encoding=encoding) as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data


#  ------------------------------------------------------------------------------------------------


def write_json(
    data, fpth="data.json", sort_keys=True, indent=4, print_fpth=False, openFile=False
):
    """
    write output to json file
    Args:
        data
        ** sort_keys = True
        ** indent=4
        ** fpth='data.json'
        ** print_fpth=True
        ** openFile=False

    Code:
        out=json.dumps(data, sort_keys=sort_keys, indent=indent)
        f = open(fpth,"w")
        f.write(out)
        f.close()
        if print_fpth ==True:
            print(fpth)
        if openFile==True:
            open_path(fpth)
        return fpth
    """
    out = json.dumps(data, sort_keys=sort_keys, indent=indent)
    f = open(fpth, "w")
    f.write(out)
    f.close()
    if print_fpth == True:
        print(fpth)
    if openFile == True:
        open_path(fpth)
    return fpth


def write_yaml(
    data, fpth="data.yaml", sort_keys=True, indent=4, print_fpth=True, openFile=False
):
    """
    write output to json file
    Args:
        data
        ** sort_keys = True
        ** fpth='data.json'
        ** print_fpth=True
        ** openFile=False
    """
    with open(fpth, "w") as outfile:
        yaml.dump(data, outfile, sort_keys=sort_keys, default_flow_style=False)
    if print_fpth == True:
        print(fpth)
    if openFile == True:
        open_path(fpth)
    return fpth


def di_from_li_of_di(li_of_di, key, value):
    """
    returns first matching dict from list of dicts

    Code:
        {l[key]: l[value] for l in li_of_di}

    Example:

        li_of_di = [
         { "name": "Tom", "age": 10 },
         { "name": "Tom", "age": 5 },
         { "name": "Pam", "age": 7 },
         { "name": "Dick", "age": 12 }
         ]

         di_from_li_of_di(li_of_di,"name","Tom")
         >>> {'name': 'Tom', 'age': 10}
    """
    return {l[key]: l[value] for l in li_of_di}


# directories -------------------------------------------------
def flatten_list(list_of_lists: list) -> list:
    """Flatten a list of (lists of (lists of strings)) for any level
    of nesting

    Args:
        list_of_lists: with mix of lists and other
    Returns:
        rt: list with no nested lists

    """
    rt = []
    for i in list_of_lists:
        if isinstance(i, list):
            rt.extend(flatten_list(i))
        else:
            rt.append(i)
    return rt


def jobno_fromdir(fdir):
    """
    returns the job number from a given file directory

    Args:
        fdir (filepath): file-directory
    Returns:
        job associated to file-directory
    Code:
        re.findall("[J][0-9][0-9][0-9][0-9]", txt)
    """
    matches = re.findall("[J][0-9][0-9][0-9][0-9]", fdir)
    if len(matches) == 0:
        job_no = "J4321"
    else:
        job_no = matches[0]
    return job_no


def find_fdir_keys(di):
    """searches dict for key that contains string 'fdir'. ignores J:\\
    can handle lists for fdir* values"""
    li = list(di.keys())
    li = flatten_list([di[l] for l in li if l[0:4] == "fdir"])
    li = [l for l in li if l != "J:\\"]
    li = [l for l in li if l != "None"]
    return li


def make_dirs_from_fdir_keys(di: dict):
    """
    creates a folder structure based on a ProjectDirs object.
    simply, the script turns the ProjectDirs object into a dict and
    searches for keys that begin with "fdir" (includes nested elements)
    and creates those dirs using Pathlib.

    Args:
        projectdirs: ProjectDirs, data object defining project setup with standard dirs

    Returns:
        li: list of directories that should now exist

    Code:
        p.mkdir(parents=True, exist_ok=True)
    """
    li = find_fdir_keys(di)
    li_made = []
    for p in li:
        try:
            if type(p) == str:
                p = pathlib.Path(p)
            p.mkdir(parents=True, exist_ok=True)
            li_made.append(p)
        except:
            s = str(p)
            print(f"failed to make dir: {s}")
    return li_made


# widget templates
def template_image_icon(fpth):
    file = open(fpth, "rb")
    image = file.read()
    return widgets.Image(
        tooltip="asdf asdad",
        value=image,
        format="png",
        width=30,
        height=5,
        layout=widgets.Layout(object_fit="contain"),
    )


def template_plus_button(description="", tooltip="add"):
    return widgets.Button(
        description=description,
        tooltip=tooltip,
        button_style="primary",
        icon="plus",
        style={"font_weight": "bold"},
        layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
    )


def template_minus_button(description="", tooltip="remove"):
    return widgets.Button(
        description=description,
        tooltip=tooltip,
        button_style="danger",
        icon="minus",
        style={"font_weight": "bold"},
        layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
    )


def template_add_remove(
    add_tooltip="add a new user defined schedule",
    remove_tooltip="remove user defined schedule",
):
    add = template_plus_button(tooltip=add_tooltip)
    remove = template_minus_button(tooltip=remove_tooltip)
    add_remove = widgets.HBox([add, remove])
    return add_remove, add, remove


def template_checkbox(value=False):
    return widgets.Checkbox(
        value=value,
        disabled=False,
        indent=False,
        layout=widgets.Layout(max_width="30px", height="30px", padding="3px"),
    )


def get_status(fpths_inputs, fpths_outputs):
    """check `st_mtime` for fpths_inputs and fpths_outputs and if any inputs
    returns 'no_outputs', 'outputs_need_updating' and 'up_to_date' depending of
    dates of last modification

    Args:
        fpths_inputs (List[pathlib.Path]): list of input files
        fpths_outputs (List[pathlib.Path]): list of output files

    Returns:
        str: 'no_outputs', 'outputs_need_updating' or 'up_to_date'
    """
    # ['no_outputs', 'up_to_date', 'outputs_need_updating']
    if len(fpths_inputs) == 0:
        return "error"
    for f in fpths_outputs:
        if f.is_file() is False:
            return "no_outputs"
    in_max = max([f.lstat().st_mtime for f in fpths_inputs])
    out_max = max([f.lstat().st_mtime for f in fpths_outputs])
    if in_max > out_max:
        return "outputs_need_updating"
    else:
        return "up_to_date"


def display_ui_tooltips(uiobj):
    """pass a ui object and display all items that contain tooltips with the tooltips exposed. NOT IN USE"""
    li = []
    for k, v in uiobj.__dict__.items():
        try:
            if "tooltip" in v.__dict__["_trait_values"]:
                li.append(v)
            else:
                pass
        except:
            pass
    return widgets.VBox(
        [widgets.HBox([l, widgets.HTML(f"<i>{l.tooltip}</i>")]) for l in li]
    )
