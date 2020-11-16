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
#     display_name: Python [conda env:mf_main]
#     language: python
#     name: conda-env-mf_main-py
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
from mf_scripts.gbxml import GbxmlParser, GbxmlReport

# from this repo
# this is an unpleasant hack. should aim to find a better solution

try:
    from ipyrun._runconfig import RunConfig
    from ipyrun._ipyeditcsv import EditCsv
    from ipyrun._ipyeditjson import EditJson
    from ipyrun._ipydisplayfile import DisplayFile, DisplayFiles
    from ipyrun.ipyrun import RunApp, RunConfigTemplated, RunAppsTemplated
except:
    from _runconfig import RunConfig
    from _ipyeditcsv import EditCsv
    from _ipyeditjson import EditJson
    from _ipydisplayfile import DisplayFile, DisplayFiles
    from ipyrun import RunApp, RunConfigTemplated, RunAppsTemplated

def get_mfuser_initials():
    user = getpass.getuser()
    return user[0]+user[2]


# -


class RunAppReport(RunApp):
    # In order to pick which graphs to show, 
    # the reporting function needs a custom function 
    # to add the graph names to a dropdown 

    def __init__(self, config, RunApps=None):
        """
        class that builds a user interface for:
        - editing inputs, 
        - running a script, 
        - reviewing the files output by the script
        - maintaining a log of when the script was last run, by who, and what the inputs were
        - allows users to reload previous input runs. 
        
        Args:
            config (dict): a dict that defines the script path, inputs path, archive inputs path, 
                log file path, output paths etc. this class inherits the RunConfig class which 
                has a default configuration for all of these things allowing the user to pass minimal 
                amounts of information to setup. 
                
        Example:
            ```
            config={
                'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
                'fdir':NBFDIR,
                }    

            r = RunApp(config) 
            from ipyrun._ipyeditjson import 
            
            ui = EditListOfDicts(li)
            ui
            ```
        """
        self.runapps = RunApps
        super().__init__(config) 
        
    def _update_comp(self, comp_runs):
        basenames = []

        for file in os.listdir(self.config["compare_run_graphs"]):
            if file.endswith(".plotly"):
                basenames.append('__'.join(file.split('__')[1:]))

        basenames = list(set(basenames))
        files_tocompare = []

        for basename in basenames:
            to_compare = True

            for name in comp_runs:
                fpth = os.path.join(self.config["compare_run_graphs"],"{0}__{1}".format(name,basename))
                if not os.path.exists(fpth):
                    to_compare = False

            if to_compare:
                files_tocompare.append(basename)
                
        return files_tocompare
        
    def _report_chooser_onchange(self, change):
        if change['type'] != 'change' or change['name'] != 'value':
            return
        
        for widget in self.editjson.widgets:
            if "tags" in widget.di:
                if widget.di["tags"] in change["owner"].options.values():
                    value = (change["new"] not in widget.di["tags"])
                    widget.di["disabled"] = value
                    widget.widget_only.disabled = value
                    widget.widget_only.value = False

    def _update_comp_onchange(self, change):
        if change['type'] != 'change' or change['name'] != 'value':
            return
        tmp = []
        for nested_w in self.editjson.widgets:
            if nested_w.nested_g and not nested_w.widget_only.disabled:
                for widget in nested_w.nested_g.widgets:
                    widget.widget_only.observe(self._update_comp_onchange)
                    if "tags" in widget.di:
                        if "process-comparison" in widget.di["tags"]:
                            tmp.append(widget.widget_only.value)
                    
        comp_graphs = self._update_comp(tmp)
        for widget in self.editjson.widgets:
            if "tags" in widget.di:
                if "comparison-graphs" in widget.di["tags"]:
                    value_list = list(widget.di["value"])
                    for value in value_list:
                        if value not in comp_graphs:
                            value_list.remove(value)
                    widget.di["value"] = tuple(value_list)
                    widget.widget_only.value = tuple(value_list)
                    widget.di["options"] = comp_graphs
                    widget.widget_only.options = comp_graphs
        return
            
    def _edit_inputs(self, sender):
        
        comp_vals = {}

        if self.runapps:
            compinputs = self.runapps._get_process_names()[1:]
            comp_vals = [""] + compinputs

            # Edit JSON, adding list of models
            json_data = read_json(self.config["fpth_inputs"])
            for nested_el in json_data:
                if isinstance(nested_el["value"], list):
                    for element in nested_el["value"]:
                        if "tags" in element:
                            if "single-process" in element["tags"]:
                                element["options"] = comp_vals
                                if element["value"] not in comp_vals:
                                    element["value"] = ""  
                            elif "mult-process" in element["tags"]:
                                for value in element["value"]:
                                    if value not in comp_vals:
                                        element["value"].remove(value)   
                                element["options"] = comp_vals
                
            write_json(json_data, fpth=self.config["fpth_inputs"])
            
        self.editjson = EditJson(self.config)

        for widget in self.editjson.widgets:
            if "tags" in widget.di:
                widget.widget_only.observe(self._update_comp_onchange)
                if "report-type" in widget.di["tags"]:
                    widget.widget_only.observe(self._report_chooser_onchange)
                    
        with self.out:
            clear_output()
            display(self.editjson)


