# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3.9 (XPython)
#     language: python
#     name: xpython
# ---

# +
import os
import importlib.util
import pathlib
from shutil import copyfile
import copy
import getpass
import json
from dataclasses import field, asdict #dataclass, 
from dacite import from_dict
from typing import Optional, List, Dict, Type, Any
from pydantic import BaseModel, FilePath #  ADD PYDANTIC IN THE FUTURE TO EXPORT TO SCHEMA
from datetime import datetime
#import pydantic
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder

from mfom.directories import ProjectDirs, make_project_dirs
from mfom.document import DocumentHeader

from ipyrun.utils import flatten_list, make_dir, recursive_glob, time_meta_data, write_json, read_json, make_dirs_from_fdir_keys, jobno_fromdir
from ipyrun.utils import get_time_of_most_recent_content_modification
from ipyrun.constants import FDIR_ROOT_EXAMPLE, FDIR_APP_EXAMPLE, FPTH_SCRIPT_EXAMPLE

# + tags=[]
def pydantic_dataclass_to_file(data: Type[dataclass], fpth='pydantic_dataclass.json'):
    """writes a pydantic BaseModel to file"""
    f = open(fpth, "w")
    f.write(json.dumps(data, indent=4, default=pydantic_encoder))
    f.close()
    return fpth

# base ------------------------------
@dataclass
class BaseParams:
    fdir: str = FDIR_APP_EXAMPLE
    fdir_appdata: str = 'None'
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
    fdir_inputs_archive: str = os.path.join(fdir_inputs,'archive')
    fpth_inputs: str = os.path.join(fdir_inputs,'inputs-' + BaseParams.process_name + '.' + ftyp_inputs)
    fpth_template_input: str = 'fpth_template_input'
    fpth_inputs_options: InputOptions = InputOptions(
        project=InputDirs(fdir=fdir_inputs),
        template=InputDirs(fdir=fdir_template_inputs))
    create_execute_file: bool = False
    fdir_execute: str = 'None'
    fpth_execute: str = 'None'

    def __post_init__(self):
        # updates the inputs relative to changes in base params or class initiation
        super().__post_init__()
        self.fdir_inputs = os.path.join(self.fdir_appdata,'inputs')
        self.fdir_template_inputs = os.path.join(os.path.dirname(self.fpth_script),'template_inputs')
        self.fdir_inputs_archive = os.path.join(self.fdir_inputs,'archive')
        self.fpth_inputs = os.path.join(self.fdir_inputs,'inputs-' + self.process_name + '.' + self.ftyp_inputs)
        self.fpth_inputs_options = _fpth_inputs_options(self)
        self.fpth_template_input = _fpth_template_input(self)
        #_fpth_inputs_file_from_template(self)
        if self.create_execute_file:
            self.fdir_execute = os.path.join(self.fdir_appdata,'execute')
            self.fpth_execute = os.path.join(self.fdir_execute,'execute-' + self.process_name + '.' + self.ftyp_inputs)

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
        if print_errors:
            # TODO: sort out test scripts, examples and defaults
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

def _fpth_inputs_options(inputs: Inputs, print_errors=False) -> InputOptions:
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
        }
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
        # TODO: sort out test scripts, examples and defaults
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
        

# outputs -------------------------------
        
@dataclass
class File:
    fpth: str
    fdir: str = ''
    author: str = 'unknown'
    time_of_most_recent_content_modification: datetime = None
    description: str = None
    note: str = ''
        
    def __post_init__(self):
        # updates the inputs relative to changes in base params or class initiation
        self.fdir = os.path.dirname(self.fpth)
        self.author = getpass.getuser()  #  TODO: os.stat(path).st_uid # for author file instead? 
        self.time_of_most_recent_content_modification = get_time_of_most_recent_content_modification(self.fpth)
        
@dataclass
class Output(File):
    document_header: Optional[DocumentHeader] = None #https://github.com/samuelcolvin/pydantic/issues/1223
        
    def __post_init__(self):
        # updates the inputs relative to changes in base params or class initiation
        super().__post_init__()
        
        
