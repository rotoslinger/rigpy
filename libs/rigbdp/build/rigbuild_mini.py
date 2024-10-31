import importlib

from maya import cmds, mel

from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts

importlib.reload(sdk_utils)
importlib.reload(corrective)
importlib.reload(post_scripts)

r'''
In order to get a successful rig build there are a few prerequisites
1. Export your sculpts using shapes (you need to use the full path to this file as an arg)
2. Export your set driven keys using sdk_utils
    - this is optional, you only need this if you have custom sdks
    - this looks like:

#################################### Usage ####################################
import importlib
from rigbdp.import_export import sdk_utils
importlib.reload(sdk_utils) # the code is always being updated, reload just in case
sdk_utils.export_sdks(filepath=r'C:\Users\harri\Documents\BDP\cha_input\jsh\sdk_data.json')
###############################################################################
'''

class RigMerge:
    def __init__(self,
                 char_name,
                 MnM_rig_path,
                 corrective_mel_path,
                 sdk_data_path,
                 build_output_path=''):
        self.char_name = char_name
        self.MnM_rig_path = MnM_rig_path
        self.build_output_path = build_output_path
        self.corrective_mel_path = corrective_mel_path
        self.sdk_data_path = sdk_data_path
        
        # these paths have to be maya-ified even if you are on windows
        self.corrective_mel_path = self.corrective_mel_path.replace('\\', '/' )
        self.build_output_path = self.build_output_path.replace('\\', '/' )


    def merge(self):
        self.new_scene()
        self.import_mnm_rig()
        self.corrective_prep()
        self.import_correctives()
        self.import_sdk_data()


    def init_mnm_rig(self):
        # 1. Create a new scene
        cmds.file(new=True, force=True)

        # 2. Import the MnM rig build
        self.__import_rig_clean()

        # Finally, 
        # If no build output, leave saving up to user discretion
        if not self.build_output_path: return
        
        # If build output path given, save file
        cmds.file(rename=self.build_output_path)
        cmds.file(save=True, type='mayaAscii')


    def import_correctives(self):
        # 3. Clean up the scene for corrective import
        corrective.pre_import_bs_cleanup(char_name=self.char_name)

        # 4. Import correctives
        mel.eval(f'source "{self.corrective_mel_path}";')


    def import_sdk_data(self):
        # 5. Import and rebuild set driven key data
        sdk_utils.import_sdks(self.sdk_data_path)


    def __import_rig_clean(self):
        cmds.file(self.MnM_rig_path, i=True, namespace=":", preserveReferences=True)
        # Flatten namespaces (remove them)
        cmds.namespace(set=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for ns in namespaces:
            if ns not in ['UI', 'shared']:
                cmds.namespace(force=True, moveNamespace=(ns, ':'))
                cmds.namespace(removeNamespace=ns)


# #################################### Usage ####################################
# # Initialize the RigMerger instance with file paths
# rig_merge = RigMerge(
#     char_name='jsh',
#     MnM_rig_path=r'C:\Users\harri\Documents\BDP\cha_input\jsh\jsh_RIG_200_v008MnM.ma',
#     corrective_mel_path=r'C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES\M_jsh_base_body_geoShapes_blendShape.mel',
#     sdk_data_path=r'C:\Users\harri\Documents\BDP\cha_input\jsh\sdk_data.json',
#     build_output_path=r'C:\Users\harri\Documents\BDP\cha_output\jsh_RIG_200_v008.ma'
# )

# # 1. Create a new scene, Import the MnM rig build
# rig_merge.init_mnm_rig()

# # --- pre corrective import scripts
# post_scripts.create_upchest_sculpt_jnt()

# # 2. Import correctives
# rig_merge.import_correctives()

# # --- pre sdk scripts

# # 3.  Import and rebuild set driven key data
# rig_merge.import_sdk_data()
# ###############################################################################
