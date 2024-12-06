#######################################
# DYNAMIC GEN
import importlib
from maya import cmds, mel

from rigbdp.build import build_utils as rig_utils
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
version = 19
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
char_dir = found_dirs['char_dir']
extra_models = found_dirs['extra_models']

# Initialize your builder 
rig_merge = rigbuild_mini.RigMerge(
    char_name=char_name,
    input_rig_path=input_rig_path,
    SHAPES_mel_paths=SHAPES_mel_paths,
    build_output_path=build_output_path,
    sdk_data_path=sdk_data_path,
    wrap_eyebrows=True,
    extra_geo_importpath=extra_models,
    char_dir=char_dir,

)

# 1. Create a new scene, Import the MnM rig build
rig_merge.add_vendor_rig()

rig_merge.smart_skin_copy('teshi_base_cloth_top_fabric_mesh',
                          'teshi_base_cloth_top_fabric_low_mesh',
                          'teshi_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster')
cmds.connectAttr('preferences.showClothes','teshi_base_cloth_low_grp.v')

# --- pre corrective import scripts

# 2. Import correctives
rig_merge.import_correctives()

geo_name='teshi_base_cloth_top_fabric_low_meshShape'
cmds.blendShape(geo_name, name = 'M_teshi_base_cloth_top_fabric_low_geoShapes_blendShape',
                before=True)


# --- pre sdk scripts

# 3.  Import and rebuild set driven key data teshi doesn't have any custom sdks
# rig_merge.import_sdk_data()

cmds.delete(['teshi_base_cloth_top_fabric_mesh'])

# Post build save
cmds.file(save=True, type='mayaAscii')


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
