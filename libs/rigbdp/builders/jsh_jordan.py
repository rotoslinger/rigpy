#######################################
# DYNAMIC GEN
import importlib, os
from maya import cmds, mel

from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini
from rigbdp.builders import bdp_rig_mods
MODULES = [rig_utils, sdk_utils, corrective, post_scripts, rigbuild_mini, bdp_rig_mods]
for mod in MODULES:
    importlib.reload(mod)
# END DYNAMIC GEN

##################################### Helpful export snippets ######################################
# # Set Driven Key Export
# # if you need to export all set driven keys in the entire scene, run this
# sdk_utils.export_sdks(filepath=r'C:\Users\harri\Documents\BDP\cha_input\jsh\sdk_data.json')
# # SHAPES load mesh error
# # if shapes complains and won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this
####################################################################################################

sep = os.path.sep

char_name = 'jsh'
output_format = ''
new_version = 11
char_dir= rf'C:\Users\harri\Documents\BDP\build_demo'
SHAPES_dir_name = 'SHAPES'
SHAPES_mel_filenames = ['M_jsh_base_body_geoShapes_blendShape.mel',
                        'M_jsh_base_cloth_top_fabric_geoShapes_blendShape']
sdk_filename = 'sdk_data.json'
output_dir_name = 'output'
MnM_build_file = 'jsh_RIG_200_v008_MnM.ma'

### class args to be dynamically created:
# At any point you can hardcode any of these and plug them directly into the class
MnM_rig_path=None
SHAPES_mel_paths=None
build_output_path=None
sdk_data_path=None

### Dynamically build paths
char_dir = rf'{char_dir}{sep}{char_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\build_demo\}{jsh}{\}
output_filename=f'{char_name}_RIG_200_v{new_version:03}.ma' # for example --- {jsh}_RIG_200_v0{11}.ma
output_dir = rf'{char_dir}{output_dir_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\cha_input\jsh\}{output}{\}
SHAPES_dir = rf'{char_dir}{SHAPES_dir_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\cha_input\jsh\}{SHAPES}{\}
SHAPES_mel_paths=[]
for mel_file in SHAPES_mel_filenames:
    SHAPES_mel_paths.append(f'{SHAPES_dir}{mel_file}') 
# for example --- ['C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES\}{M_jsh_base_body_geoShapes_blendShape.mel}',
#                  'C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES\}{M_jsh_base_cloth_top_fabric_geoShapes_blendShape.mel}']

### Final filepath args: 
MnM_rig_path = rf'{char_dir}{MnM_build_file}'
SHAPES_mel_paths = SHAPES_mel_paths
build_output_path = f'{output_dir}{output_filename}' # for example --- '{C:\Users\harri\Documents\BDP\cha_input\jsh\output\}{jsh_RIG_200_v011.ma}'
sdk_data_path = rf'{char_dir}{sdk_filename}'

# ### Debug filepaths:
# print('char_name = ', char_name)
# print('MnM_rig_path = ', MnM_rig_path)
# print('SHAPES_mel_paths = ', SHAPES_mel_paths)
# print('build_output_path = ', build_output_path)
# print('sdk_data_path = ', sdk_data_path)

### Initialize the RigMerge instance with file paths
rig_merge = rigbuild_mini.RigMerge(
    char_name=char_name,
    MnM_rig_path=MnM_rig_path,
    SHAPES_mel_paths=SHAPES_mel_paths,
    build_output_path=build_output_path,
    sdk_data_path=sdk_data_path,
)
# PRE. custom scripts can go here
# example.pre_function()

# 1. Create a new scene, Import the MnM rig build
rig_merge.init_mnm_rig()

#################################
# 1a. custom scripts
bdp_rig_mods.BDP_outSkel_rigMod()
#################################

# 2. Import correctives
rig_merge.import_correctives()

#################################
# 2a. custom scripts
bdp_rig_mods.connect_common_blendshapes(char_name='jsh')
#################################

# 3.  Import and rebuild set driven key data
rig_merge.import_sdk_data()

#################################
# 3a. custom scripts can go here
# example.function()
#################################















# path_to_SHAPES_data = r'C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES'
# corrective_mel_paths=[fr'{path_to_SHAPES_data}\M_jsh_base_body_geoShapes_blendShape.mel',
#                       fr'{path_to_SHAPES_data}\M_jsh_base_cloth_top_fabric_geoShapes_blendShape.mel'
#                       ]

# rig_merge = rigbuild_mini.RigMerge(
#     char_name=char_name,
#     MnM_rig_path=MnM_rig_path_2024,
#     # MnM_rig_path_2022=MnM_rig_path_2022,
#     SHAPES_mel_paths=SHAPES_mel_files,
#     build_output_path=r'C:\Users\harri\Documents\BDP\build_demo\jsh\output\jsh_RIG_200_v011.ma',
#     sdk_data_path=r'C:\Users\harri\Documents\BDP\cha_input\jsh\sdk_data.json',

# )
