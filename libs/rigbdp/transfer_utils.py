from importlib import reload

from maya import cmds
from maya import mel

import rpdecorator

@rpdecorator.undo_chunk
def sel_all_rename(old_name='jsh', new_name='teshi'):
    # Transfers are a lot easier when all names of a character are replaced before export
    # It is less work:
    # you do this once before export, you avoid having to do it in 2 maya ascii, and 1 mel file. 
    everything = cmds.ls(shapes=False)
    renamed_nodes = set()  # To track renamed nodes and avoid reprocessing
    
    for node in everything:
        if old_name in node and node not in renamed_nodes:
            updated_name = node.replace(old_name, new_name)
            cmds.rename(node, updated_name, ignoreShape=True)
            renamed_nodes.add(updated_name)  # Add the new name to the set

@rpdecorator.undo_chunk
def duplicate_and_rename(selection=None):
    """
    meant for replacing all meshes in a SHAPES export with the neutral of another char
    """
    if not selection:
        selection = cmds.ls(selection=True)
    
    if len(selection) < 2:
        cmds.error("Please select the base mesh first, followed by one or more target meshes.")
        return
    
    # The first selected object is the base mesh, the rest are the target meshes
    base_mesh = selection[0]

    # Make sure the base mesh is parented to world, this may not be the case if it is imported
    #cmds.parent(base_mesh, w=True)

    target_meshes = selection[1:]
    
    for target in target_meshes:
        # Duplicate the base mesh
        duplicate = cmds.duplicate(base_mesh)[0]
        
        # Delete the target mesh
        cmds.delete(target)
        
        # Rename the duplicate to the name of the target mesh
        cmds.rename(duplicate, target)
        
# # To run, select the base mesh first, then the target meshes, and run:
# duplicate_and_rename()



def get_blendshape_shapes_attrs(blendshape_node, shapes_version=51100):
    """
    Adds SHAPES-related attributes to a blendShape node if they do not already exist,
    and returns a list of the full attribute names.

    :param str blendshape_node: Name of the blendShape node.
    :return: List of full attribute names on the blendShape node.
    :rtype: list
    """
    attributes = {
        'SHAPESVersion': {'type': 'long', 'value': shapes_version, 'lock': True},
        'SHAPESData': {'type': 'message'},
        'SHAPESDrivenSetGroup': {'type': 'message'},
        'SHAPESDrivenSet': {'type': 'message', 'multi': True, 'indexMatters': False},
        'SHAPESSolver': {'type': 'message', 'multi': True, 'indexMatters': False}
    }

    attr_list = []

    for attr_name, attr_info in attributes.items():
        full_attr = f'{blendshape_node}.{attr_name}'
        
        # Check if the attribute already exists
        if not cmds.attributeQuery(attr_name, node=blendshape_node, exists=True):
            # Create attribute based on the specified type and options
            cmds.addAttr(blendshape_node, longName=attr_name, attributeType=attr_info['type'], 
                         multi=attr_info.get('multi', False), 
                         indexMatters=attr_info.get('indexMatters', True))
            
            # If it's the SHAPESVersion, set its value and lock
            if attr_name == 'SHAPESVersion':
                cmds.setAttr(full_attr, attr_info['value'], lock=attr_info['lock'])
        
        # Append the full attribute name to the list
        attr_list.append(full_attr)
    
    return attr_list

def add_pi_shapes_attrs(pose_interpolator, joint, blendshape):
    '''
    Adds pose interpolator custom attributes needed by SHAPES to recognize a pose interpolator

    # an example of how to name a new pose_interpolator

    blendshape = 'M_jsh_base_body_geoShapes_blendShape'
    joint = 'M_neckHead00Out_jnt'

    pose_interpolator = f'{blendshape}_{joint}_PIShape'
    '''
    # create the blendshape data if it doesn't already exist
    get_blendshape_shapes_attrs(blendshape)

    # Define the object name for simplicity

    # Add attributes
    cmds.addAttr(pose_interpolator, attributeType='message', longName='SHAPES_wd')
    cmds.addAttr(pose_interpolator, attributeType='message', longName='solverGroupMessage')
    cmds.addAttr(pose_interpolator, longName='solverGroup', hidden=True, dataType='string')

    # Set the attribute value for solverGroup
    cmds.setAttr(f'{pose_interpolator}.solverGroup', f'{joint}_PI', type='string')

    # Connect attributes with -na and -f flags
    # Will create a new index (if needed) and connect it
    cmds.connectAttr(f'{pose_interpolator}.solverGroupMessage',
                     f'{blendshape}.SHAPESSolver',
                     nextAvailable=True, force=True)
    

def add_psd_to_shapes():
    # Add prexisting pose interpolator to shapes
    ''''''