# +
class EditJsonOverheating(EditJson):

    def __init__(self, config):
        super().__init__(config) 
        self.gbxmldf = None
        self._init_custom_buttons()
        
    def _init_custom_buttons(self):
        self.update_gbxml = widgets.Button(description='update from gbxml',button_style='warning',style={'font_weight':'bold'})
        self.button_bar.children += (self.update_gbxml,)
        #self.custom_bar = widgets.HBox([self.update_gbxml])
        self.update_gbxml.on_click(self._test)
        
    def _test(self, sender):
        gbxml_fpth = None
        for li in self.flattened_li():
            if 'tags' in li:
                if 'model_fpth' in li['tags']:
                    dirname = os.path.dirname(li['value'])
                    filename = os.path.basename(os.path.dirname(li['value'])) + '.xml'
                    gbxml_fpth = os.path.join(dirname,filename)
        if os.path.exists(gbxml_fpth):
            self._save_changes(None)
            self.li = read_json(self.fpth_inputs)
            for li in self.li:
                if 'tags' in li:
                    if 'fabrics-breakdown' in li['tags']:
                        fsum = GbxmlReport(gbxml_fpth).fabric_summ
                        li['editable'] = False
                        li['widget'] = "ipyagrid"
                        li['value'] = fsum.to_json(orient="columns")
                        '''for index, row in fsum.iterrows():
                            tmplabel = copy.copy(textlabel)
                            tmplabel['name'] = 'U Value'
                            tmplabel['label'] = str(index)
                            tmplabel['value'] = str(row["U-value_WPerSquareMeterK"])
                            li['value'].append(tmplabel)'''
            self._save_changes(None)
            self._update_from_file()
            self.apps_layout.children = self._get_apps_layout()
        
    def flattened_li(self):
        tmp_li = []
        def flatten(cur_li):
            for li in cur_li:
                tmp_li.append(li)
                if isinstance(li["value"], list) and li["value"]:
                    if isinstance(li["value"][0], dict):
                        flatten(li["value"])
            return
                    
        flatten(self.li)
        return tmp_li

    def display(self):
        box = widgets.VBox([
            self.button_bar,
            self.temp_message,
            self.inputform,
        ])
        self.layout = box
        display(self.layout)
        self.apps_layout = widgets.VBox(self._get_apps_layout())
        display(self.apps_layout)
        display(self.out)
        
class RunAppOverheating(RunApp):
    def _edit_inputs(self, sender):
        with self.out:
            clear_output()
            editjson = EditJsonOverheating(self.config)
            #display(editjson.test())
            display(editjson)


# -

