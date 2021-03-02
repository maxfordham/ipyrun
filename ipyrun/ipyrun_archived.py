# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: mf_base
#     language: python
#     name: mf_base
# ---

# +
import os
NBFDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import update_display, display, Image, JSON, Markdown, HTML, clear_output
import subprocess
from shutil import copyfile
import getpass
import importlib.util
import copy

import plotly.io as pio
import plotly.graph_objects as go

# widget stuff
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet

# core mf_modules
from mf_modules.file_operations import make_dir
from mf_modules.pandas_operations import del_matching
from mf_modules.mydocstring_display import display_module_docstring
from mf_modules.jupyter_formatting import display_python_file
from mf_modules.pydtype_operations import read_json, write_json

# from this repo
# this is an unpleasant hack. should aim to find a better solution

try:
    from ipyrun._runconfig import RunConfig
    from ipyrun._ipyeditcsv import EditCsv
    from ipyrun._ipyeditjson import EditJson
    from ipyrun._ipydisplayfile import DisplayFile, DisplayFiles
    from ipyrun.ipyrun import RunApp
except:
    from _runconfig import RunConfig
    from _ipyeditcsv import EditCsv
    from _ipyeditjson import EditJson
    from _ipydisplayfile import DisplayFile, DisplayFiles
    from ipyrun import RunApp

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0]+user[2]


