__custom_import__ = ['get_info']

for mod in __custom_import__:
    exec('from .' + mod + ' import *')