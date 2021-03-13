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
FDIR = os.path.dirname(os.path.realpath('__file__'))
import importlib.util
from shutil import copyfile
from mf_modules.datamine_functions import recursive_glob
from mf_modules.file_operations import make_dir
from mf_modules.pydtype_operations import write_json, flatten_list
import copy

#from IPython.display import Markdown
#display(Markdown('<img src="../../ipypdt/img/check-xlsx.png" width="1200" height="400">'))

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Type
#from pydantic import BaseModel, FilePath #  ADD PYDANTIC IN THE FUTURE TO EXPORT TO SCHEMA
import pathlib
from dacite import from_dict

#from mf_modules.job_dirs import JobDirs, ScheduleDirs, make_dirs_from_fdir_keys
from mf_om.directories import JobDirs, make_dirs_from_fdir_keys
from mf_modules.pydtype_operations import flatten_list
from mf_modules.file_operations import make_dir, jobno_fromdir
# -

FDIR_EXAMPLE = '.'
FPTH_SCRIPT_EXAMPLE = os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')


# +

# base ------------------------------
@dataclass
class BaseParams:
    fdir: str = FDIR_EXAMPLE
    fdir_appdata: str = os.path.join(fdir,'appdata')
    fpth_script: str = FPTH_SCRIPT_EXAMPLE
    script_name: str = 'script_name'
    process_name: str = 'None'
    pretty_name: str = 'None'
    job_no: str = 'J4321'

    def __post_init__(self):
        self.fdir_appdata = os.path.join(self.fdir,'appdata')
        self.job_no = jobno_fromdir(self.fdir)
        self.script_name = os.path.splitext(os.path.basename(self.fpth_script))[0]
        self.process_name, self.pretty_name = default_names_BaseParams(self)

def default_names_BaseParams(base_params: BaseParams):
    """create default names"""
    if base_params.process_name == 'None':
        process_name = base_params.script_name
    else:
        process_name = base_params.process_name
    if base_params.pretty_name == 'None':
        pretty_name = base_params.process_name
    else:
        pretty_name = base_params.pretty_name
    return process_name, pretty_name


# config ----------------------------
@dataclass
class Config(BaseParams):
    """where to save the script config files"""
    fdir_config: str = os.path.join(BaseParams.fdir_appdata,'config')
    fnm_config: str = 'config-' + BaseParams.process_name + '.json'
    fpth_config: str = os.path.join(fdir_config,fnm_config)

    def __post_init__(self):
        super().__post_init__()
        self.fdir_config = os.path.join(self.fdir_appdata,'config')
        self.fnm_config = 'config-' + self.process_name + '.json'
        self.fpth_config = os.path.join(self.fdir_config,self.fnm_config)

# inputs ----------------------------
@dataclass
class InputDirs:
    fdir: str = '.'
    fpths: List[str] = field(default_factory=list)

@dataclass
class InputOptions:
    project: InputDirs
    template: InputDirs

# not used here. for SimpleEditJson only. 
@dataclass
class SimpleInputs:
    """NOT IN USE. defines simple input locations for SimpleEditJson"""
    fdir_inputs: str = 'fdir_inputs'
    fdir_template_inputs: str = 'fdir_template_inputs'
    fpth_inputs: str = 'fpth_inputs'
    fpth_inputs_options: InputOptions = InputOptions(
        project=InputDirs(fdir=fdir_inputs),
        template=InputDirs(fdir=fdir_template_inputs))

