import os, importlib

from maya import cmds, mel

from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, vis_rig
from rigbdp import utils as rig_utils

importlib.reload(sdk_utils)
importlib.reload(corrective)
importlib.reload(post_scripts)
importlib.reload(vis_rig)
importlib.reload(rig_utils)

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
                #  MnM_rig_path_2022,
                 SHAPES_mel_paths,
                 build_output_path,
                 sdk_data_path=None,
                 wrap_eyebrows=True):
        self.char_name = char_name
        self.MnM_rig_path = MnM_rig_path
        # self.MnM_rig_path_2022 = MnM_rig_path_2022
        self.build_output_path = build_output_path
        if not type(SHAPES_mel_paths) == list: SHAPES_mel_paths = [SHAPES_mel_paths]
        self.SHAPES_mel_paths = SHAPES_mel_paths
        self.sdk_data_path = sdk_data_path

        # populate a list called self.corrective_meshes from the self.corrective_mel_paths
        self.__get_corrective_meshes_from_mel()

        
        # these paths have to be maya-ified even if you are on windows

        self.SHAPES_mel_paths = [p.replace('\\', '/' ) for p in self.SHAPES_mel_paths]
        self.build_output_path = self.build_output_path.replace('\\', '/' )
        self.wrap_eyebrows = wrap_eyebrows


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
        vis_rig.setup_rig_vis(channel_box = True,
                              hidden_in_outliner=False,
                              skin_jnt_vis=False, sculpt_jnt_vis=False)
        if self.wrap_eyebrows:
            rig_utils.wrap_eyebrows()

        # NOTE: placeholder until we figure out what to do with broken ffds
        self.__deactivate_broken_ffds()
        cmds.setAttr("preferences.showClothes", 1)
        rig_utils.clean_intermediate_nodes()
        cmds.file(save=True, type='mayaAscii')


    def import_correctives(self):
        # # 3. Clean up the scene for corrective import
        # corrective.pre_import_bs_cleanup(char_name=self.char_name)
        
        # 3. Clean up the scene for corrective import
        for mesh in self.corrective_meshes:
            corrective.pre_import_bs_cleanup_NEW(mesh_name=mesh)

        # 4. Import correctives
        for path in self.SHAPES_mel_paths:
            mel.eval(f'source "{path}";')

        # 4a. Turn on all model_fix blendshape targets for every blendShape in the scene
        blendshapes = cmds.ls(type='blendShape')
        for bs in blendshapes:
            mod_fix_tgt = f'{bs}.model_fix'
            if cmds.objExists(mod_fix_tgt):
                cmds.setAttr(mod_fix_tgt, 1)
                cmds.setAttr(mod_fix_tgt, edit=True, lock=True)
        cmds.file(save=True, type='mayaAscii')


    def import_sdk_data(self):
        # 5. Import and rebuild set driven key data
        sdk_utils.import_sdks(self.sdk_data_path)
        cmds.file(save=True, type='mayaAscii')


    def __import_rig_clean(self):
        # maya_version_year = cmds.about(version=True)

        # if '2022' in str(maya_version_year):
        #     self.build_output_path = f'{self.build_output_path}_maya2022'
        #     print('THE YEAR IS 2022')
        #     self.MnM_rig_path = self.MnM_rig_path_2022

        cmds.file(self.MnM_rig_path, i=True, namespace=":", preserveReferences=True)

        # Flatten namespaces (remove them)
        cmds.namespace(set=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for ns in namespaces:
            if ns not in ['UI', 'shared']:
                cmds.namespace(force=True, moveNamespace=(ns, ':'))
                cmds.namespace(removeNamespace=ns)

    def __deactivate_broken_ffds(self):
        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretch_ffd.envelope', 0)
        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretchGlobal_ffd.envelope', 0)
        
    def __get_corrective_meshes_from_mel(self):
        self.corrective_meshes=[]
        for name in self.SHAPES_mel_paths:
            _,tail = os.path.split(name)
            name, _ = os.path.splitext(tail)

            prefix = 'M_'
            suffix = 'Shapes_blendShape'
            # Check if the blendshape name contains the expected prefix and suffix
            if name.startswith(prefix) and name.endswith(suffix):
                # Strip the prefix and suffix to extract the mesh name
                mesh_name = name[len(prefix):-len(suffix)]
                self.corrective_meshes.append(mesh_name)
            else:
                continue

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