# +
###################
# ARCHIVED
###################
class RunAppsMrunsOld():
    # Archived version of RunAppsMruns,
    # with inline compare files function
    def __init__(self, di, fdir_input, fdir_output):
        """
        Args:
            di (object): list of RunApp input configs.
                can explicitly specify a different RunApp to be used when passing
                the list
            fdir_input (filename): Directory, where Model Run JSON files
                            will be stored
            fdir_output (filename): Directory, where output files
                            will be stored
        """

        di_config = RunConfig(di).config
        self.batch = []
        self.fdir_input = os.path.join(di_config['fdir_inputs'], r'modelruninputs')
        self.fdir_output = fdir_output

        if not os.path.exists(self.fdir_input):
            os.makedirs(self.fdir_input)

        for filename in os.listdir(self.fdir_input):
            if filename.endswith(".json"):
                self.batch.append(self._create_process(process_name=os.path.splitext(filename)[0], di=di))

        filename = os.path.basename(fpth_script)
        process_name = '{0}_{1}'.format(os.path.splitext(filename)[0],'000')

        if not self.batch:
            self.batch.append(self._create_process(process_name=process_name, di=di))

        self.inputconfigs = self.batch

        self.processes = self._update_configs()
        self.li = []
        self._form()
        self._init_controls()

        for process in self.processes:
            self.li.append(process['app'](process['config']))
        self.out = widgets.Output()

    def _create_process(self, process_name, di):
        tmp = copy.deepcopy(di)
        fpth_input = os.path.join(self.fdir_input, process_name + '.json')
        tmp['script_outputs'][0]['fnm'] = os.path.join(self.fdir_output, process_name)
        tmp['fpth_inputs'] = fpth_input
        tmp['fdir_inputs'] = self.fdir_input
        tmp.update({'process_name':process_name})
        return {'app':RunApp,'config':tmp}

    def _update_configs(self):
        newconfigs = []
        for config in self.inputconfigs:
            newconfigs.append(self._create_config(config))
        return newconfigs

    def _create_config(self, config):
        if list(config.keys()) == ['app','config']:
            # app to use already explicitly specified
            return config
        else:
            # assume the config got passed without the associated app
            return{'app': RunApp, 'config': config}


    def _form(self):
        self.reset = widgets.Button(icon='fa-eye-slash',#'fa-repeat'
                                tooltip='removes temporary output view',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.help = widgets.Button(icon='fa-question-circle',
                                tooltip='describes the functionality of elements in the RunApp interface',
                                style={'font_weight':'bold'},
                                layout=widgets.Layout(width='5%'))
        self.run_batch = widgets.Button(description='run batch',
                                tooltip='execute checked processes below',
                                button_style='success',
                                style={'font_weight':'add'})
        self.add_run = widgets.Button(description='add run',
                                tooltip='add new run, based on another run',
                                button_style='warning',
                                style={'font_weight':'bold'})
        self.compare_runs = widgets.Button(description='compare run',
                                tooltip='Compare multiple runs',
                                button_style='info',
                                style={'font_weight':'bold'})
        self.form = widgets.HBox([self.reset, self.help, self.run_batch, self.add_run, self.compare_runs],
                        layout=widgets.Layout(width='100%',align_items='stretch'))

    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.run_batch.on_click(self._run_batch)
        self.compare_runs.on_click(self._compare_runs)
        self.add_run.on_click(self._add_run)

    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['MF_ROOT'],r'ipyrun\docs\images\RunBatch.png')
            display(Image(fpth))

    def _reset(self, sender):
        with self.out:
            clear_output()
        for l in self.li:
            l._reset(sender)

    def _get_process_names(self):
        return [process['config']['process_name'] for process in self.processes]

    def _get_apps_layout(self):
        return [widgets.VBox([l.layout, l.out]) for l in self.li]

    def _add_run(self, sender):

        # Create Dropdown & Run Button
        self.add_run_dd = widgets.Dropdown(
                options=self._get_process_names(),
                description='Run to Copy:',
                disabled=False)
        self.add_run_btn = widgets.Button(description='add chosen run',
                    tooltip='add chosen run',
                    button_style='primary',
                    style={'font_weight':'bold'})

        self.add_run_btn.on_click(self._run_add_run) # OnClick method
        with self.out:
            clear_output()
            display(self.add_run_dd)
            display(self.add_run_btn)

    def _run_add_run(self,sender):

        # Pull selected process from dropdown
        dd_val = self.add_run_dd.value
        dd_split = str(self.add_run_dd.value).split('_')

        # Get basename of selected process
        if(dd_split[-1].isdigit()):
            dd_process_name_base = "_".join(dd_split[:-1])
        else:
            dd_process_name_base = dd_val

        # Create new process name, by
        # appending the next number to the basename
        current_num = 0
        num_exists = True
        new_process_name = ""
        while (num_exists):
            new_process_name = '{0}_{1}'.format(dd_process_name_base,str(current_num).zfill(3))
            if new_process_name in self._get_process_names():
                current_num = current_num + 1
            else:
                num_exists = False

        # Copy the selected process to the new process
        new_process = None
        old_process = None
        for process in self.processes:
            if(process['config']['process_name'] == dd_val):
                old_process = copy.deepcopy(process['config'])

        # Copy old inputs file, to create new inputs file
        src = old_process['fpth_inputs']
        fdir_inputs = old_process['fdir_inputs']
        dst = os.path.join(fdir_inputs, '{0}{1}'.format(new_process_name,os.path.splitext(src)[1]))
        copyfile(src,dst)

        new_process = self._create_process(new_process_name, old_process)
        new_process = self._create_config(new_process)

        # Add new process to data within RunApps
        self.inputconfigs.append(new_process)
        self.processes.append(new_process)
        self.li.append(new_process['app'](new_process['config']))
        self.add_run_dd.options=self._get_process_names() # Update Dropdown

        # Display new process
        self.apps_layout.children = self._get_apps_layout()
        '''with self.out:
            display(self.li[-1])'''

    def _run_batch(self, sender):
        cnt = 0
        ttl = 0
        for l in self.li:
            ttl = ttl + 1
            if l.check.value:
                cnt = cnt + 1

        with self.out:
            clear_output()
            display(Markdown('{0} out of {1} scripts selected to be run'.format(cnt,ttl)))
            for l in self.li:
                if l.check.value:
                    display(Markdown('running: {0}'.format(l.config['process_name'])))
                    l._run_script('sender')
                    l._log() # 'sender'

    def _compare_runs(self, sender):
        cnt = 0
        ttl = 0
        for l in self.li:
            ttl = ttl + 1
            if l.check.value:
                cnt = cnt + 1
        with self.out:
            clear_output()
            display(Markdown('{0} out of {1} scripts selected to be run'.format(cnt,ttl)))

            self.compare_run_dd = widgets.Dropdown(
                    options=self._update_compare_dd(),
                    description='Pick graph:',
                    disabled=False)
            self.compare_run_btn = widgets.Button(description='Compare',
                        tooltip='Compare',
                        button_style='primary',
                        style={'font_weight':'bold'})

            self.compare_run_btn.on_click(self._run_compare_runs) # OnClick method
            display(self.compare_run_dd)
            display(self.compare_run_btn)

    def _update_compare_dd(self):
        self.l_checked = []
        graphs_count = {}
        graphs_tocompare = []
        for l in self.li:
            if l.check.value:
                out_dir = l.config['fpths_outputs']['0']
                self.l_checked.append(out_dir)
                for file in os.listdir(out_dir):
                    if file.endswith(".plotly"):
                        if file in graphs_count:
                            graphs_count[file] += 1
                        else:
                            graphs_count[file] = 1
        for graph in graphs_count:
            if graphs_count[graph] == len(self.l_checked):
                graphs_tocompare.append(graph)
        return graphs_tocompare

    def _run_compare_runs(self, sender):

        with self.out:

            self.compare_run_dd.options = self._update_compare_dd()
            filename = self.compare_run_dd.value

            data_raw = []
            for l in self.l_checked:
                data_raw.append((l,pio.read_json(os.path.join(l, filename))))

            layout = data_raw[0][1]['layout']
            data_interim = [(x[0], x[1]['data']) for x in data_raw]

            clear_output()
            legend_names = []
            data_out = []

            colors = ["lightskyblue",
                    "mediumseagreen",
                    "goldenrod",
                    "deeppink",
                    "LightGray",
                    "mediumspringgreen",
                     "darksalmon"]
            color_index = 0

            for dataset in data_interim:
                for scatter in dataset[1]:
                    if scatter['name'] not in legend_names:
                        plot = scatter
                        if scatter['name'] != "External temperature":
                            plot['name'] = scatter['name'] + ' - ' + os.path.basename(dataset[0])
                            plot['line']['color'] = colors[color_index]
                            color_index += 1
                        data_out.append(plot)
                        legend_names.append(plot['name'])

            fig = go.Figure(
                data=tuple(data_out),
                layout=layout
            )

            display(self.compare_run_dd)
            display(self.compare_run_btn)
            fig.show()


    def display(self):
        display(self.form)
        display(self.out)
        self.apps_layout = widgets.VBox(self._get_apps_layout())
        display(self.apps_layout)

    def _ipython_display_(self):
        self.display()

###################
# ARCHIVED
###################
class RunAppComparison(RunApp):
    # In order to pick which models to compare,
    # the reporting function needs a custom function
    # to add the model names to a dropdown
    def _edit_inputs(self, sender):
        comp_vals = {}

        if "fdir_compareinputs" in self.config:

            # Create list of models
            comp_vals_dir = self.config["fdir_compareinputs"]
            comp_vals = [file.split('__')[0] for file in os.listdir(comp_vals_dir)]
            comp_vals = list(set(comp_vals)) # Get unique values

            # Edit JSON, adding list of models
            json_data = read_json(self.config["fpth_inputs"])
            for element in json_data:
                if element["name"] == "Benchmark" or element["name"] == "As Designed":
                    element["options"] = comp_vals
                    if element["value"] not in comp_vals:
                        element["value"] = None
                '''elif element["name"] == "Comparison":
                    element["options"] = comp_vals
                    for value in element["value"]:
                        if value not in comp_vals:
                            element["value"].remove(value)'''

            write_json(json_data, fpth=self.config["fpth_inputs"])

        with self.out:
            clear_output()
            display(EditJson(self.config))
