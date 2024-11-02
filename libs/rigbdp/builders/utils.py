import importlib
from maya import cmds, mel

from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini

# Step 1: Create a list of modules
TMP = [
    rig_utils,
    sdk_utils,
    corrective,
    post_scripts,
    rigbuild_mini,
]

# Step 2: Create __all__ for module names
__all__ = [module.__name__ for module in TMP]

# Step 3: Update globals to include the modules
globals().update({module.__name__: module for module in TMP})

def reload_all():
    for mod in TMP:
        importlib.reload(mod)

# Example usage (after importing this module):
# from your_module import * 
# You can now directly access functions and classes from utils, sdk_utils, corrective, post_scripts, rigbuild_mini
