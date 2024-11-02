# rigbdp/builders/__init__.py
import importlib
from maya import cmds, mel

# Import modules and create aliases if necessary
from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils
from rigbdp.import_export import corrective
from rigbdp.build import post_scripts
from rigbdp.build import rigbuild_mini
from rigbdp.builders import bdp_rigMods as rig_mods
# Step 1: Create a list of modules for easy reloading
MODULES = [
    rig_utils,
    sdk_utils,
    corrective,
    post_scripts,
    rigbuild_mini,
    rig_mods,
]

# Step 2: Update globals to include the modules
globals().update({module.__name__: module for module in MODULES})
def reload_all():
    """Reload all modules in the MODULES list."""
    for mod in MODULES:
        importlib.reload(mod)
        print(f'reloaded {mod}')

# Optionally expose all the modules
__all__ = [mod.__name__ for mod in MODULES] + ['reload_all']

reload_all()
print('modules have been refreshed')



# # DYNAMIC GEN

# # Dynamically generated code block from module
# #

# '''
# The three lines of imports below will dynamically get all shared imports.

# It is important to know these imports can be found here:
# rigpy/libs/rigbdp/builders/__init__.py

# This allows us to keep all common imports in a single file, and not have
# to hand edit a large amount of files every time we want to add something new.
# '''
# import rigbdp.builders
# importlib.reload(rigbdp.builders)
# from rigbdp.builders import *
# # END DYNAMIC GEN