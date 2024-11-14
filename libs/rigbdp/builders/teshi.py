#######################################
# DYNAMIC GEN
import importlib
#from maya import cmds, mel

from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini, build_pathing
from rigbdp.builders import bdp_rig_mods

MODULES = [rig_utils, sdk_utils, corrective, post_scripts,
           rigbuild_mini, build_pathing, bdp_rig_mods]
for mod in MODULES:
    importlib.reload(mod)
# END DYNAMIC GEN
#######################################

# #################################### Helpful export snippets ######################################
# # Create character directory structure
# # --- Character directories to assist in build automation
# char_name = 'teshi'
# dir_to_char = r'C:\Users\harri\Documents\BDP\build'
# created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)   # char_name, dir_to_char, new_version, MnM_extension='.ma',
# # ---------------------------------------------------------------------------------------------------
# # Set Driven Key Export
# # --- Export all set driven keys in the scene
# sdk_data_path = r'C:\Users\harri\Documents\BDP\build\teshi\input\sdk_data.json'
# sdk_utils.export_sdks(filepath=sdk_data_path)
# # ---------------------------------------------------------------------------------------------------
# # SHAPES load mesh error
# # --- if shapes won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this
# # ---------------------------------------------------------------------------------------------------
# # Find build files
# # --- Automatically find files used in the build
# dir_to_char = r'C:\Users\harri\Documents\BDP\build'
# char_name = 'teshi'
# created_dirs = build_pathing.find_files(char_name=char_name, dir_to_char=dir_to_char, new_version_number=13, MnM_extension='.ma')  # char_name, dir_to_char, new_version, MnM_extension='.ma',
# # When the output prints, paste it in BUILDER PATHS section
# # ###################################################################################################


########################################### BUILDER PATHS ##########################################
# Copy these paths to your builder
char_name = 'teshi'
MnM_rig_path = r'C:\Users\harri\Documents\BDP\build\teshi\input\teshi_RIG_200_v011.ma'
SHAPES_mel_paths = [r'C:\Users\harri\Documents\BDP\build\teshi\SHAPES\M_teshi_base_body_geoShapes_blendShape.mel']
build_output_path = r'C:\Users\harri\Documents\BDP\build\teshi\output\teshi_RIG_200_v013.ma'
sdk_data_path = r'C:\Users\harri\Documents\BDP\build\teshi\input\sdk_data.json'
####################################################################################################

rig_merge = rigbuild_mini.RigMerge(
    char_name=char_name,
    MnM_rig_path=MnM_rig_path,
    # MnM_rig_path_2022=MnM_rig_path_2022,
    SHAPES_mel_paths=SHAPES_mel_paths,
    build_output_path=build_output_path,
    # sdk_data_path=sdk_data_path,
)

# 1. Create a new scene, Import the MnM rig build
rig_merge.init_mnm_rig()

# --- pre corrective import scripts
bdp_rig_mods.BDP_outSkel_rigMod()

# 2. Import correctives
rig_merge.import_correctives()
# cmds.setAttr("preferences.showClothes", 1)
# doDetachSkin 3 { "1", "1", "1" };

# --- pre sdk scripts


# 3.  Import and rebuild set driven key data teshi doesn't have any custom sdks
# rig_merge.import_sdk_data()
