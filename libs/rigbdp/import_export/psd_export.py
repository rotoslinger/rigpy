from maya import cmds, mel






import maya.cmds as cmds

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


def create_blendshape_with_import(geo, shapes_file_path, data_file_path):
    """
    Imports shape and data nodes, then creates a blendShape deformer with custom attributes.

    :param str geo: Geometry name.
    :param str shapes_file_path: File path for importing shape nodes.
    :param str data_file_path: File path for importing data node.
    """
    # Retrieve the namespace for the geometry
    space = cmds.namespaceInfo(geo, fn=True)

    # Create blendShape node
    blendshape_name = f'{geo}_blendShape'
    blendshape_node = cmds.deformer(f'{geo}', type='blendShape', foc=True, name=blendshape_name)[0]

    # Add custom attributes
    get_blendshape_shapes_attrs(blendshape_node)

    # List shapes and intermediates
    all_shapes = cmds.listRelatives(f'{geo}', shapes=True, fullPath=True) or []
    shapes = cmds.listRelatives(f'{geo}', shapes=True, noIntermediate=True, fullPath=True) or []
    intermediates = list(set(all_shapes) - set(shapes)) if shapes else all_shapes

    # Connect SHAPESData attribute
    cmds.connectAttr(f'{blendshape_node}.SHAPESData', f'{blendshape_name}_data.SHAPESData', force=True)

    return {
        'blendshape_node': blendshape_node,
        'all_shapes': all_shapes,
        'shapes': shapes,
        'intermediates': intermediates
    }


def add_shapes_sdk_attr(blendshape_node, sdk_node):
    """
    Adds the SHAPES_sdk message attribute to a blendShape node and connects it to a set-driven key node.
    """
    # Define the full attribute name
    shapes_sdk_attr = f'{blendshape_node}.SHAPES_sdk'
    
    # Check if the attribute already exists on the blendShape node
    if not cmds.attributeQuery('SHAPES_sdk', node=blendshape_node, exists=True):
        # Add the SHAPES_sdk message attribute
        cmds.addAttr(blendshape_node, longName='SHAPES_sdk', attributeType='message')
    
    # Check if the connection exists and connect if it doesn't
    if not cmds.isConnected(shapes_sdk_attr, f'{sdk_node}.message'):
        cmds.connectAttr(f'{sdk_node}.message', shapes_sdk_attr, force=True)

    return shapes_sdk_attr


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



import maya.cmds as cmds

def create_pose_interpolator(name, parent_node, driver_node, control_node):
    """
    Creates a new pose interpolator with a specified name, parent, driver, and control.
    
    :param str name: Name for the pose interpolator transform node.
    :param str parent_node: Name of the parent node to attach the interpolator to.
    :param str driver_node: Name of the driver node for the interpolator.
    :param str control_node: Name of the control node for the interpolator.
    :return: The created pose interpolator node.
    :rtype: str
    """
    # Create pose interpolator node
    pose_interpolator = cmds.createNode('poseInterpolator', name=f'{name}Shape')
    transform_node = cmds.listRelatives(pose_interpolator, parent=True)[0]
    transform_node = cmds.rename(transform_node, name)
    
    # Set visibility and parent
    cmds.setAttr(f'{transform_node}.visibility', 0, lock=True)
    cmds.parent(transform_node, parent_node)
    
    # Set transform matrix
    cmds.xform(transform_node, matrix=[1, 0, 0, 0,
                                       0, 1, 0, 0,
                                       0, 0, 1, 0,
                                       0, 0, 0, 1])

    # Add required attributes to the interpolator
    cmds.addAttr(pose_interpolator, longName='twistAxis', attributeType='long')
    cmds.addAttr(pose_interpolator, longName='opposite', attributeType='bool')
    cmds.addAttr(pose_interpolator, longName='driverList', shortName='dl', attributeType='compound', numberOfChildren=3, multi=True, hidden=True)
    cmds.addAttr(pose_interpolator, longName='driverInput', shortName='di', dataType='matrix', parent='driverList', hidden=True)
    cmds.addAttr(pose_interpolator, longName='controlNode', shortName='cn', attributeType='message', parent='driverList')
    cmds.addAttr(pose_interpolator, longName='poseList', shortName='p', attributeType='compound', numberOfChildren=6, multi=True, hidden=True, parent='driverList')
    cmds.addAttr(pose_interpolator, longName='poseMatrix', shortName='pmat', dataType='matrix', parent='poseList')
    cmds.addAttr(pose_interpolator, longName='poseParentMatrix', shortName='ppmat', dataType='matrix', parent='poseList')
    cmds.addAttr(pose_interpolator, longName='poseMode', shortName='pmd', attributeType='long', parent='poseList')
    cmds.addAttr(pose_interpolator, longName='controlPoseAttributes', shortName='cpa', dataType='stringArray', parent='poseList')
    cmds.addAttr(pose_interpolator, longName='controlPoseValues', shortName='cpv', dataType='doubleArray', parent='poseList')
    cmds.addAttr(pose_interpolator, longName='controlPoseRotateOrder', shortName='cpro', attributeType='long', parent='poseList')
    
    # Set interpolator attributes
    interpolator_attrs = {
        'regularization': 0,
        'interpolation': 0,
        'outputSmoothing': 0,
        'allowNegativeWeights': 0,
        'enableRotation': 0,
        'enableTranslation': 1,
    }
    for attr, value in interpolator_attrs.items():
        cmds.setAttr(f'{pose_interpolator}.{attr}', value)
    
    # Set driver attributes
    cmds.setAttr(f'{pose_interpolator}.driver[0].driverTwistAxis', 0)
    cmds.setAttr(f'{pose_interpolator}.driver[0].driverRotateOrder', 0)
    cmds.setAttr(f'{pose_interpolator}.driver[0].driverEulerTwist', 0)

    # Connect attributes if source attributes exist
    if cmds.objExists(f'{driver_node}.worldMatrix[0]'):
        cmds.connectAttr(f'{driver_node}.worldMatrix[0]', f'{pose_interpolator}.driverList[0].driverInput', force=True)
    
    if cmds.objExists(f'{control_node}.message'):
        cmds.connectAttr(f'{control_node}.message', f'{pose_interpolator}.driverList[0].controlNode', force=True)

    return transform_node

# Usage example:
# pose_interpolator_node = create_pose_interpolator('M_jsh_base_body_geoShapes_blendShape_L_lips_jntPSD_PI', 'L_lips_offset', 'L_lips_jntPSD', 'L_lips_ctrl')
# print(pose_interpolator_node)