@dataclass
class Inputs(BaseParams):
    """defines locations of project and template input files"""
    ftyp_inputs: str = 'json'
    fdir_inputs: str = os.path.join(BaseParams.fdir_appdata,'inputs')
    fdir_template_inputs: str = os.path.join(os.path.dirname(BaseParams.fpth_script),'inputs')
    fdir_inputs_archive: str = os.path.join(BaseParams.fdir_appdata,'archive')
    fpth_inputs: str = os.path.join(fdir_inputs,'inputs-' + BaseParams.process_name + '.' + ftyp_inputs)
    fpth_template_input: str = 'fpth_template_input'
    fpth_inputs_options: InputOptions = InputOptions(
        project=InputDirs(fdir=fdir_inputs),
        template=InputDirs(fdir=fdir_template_inputs))
    create_execute_file: bool = False
    fpth_execute: str = 'None'

    def __post_init__(self):
        # updates the inputs relative to changes in base params or class initiation
        super().__post_init__()
        self.fdir_inputs = os.path.join(self.fdir_appdata,'inputs')
        self.fdir_template_inputs = os.path.join(os.path.dirname(self.fpth_script),'template_inputs')
        self.fdir_inputs_archive = os.path.join(self.fdir_appdata,'archive')
        self.fpth_inputs = os.path.join(self.fdir_inputs,'inputs-' + self.process_name + '.' + self.ftyp_inputs)
        self.fpth_inputs_options = _fpth_inputs_options(self)
        self.fpth_template_input = _fpth_template_input(self)
        #_fpth_inputs_file_from_template(self)
        if self.create_execute_file:
            self.fpth_execute = os.path.join(self.fdir_inputs,'execute-' + self.process_name + '.' + self.ftyp_inputs)
            
    

#  setting default inputs
def _fpth_template_input(inputs: Inputs, print_errors=False) -> str:
    """looks for template input files locally to the script"""
    """finds template inputs files"""
    fpths = recursive_glob(rootdir=inputs.fdir_template_inputs,
                          pattern='*'+'inputs-' + inputs.script_name+'.*',
                          recursive=True)
    if len(fpths) == 0:
        fpth_default = os.path.join(inputs.fdir_inputs, 'inputs-'+inputs.process_name) + '.json'
        error = 'could not find template input: {0}'.format(os.path.join(inputs.fdir_inputs, inputs.process_name))
        print(error)
        fpths.append(fpth_default)
    fpth_template_input = fpths[0]
    return fpth_template_input

def _fpth_inputs_file_from_template(inputs: Inputs, print_errors=False) -> None:
    """copies template inputs file into local folder"""
    if os.path.isfile(inputs.fpth_template_input):
        if not os.path.isfile(inputs.fpth_inputs):
            if not os.path.isdir(os.path.dirname(inputs.fpth_inputs)):
                make_dir(os.path.dirname(inputs.fpth_inputs))
            copyfile(inputs.fpth_template_input, inputs.fpth_inputs)

def _fpth_inputs_options(inputs: Inputs, print_errors=True) -> InputOptions:
    """finds all input options (from templates and from past runs)"""
    patterns = ['*' + inputs.process_name + '*', '*' + inputs.script_name + '*']
    patterns = list(set(patterns))
    di = {
        'template':{
            'fdir': inputs.fdir_template_inputs,
            'fpths':[]
        },
        'project':{
            'fdir': inputs.fdir_inputs,
            'fpths':[]
        },
    }
    # NOTE. this is no longer how it gets the project files...
    # these are taken from the log.csv ouptut.
    errors = []
    cnt = 0
    valid_exts = ['.csv','.json']
    for k,v in di.items():
        for pattern in patterns:
            fpths = recursive_glob(rootdir=v['fdir'],pattern=pattern,recursive=True)
            fpths = [fpth for fpth in fpths if '.ipynb_checkpoints' not in fpth]
            di[k]['fpths'].extend(fpths)
            di[k]['fpths'] = list(set(di[k]['fpths']))
            cnt += len(fpths)
            errors.append(['{0} not csv or json'.format(fpth) for fpth in fpths if os.path.splitext(fpth)[1] not in valid_exts])
    if cnt == 0:
        errors.append('couldnt find and input files within the templates folder or in the project folder')
    if print_errors:
        [print(p) for p in flatten_list(errors)]
    return from_dict(data=di,data_class=InputOptions)


