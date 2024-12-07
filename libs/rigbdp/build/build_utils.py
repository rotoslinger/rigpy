import re, json
from importlib import reload
from functools import wraps
from maya import cmds
from rigbdp.build import locking
reload(locking)

import maya.cmds as cmds

def return_created_nodes(func):
    """
    This function is to return nodes created by a maya command that doesn't return anything
    
    It does this by:
    1. find all nodes before function runs
    2. run function
    3. find all nodes after the function runs
    4. find the nodes that were not in the first list - these are the created nodes
    5. return the newly created nodes

    """
    def wrapper(*args, **kwargs):
        # Get the current list of all nodes in the scene before running the function
        all_nodes_before = cmds.ls(long=True)
        
        # Run the function
        result = func(*args, **kwargs)
        
        # Get the list of all nodes after running the function
        all_nodes_after = cmds.ls(long=True)
        
        # Find the difference between nodes before and after
        created_nodes = list(set(all_nodes_after) - set(all_nodes_before))
        
        return created_nodes  # Return the list of created nodes
    
    return wrapper


def wrap_eyebrows():
    eyebrows_mesh = f'*_base_fur_C_eyebrows_mesh'
    eyebrows_mesh = cmds.ls(eyebrows_mesh)
    if not eyebrows_mesh:return
    eyebrows_mesh=eyebrows_mesh[0]
        
    # cmds.delete(skin_cluster)
    char_name = eyebrows_mesh.split('_')[0]
    body_mesh = f'{char_name}_base_body_geo'
    cmds.delete(eyebrows_mesh, constructionHistory=True)
    cmds.select(eyebrows_mesh, body_mesh)
    wrapped_function = return_created_nodes(cmds.CreateWrap)
    created_nodes = wrapped_function()
    wrap = [w for w in created_nodes if 'wrap' in cmds.objectType(w)][0]
    wrap = cmds.rename(wrap, f'{eyebrows_mesh}_wrap')
    # Use these settings for speed
    cmds.setAttr(f'{wrap}.maxDistance', 1)
    cmds.setAttr(f'{wrap}.weightThreshold', 0)
    cmds.setAttr(f'{wrap}.autoWeightThreshold', 0)
    cmds.setAttr(f'{wrap}.exclusiveBind', 0)
    cmds.setAttr(f'{wrap}.falloffMode', 0)
    cmds.setAttr(f'{body_mesh}.inflType', 2)

def clean_intermediate_nodes():
    '''
    This will get rid of extraneous intermediate nodes that would cause a SHAPES
    load to fail. There should only be a ShapeOrig.
    If there are more, for example ShapeOrig1, SHAPES will complain and tell you
    that only one intermediate node is allowed.
    '''

    blendshapes = cmds.ls(type='blendShape')
    final_shapes = []
    for bs in blendshapes:
        geos = cmds.blendShape(bs,
                               query=True, geometry=True)
        
        # All geo in list must have a wildcard added for ls's * filter to work
        geos = [f'{g}*' for g in geos]
        # Make sure to unpack the list *[], ls doesn't like a list for its first p-arg
        shapes = cmds.ls(*geos)
        shapes = [s for s in shapes if 'ShapeOrig' in s and not re.search(r'ShapeOrig$', s)]
        
        final_shapes += shapes
    # use set to remove any duplicate entries (Minimo put multiple blendshapes on meshes)
    final_shapes = list(set(final_shapes))
    cmds.delete(final_shapes)


OTHER = ['M_freeze_env', 'spaces_grp', 'modules_grp', 'rigGeo_ndStep_grp', 'rigGeo_200_grp']


def suppress_warnings(func):
    # suppress_warnings, but only while the function runs. Func is safe to fail.  Do not use with quit() or sys.exit()!
    @wraps(func)
    def wrapper(*args, **kwargs):
        cmds.scriptEditorInfo(suppressWarnings=True)
        result = func(*args, **kwargs)
        cmds.scriptEditorInfo(suppressWarnings=False)
        return result
    return wrapper