#  TODO: retire "lkup_outputs_from_script" functionality
@dataclass
class Outputs(BaseParams):
    """defines location of output files. note. fpths_outputs built from script_outputs"""
    script_outputs: List[Output] = field(default_factory=list) #  lambda:[Output(fdir_rel='')]  #  Dict[str:Output] = field(default_factory=dict)?
    lkup_outputs_from_script: bool = False
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
    if type(script_outputs) != Outputs:
        try:
            script_outputs = from_dict(data=script_outputs,data_class=Outputs)
        except:
            pass
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
    config_job: ProjectDirs = None # field(default_factory=ProjectDirs)
    config_ui: Any = None # field(default_factory=ProjectDirs)
    config_type: str = None
    
    def __post_init__(self):
        super().__post_init__()
        self.config_type = str(type(self))

def make_dirs_AppConfig(ac: AppConfig):
    """
    makes all of the "fdirs" directories in an AppConfig object
    """
    make_dirs_from_fdir_keys(asdict(ac))
    
    try:
        if issubclass(type(ac.config_job), BaseModel):  # TODO: update AppConfig to be a BaseModel rather than @dataclass
            make_project_dirs(ac.config_job)
        else:
            make_dirs_from_fdir_keys(asdict(ac.config_job))
    except:
        print('didnt make config_job')
        pass

if __name__ =='__main__':

    Ac = AppConfig(fdir=FDIR_APP_EXAMPLE,
                   process_name='pretty_name',
                   #pretty_name='boo',
                   fpth_script=FPTH_SCRIPT_EXAMPLE, 
                   #script_outputs=[Output(fpth='asdf',description='asd')],
                   create_execute_file=True,
                   #config_job=ProjectDirs()
                  )
    from pprint import pprint
    make_dirs_AppConfig(Ac)
    pprint(asdict(Ac))


# +
def class_obj_from_type_string(class_type_string:str)-> Type:
    """
    given the str(type(Obj)) of an Obj, this function
    imports it from the relevant lib (using getattr and
    importlib) and returns the Obj. 
    
    makes it easy to define class used as a string in a json
    object and then use this class to re-initite it.
    
    Args:
        class_type_string
    Returns: 
        obj
    """
    
    def find(s, ch):
        return [i for i, ltr in enumerate(s) if ltr == ch]
    cl = class_type_string
    ind = find(cl, "'")
    nm  = cl[ind[0]+1:ind[1]]
    nms =  nm.split('.')
    clss = nms[-1:][0]
    mod = '.'.join(nms[:-1])
    return getattr(importlib.import_module(mod), clss)


class RunConfig():

    def __init__(self,
                 config_app: AppConfig,
                 #config_app_type: Type[AppConfig]=AppConfig,
                 revert_to_file:bool=False,
                 #config_overrides={},
                 #config_job: Type[ProjectDirs]=ProjectDirs(),
                 #lkup_outputs_from_script: bool=True,
                 ):
        """
        class that manages cache directories and input/output file-locations for the RunApp
        
        Args:
            config_app: contains fdirs/fpths for inputs, log files and general app config
            revert_to_file: if a config file already exists, then AppConfig is updated based on that 
        """
        self._init_RunConfig(config_app, revert_to_file=revert_to_file)# lkup_outputs_from_script=lkup_outputs_from_script) #config_job=config_job,

    def _init_RunConfig(self,config_app, revert_to_file=True):# lkup_outputs_from_script=True): #config_job=ProjectDirs(),
        self.revert_to_file = revert_to_file
        self.errors = []
        self._update_config(config_app)
        self.errors = []
        self._make_dirs()
        if self.config_app.lkup_outputs_from_script:
            self.script_outputs_template = _script_outputs_template(self.config_app)
            self.config_app.script_outputs = self.script_outputs_template
        self._inherit_AppConfig() # TODO: remove this

    def _update_config(self, config_app):
        """
        a configuration dict is passed to the app that defines the configuration variables
        of the app. e.g filepaths for the script path, user inputs template file etc.
        where explicit inputs are not given this function updates the config dict with
        default values, flagging any errors that are spotted on the way.
        """
        #if type(config_app) != AppConfig:
        #    print('DEPRECATION WARNING! - the "config_app" var passed to the RunConfig class should be an AppConfig object not a dict')
        #    self.config_app = from_dict(data=config_app,data_class=AppConfig)
        #else:
        if self.revert_to_file:
            if os.path.isfile(config_app.fpth_config):
                try:
                    self.config_app = RunConfig.config_from_json(config_app.fpth_config)
                except:
                    print('Reading AppConfig from: {0}'.format(config_app.fpth_config))
                    print('not a valid AppConfig object {0} '.format(config_app.fpth_config))
                    self.config_app = config_app
            else:
                self.config_app = config_app
        else:
            self.config_app = config_app

        _fpth_inputs_file_from_template(self.config_app)

    def _inherit_AppConfig(self):
        self.__dict__.update(**self.config)

    @property
    def config(self):
        return asdict(self.config_app)
        #out['job_config'] = asdict(self.config_job)

    def _make_dirs(self):
        """if fdir in string of key folder made from value"""
        make_dirs_from_fdir_keys(asdict(self.config_app))
        try:
            make_dirs_from_fdir_keys(asdict(self.config_job.config_job))  # add recursive func to make_dirs_from_fdir_keys
        except:
            pass
        #make_dirs_AppConfig(self.config_app)

    def _template_input_ext(self):
        return os.path.splitext(self.fpth_template_input)[1]

    def config_to_json(self):
        pydantic_dataclass_to_file(self.config_app,fpth=self.config_app.fpth_config)
        
    @staticmethod
    def config_from_json(fpth: str) -> AppConfig:
        di = read_json(fpth)
        classtype = class_obj_from_type_string(di['config_type'])
        return classtype(**di)
        
    @property
    def fpths_outputs(self): 
        print('DEPRECATED: use self.config_app.fpths_outputs instead')
        return [s['fpth'] for s in self.script_outputs]

