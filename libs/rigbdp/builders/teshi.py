#######################################
# DYNAMIC GEN
import importlib
#from maya import cmds, mel

from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini, build_pathing
from rigbdp.builders.rigmods import rig_mods

MODULES = [rig_utils, sdk_utils, corrective, post_scripts,
           rigbuild_mini, build_pathing, rig_mods]
for mod in MODULES:
    importlib.reload(mod)
# END DYNAMIC GEN
#######################################

#########################################################
# Unique char args
dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
char_name = 'teshi'
version = 14
#########################################################

# If you don't have the directories, this will create them.
created_dirs = build_pathing.create_char_structure(char_name=char_name,
                                                   dir_to_char=dir_to_char)

# FIND BUILD FILES DYNAMICALLY - To bake out the directories see example snippets at the bottom
found_dirs = build_pathing.return_found_files(char_name=char_name,
                                              dir_to_char=dir_to_char,
                                              new_version_number=version)
char_name = found_dirs['char_name']
input_rig_path = found_dirs['input_rig_path']
SHAPES_mel_paths = found_dirs['SHAPES_mel_paths']
build_output_path = found_dirs['build_output_path']
sdk_data_path = found_dirs['sdk_data_path']


# Initialize your builder 
rig_merge = rigbuild_mini.RigMerge(
    char_name=char_name, 
    input_rig_path=input_rig_path,
    SHAPES_mel_paths=SHAPES_mel_paths,
    build_output_path=build_output_path,
    sdk_data_path=sdk_data_path,
    wrap_eyebrows=True,
)


# 1. Create a new scene, Import the MnM rig build
rig_merge.add_vendor_rig()

# --- pre corrective import scripts
rig_mods.BDP_outSkel_rigMod()

# 2. Import correctives
rig_merge.import_correctives()

# --- pre sdk scripts

# 3.  Import and rebuild set driven key data teshi doesn't have any custom sdks
# rig_merge.import_sdk_data()



# # #################################### Helpful export snippets ###################################

# # # Create character directory structure
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'teshi'
# created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)

# # # ----------------------------------------------------------------------------------------------

# # # Set Driven Key Export
# # # --- Export all set driven keys in the scene
# sdk_data_path = r'C:\Users\harri\Documents\BDP\cha\teshi\input\sdk_data.json'
# sdk_utils.export_sdks(filepath=sdk_data_path)

# # # ----------------------------------------------------------------------------------------------

# # # SHAPES load mesh error
# # # --- if shapes won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this

# # # ----------------------------------------------------------------------------------------------

# # # IF YOU WANT TO BAKE OUT BUILD FILES
# # # --- Automatically find files used in the build
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'teshi'
# found_dirs = build_pathing.find_files(char_name=char_name,
#                                       dir_to_char=dir_to_char, 
#                                       new_version_number=8)
# # # When the output prints, paste it in BUILDER PATHS section

# # ################################################################################################
