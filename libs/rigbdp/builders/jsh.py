### DYNAMIC GEN
import importlib, os
from maya import cmds, mel


from rigbdp.build import build_utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini, build_pathing
from rigbdp.builders.rigmods import rig_mods

MODULES = [rig_utils, sdk_utils, corrective, post_scripts,
           rigbuild_mini, build_pathing, rig_mods]
for mod in MODULES:
    importlib.reload(mod)
### DYNAMIC GEN

#########################################################
# Unique char args
dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
char_name = 'jsh'
version = 15
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


#--------------------------------------------------------

# PRE. custom scripts can go here
# example.pre_function()

#--------------------------------------------------------

# 1. BUILDER - Create a new scene, Import the MnM rig build
rig_merge.add_vendor_rig()
rig_merge.smart_skin_copy('jsh_base_cloth_top_fabric_mesh',
                          'jsh_base_cloth_top_fabric_low_mesh',
                          'jsh_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster')
rig_merge.smart_skin_copy('jsh_base_cloth_pants_fabric_mesh',
                          'jsh_base_cloth_pants_fabric_low_mesh',
                          'jsh_base_cloth_pants_fabric_mesh_bodyMechanics_skinCluster')
cmds.connectAttr('preferences.showClothes','jsh_base_cloth_low_grp.v')


# 1a. custom scripts

#--------------------------------------------------------

# 2. BUILDER - Import correctives
rig_merge.import_correctives()


# CUSTOM BLENDSHAPE CREATION because the body blendshape is driving all of the shirt blendshapes
# we don't have to do a SHAPES build for it. This should become the standard for all clothing 
# sculpts:
geo_name='jsh_base_cloth_top_fabric_low_meshShape'
cmds.blendShape(geo_name, name = 'M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
                before=True)
cmds.blendShape('M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
                edit=True,
                ip=r'C:\Users\harri\Documents\BDP\cha\jsh\maya_shapes\shirt.shp')

# 2a. custom scripts
rig_mods.connect_common_blendshapes(char_name='jsh')

#--------------------------------------------------------

# 3. BUILDER - Import and rebuild set driven key data
rig_merge.import_sdk_data()


# 3a. custom scripts can go here
# example.function()

#--------------------------------------------------------

cmds.delete(['jsh_base_cloth_top_fabric_mesh', 'jsh_base_cloth_pants_fabric_mesh'])

# Post build save
cmds.file(save=True, type='mayaAscii')




# # #################################### Helpful export snippets ###################################

# # # Create character directory structure
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'jsh'
# created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)

# # # ----------------------------------------------------------------------------------------------

# # # Set Driven Key Export
# # # --- Export all set driven keys in the scene
# sdk_data_path = r'C:\Users\harri\Documents\BDP\cha\jsh\input\sdk_data.json'
# sdk_utils.export_sdks(filepath=sdk_data_path)

# # # ----------------------------------------------------------------------------------------------

# # # SHAPES load mesh error
# # # --- if shapes won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this

# # # ----------------------------------------------------------------------------------------------

# # # IF YOU WANT TO BAKE OUT BUILD FILES
# # # --- Automatically find files used in the build
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'jsh'
# found_dirs = build_pathing.find_files(char_name=char_name,
#                                       dir_to_char=dir_to_char, 
#                                       new_version_number=8)
# # # When the output prints, paste it in BUILDER PATHS section

# # ################################################################################################
# from importlib import reload
# from rigbdp import utils
# from rigbdp.build import locking
# reload(utils)
# reload(locking)
# locking.set_history_visibility(1)

# export_path = r'C:\Users\harri\Documents\BDP\build_demo\jsh'
# utils.smart_copy_skinweights(source_mesh='jsh_base_cloth_top_fabric_mesh',
#                              target_mesh='jsh_base_cloth_top_fabric_low_mesh',
#                              skin_clusters=['jsh_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster'],
#                              filepath=export_path)
# utils.smart_copy_skinweights(source_mesh='jsh_base_cloth_pants_fabric_mesh',
#                              target_mesh='jsh_base_cloth_pants_fabric_low_mesh',
#                              skin_clusters=['jsh_base_cloth_pants_fabric_mesh_bodyMechanics_skinCluster'],
#                              filepath=export_path)