class RunAppsOverheating(RunAppsTemplated):

    def __init__(self, di, app=RunAppOverheating, folder_name=None):
        super().__init__(di, app, folder_name) 
            
    def _create_process(self, process_name='TEMPLATE', template_process=None):
        process_di = copy.deepcopy(self.di)
        process_di['process_name'] = process_name
        process_di['pretty_name'] = process_name
        process_di['display_prefix'] = process_name
        process = self.configapp(process_di)
        process.config['fpth_inputs'] = process._fpth_inputs(process_name=process_name,template_process=template_process)
        return {'app':self.app,'config':process.config}
    
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
                                button_style='primary',
                                style={'font_weight':'bold'})
        self.del_run = widgets.Button(description='delete run',
                                tooltip='delete a run',
                                button_style='danger',
                                style={'font_weight':'bold'})
        self.comp_inputs = widgets.Button(description='compare inputs',
                                tooltip='show table that compares inputs',
                                button_style='warning',
                                style={'font_weight':'bold'})
        self.comp_outputs = widgets.Button(description='compare outputs',
                                tooltip='show table that compares outputs',
                                button_style='warning',
                                style={'font_weight':'bold'})
        self.form = widgets.HBox([self.reset, self.help, self.run_batch, self.comp_inputs, self.comp_outputs, self.add_run, self.del_run],
                        layout=widgets.Layout(width='100%',align_items='stretch'))   
    
    def _init_controls(self):
        self.help.on_click(self._help)
        self.reset.on_click(self._reset)
        self.run_batch.on_click(self._run_batch)
        self.add_run.on_click(self._add_run)
        self.del_run.on_click(self._del_run)
        self.comp_inputs.on_click(self._comp_inputs)
        self.comp_outputs.on_click(self._comp_outputs)
        
    def _help(self, sender):
        with self.out:
            clear_output()
            fpth = os.path.join(os.environ['mf_root'],r'ipyrun\docs\images\RunBatch.png')
            display(Image(fpth))
            
    def _reset(self, sender):
        with self.out:
            clear_output()
        for l in self.li:
            l._reset(sender)

    def _get_process_names(self):
        return [process['config']['process_name'] for process in self.processes]
    
    def _get_apps_layout(self):
        return [widgets.VBox([l.layout, l.out]) for l in self.li[1:]]

    def _comp_inputs(self, sender):
        # Onclick method for Compare Inputs
        
        def parse_inputs(values, inputs, name):
            # Input parse for JSON file
            for l in values:
                if l['name'] != 'Linked Files' and l['name'] !='Refs' and l['name'] !='Model File Path' and l['name'] != 'Fabrics - Breakdown':
                    if type(l['value']) is list:
                        inputs = parse_inputs(l['value'], inputs, l['name'])
                    else:
                            inputs[l['name']] = [l['value']]
            return inputs
            
        def unique_row(series):
            # Styler function for unique rows
            unique_tester = False
            for element in series:
                if element != series[0]:
                    unique_tester = True
            return ['background-color: yellow' if unique_tester else '' for element in series]
                    
        dfs = []
        
        for l in self.li[1:]:
            # Get inputs from each process
            fpth = l.config['fpth_inputs']
            inputs = read_json(fpth)
            calc_inputs = parse_inputs(inputs, {}, 'Misc')
            
            # Create dataframe from inputs
            df = pd.DataFrame(data=calc_inputs)
            df = df.T
            df.columns = [l.config['pretty_name']]
            dfs.append(df)
        
        # Concatenate all dataframes
        df_out = pd.concat(dfs, axis=1, join='inner', ignore_index=False, sort=False)
        
        # Add yellow to unique rows
        df_out = df_out.style.apply(unique_row, axis=1)

        with self.out:
            clear_output()
            display(df_out)
            
    def _comp_outputs(self, sender):
        
        # Create Dropdown & Run Button
        self.comp_out_runs = widgets.SelectMultiple(
                options=self._get_process_names()[1:],
                description='Runs:',
                disabled=False)
        self.comp_out_dd = widgets.Dropdown(
                options=[],
                description='Outputs:',
                disabled=False)
        self.comp_out_btn = widgets.Button(description='Compare Outputs',
                    tooltip='Compare Outputs',
                    button_style='primary',
                    style={'font_weight':'bold'})
        
        self.comp_out_btn.on_click(self._run_comp_outputs) # Onlick method
        self.comp_out_runs.observe(self.update_comp_out)
        
        with self.out:
            clear_output()
            display(self.comp_out_runs)
            display(self.comp_out_dd)
            display(self.comp_out_btn)
    
    def update_comp_out(self, change):
        if change['type'] != 'change' or change['name'] != 'value':
            return

        self.dataset_raw = copy.copy(self.comp_out_runs.value)
    
        basenames = []

        for file in os.listdir(self.di["script_outputs"]["0"]["fnm"]):
            if file.endswith(".plotly"):
                basenames.append('__'.join(file.split('__')[1:]))

        basenames = list(set(basenames))
        files_tocompare = []
        for basename in basenames:
            to_compare = True

            for name in change['new']:
                fpth = os.path.join(self.di["script_outputs"]["0"]["fnm"],"{0}__{1}".format(name,basename))
                if not os.path.exists(fpth):
                    to_compare = False

            if to_compare:
                files_tocompare.append(basename)
        self.comp_out_dd.options = files_tocompare

    def comp_temps(self, params, filename, colors):
        data_out = []
        legend_names = []
        color_index = 0
        for data_raw in self.dataset_raw:
            fpth = os.path.join(self.di["script_outputs"]["0"]["fnm"],"{0}__{1}".format(data_raw,filename))
            graph = pio.read_json(fpth)['data']
            for scatter in graph:
                if scatter['name'] not in legend_names:
                    plot = scatter
                    plot['line']['width'] = 1.5
                    if scatter['name'] not in params[1]:
                        name = "{0} - {1}".format(scatter['name'], os.path.basename(data_raw))
                        plot['name'] = name
                        plot['line']['color'] = colors[color_index]
                        data_out.append(plot)
                        color_index += 1
                        if color_index > len(colors):
                            color_index = 0
                    else:
                        plot['line']['color'] = params[1][scatter['name']]
                        data_out.insert(0, plot)

                    legend_names.append(plot['name'])

        fpth = os.path.join(self.di["script_outputs"]["0"]["fnm"],"{0}__{1}".format(self.dataset_raw[0],filename))
        layout = pio.read_json(fpth)['layout']
        fig = go.Figure(
            data=tuple(data_out),
            layout=layout
        )
        fig.update_layout(legend=dict(
            yanchor="bottom",
            y=-0.5,
            xanchor="left",
            x=0
        ))
        return fig
        
    def _run_comp_outputs(self, sender):
        # Create Comparison Graph, for each file
        filename = self.comp_out_dd.value
        colors = ["DodgerBlue",
                  "MediumSeaGreen",
                  "Peru",
                  "LightGray",
                  "Turquoise",
                  "darksalmon",
                  "goldenrod"]
        comp_funcs = {
            'temps': [self.comp_temps, 
                      {"External Temperature":"Crimson"}
                     ]
        }

        fig = []
        prefix = self.comp_out_dd.value.split('__')[0]
        if prefix in comp_funcs:
            fig = comp_funcs[prefix][0](comp_funcs[prefix], filename, colors)
            
        with self.out:
            clear_output()
            display(self.comp_out_runs)
            display(self.comp_out_dd)
            display(self.comp_out_btn)
            display(fig)