# -

if __name__ =='__main__':
    
    #  example - extending AppConfig
    @dataclass
    class Project:#(BaseModel)
        projectName: str = 'Digital Design'
        projectNumber: str = 'J4321'
            
    @dataclass
    class ProjectDirs(Project):#,BaseModel
        fdirProjectsRoot: str = 'J:\\'
        fdirProject: str = 'fdirProject'#os.path.join(fdirProjectsRoot, str(Project.projectNumber))
        fdirSchedule: str = ''
        fdirRevit: str = os.path.join(fdirProject, 'Cad', 'Revit')
        fdirAutomation: str = os.path.join(fdirProject, 'Automation')

        def __post_init__(self):
            self.fdirProject = os.path.join(self.fdirProjectsRoot, self.projectNumber)
            self.fdirSchedule = os.path.join(self.fdirProject, 'Schedule')
            self.fdirRevit = os.path.join(self.fdirProject, 'Cad', 'Revit')
            self.fdirAutomation = os.path.join(self.fdirProject, 'Automation')

    @dataclass 
    class ExtendAppConfig(AppConfig):
        config_job: ProjectDirs

        def __post_init__(self):
            # updates the inputs relative to changes in base params or class initiation
            super().__post_init__()
            
    fdir=os.path.join('..','examples','J0000','Automation')
    fpth_script=os.path.join('..','examples','scripts','expansion_vessel_sizing.py')
    
    config_app = ExtendAppConfig(
        fdir=FDIR_APP_EXAMPLE,
        fpth_script=FPTH_SCRIPT_EXAMPLE,
        create_execute_file=True,
        process_name='GrilleSchedule',
        config_job=ProjectDirs(
            fdirProjectsRoot=fdir,
            projectNumber='J0000',
        )
    )
    RC = RunConfig(config_app)
    RC.config_to_json()

#Output()
if __name__ =='__main__':

    config = {
        'fpth_script':FPTH_SCRIPT_EXAMPLE,
        'fdir':FDIR_APP_EXAMPLE,
        'script_outputs': [
            {
                'fpth':FPTH_SCRIPT_EXAMPLE,
                'description': "a pdf report from word"
            }
        ]
    }
    from pprint import pprint
    #config_job=ProjectDirs(fdirProjectsRoot='.')

    print('AppConfig: vanilla')
    print('--------------------')
    config_app = AppConfig(**config)
    rc = RunConfig(config_app)#, config_job=config_job)#,lkup_outputs_from_script=False
    rc.config_to_json()
    from ipyrun.utils import open_file
    open_file(rc.config_app.fpth_config)
    pprint(rc.config)
    print('')


if __name__ =='__main__':
    #  validate round trip: AppConfig dataclass from json
    obj = rc.config_from_json(rc.config_app.fpth_config)
