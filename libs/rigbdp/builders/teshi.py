#######################################
# DYNAMIC GEN
import importlib
from maya import cmds, mel

from rigbdp import utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini
from rigbdp.builders import bdp_rig_mods
MODULES = [rig_utils, sdk_utils, corrective, post_scripts, rigbuild_mini, bdp_rig_mods]
for mod in MODULES:
    importlib.reload(mod)
# END DYNAMIC GEN
#######################################


# Helpful export snippets (make sure to comment out...)
# rig_utils.clean_intermediate_nodes() # - if shapes complains about intermediate nodes, run this
# sdk_utils.export_sdks(filepath=r'C:\Users\harri\Documents\BDP\cha_input\teshi\sdk_data.json')

# Initialize the RigMerger instance with file paths
MnM_rig_path_2024 = r'C:\Users\harri\Documents\BDP\cha_input\teshi\teshi_RIG_200_v009_MnM.ma'
MnM_rig_path_2022 = r'C:\Users\harri\Documents\BDP\cha_input\teshi\teshi_RIG_200_v009_maya2022_MnM.ma'

rig_merge = rigbuild_mini.RigMerge(
    char_name='teshi',
    MnM_rig_path=MnM_rig_path_2024,
    MnM_rig_path_2022=MnM_rig_path_2022,
    corrective_mel_path=r'C:\Users\harri\Documents\BDP\cha_input\teshi\SHAPES\M_teshi_base_body_geoShapes_blendShape.mel',
    sdk_data_path=r'C:\Users\harri\Documents\BDP\cha_input\teshi\sdk_data.json',
    build_output_path=r'C:\Users\harri\Documents\BDP\cha_output\teshi\teshi_RIG_200_v010.ma',
    joint_vis_prefs=False,
)

# 1. Create a new scene, Import the MnM rig build
rig_merge.init_mnm_rig()

# --- pre corrective import scripts
bdp_rig_mods.BDP_outSkel_rigMod()

# 2. Import correctives
rig_merge.import_correctives()

# --- pre sdk scripts

# 3.  Import and rebuild set driven key data teshi doesn't have any custom sdks
# rig_merge.import_sdk_data()
