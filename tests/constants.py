import pathlib

DIR_TESTS = pathlib.Path(__file__).parent
DIR_EXAMPLE_PROCESS = DIR_TESTS / 'examples' / 'line_graph'
FDIR_APPDATA = DIR_TESTS / 'examples' / 'fdir_appdata'
PATH_EXAMPLE_SCRIPT = DIR_TESTS / 'examples' / 'script_line_graph.py'
DIR_EXAMPLE_BATCH = DIR_TESTS / 'examples' / 'line_graph_batch'

DIR_EXAMPLES = DIR_TESTS / '..' / 'examples' 
DIR_EXAMPLE_APP = DIR_EXAMPLES / 'linegraph' / 'linegraph_app.py'