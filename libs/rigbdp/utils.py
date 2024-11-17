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

# Example usage:

# @return_created_nodes
# def example_function():
#     """
#     Example function to demonstrate node creation.
#     """
#     # Create a cube (this will be tracked)
#     cmds.polyCube(name="exampleCube")

# # Call the wrapped function
# created_nodes = example_function()
# print("Created nodes:", created_nodes)


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
    cmds.setAttr(f'{body_mesh}.inflType',1)
    # print('THIS IS THE NEW WRAP!!!! : ', wrap)

def get_skinclusters_on_mesh(mesh):
    skin_clusters=[]

    for skin_cluster in cmds.ls(type='skinCluster'):
        geoms = cmds.skinCluster(skin_cluster, q=True, geometry=True)
        if not geoms: continue
        '''
        Finding the skincluster associated with the mesh

        We really only care about things that end in Shape

        Because the skincluster geometry query only returns shape names, we need to check if
        the geometry in the skincluster ends in Shape. If this is true, any partial naming matches
        get culled out and you can focus on only meshes.
        '''
        # makes sure that string eyebrows_mesh is in the skincluster, and also ends with meshShape 
        if mesh in geoms[0] and geoms[0].endswith('Shape'):
            skin_clusters.append(skin_cluster)
            #cmds.skinCluster(skin_cluster, edit=True, unbind=True)
    return skin_clusters

def replace_keys_with_string(dictionary, source_name, target_name):
    """Replace occurrences of source_name with target_name in each dictionary key."""
    new_dict = {}
    for key, value in dictionary.items():
        new_key = key.replace(source_name, target_name)
        new_dict[new_key] = value
    return new_dict





def replace_keys_and_values_in_nested_dict(dictionary, source_name, target_name):
    """Recursively replace occurrences of source_name with target_name in all string keys and values."""
    new_dict = {}
    for key, value in dictionary.items():
        # Replace in the key if it's a string
        new_key = key.replace(source_name, target_name) if isinstance(key, str) else key
        
        # If value is a dictionary, recurse
        if isinstance(value, dict):
            new_value = replace_keys_and_values_in_nested_dict(value, source_name, target_name)
        # Replace in the value if it's a string
        elif isinstance(value, str):
            new_value = value.replace(source_name, target_name)
        else:
            new_value = value
        
        # Assign the modified key and value to the new dictionary
        new_dict[new_key] = new_value
    
    return new_dict


def smart_copy_skinweights(source_mesh, target_mesh,
                           skin_clusters=[],
                           filepath=r'C:\Users\harri\Documents\BDP\cha\jsh\input'):
    if not skin_clusters:
        skin_clusters = get_skinclusters_on_mesh(source_mesh)
    # print('GEOMS', source_mesh)
    # print('SKINCLUSTERS ', skin_clusters)
    src_skin_influences = {}
    src_connection_maps = {}
    target_skinclusters = []

    target_connection_maps = {}
    for idx, source_skincluster in enumerate(skin_clusters):
        # try:
        map = locking.get_compound_attr_connect_map(node = source_skincluster, compound_attr='matrix')
        locking.export_to_json(map, filename_prefix=source_skincluster,
                               file_path=filepath, suffix='CONNECTION_MAP')

        src_connection_maps[f'{source_skincluster}_MAP'] = map
        locking.connect_skin_joints(map, source_skincluster)
        influences = cmds.skinCluster(source_skincluster, query=True, influence=True)
        src_skin_influences[source_skincluster]=influences
        # except Exception as e:
        #     print('ERROR : ', e)
        #     influences = cmds.skinCluster(source_skincluster, query=True, influence=True)
        #     skin_influence_map[source_skincluster]=influences
    # target_skin_influence_map = replace_keys_with_string(src_skin_influence_map, source_mesh, target_mesh)
    for source_skincluster in src_skin_influences:
        # print(f'skincluster: {source_skincluster}\ninfluences: {skin_influence_map[source_skincluster]}')
        skincluster_new_name = source_skincluster.replace(source_mesh, target_mesh)
        target_skinclusters.append(skincluster_new_name)

        if not cmds.objExists(skincluster_new_name):
            skincluster_new_name = cmds.skinCluster(target_mesh,
                                                  src_skin_influences[source_skincluster],
                                                  bindMethod=0,
                                                  toSelectedBones=True,
                                                  multi=True,
                                                  name=skincluster_new_name)[0]
        # print('INFLUENCES ',skin_influence_map[source_skincluster])
        # print('COPYING FOR ',source_skincluster)
        cmds.copySkinWeights(sourceSkin=source_skincluster,
                                destinationSkin=skincluster_new_name,
                                noMirror=True,
                                influenceAssociation=['label', 'name', 'oneToOne'] # "oneToOne" 'label'
                                )
    

    for idx, source_skincluster in enumerate(skin_clusters):
        json_data = locking.import_json_conn_map(file_path=filepath, filename_prefix=source_skincluster, suffix="CONNECTION_MAP")
        locking.connect_matrix_mults(connection_map=json_data, skincluster_name=source_skincluster)

        new_json_data = replace_keys_and_values_in_nested_dict(json_data, source_mesh, target_mesh)

        # print(json.dumps(new_json_data, indent=4))
        locking.connect_matrix_mults(connection_map=new_json_data, skincluster_name=target_skinclusters[idx], debug=False)
        # print('Connected new Matrix mults', skincluster_new_name)


# from importlib import reload
# from rigbdp import utils
# from rigbdp.build import locking
# reload(utils)
# reload(locking)
# locking.set_history_visibility(1)

# export_path = r'C:\Users\harri\Documents\BDP\cha\jsh'
# utils.smart_copy_skinweights(source_mesh='jsh_base_cloth_top_fabric_mesh',
#                              target_mesh='jsh_base_cloth_top_fabric_low_mesh',
#                              skin_clusters=['jsh_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster'],
#                              filepath=export_path)
# utils.smart_copy_skinweights(source_mesh='jsh_base_cloth_pants_fabric_mesh',
#                              target_mesh='jsh_base_cloth_pants_fabric_low_mesh',
#                              skin_clusters=['jsh_base_cloth_pants_fabric_mesh_bodyMechanics_skinCluster'],
#                              filepath=export_path)



    # # for key in src_connection_maps:
    # #     target_connection_maps = replace_keys_with_string(src_skin_influences, source_mesh, target_mesh)
    # for skincluster in src_connection_maps:
    #     target_connection_maps[skincluster]=replace_keys_with_string(src_connection_maps[skincluster], source_mesh, target_mesh)


    # # target_connection_maps = replace_keys_with_string(src_skin_influences, source_mesh, target_mesh)
    # # print(json.dumps(target_connection_maps, indent=4))

    # for skin in src_connection_maps:
    #     locking.connect_matrix_mults(src_connection_maps[skin], skin)

    # for skin in target_connection_maps:
    #     locking.connect_matrix_mults(target_connection_maps[skin], skin)


# connections_data = get_compound_attr_connect_map(node='teshi_base_body_geo_bodyMechanics_skinCluster',
#                                                  compound_attr='matrix')
# export_to_json(connections_data,
#                filename_prefix='teshi_base_body_geo_bodyMechanics_skinCluster',
#                file_path=r'C:\Users\harri\Documents\BDP\cha\teshi',
#                suffix='MATRIX_CONNECTIONS')

    


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