# log -------------------------------
@dataclass
class Log(BaseParams):
    """defines location of log files"""
    fdir_log: str = os.path.join(BaseParams.fdir_appdata,'log')
    fnm_log: str = 'log-' + BaseParams.process_name + '.csv'
    fpth_log: str = os.path.join(fdir_log,fnm_log)

    def __post_init__(self):
        # updates the inputs relative to changes in base params or class initiation
        super().__post_init__()
        self.fdir_log = os.path.join(self.fdir_appdata,'log')
        self.fnm_log = 'log-' + self.process_name + '.csv'
        self.fpth_log = os.path.join(self.fdir_log, self.fnm_log)
"""
# outputs -------------------------------
@dataclass
class Output:
    #defines location of an output file
    fdir_rel: str = ''
    fnm: str ='fnm.json'
    description: str = 'description of output'
    display_preview: bool = True

@dataclass
class Outputs(BaseParams):
    #defines location of output files. note. fpths_outputs built from script_outputs
    fdir_outputs: str = os.path.join(BaseParams.fdir,'outputs')
    fdirs_outputs: List[str] = field(default_factory=list)
    script_outputs: List[Output] = field(default_factory=list) #  lambda:[Output(fdir_rel='')]  #  Dict[str:Output] = field(default_factory=dict)?
    fpths_outputs: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.fdir_outputs = os.path.join(self.fdir,'outputs')
        self.fdirs_outputs = _fdirs_from_script_outputs_dict(self)
        self.fpths_outputs = _fpths_from_script_outputs_dict(self)

def _fdirs_from_script_outputs_dict(outputs: Outputs):
    return [os.path.realpath(os.path.join(outputs.fdir_outputs,s.fdir_rel)) for s in outputs.script_outputs] #  .items()

def _fpths_from_script_outputs_dict(outputs: Outputs):
    return [os.path.realpath(os.path.join(outputs.fdir_outputs,s.fdir_rel,s.fnm)) for s in outputs.script_outputs] #  .items()
"""

# outputs -------------------------------
@dataclass
class Output:
    """defines location of an output file"""
    fpth: str
    description: str

@dataclass
class Outputs(BaseParams):
    """defines location of output files. note. fpths_outputs built from script_outputs"""
    script_outputs: List[Output] = field(default_factory=list) #  lambda:[Output(fdir_rel='')]  #  Dict[str:Output] = field(default_factory=dict)?
    
    @property
    def fpths_outputs(self): 
        return [s.fpth for s in self.script_outputs]


def _script_outputs_template(outputs: Outputs):
    """
    looks in the script file and finds and returns object called "script_outputs".
    this should be a list of Output objects.
    """
    if os.path.isfile(outputs.fpth_script):
        try:
            spec = importlib.util.spec_from_file_location(outputs.script_name, outputs.fpth_script)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            script_outputs = foo.script_outputs
        except:
            print('error loading script: {0}'.format(outputs.fpth_script)) #  add to logging instead
            script_outputs = []
    else:
        print('script not exist: {0}'.format(outputs.fpth_script)) #  add to logging instead
        script_outputs = []
    return script_outputs

@dataclass
class AppConfig(Config, Inputs, Log, Outputs):
    """
    ---------------------------------
    Atrributes:
        fpth_script
        process_name
        pretty_name
        script_outputs
        
    **NOTE** 
    All other params are overwritten on initiation of an AppConfig obj using the __post_init__
    ---------------------------------
    """
    pass
    #jobno: int = 4321

def make_dirs_AppConfig(Ac: AppConfig):
    """
    makes all of the "fdirs" directories in an AppConfig object
    """
    make_dirs_from_fdir_keys(asdict(Ac))

