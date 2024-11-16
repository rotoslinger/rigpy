# builtins
import importlib

# third party
from maya import mel
from maya import cmds

# custom
from rigbdp.import_export import file
importlib.reload(file)

import maya.mel as mel
import os

def source_and_run_mel(filepath, proc_name, *proc_args):
    """
    Args:
        filepath (str): The full file path to the MEL script.
        proc_name (str): The name of the procedure to call from the MEL script.
        *proc_args: The arguments to pass to the MEL procedure (if any).
        
    Returns:
        The result of the MEL procedure (if any) or None.
    """
    # Normalize the file path for cross-platform compatibility
    filepath = os.path.normpath(filepath)
    
    # Check if the file exists
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"MEL script not found: {filepath}")
    
    # Get the directory and script name (without extension)
    script_dir, script_file = os.path.split(filepath)
    script_name = os.path.splitext(script_file)[0]
    
    # Add the script directory to the MEL search path (if needed)
    mel.eval(f'addToRecentScriptTable("{script_dir}", "mel")')
    
    # Source the script
    mel.eval(f'source "{script_name}";')
    
    # Construct the MEL command to run the procedure with arguments
    mel_command = f'{proc_name}({" ".join(map(str, proc_args))});'
    
    # Run the procedure
    return mel.eval(mel_command)

# # Example usage
# try:
#     result = source_and_run_mel('/path/to/your/script/myMelScript.mel', 'SHAPES_getNamespace', 'myGeometry')
#     print(result)
# except FileNotFoundError as e:
#     print(e)


def import_correctives(filepath, proc_name, *proc_args):
    source_and_run_mel('/path/to/your/script/myMelScript.mel', 'SHAPES_getNamespace', 'myGeometry')
    from maya import cmds


def pre_import_bs_cleanup(char_name):
    # cleanly delete the old blendshape without deleting any Minimo nodes.
    '''
    ---background
    Maya automatically does garbage collection.

    When the blendshape is deleted using the ui the Minimo nodes for driving
    the blendshape weights are also deleted.

    This script will first delete connections, then delete the blendshape,
    then SHAPES can properly rebuild all of the connections 
    '''
    node = f"M_{char_name}_base_body_geoShapes_blendShape"
    compound_attr = 'weight'
    # Get the full path of the compound attribute (node + compound attribute)
    full_attr = f'{node}.weight'
    # Get all indices for the compound array
    bs_weight_names = cmds.listAttr(full_attr, multi=True)
    connections = []
    for name in bs_weight_names:
        full_attr = f'{node}.{name}'
        connections.append(cmds.listConnections(full_attr, plugs=True, source=True, destination=False)[0])
        print(connections)
    for idx, name in enumerate(bs_weight_names):
        print(f'{node}.{name}')
        print(connections[idx])
        cmds.disconnectAttr(connections[idx], f'{node}.{name}')
    cmds.delete(f"M_{char_name}_base_body_geoShapes_blendShape")


def pre_import_bs_cleanup_NEW(side=None, mesh_name='jsh_base_cloth_top_fabric_mesh'):
    # cleanly delete the old blendshape without deleting any Minimo nodes.
    '''
    ---background
    Maya automatically does garbage collection.

    When the blendshape is deleted using the ui the Minimo nodes for driving
    the blendshape weights are also deleted.

    This script will first delete connections, then delete the blendshape,
    then SHAPES can properly rebuild all of the connections
    
    '''

    suffix = mesh_name.split('_')[-1]
    mesh_name = mesh_name.replace(suffix,'')
    if not side:side='M'
    blendshape = f"{side}_{mesh_name}geoShapes_blendShape"
    if not cmds.objExists(blendshape):return
    print('BLENDSHAPE NAME : ', blendshape)
    # Get the weight attr
    full_attr = f'{blendshape}.weight'
    # Get all indices for the compound array
    bs_weight_names = cmds.listAttr(full_attr, multi=True)
    connections = []
    for name in bs_weight_names:
        full_attr = f'{blendshape}.{name}'
        connections.append(cmds.listConnections(full_attr, plugs=True, source=True, destination=False)[0])
        print(connections)
    for idx, name in enumerate(bs_weight_names):
        print(f'{blendshape}.{name}')
        print(connections[idx])
        cmds.disconnectAttr(connections[idx], f'{blendshape}.{name}')
    cmds.delete(blendshape)


def post_import(char_name):
    # if a second ShapeOrig was created, delete it, the node network will not be interrupted 
    if cmds.objExists(f"{char_name}_base_body_geoShapeOrig1"):
        cmds.delete(f"{char_name}_base_body_geoShapeOrig1")
        print("deleted")

def select_blendshape(char_name):
    # important to keep an eye on the blendshape in node editor
    # use this script to easily select it
    cmds.select(f"M_{char_name}_base_body_geoShapes_blendShape")

def get_blendshape_connections(blendshape):
    full_attr = f'{blendshape}.weight'
    # Get all indices for the compound array
    bs_weight_names = cmds.listAttr(full_attr, multi=True)
    connections = []
    for name in bs_weight_names:
        full_attr = f'{blendshape}.{name}'
        connections.append(cmds.listConnections(full_attr, plugs=True, source=True, destination=False)[0])
        print(connections)
    for idx, name in enumerate(bs_weight_names):
        print(f'{blendshape}.{name}')
        print(connections[idx])
        # cmds.disconnectAttr(connections[idx], f'{blendshape}.{name}')


def blendshape_connection_export(blendshape):

    # get the in and out connections
    get_blendshape_connections(blendshape)


def SHAPES_export():
    '''
    shpUI_customExportPathCheck
    
    '''