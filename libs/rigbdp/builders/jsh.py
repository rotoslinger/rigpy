### DYNAMIC GEN
import importlib, os
from maya import cmds, mel


from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini, build_pathing
from rigbdp.builders.rigmods import rig_mods

MODULES = [rig_utils, sdk_utils, corrective, post_scripts,
           rigbuild_mini, build_pathing, rig_mods]
for mod in MODULES:
    importlib.reload(mod)
### DYNAMIC GEN

#################################### Helpful export snippets ######################################
# Create character directory structure
dir_to_char = r'C:\Users\harri\Documents\BDP\build'
char_name = 'jsh'
created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)   # char_name, dir_to_char, new_version, input_extension='.ma',
# ---------------------------------------------------------------------------------------------------
# Set Driven Key Export
# --- Export all set driven keys in the scene
# sdk_data_path = r'C:\Users\harri\Documents\BDP\build\jsh\input\sdk_data.json'
# sdk_utils.export_sdks(filepath=sdk_data_path)
# ---------------------------------------------------------------------------------------------------
# SHAPES load mesh error
# --- if shapes won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this
# ---------------------------------------------------------------------------------------------------
# Find build files
# --- Automatically find files used in the build
dir_to_char = r'C:\Users\harri\Documents\BDP\build'
char_name = 'jsh'
found_dirs = build_pathing.find_files(char_name=char_name, dir_to_char=dir_to_char, new_version_number=13, input_extension='.ma')   # char_name, dir_to_char, new_version, input_extension='.ma',
# When the output prints, paste it in BUILDER PATHS section
###################################################################################################

########################################### BUILDER PATHS ##########################################
# Copy these paths to your builder
char_name = 'jsh'
input_rig_path = r'C:\Users\harri\Documents\BDP\build\jsh\input\jsh_RIG_200_v010MnM.ma'
SHAPES_mel_paths = [r'C:\Users\harri\Documents\BDP\build\jsh\SHAPES\M_jsh_base_body_geoShapes_blendShape.mel']
build_output_path = r'C:\Users\harri\Documents\BDP\build\jsh\output\jsh_RIG_200_v026.ma'
sdk_data_path = r'C:\Users\harri\Documents\BDP\build\jsh\input\sdk_data.json'
####################################################################################################


### Initialize the RigMerge instance with file paths
rig_merge = rigbuild_mini.RigMerge(
    char_name=char_name,
    input_rig_path=input_rig_path,
    SHAPES_mel_paths=SHAPES_mel_paths,
    build_output_path=build_output_path,
    sdk_data_path=sdk_data_path,
    wrap_eyebrows=True,
    

)

#--------------------------------------------------------

# PRE. custom scripts can go here
# example.pre_function()

#--------------------------------------------------------

# 1. BUILDER - Create a new scene, Import the MnM rig build
rig_merge.add_vendor_rig()


# 1a. custom scripts
rig_mods.BDP_outSkel_rigMod()
# bdp_rig_mods.create_lips_sculpt_jnts()

#--------------------------------------------------------

# 2. BUILDER - Import correctives
rig_merge.import_correctives()
geo_name='jsh_base_cloth_top_fabric_low_meshShape'
cmds.blendShape(geo_name, name = 'M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
                before=True)
cmds.blendShape('M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
                edit=True,
                ip=r'C:\Users\harri\Documents\BDP\build\jsh\maya_shapes\shirt.shp')

# 2a. custom scripts
rig_mods.connect_common_blendshapes(char_name='jsh')

#--------------------------------------------------------

# 3. BUILDER - Import and rebuild set driven key data
rig_merge.import_sdk_data()


# 3a. custom scripts can go here
# example.function()

#--------------------------------------------------------

# Post build save
cmds.file(save=True, type='mayaAscii')