if __name__ =='__main__':
    fdir=r'C:\engDev\git_mf\ipypdt\example\J0000'
    Ac = AppConfig(fdir=fdir,process_name='pretty_name',pretty_name='boo',fpth_script=os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\test\test.py'), script_outputs=[Output(fpth='asdf',description='asd')])
    from pprint import pprint
    make_dirs_AppConfig(Ac)
    pprint(asdict(Ac))


# -

class RunConfig():

    def __init__(self,
                 config_app: Type[AppConfig],
                 #config_overrides={},
                 config_job: Type[JobDirs]=JobDirs(),
                 lkup_outputs_from_script: bool=True,
                 ):
        """
        class that manages cache directories and input/output file-locations for the RunApp
        
        Args:
            config_app: contains fdirs/fpths for inputs, log files and general app config
            congfig_job: contains fdirs/fpths for data that will be passed to the app / created by the app
            lkup_outputs_from_script: bool, default = True, if true, the RunConfig will look in the script for 
                a dataobject called "script_outputs" (Type == Outputs)
        """
        self._init_RunConfig(config_app, config_job=config_job, lkup_outputs_from_script=lkup_outputs_from_script)

    def _init_RunConfig(self, config_app, config_job=JobDirs(), lkup_outputs_from_script=True):
        self.errors = []
        #self.config_overrides = config_overrides
        self._init_config_job(config_job)
        self._update_config(config_app)
        self.lkup_outputs_from_script = lkup_outputs_from_script
        
        self.errors = []
        self._make_dirs()
        if self.lkup_outputs_from_script:
            self.script_outputs_template = _script_outputs_template(self.config_app)
            self.config_app.script_outputs = self.script_outputs_template
        self._inherit_AppConfig()

    def _init_config_job(self, config_job):
        self.config_job = config_job

    def _update_config(self, config_app):
        """
        a configuration dict is passed to the app that defines the configuration variables
        of the app. e.g filepaths for the script path, user inputs template file etc.
        where explicit inputs are not given this function updates the config dict with
        default values, flagging any errors that are spotted on the way.
        """
        if type(config_app) != AppConfig:
            print('DEPRECATION WARNING! - the "config_app" var passed to the RunConfig class should be an AppConfig object not a dict')
            self.config_app = from_dict(data=config_app,data_class=AppConfig)
        else:
            self.config_app = config_app
        _fpth_inputs_file_from_template(self.config_app)

    def _inherit_AppConfig(self):
        self.__dict__.update(**self.config)

    @property
    def config(self):
        out = asdict(self.config_app)
        out['job_config'] = asdict(self.config_job)
        return out

    def _make_dirs(self):
        """if fdir in string of key folder made from value"""
        make_dirs_from_fdir_keys(asdict(self.config_app))
        make_dirs_from_fdir_keys(asdict(self.config_job))
        #make_dirs_AppConfig(self.config_app)

    def _template_input_ext(self):
        return os.path.splitext(self.fpth_template_input)[1]

    def config_to_json(self):
        write_json(self.config,
                   sort_keys=True,
                   indent=4,
                   fpth=self.config['fpth_config'],
                   print_fpth=False,
                   openFile=False)

# +

if __name__ =='__main__':
    config = {
        'fpth_script':r'C:\engDev\git_mf\ipypdt\ipypdt\rvttxt_to_schedule.py',#os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        'process_name':'pipework',
        'fdir':'.',
        #'fpth_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test\test.csv',
        #'fdir_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test'
        }

    config0 = {
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':FDIR,
        'script_outputs': [
            {
                'fdir':r'..\reports',
                'fnm': r'JupyterReportDemo.pdf',
                'description': "a pdf report from word"
            }
        ]
    }
    config1 = {
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),#,
        'process_name':'pipework',
        'fdir':'.',
        #'fpth_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test\test.csv',
        #'fdir_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test'
        }
    from pprint import pprint
    config_job=JobDirs(fdirRoot='.')
    config_app = AppConfig(**config1)
    rc = RunConfig(config_app,config_job=config_job,lkup_outputs_from_script=True)#, config_job=config_job)
    pprint(rc.config)
