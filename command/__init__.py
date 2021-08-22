from os.path import dirname, basename, isfile, join
import importlib
import glob
modules = glob.glob(join(dirname(__file__), "*.py"))
for f in modules:
    if isfile(f) and not f.endswith('__init__.py'):
        importlib.import_module("." + basename(f)[:-3], "command")
