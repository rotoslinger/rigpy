import os, importlib, glob

from maya import cmds, mel
from rigbdp.builders.rigmods import rig_mods
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, vis_rig
from rigbdp import utils as rig_utils

importlib.reload(rig_mods)
importlib.reload(sdk_utils)
importlib.reload(corrective)
importlib.reload(post_scripts)
importlib.reload(vis_rig)
importlib.reload(rig_utils)

r'''
### Step 1. Character Directory Structure ####
Before starting the build process, I would recommend creating a character directory structure.
You can use the following code to do this automatically:

from rigbdp.build import build_pathing
char_name = 'jsh'
dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
create_char_structure(char_name=char_name, dir_to_char=dir_to_char )

This will create the following structure:
# ├── jsh
# │   ├──── SHAPES # --- all SHAPES export files must be saved here
# │   ├──── input # --- put the minimo build & sdk_data.json here
# │   └──── output # --- find your rig here after you build
----------------------------------------------------------------------------------------------------

### Step 2. Exporting & Build prep ####
In order to get a successful rig build there are a few prerequisites:

1. You must have SHAPES export files.
   - First export your sculpts using SHAPES.
   - All files that are exported must remain in the same directory.
   - You will need to provide a path to the mel file
2. Export your set driven keys using sdk_utils
    - this is optional, you only need this if you have custom sdks
    - I would recommend using the filename 'sdk_data.json', by doing this you can automatically
      retrieve the sdk data file later.
    - to export, see the code below

# --- Export sdk data
from rigbdp.import_export import sdk_utils
sdk_utils.export_sdks(filepath=r'C:\Users\harri\Documents\BDP\cha_input\jsh\sdk_data.json')

----------------------------------------------------------------------------------------------------

### Step 3. The Build ####

In order to build you need to provide the following arguments:

1. char_name - The name of the char
2. MnM_rig_path - The path to the latest minimo build.
3. SHAPES_mel_paths - The path to the SHAPES export data.
4. build_output_path - The path to save the new file.
5. sdk_data_path - The path to the sdk data.
6. wrap_eyebrows - Whether or not to wrap the eyebrows to the body.

Generating the args.

It is possible to automatically generate these args if you have set up your character directory
structure as described in Step 1. You will to run the mel script below.

# --- Generate args script
char_name = 'jsh'
dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
new_version = 11
file_paths = build_pathing.find_files(char_name=char_name, dir_to_char=dir_to_char, new_version=new_version)

# --- Output
########################################### BUILDER PATHS ##########################################
# Copy these paths to your builder
char_name = 'jsh'
MnM_rig_path = r'C:\Users\harri\Documents\BDP\cha\jsh\input\jsh_RIG_200_v008_MnM.ma'
SHAPES_mel_paths = [r'C:\Users\harri\Documents\BDP\cha\jsh\SHAPES\M_jsh_base_body_geoShapes_blendShape.mel',
                  r'C:\Users\harri\Documents\BDP\cha\jsh\SHAPES\M_jsh_base_cloth_top_fabric_geoShapes_blendShape.mel']
build_output_path = r'C:\Users\harri\Documents\BDP\cha\jsh\output\jsh_RIG_200_v011.ma'
sdk_data_path = r'C:\Users\harri\Documents\BDP\cha\jsh\input\sdk_data.json'
####################################################################################################
'''
# To execute mel code one line at a time:
def execute_mel_file_with_error_handling(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            try:
                mel.eval(line.strip())
            except RuntimeError as e:
                print(f"Error executing command '{line.strip()}': {e}")


class RigMerge:
    def __init__(self,
                 char_name,
                 input_rig_path,
                 SHAPES_mel_paths,
                 build_output_path,
                 sdk_data_path=None,
                 wrap_eyebrows=True,
                 nowake_build=False,
                 bs_conn_paths=None):
        self.char_name = char_name
        self.input_rig_path = input_rig_path
        self.build_output_path = build_output_path
        if not type(SHAPES_mel_paths) == list: SHAPES_mel_paths = [SHAPES_mel_paths]
        self.SHAPES_mel_paths = SHAPES_mel_paths
        self.sdk_data_path = sdk_data_path
        self.bs_conn_paths = bs_conn_paths

        self.__input_file_check()

        # populate a list called self.corrective_meshes from the self.corrective_mel_paths
        self.__get_corrective_meshes_from_mel()

        # these paths have to be maya-ified even if you are on windows
        self.SHAPES_mel_paths = [p.replace('\\', '/' ) for p in self.SHAPES_mel_paths]
        self.build_output_path = self.build_output_path.replace('\\', '/' )
        self.wrap_eyebrows = wrap_eyebrows
        self.nowake_build = nowake_build


    def add_vendor_rig(self):
        self.__input_file_check()

        # 1. Create a new scene
        cmds.file(new=True, force=True)

        # 2. Import the MnM rig build
        self.__import_rig_clean()

        # Finally, 
        # If no build output, leave saving up to user discretion
        if not self.build_output_path: return

        # If build output path given, save file
        cmds.file(rename=self.build_output_path)

        # NOTE: Turn off the ffds for correctives import
        self.__minimo_add_vendor_overs()

        cmds.file(save=True, type='mayaAscii')


    def import_correctives(self, bs_cleanup=True):
        # # 3. Clean up the scene for corrective import
        # corrective.pre_import_bs_cleanup(char_name=self.char_name)
        
        # 3. Clean up the scene for corrective import
        for blendshape in self.corrective_blendshapes:
            if bs_cleanup:
                corrective.SHAPES_blendshape_cleanup(blendshape)

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
        rig_utils.clean_intermediate_nodes()

        if self.bs_conn_paths:
            for bs_path in self.bs_conn_paths:
                corrective.reconnect_blendshapes(bs_path)

        # NOTE: Turn on the ffds after correctives import
        self.__minimo_post_corrective_overs()


    def import_sdk_data(self):
        # 5. Import and rebuild set driven key data
        sdk_utils.import_sdks(self.sdk_data_path)
        cmds.file(save=True, type='mayaAscii')


    def __import_rig_clean(self):
        cmds.file(self.input_rig_path, i=True, namespace=":", preserveReferences=True)

        # Flatten namespaces (remove them)
        cmds.namespace(set=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for ns in namespaces:
            if ns not in ['UI', 'shared']:
                cmds.namespace(force=True, moveNamespace=(ns, ':'))
                cmds.namespace(removeNamespace=ns)

    def __minimo_add_vendor_overs(self):
        if self.nowake_build:return
        vis_rig.setup_rig_vis(channel_box = True,
                              hidden_in_outliner=False,
                              skin_jnt_vis=False, sculpt_jnt_vis=False)
        if self.wrap_eyebrows:
            rig_utils.wrap_eyebrows()

        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretch_ffd.envelope', 0)
        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretchGlobal_ffd.envelope', 0)
        if cmds.objExists("preferences.showClothes"):
            cmds.setAttr("preferences.showClothes", 1)


    def __minimo_post_corrective_overs(self):
        if self.nowake_build:return

        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretch_ffd.envelope', 1)
        cmds.setAttr(f'{self.char_name}_base_body_geo_headSquashAndStretchGlobal_ffd.envelope', 1)
        if cmds.objExists("preferences.showClothes"):
            cmds.setAttr("preferences.showClothes", 1)


    def __nowake_post_corrective_overs(self):
        if self.bs_conn_paths:
            ''
    
    def rebuild_clothing_sculpts():
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


    def __input_file_check(self):
        if not self.input_rig_path:
            input_rig_path = os.path.split(self.build_output_path)[0].replace('output', 'input')
            cmds.error(f'''\n{input_rig_path} does not contain any .ma or .mb files.\nPlease add a rig vendor rig before trying to build.''')

    def __get_corrective_meshes_from_mel(self):
        self.corrective_blendshapes=[]
        for name in self.SHAPES_mel_paths:
            _,tail = os.path.split(name)
            name, _ = os.path.splitext(tail)
            print('Found SHAPES data for: ', name)
            self.corrective_blendshapes.append(name)

            # prefix = 'M_'
            # suffix = 'Shapes_blendShape'
            # # Check if the blendshape name contains the expected prefix and suffix
            # if name.startswith(prefix) and name.endswith(suffix):
            #     # Strip the prefix and suffix to extract the mesh name
            #     mesh_name = name[len(prefix):-len(suffix)]
            #     self.corrective_meshes.append(mesh_name)
            # else:
            #     continue

# ########################################### Example Usage #########################################

# #########################################################
# # Unique char args
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'jsh'
# version = 13
# #########################################################

# # If you don't have the directories, this will create them.
# created_dirs = build_pathing.create_char_structure(char_name=char_name,
#                                                    dir_to_char=dir_to_char)

# # FIND BUILD FILES DYNAMICALLY - To bake out the directories see example snippets at the bottom
# found_dirs = build_pathing.return_found_files(char_name=char_name,
#                                               dir_to_char=dir_to_char,
#                                               new_version_number=version)
# char_name = found_dirs['char_name']
# input_rig_path = found_dirs['input_rig_path']
# SHAPES_mel_paths = found_dirs['SHAPES_mel_paths']
# build_output_path = found_dirs['build_output_path']
# sdk_data_path = found_dirs['sdk_data_path']


# # Initialize your builder 
# rig_merge = rigbuild_mini.RigMerge(
#     char_name=char_name, 
#     input_rig_path=input_rig_path,
#     SHAPES_mel_paths=SHAPES_mel_paths,
#     build_output_path=build_output_path,
#     sdk_data_path=sdk_data_path,
#     wrap_eyebrows=True,
# )


# #--------------------------------------------------------

# # PRE. custom scripts can go here
# # example.pre_function()

# #--------------------------------------------------------

# # 1. BUILDER - Create a new scene, Import the MnM rig build
# rig_merge.add_vendor_rig()


# # 1a. custom scripts
# rig_mods.BDP_outSkel_rigMod()
# # bdp_rig_mods.create_lips_sculpt_jnts()

# #--------------------------------------------------------

# # 2. BUILDER - Import correctives
# rig_merge.import_correctives()
# geo_name='jsh_base_cloth_top_fabric_low_meshShape'
# cmds.blendShape(geo_name, name = 'M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
#                 before=True)
# cmds.blendShape('M_jsh_base_cloth_top_fabric_low_geoShapes_blendShape',
#                 edit=True,
#                 ip=r'C:\Users\harri\Documents\BDP\cha\jsh\maya_shapes\shirt.shp')

# # 2a. custom scripts
# rig_mods.connect_common_blendshapes(char_name='jsh')

# #--------------------------------------------------------

# # 3. BUILDER - Import and rebuild set driven key data
# rig_merge.import_sdk_data()


# # 3a. custom scripts can go here
# # example.function()

# #--------------------------------------------------------

# # Post build save
# cmds.file(save=True, type='mayaAscii')

# # #################################### Helpful export snippets ###################################

# # # Create character directory structure
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'dmytryk'
# created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)

# # # ----------------------------------------------------------------------------------------------

# # # Set Driven Key Export
# # # --- Export all set driven keys in the scene
# sdk_data_path = r'C:\Users\harri\Documents\BDP\cha\dmytryk\input\sdk_data.json'
# sdk_utils.export_sdks(filepath=sdk_data_path)

# # # ----------------------------------------------------------------------------------------------

# # # SHAPES load mesh error
# # # --- if shapes won't load a mesh, run this
# rig_utils.clean_intermediate_nodes() # - if shapes complains and won't load a mesh, run this

# # # ----------------------------------------------------------------------------------------------

# # # IF YOU WANT TO BAKE OUT BUILD FILES
# # # --- Automatically find files used in the build
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# char_name = 'dmytryk'
# found_dirs = build_pathing.find_files(char_name=char_name,
#                                       dir_to_char=dir_to_char, 
#                                       new_version_number=8)
# # # When the output prints, paste it in BUILDER PATHS section

# # ################################################################################################
