import importlib

from maya import cmds, mel

from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini

importlib.reload(sdk_utils)
importlib.reload(corrective)
importlib.reload(post_scripts)
importlib.reload(rigbuild_mini)

# sdk export for teshi (make sure to comment out...)
# sdk_utils.export_sdks(filepath=r'C:\Users\harri\Documents\BDP\cha_input\teshi\sdk_data.json')

# Initialize the RigMerger instance with file paths
rig_merge = rigbuild_mini.RigMerge(
    char_name='teshi',
    MnM_rig_path=r'C:\Users\harri\Documents\BDP\cha_input\teshi\teshi_RIG_200_v009_MnM.ma',
    corrective_mel_path=r'C:\Users\harri\Documents\BDP\cha_input\teshi\SHAPES\M_teshi_base_body_geoShapes_blendShape.mel',
    sdk_data_path=r'C:\Users\harri\Documents\BDP\cha_input\teshi\sdk_data.json',
    build_output_path=r'C:\Users\harri\Documents\BDP\cha_output\teshi_RIG_200_v010.ma'
)

# 1. Create a new scene, Import the MnM rig build
rig_merge.init_mnm_rig()

# --- pre corrective import scripts
post_scripts.create_upchest_sculpt_jnt()

# 2. Import correctives
rig_merge.import_correctives()

# --- pre sdk scripts

# 3.  Import and rebuild set driven key data teshi doesn't have any custom sdks
rig_merge.import_sdk_data()
