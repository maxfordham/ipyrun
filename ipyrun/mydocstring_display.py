"""
wrappers around mydocstring. 
consider incorporating into the core package. 
"""

import os
import subprocess
from IPython.display import display, Markdown
try:
    from IPython.display import Image #  this is due to a known issue with xeus-python. remove try except in future.
except:
    pass
from ipyrun.utils import read_module_docstring

#  from mf_modules.pydtype_operations import list_items_after
def list_items_after(li,after='Image'):
    """
    list all items in list after a given item 
    is found

    Args:
        li (list): 
        **after (?): list item after which new list begins
            uses find in so partial string matches work

    Returns:
        li_ (list): category
    """
    li_=[]
    b=False
    for l in li:
        if after in l:
            b=True
        li_.append(b)
    if True not in li_:
        return None
    else:
        index = [n for n in range(0,len(li_)) if li_[n]]
        return li[index[0]:index[len(index)-1]+1]

def docstring_img_list(doc):

    def get_imgs(li):
        li1=[]
        for n in range(1,len(li)):
            if li[n][0:4]!='    ':
                break
            else:
                li1.append(li[n].strip())
        li1 = list(filter(None, li1))
        return li1

    def replace_env_var(s):
        char='%'
        ind = [n for n in range(0,len(list(s))) if list(s)[n]==char]
        var = ''.join(list(s)[ind[0]:ind[1]+1])
        return s.replace(var,os.environ[var.replace(char,'')])

    def replace_env_vars(li):
        return [replace_env_var(l) for l in li]
    
    li = list_items_after(doc.split('\n'),after='Image')
    if li == None:
        return li
    li = get_imgs(li)
    li = replace_env_vars(li)
    return li
    
def display_doc_imgs(li):
    [display(Image(l)) for l in li];
    
#def display_module_docstring(doc):
#    li = docstring_img_list(doc)
#    display_doc_imgs(li)
#    print(doc)

    
def docstringimgs_from_path(fpth):
    doc = read_module_docstring(fpth)
    li = docstring_img_list(doc)
    display_doc_imgs(li)
    
def display_module_docstring(fpth):
    doc = read_module_docstring(fpth)
    li = docstring_img_list(doc)
    if li != None:
        display_doc_imgs(li)

    d = subprocess.check_output(['mydocstring', fpth, '.', '--markdown'])
    d = d.decode('utf-8')
    display(Markdown(d))
    
def display_function_docstring(fpth,function_name):

    #doc = read_module_docstring(fpth)

    d = subprocess.check_output(['mydocstring', fpth, function_name, '--markdown'])
    li = docstring_img_list(d.decode('utf-8'))
    if li != None:
        display_doc_imgs(li)
    d = d.decode('utf-8')
    display(Markdown(d))
    
if __name__ == "__main__":
    if __debug__:
        import os
        fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py')
        fpth = os.path.join(os.environ['mf_root'], r'MF_Toolbox\dev\mf_modules\gbxml.py')
        display_module_docstring(fpth)
        print('done')
    else:
        import sys
        fpth = sys.argv[1]
        display_module_docstring(fpth)
    