@suppress_warnings
def setup_rig_vis(channel_box = True, hidden_in_outliner=False, skin_jnt_vis=False, sculpt_jnt_vis=True):
    # create divider
    if not cmds.objExists('preferences.__________________'):
        cmds.addAttr('preferences', longName="__________________", attributeType='enum', enumName='_________:')
        cmds.setAttr('preferences.__________________', e=True, channelBox=True)

    long_names=['rig_hidden_in_outliner', 'skin_joints_vis', 'sculpt_joints_vis']
    nice_names=['Rig Hidden In Outliner', 'Skin Joints Visibility', 'Sculpt Joints Visibility']

    for index, attr in enumerate(long_names):
        if not cmds.objExists(f'preferences.{attr}'):
            cmds.addAttr('preferences', longName=long_names[index], niceName=nice_names[index], attributeType='bool')
        cmds.setAttr(f'preferences.{attr}', e=True, channelBox=True)

    hidden_in_outliner_attr = 'preferences.rig_hidden_in_outliner'
    skin_vis_attr = 'preferences.skin_joints_vis'
    sculpt_vis_attr = 'preferences.sculpt_joints_vis'
    full_attrs = [hidden_in_outliner_attr, skin_vis_attr, sculpt_vis_attr]

    rig_root = 'rig_grp'
    skin_grp = 'skel_grp'
    sculpt_jnts = 'M_masterWalkOut_jnt'
    all_objects = [rig_root, skin_grp, sculpt_jnts] + OTHER

    for obj in all_objects:
        cmds.connectAttr(hidden_in_outliner_attr, f'{obj}.hiddenInOutliner', force=True)
        cmds.setAttr(f'{obj}.v', e=True, lock=False, channelBox=channel_box, keyable=False)
        if 'skel' in obj:
            cmds.connectAttr(skin_vis_attr, f'{skin_grp}.v', force=True)
        if 'M_masterWalkOut_jnt' in obj:
            cmds.connectAttr(sculpt_vis_attr, f'{sculpt_jnts}.v', force=True)
    full_attrs.insert(0, 'preferences.__________________')

    # sets arg attr vals
    arg_attrs = [None, hidden_in_outliner, skin_jnt_vis, sculpt_jnt_vis]

    cmds.setAttr(f'{rig_root}.v', True)

    # whether to see in the channel box
    for index, name in enumerate(full_attrs):
        cmds.setAttr(name, e=True, channelBox=channel_box)
        if index > 0:
            cmds.setAttr(name, arg_attrs[index])

def unlock_skin_jnts(skincluster_name, file_path, unlock=True):

    if unlock:
        connections_data = locking.get_compound_attr_connect_map(node=skincluster_name, compound_attr='matrix')
        locking.export_to_json(connections_data, filename_prefix=skincluster_name, file_path=file_path, suffix='CONNECTION_MAP')

        # import #
        json_data = locking.import_json_conn_map(file_path=file_path, filename_prefix=skincluster_name,suffix="CONNECTION_MAP")

        # connect joints to skincluster #
        locking.connect_skin_joints(connection_map=json_data, skincluster_name=skincluster_name)
    else:
        # import #
        json_data = locking.import_json_conn_map(file_path=file_path, filename_prefix=skincluster_name,suffix="CONNECTION_MAP")

        # connect matrixMultipliers to skincluster #
        locking.connect_matrix_mults(connection_map=json_data, skincluster_name=skincluster_name)
    ##########################################################################################################

# example:
# skincluster_name = 'jsh_base_hat_body_fabric_geo_bodyMechanics_skinCluster'
# file_path=r'C:\Users\harri\Documents\BDP\cha\jsh'
# unlock_skin_jnts(skincluster_name, file_path, unlock=True)
# unlock_skin_jnts(skincluster_name, file_path, unlock=False)