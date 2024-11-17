import json, statistics, re, math, inspect

import maya.cmds as cmds
import maya.api.OpenMaya as om
import numpy as np



def create_bounding_box_cube(bounding_box, name='bounds_cube', parent=None):
    '''
    Args:
        bounding_box (MBoundingBox): An maya.api.OpenMaya 2 MBoundingBox. Library is important,
                                     you will error out if an maya.OpenMaya MBoundingBox
        name (str): Name to give the new polyCube.
        parent (None/str): The MFnMesh object representing the mesh to test against.
    Return:

    '''
    width = bounding_box.width
    height = bounding_box.height
    depth = bounding_box.depth

    # Create the poly cube with the correct dimensions
    cube_name = cmds.polyCube(w=width, h=height, d=depth,
                              name=name, parent=parent,
                              constructionHistory=False)[0]

    # Get the center of the bounding box
    bbox_center = bounding_box.center

    # Move the cube to the center of the bounding box
    cmds.xform(cube_name, translation=(bbox_center.x, bbox_center.y, bbox_center.z))
    return cube_name


def curve_unnormalized(pts, name='linearCurve', parent=None):
    # creates a curve where each point is a numerical parameter starting with a 0 index
    # For example, a curve with seven points will have a 0-6 parameterization.
    if not pts or len(pts) < 2:
        raise ValueError("At least two points are required to create a linear curve.")
    curve = cmds.curve(d=1, p=pts, name=name)  
    if parent and cmds.objExists(parent):
        cmds.parent(curve, parent)
    return curve
########################################## Usage example ###########################################
# points = [ (0, 0, 0), (1, 2, 0), (2, 4, 0)]
# # Create the curve with a specified name and optional parent (None in this case)
# curve_name = create_linear_curve_unnormalized(points, name='sevenPointCurve', parent=None)
# print(f"Created curve: {curve_name}")
####################################################################################################


# TODO some of this code should be made more agnostic and moved to a new module called analyze shape
def sort_jnts_in_xy(joints):
    """
    Analyze a cloud of joints to determine if it is longer along the X or Y axis.
    Sorts the joints based on the primary axis and determines the axis direction.

    Args:
        joints (list): List of joint names.

    Returns:
        tuple: (sorted_joints, primary_axis, axis_direction), where:
            - sorted_joints (list): List of joints ordered by position along the primary axis.
            - primary_axis (str): The primary axis ('x' or 'y') based on the longest dimension.
            - axis_direction (str): Direction ('+' or '-')
              based on the orientation of the sorted joints.
    """
    if not joints:
        return [], None, None

    # Determine the bounding box for the cloud of joints
    x_positions = [cmds.xform(joint, q=True, ws=True, t=True)[0] for joint in joints]
    y_positions = [cmds.xform(joint, q=True, ws=True, t=True)[1] for joint in joints]

    # Calculate the length of the bounding box in X and Y directions
    x_length = max(x_positions) - min(x_positions)
    y_length = max(y_positions) - min(y_positions)

    # Determine the primary axis
    axis_plane = 'x' if x_length > y_length else 'y'
    axis_index = 0 if axis_plane == 'x' else 1

    # Determine the side if primary axis is X
    if axis_plane == 'x':
        avg_x_position = sum(x_positions) / len(x_positions)
        side = 'right' if avg_x_position < 0 else 'left'
        
        # Set sort order based on side/position.
        # Arms are sort rules depend on side, left 
        if side == 'right':
            sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True, 
                                                                    ws=True, t=True)[axis_index],
                                                                    reverse=True)
            joint_chain_direction = '-x'  # highest to lowest for left side
        else:
            sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True, 
                                                                    ws=True, t=True)[axis_index])
            joint_chain_direction = '+x'  # lowest to highest for right side
    
    else:  # primary_axis == 'y'
        sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True,
                                                                ws=True, t=True)[axis_index],
                                                                reverse=True)
        joint_chain_direction = '-y'  # always highest to lowest for Y axis

    ordered_joint_positions = [cmds.xform(p, q=True, ws=True, t=True) for p in sorted_joints]
    joint_data = {'sorted_joints':sorted_joints,
                   'ordered_joint_positions': ordered_joint_positions,
                   'axis_plane': axis_plane,
                   'joint_chain_direction': joint_chain_direction}

    return joint_data
########################################## Usage example ###########################################
# # Maya usage example
# from importlib import reload
# from CW import maya_auto_weight
# reload(maya_auto_weight)

# left_arm_joints = ['LeftHand','LeftForeArm_out_bind_tw00', 'LeftForeArm_out_bind_tw01', 'LeftForeArm_out_bind_tw02', 'LeftForeArm_out_bind_tw03', 'LeftForeArm_out_bind_tw04', 'LeftForeArm_out_bind_tw05', 'LeftArm_out_bind_tw00', 'LeftArm_out_bind_tw01', 'LeftArm_out_bind_tw02', 'LeftArm_out_bind_tw03', 'LeftArm_out_bind_tw04', 'LeftArm_out_bind_tw05']
# right_arm_joints = ['RightForeArm_out_bind_tw00', 'RightForeArm_out_bind_tw01', 'RightHand','RightForeArm_out_bind_tw02', 'RightForeArm_out_bind_tw03', 'RightForeArm_out_bind_tw04', 'RightForeArm_out_bind_tw05', 'RightArm_out_bind_tw00', 'RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05']
# left_leg_joints = ['LeftUpLeg_out_bind_tw00', 'LeftUpLeg_out_bind_tw01', 'LeftUpLeg_out_bind_tw02', 'LeftUpLeg_out_bind_tw03', 'LeftUpLeg_out_bind_tw04', 'LeftUpLeg_out_bind_tw05', 'LeftLeg_out_bind_tw00', 'LeftLeg_out_bind_tw01', 'LeftLeg_out_bind_tw02', 'LeftLeg_out_bind_tw03', 'LeftLeg_out_bind_tw04', 'LeftLeg_out_bind_tw05']
# right_leg_joints = ['RightUpLeg_out_bind_tw00', 'RightUpLeg_out_bind_tw01', 'RightUpLeg_out_bind_tw02', 'RightUpLeg_out_bind_tw03', 'RightUpLeg_out_bind_tw04', 'RightUpLeg_out_bind_tw05', 'RightLeg_out_bind_tw05', 'RightLeg_out_bind_tw00', 'RightLeg_out_bind_tw01', 'RightLeg_out_bind_tw02', 'RightLeg_out_bind_tw03', 'RightLeg_out_bind_tw04']

# joint_data = maya_auto_weight.sort_jnts_in_xy(right_leg_joints)
# print('sorted_joints : ', joint_data['sorted_joints'])
# print('ordered_joint_positions : ', joint_data['ordered_joint_positions'])
# print('axis_plane : ', joint_data['axis_plane'])
# print('joint_chain_direction : ', joint_data['joint_chain_direction'])
####################################################################################################

def curve_from_jnts(joints, name=None, parent=None):
    joint_data = sort_jnts_in_xy(joints)
    if not name:
        name = f'{joints[0]}_crv'
    joint_data = sort_jnts_in_xy(joints)
    curve = curve_unnormalized(joint_data['ordered_joint_positions'], name, parent)
    joint_param_dict = [{jnt:idx} for (idx, jnt) in enumerate(joints)]
    return joint_param_dict, curve
########################################## Usage example ###########################################
# from importlib import reload
# from CW import maya_auto_weight
# reload(maya_auto_weight)
# maya_auto_weight.curve_from_jnts(maya_auto_weight.sort_jnts_in_xy(left_arm_joints)['sorted_joints'])
# maya_auto_weight.curve_from_jnts(maya_auto_weight.sort_jnts_in_xy(right_arm_joints)['sorted_joints'])
# maya_auto_weight.curve_from_jnts(maya_auto_weight.sort_jnts_in_xy(left_leg_joints)['sorted_joints'])
# maya_auto_weight.curve_from_jnts(maya_auto_weight.sort_jnts_in_xy(right_leg_joints)['sorted_joints'])
####################################################################################################
def get_dag_path(object_name):
    # Utility function to get the DAG path of an object
    selection_list = om.MSelectionList()
    selection_list.add(object_name)
    dag_path = selection_list.getDagPath(0)
    return dag_path

def get_transform_matrix(transform_name):
    """
    Retrieve the transformation matrix of a specified transform node.
    
    :param str transform_name: Name of the transform node.
    :return: Transformation matrix of the transform.
    :rtype: om.MMatrix
    """
    selection_list = om.MSelectionList()
    selection_list.add(transform_name)
    transform_obj = selection_list.getDependNode(0)
    transform_fn = om.MFnTransform(transform_obj)
    return transform_fn.transformation().asMatrix()

def get_mesh_points(mesh):
    """
    Retrieve all vertex points of a mesh in world space.
    
    :param str mesh: Name of the mesh node.
    :return: List of points in world space.
    :rtype: list[om.MPoint]
    """
    print(mesh)
    mesh_fn = om.MFnMesh(get_dag_path(mesh))
    return mesh_fn.getPoints(om.MSpace.kWorld)

def create_oriented_bounding_box(mesh, debug=False):
    """
    Calculate the oriented bounding box (OBB) for a mesh and optionally visualize it.
    
    :param str mesh: Name of the mesh node to calculate the OBB for.
    :param bool debug: Whether to visualize the OBB with a polycube.
    :return: Min and max points of the OBB.
    :rtype: tuple[om.MPoint, om.MPoint]
    """
    # Step 1: Get mesh points in world space
    points = get_mesh_points(mesh)
    points_array = np.array([[point.x, point.y, point.z] for point in points])
    
    # Step 2: Compute the covariance matrix of the points
    cov_matrix = np.cov(points_array.T)

    # Step 3: Perform Eigen decomposition to get the principal axes
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # Step 4: Get the min and max bounds along each principal axis
    min_point = om.MPoint(min(points_array[:, 0]), min(points_array[:, 1]), min(points_array[:, 2]))
    max_point = om.MPoint(max(points_array[:, 0]), max(points_array[:, 1]), max(points_array[:, 2]))

    # Step 5: Visualize with a debug cube (if debug is True)
    if debug:
        create_debug_cube(min_point, max_point, eigenvectors)

    return min_point, max_point

def create_debug_cube(min_point, max_point, eigenvectors):
    """
    Create a polycube to visualize the oriented bounding box (OBB) with rotation.
    
    :param om.MPoint min_point: Minimum point of the OBB.
    :param om.MPoint max_point: Maximum point of the OBB.
    :param numpy.ndarray eigenvectors: Principal axes (rotation) of the OBB.
    """
    # Step 1: Calculate the width, height, and depth of the bounding box
    width = max_point.x - min_point.x
    height = max_point.y - min_point.y
    depth = max_point.z - min_point.z
    
    # Step 2: Create the polycube with the calculated dimensions
    debug_cube = cmds.polyCube(w=width, h=height, d=depth)[0]
    
    # Step 3: Position the cube at the center of the bounding box
    center = [(min_point.x + max_point.x) * 0.5, 
              (min_point.y + max_point.y) * 0.5, 
              (min_point.z + max_point.z) * 0.5]
    cmds.move(center[0], center[1], center[2], debug_cube)
    
    # Step 4: Apply rotation to align with the principal axes of the mesh
    # Convert eigenvectors to Euler angles
    rotation_matrix = np.array(eigenvectors)
    euler_rotation = om.MEulerRotation(*rotation_matrix[0])  # Use the first eigenvector for rotation
    
    # Convert Euler rotation from radians to degrees for Maya
    euler_rotation_degrees = om.MEulerRotation(
        np.degrees(euler_rotation.x),
        np.degrees(euler_rotation.y),
        np.degrees(euler_rotation.z)
    )

    # Apply the rotation using cmds.xform
    cmds.xform(debug_cube, rotation=(euler_rotation_degrees.x, euler_rotation_degrees.y, euler_rotation_degrees.z))


def get_xform_as_mvector(obj):
    """
    Retrieve the translation of an object as an MVector.
    
    :param str obj: The name of the object to query.
    :return: The translation of the object as an MVector.
    :rtype: om.MVector
    """
    # Get translation in world space using cmds.xform
    translation = cmds.xform(obj, q=True, ws=True, t=True)
    
    # Convert the translation to an MVector
    return om.MVector(translation[0], translation[1], translation[2])

def find_points_between(from_point, to_point, point_list):
    """
    Find and select all points that lie between two transforms.
    
    :param str from_point: The 'from' transform's name.
    :param str to_point: The 'to' transform's name.
    :param list[str] point_list: List of point names (or objects) to check.
    :return: List of points that lie between the two transforms.
    :rtype: list[str]
    """
    # Get the translation vectors for the from_point and to_point
    from_vector = get_xform_as_mvector(to_point)-get_xform_as_mvector(from_point)
    to_vector = get_xform_as_mvector(from_point)-get_xform_as_mvector(to_point)
    from_vector.normalize()
    to_vector.normalize()

    # List to hold the points that are between
    points_between = []

    # Iterate through the points and check if they lie between the two transforms
    for point in point_list:
        point_vector = get_xform_as_mvector(point)
        
        # Calculate direction from from_point to this point
        from_vector_to_point = point_vector - from_vector
        from_vector_to_point.normalize()

        to_vector_to_point = point_vector - to_vector
        to_vector_to_point.normalize()

        # Dot product test: Check if the point lies between the two direction vectors
        if (from_vector * from_vector_to_point) >= 0:
        # if (from_vector * from_vector_to_point) >= 0 and (to_vector * from_vector_to_point) >= 0:
            points_between.append(point)

    # Select the points that are found between the transforms
    cmds.select(points_between)
    return points_between

def create_debug_prim(name, cube_or_sphere=True, position=(0, 0, 0)):
    """
    Creates a cube if it does not already exist in the scene, and names it based on the argument.
    
    :param str name: The name of the cube to create.
    :param tuple position: The position to place the cube at (default: (0, 0, 0)).
    :return: The name of the created or existing cube.
    :rtype: str
    """
    # Check if the cube with the given name already exists
    if not cmds.objExists(name):
        object=''
        # Create the cube and position it
        if cube_or_sphere:
            object = cmds.polyCube(name=name)[0]
        else:
            object = cmds.polySphere(name=name)[0]
        cmds.xform(object, translation=position)
    else:
        # If it already exists, return the existing cube
        object = name

    return object

def get_xform_as_mvector(object_name):
    """
    Retrieve the translation of an object as an MVector.
    Not performant, should only be used for debugging
    """
    return om.MVector(cmds.xform(object_name, query=True, translation=True, worldSpace=True))

def create_rotation_from_objects(source_object, target_object):
    """
    Calculates and applies the rotation to the source object to aim at the target object.
    
    :param str source_object: The object that will be rotated.
    :param str target_object: The object that the source object will aim at.
    """
    # Get the positions of the source and target objects
    source_position = get_xform_as_mvector(source_object)
    target_position = get_xform_as_mvector(target_object)
    
    # Calculate the direction vector from the source to the target
    direction_vector = target_position - source_position
    
    # Normalize the direction vector
    direction_vector.normalize()
    
    # Assume the source vector should point along the positive X axis
    source_vector = om.MVector(1, 0, 0)
    
    # Rotate the source vector to the target vector using MVector.rotateTo
    quaternion = source_vector.rotateTo(direction_vector)
    
    # Convert the quaternion to Euler rotation
    euler_rotation = quaternion.asEulerRotation()
    
    # Apply the Euler rotation to the source object using xform
    cmds.xform(source_object,rotation=(math.degrees(euler_rotation[0]),
                                        math.degrees(euler_rotation[1]),
                                        math.degrees(euler_rotation[2])), worldSpace=True)
# Example usage:
# source_object = 'pCube1'  # Example source object (the one to be rotated)
# target_object = 'pCube2'  # Example target object (the one to aim at)

# create_rotation_from_objects(source_object, target_object)


def create_debug_plane(name, position):
    # Create the polyplane
    if not cmds.objExists(name):
        name = cmds.polyPlane(name=name, width=5, height=5, subdivisionsX=1, subdivisionsY=1, axis=[1,0,0])[0]

        # Move the plane to the source position
        cmds.xform(name, worldSpace=True, translation=(position))

        # Turn on the normal display for visualizing the face normal
        cmds.polyOptions(name, displayNormal=True)
        cmds.select(name)
        cmds.ToggleFaceNormalDisplay(name)


def directional_vector_to_plane(from_plane, to_plane, point, move_to_plane=True):
    """
    Projects a point onto an infinite plane defined by two transforms, from_plane and to_plane.
    
    :param str from_plane: The source plane transform.
    :param str to_plane: The target plane transform.
    :param om.MVector point: The point to project onto the plane.
    :return: The projected point as an MVector.
    :rtype: om.MVector
    """
    # Get the world-space positions of the from_plane and to_plane
    point_position = get_xform_as_mvector(point)
    from_position = get_xform_as_mvector(from_plane)
    to_position = get_xform_as_mvector(to_plane)
    
    # Calculate the direction from the from_plane to the to_plane
    plane_direction = to_position - from_position
    
    # Normalize the direction to get the plane's normal
    plane_direction.normalize()

    # Project the point onto the plane along the normal direction
    point_to_plane = point_position - from_position
    dot_product = point_to_plane * plane_direction
    projected_point = point_position - dot_product * plane_direction
    
    if move_to_plane:
        cmds.xform(point, worldSpace=True, translation=(projected_point.x,
                                                        projected_point.y,
                                                        projected_point.z))
    
    directional_vector = point_position - projected_point
    directional_vector.normalize()
    
    return directional_vector

def is_point_between_points(point, from_point, to_point):
    # Create a vector from and a vector to
    vector_from = get_xform_as_mvector(to_point) - get_xform_as_mvector(from_point)
    vector_from.normalize()
    vector_to = get_xform_as_mvector(from_point) - get_xform_as_mvector(to_point)
    vector_to.normalize()

    # find the directional vector from the point to the from_plane representing an infinite plane

    # create a directional vector by projecting to the to_plane
    projected_point_from = directional_vector_to_plane(from_point, to_point, point, move_to_plane=False)
    dot_product_from = projected_point_from * vector_from

    print(f'The projected dot product of {point} from_plane : ', dot_product_from)
    cmds.select(point)

    # find the directional vector from the point to the to_plane representing an infinite plane

    # create a directional vector by projecting to the from_plane
    projected_point_to = directional_vector_to_plane(to_point, from_point, point, move_to_plane=False)
    dot_product_to = projected_point_to * vector_to

    print('The projected dot product of point_01 to_plane : ', dot_product_to)
    cmds.select(point)


    # if the point is between, both of the dot products will either 1.0 or .99999
    # if either are below 0 they are not between
    # if they are 0 they are on a plane, technically not between, but we will treat them as such
    if dot_product_from >= 0 and dot_product_to >= 0:
        print( f'{point} is between')
    else:
        print( f'{point} is not between')

def debug_find_points_between():

    from_plane = "plane_from"
    to_plane = "plane_to"
    
    
    create_debug_plane(from_plane, position=(0, 0, 0))
    create_debug_plane(to_plane, position=(10, 0, 0))
    
    # Rotate the plane to point towards the target (Only used to visually debug)
    create_rotation_from_objects(source_object=from_plane, target_object=to_plane)
    create_rotation_from_objects(source_object=to_plane, target_object=from_plane)



    # Example usage:
    # Create pCube1 and pCube2 objects if they don't already exist, and position them
    # from_point = create_debug_prim("from_point", position=(0, 0, 0))
    # to_point = create_debug_prim("to_point", position=(10, 0, 0))
    point = create_debug_prim("point_01", cube_or_sphere=False, position=(5, 2, 0))  # Example, can be replaced by pSphere creation
    point_02 = create_debug_prim("point_02", cube_or_sphere=False, position=(15, 0, 0))


    is_point_between_points(point, from_plane, to_plane)





    # points_in_between = find_points_between(from_plane, to_plane, point_list)


    # vector_to = get_xform_as_mvector(from_plane) - get_xform_as_mvector(to_plane)


    # projected_point_to = vector_to_plane(to_plane, from_plane, point_01)
    # projected_point_to = project_point_to_plane(from_point, to_point, point_01)
    

    # point_list = [point_01, point_02]
    # points_in_between = find_points_between(from_plane, to_plane, point_list)





# Example Usage:
# mesh_name = "pSphere1"  # Example mesh
# min_point, max_point = create_oriented_bounding_box(mesh_name, debug=True)
# print("OBB Min:", min_point)
# print("OBB Max:", max_point)
# calculate_oriented_bounding_box('pCylinder1')

# def slerp(start_normal, end_normal, t):
#     # Normalize vectors to ensure they are unit vectors
#     start_normal = start_normal.normalize()
#     end_normal = end_normal.normalize()

#     # Compute the cosine of the angle between the two vectors
#     dot = start_normal * end_normal

#     # Clamp dot to avoid numerical errors
#     dot = np.clip(dot, -1.0, 1.0)

#     # If the dot product is close to 1, linearly interpolate
#     if dot > 0.9995:
#         return start_normal + t * (end_normal - start_normal)

#     # Compute the angle between the vectors
#     theta_0 = np.arccos(dot)  # Angle between vectors in radians
#     theta = theta_0 * t  # Interpolated angle

#     # Perform spherical interpolation
#     sin_theta = np.sin(theta)
#     sin_theta_0 = np.sin(theta_0)
#     scale_start = np.cos(theta) - dot * sin_theta / sin_theta_0
#     scale_end = sin_theta / sin_theta_0

#     return (start_normal * scale_start) + (end_normal * scale_end)

# def find_points_and_normals(start_vec, end_vec, start_normal, end_normal, num_points=10):
#     points = []
#     normals = []
    
#     for i in range(num_points):
#         t = i / (num_points - 1)  # Interpolate from 0 to 1
        
#         # Interpolate positionp
#         point = (start_vec * (1 - t)) + (end_vec * t)  # MVector interpolation
#         points.append(point)
        
#         # Interpolate normal using slerp
#         normal = slerp(start_normal, end_normal, t)
#         normals.append(normal)
    
#     return points, normals

# def get_selected_points_and_normals(start_normal, end_normal, num_points=10):
#     """
#     Get the selected points (vertices or control points) in Maya and apply the find_points_and_normals function to get interpolated positions and normals.
    
#     :param om.MVector start_normal: The normal vector at the start
#     :param om.MVector end_normal: The normal vector at the end
#     :param int num_points: The number of points to interpolate
#     :return: A list of interpolated points and normals
#     :rtype: tuple (list of om.MVector, list of om.MVector)
#     """
#     # Get selected vertices
#     selected_points = cmds.ls(selection=True, flatten=True)
#     if not selected_points:
#         raise ValueError("No points selected. Please select points in the scene.")

#     # Get positions of selected points
#     points_positions = []
#     for point in selected_points:
#         pos = cmds.xform(point, query=True, worldSpace=True, translation=True)
#         points_positions.append(om.MVector(pos[0], pos[1], pos[2]))

#     # Get start and end points from the selected points
#     start_vec = points_positions[0]  # First selected point
#     end_vec = points_positions[-1]   # Last selected point

#     # Call the function to interpolate points and normals
#     interpolated_points, interpolated_normals = find_points_and_normals(start_vec, end_vec, start_normal, end_normal, num_points)
    
#     return interpolated_points, interpolated_normals



def is_joint_in_skincluster(skincluster, joint):
    # Get all joints (influences) associated with the skinCluster
    influences = cmds.skinCluster(skincluster, query=True, influence=True)
    # Check if the specified joint is in the list of influences
    return joint in influences
COMPONENT_TYPE_MAP = {'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'}


def get_joint_influenced_points(skincluster, joint):
    # If the joint isn't in the skincluster, return None
    if not is_joint_in_skincluster(skincluster, joint): return None

    # Get all components influenced by the skinCluster
    geometry = cmds.skinCluster(skincluster, query=True, geometry=True)[0]
    
    COMPONENT_TYPE_MAP = {'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'}
    geo_type = cmds.objectType(geometry)
    if geo_type not in COMPONENT_TYPE_MAP.keys():
        # print(f'{__file__}:{lineno} in {function_name} - {message}')

        print(f'# Warning: Unsupported geometry type: {geo_type}. Please check your use of this function')
        return False
    component_type = COMPONENT_TYPE_MAP[geo_type]
    
    # ex: mesh f'{geometry}.vtx[0]' nurbs f'{geometry}.cv[0]' lattice f'{geometry}.pt[0]' 
    cmpnts = cmds.ls(f'{geometry}.{component_type}[*]', flatten=True)
    # if 
    if not cmpnts: return

    # Initialize lists for points and weights
    influenced_pts = []
    weights = []
    indices = []

    for cmpnt in cmpnts:
        if not cmds.objExists(cmpnt): continue  # Skip if the vertex doesn't exist
        between_bracket = re.search(r'\[(\d+)\]', cmpnt)
        indices.append((int(between_bracket.group(1))))
        

        # Get the weight for the specific joint on this vertex
        weight = cmds.skinPercent(skincluster, cmpnt, transform=joint, query=True)
        
        # If there's any weight, store the vertex and weight
        if weight > 0.0:
            influenced_pts.append(cmpnt)
            weights.append(weight)

    # Return the dictionary in the specified format
    return {'geometry': geometry, 'indices': indices, 'points': influenced_pts, 'weights': weights}
# ########################################## Usage example ###########################################
# skin_cluster = 'skinCluster10'  # Replace with your skinCluster name
# joint = 'RightArm'  # Replace with the joint you are checking
# result = get_joint_influenced_points(skin_cluster, joint)
# ####################################################################################################

def get_existing_joint_weight_data(joints, mesh_only=True):
    '''
    :param str joints: a list of joints to find weight data for
    :param bool mesh_only: If True skip any geometry that is not a mesh.
                           Meant to avoid finding weighting in things like lattices, curves, etc.

    :return: A dictionary of data related to weighting:
    ```
    # weight data map
    {
        joint1:  {'skincluster': {'geometry': geometry,       # dag node
                                  'indices': indices,         # the point indices, for MfnMesh
                                  'points': influenced_pts,   # geo.vtx[0], or .cv[0], or .pt[0]
                                  'weights': weights},         # weight value
                 'skincluster2': {'geometry': geometry, ...   # and so-on
        joint2: {...
    }
    :rtype: dict
    '''
    # mesh_only will check to see if at least one influencing geometries are meshes, if not, skip
    # mesh_only meant to avoid finding weighting in things like lattices, curves, etc.
    return_dict = {}
    all_skinclusters = cmds.ls(type='skinCluster')
    for joint in joints:
        influencing_skinclusters = []
        for skincluster in all_skinclusters:
            geometry = cmds.skinCluster(skincluster, query=True, geometry=True)[0]
            if not geometry:continue  # Skip if the skinCluster has no geometry
            
            # Skip if 'mesh_only' is set and the geometry is not a mesh
            if mesh_only and 'mesh' not in cmds.objectType(geometry):continue
            
            # Skip if the current joint does not influence this skinCluster
            if not is_joint_in_skincluster(skincluster, joint):continue
            
            # Get the points influenced by this joint and their weights
            point_weights = get_joint_influenced_points(skincluster, joint)
            if not point_weights['points']:continue  # Skip if there are no influenced points/weights
            
            # for key in point_weights:
            #     print(f'{key}: {point_weights[key]}')
            return_dict[joint] =  {f'{skincluster}': point_weights}
    return return_dict

def weight_data_between_joints(joint_start, joint_end, weight_data):
    '''
    :param str joint_start: where point weighting will start
    :param str joint_end: where point weighting will end
    :param dict weight_data: a dictionary created by func get_existing_joint_weight_data

    This is what weight data looks like:
    # weight_data
    {
        joint1:  {'skincluster': {'geometry': geometry,       # dag node
                                  'indices': indices,         # the point indices, for MfnMesh
                                  'points': influenced_pts,   # geo.vtx[0], or .cv[0], or .pt[0]
                                  'weights': weights},         # weight value
                 'skincluster2': {'geometry': geometry, ...   # and so-on
        joint2: {...
    }


    steps:                  
    create a directional vector between joint_start and joint_end
    create an infinite plane for both of these joints from the directional vector this looks like:
        plane start normal - joint_start aiming at joint_end
        plane end normal - joint_end aiming at joint_start
    as long as points fall between these two normals, they will remain in the dictionary,
    otherwise, they will be removed.
    # implementation
    begin looping through keys
        then loop through skinclusters
            from here, retrieve the geometry, create an MfnMesh (maya.api,OpenMaya)
                use my custom fuction get_dag_path like this: om.MFnMesh(get_dag_path(mesh))

                loop through the indicies, retrieve MfnMesh points from indicies, looks something like this:
                    mfn_mesh = om.MFnMesh(get_dag_path(mesh))
                    # Loop through each point in the mesh
                    for i, point in enumerate(vertex_array):
                        (do things here)

                    test whether points fall between the two infinite planes, if they do not, remove
                    them from the indicies, the points, the weights, move to 
    '''


# # Example usage
# start_normal = om.MVector(0, 0, 1)  # Start normal
# end_normal = om.MVector(0, 1, 0)    # End normal

# # Call the function with selected points in Maya
# interpolated_points, interpolated_normals = get_selected_points_and_normals(start_normal, end_normal, num_points=10)

# print("Interpolated Points:")
# for point in interpolated_points:
#     print(point)
    
# print("Interpolated Normals:")
# for normal in interpolated_normals:
#     print(normal)





def intersections_in_direction(mesh, point_from, point_to):
    # Create and normalize the direction vector
    raySource = om.MFloatPoint(point_from[0], point_from[1], point_from[2])
    rayDirection = om.MFloatVector(point_to[0], point_to[1], point_to[2])
    rayDirection.normalize()

    # Find all intersections between the ray and the mesh
    # NOTE: With all of the positional-only args, I am reminded that OpenMaya is a C++ library that
    # is wrapped for Python. For the sake of readability and debugging I have deviated from pep8
    # naming in favor of camel-case to match the method arg parameter names.
    mesh_fn = om.MFnMesh(get_dag_path(mesh))
    space = om.MSpace.kWorld
    maxParam = 10000.0
    test_both_directions = False
    tolerance = 1e-6  # Small tolerance for intersection calculations

    intersect= mesh_fn.allIntersections(raySource, # raySource - MFloatPoint (p-only arg)
                                        rayDirection, # rayDirection - MFloatVector (p-only arg)
                                        space, # space om.MSpace.kWorld (p-only arg)
                                        maxParam, # maxParam p-only arg
                                        test_both_directions, # testBothDirections p-arg only
                                        tolerance # Small tolerance (optional kwarg)
                                        )
    # Another pep8 naming deviation (just like my character count :D )
    # intersect could be returned at this point, but this self documents what is being returned...
    hitPoints, hitRayParams, hitFaces, hitTriangles, hitBary1s, hitBary2s = intersect
    return hitPoints, hitRayParams, hitFaces, hitTriangles, hitBary1s, hitBary2s

def point_inside_or_outside_normal(point, mesh_point, normal):
    # Convert the point and mesh_point to MVector objects
    point = om.MVector(point[0], point[1], point[2])
    mesh_point = om.MVector(mesh_point[0], mesh_point[1], mesh_point[2])
    normal = om.MVector(normal[0], normal[1], normal[2])
    
    # Calculate the directional vector from the point to the mesh point
    directional_vector = mesh_point - point  # mesh_point - point
    
    # Compute the dot product of the directional vector with the normal
    dot_prod = directional_vector * normal
    
    # Determine if the point is inside, outside, or on the surface
    if dot_prod > 0:
        return False  # Point is inside the mesh
    elif dot_prod < 0:
        return True  # Point is outside the mesh
    else:
        return False  # Point is exactly on the surface

def is_point_inside_mesh(point, mesh):
    """
    Determine if a point is inside or outside a mesh using ray casting.
    
    Args:
        point (tuple): The point in space (x, y, z) to test.
        mesh (MFnMesh): The MFnMesh object representing the mesh to test against.
        
    Returns:
        bool: True if the point is inside the mesh, False if outside.
    """
    # Convert point to MPoint object
    point = om.MPoint(point[0], point[1], point[2])
    
    # Create a ray origin and direction
    ray_origin = point  # The point to check
    ray_direction = om.MVector(1, 0, 0)  # Cast the ray in the positive x-direction (arbitrary choice)
    
    # Prepare the ray intersection detector
    intersection = om.MFloatArray()
    mesh_fn = om.MFnMesh(mesh)
    
    # Perform the ray intersection test
    hit_points = mesh_fn.allIntersections(ray_origin,
        ray_direction,
        om.MSpace.kWorld,
        9999, False, faceIds=None,
        triIds=None, idsSorted=False,
        accelParams=None, sortHits=False)
    
    # If the number of intersections is odd, the point is inside; if even, it's outside
    if len(hit_points) % 2 == 1:
        return True  # Inside
    else:
        return False  # Outside

def inside_points_between_bounds(mesh, axis, curve, axis_bounds_start, axis_bounds_end):
    # Finds all points that fall between two bounds on a specified axis.
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    # make the bounds a bit more agnostic just in case...
    lower_bound = min(axis_bounds_start[axis_index], axis_bounds_end[axis_index])
    upper_bound = max(axis_bounds_start[axis_index], axis_bounds_end[axis_index])
    start_vector = om.MVector(axis_bounds_start)
    # Get the mesh vertices in world space
    mfn_mesh = om.MFnMesh(get_dag_path(mesh))
    vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)
    
    # Initialize the result dictionary
    result = {'points': [], 'point_indices': [], 'point_on_curve_params': [],
              'point_normals': [], 'face_indices': [], 'normal_jnt_dot_products': [], }
    curve_fn = om.MFnNurbsCurve( get_dag_path(curve))


    # Initialize vertex iterator
    vertex_iter = om.MItMeshVertex(get_dag_path(mesh))
    
    # Loop through each point in the mesh
    for i, point in enumerate(vertex_array):
        # Check if the point falls within the bounds along the specified axis
        if lower_bound <= point[axis_index] <= upper_bound:
            point = om.MPoint(round(point.x, 3), round(point.y, 3), round(point.z, 3))
            normal = vertex_iter.getNormal() # vectorA of dot product
            dir_vector = start_vector-om.MVector(point) # vectorB of dot product
            point_on_curve, param = curve_fn.closestPoint(point, space=om.MSpace.kWorld)
            # inside = point_inside_or_outside_normal(point=point,
            #                                         mesh_point=point_on_curve, normal=normal)
            result['points'].append(point)
            result['point_indices'].append(i)
            result['point_on_curve_params'].append(param)
            result['point_normals'].append(normal)

            # face_indices
            connected_faces = vertex_iter.getConnectedFaces()
            [result['face_indices'].append(i) for i in connected_faces]

            # normal_jnt_dot_products
            result['normal_jnt_dot_products'].append(normal*dir_vector)
            # next
            vertex_iter.setIndex(i)



    # Return map
    # {'points', 'point_indices', 'point_normals',
    #  'face_indices', 'normal_jnt_dot_products'}

    return result
# Example usage:
# mesh = 'pCube1'  # Replace with your actual mesh name
# axis = 'x'
# axis_bounds_start = [-11.440300196409224, 122.78700000606477, -3.1314835883677006]
# axis_bounds_end = [-49.18710961937904, 122.78700000606483, -3.131483588367699]
# points_between_bounds = points_between_bounds(mesh, axis, axis_bounds_start, axis_bounds_end)
# print(points_between_bounds)



def get_point_bounding_box(maya_vertices):
    """
    Get the bounding box of a set of points using cmds.exactWorldBoundingBox and OpenMaya's MBoundingBox.

    Args:
        points (list): A list of point coordinates in the format [(x, y, z), ...].

    Returns:
        om.MBoundingBox: The bounding box containing all points.
    """
    # Get the exact world bounding box of the points using cmds
    
    min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(maya_vertices)

    min_point = om.MPoint(min_x, min_y, min_z)
    max_point = om.MPoint(max_x, max_y, max_z)
    print('MIN POINT : ', min_point)
    print('MAX POINT : ', max_point)

    # Create an MBoundingBox object using the min and max values
    bbox = om.MBoundingBox()
    bbox.expand(min_point)
    bbox.expand(max_point)
    
    # print('bbox.min : ',bbox.min)
    # print('bbox.max : ',bbox.max)
    # print('bbox.center : ',bbox.center)
    # print('bbox.depth : ',bbox.depth)
    # print('bbox.height : ',bbox.height)
    # print('bbox.width : ',bbox.width)
    return bbox


def select_limbs_from_points(points, mesh, limb_type='legs', debug=True):
    """
    Select vertices from either the arms or legs of a T-posed biped based on a dictionary of points and indices.
    Dynamically determines the bounds based on the provided points.

    Args:
        points (dict): A dictionary with point (x, y, z) tuples as keys and vertex indices as values.
        mesh_name (str): The name of the mesh in Maya.
        limb_type (str): Type of limb to select. Can be "legs" or "arms".

    Returns:
        None
    """
    
    # Clear current selection
    cmds.select(clear=True)

    # Get the bounding box of the points
    mfn_mesh = om.MFnMesh(get_dag_path(mesh))
    mesh_bounds = mfn_mesh.boundingBox
    
    
    
    named_vertices = [f'{mesh}.vtx[{idx}]' for idx in points.values()]
    print(len(points.keys()))

    bbox = get_point_bounding_box(named_vertices)


    if limb_type == 'legs':
        # Bottom half of the bounding box for legs
        y_range_min = bbox.min.y
        y_range_max = bbox.min.y + (bbox.max.y - bbox.min.y) * 0.5
        x_range_min = bbox.min.x * 0.5
        x_range_max = bbox.max.x * 0.5

    elif limb_type == 'arms':
        # Top half of the bounding box for arms
        y_range_max = (mesh_bounds.max.y)

        y_range_min = mesh_bounds.max.y * .5
        y_range_max = mesh_bounds.max.y
        x_range_min = bbox.min.x 
        x_range_max = bbox.max.x

    else:
        cmds.error("Invalid limb type. Choose either 'legs' or 'arms'.")

    # Create a new bounding box with the manipulated range
    modified_bbox = om.MBoundingBox(
        om.MPoint(x_range_min, y_range_min, bbox.min.z),
        om.MPoint(x_range_max, y_range_max, bbox.max.z)
    )
    cube_name = 'bounds_cube'
    if cmds.objExists(cube_name):
        cmds.delete(cube_name)
    if debug:
        width = modified_bbox.width
        height = modified_bbox.height
        depth = modified_bbox.depth

        # Create the poly cube with the correct dimensions
        cube_name = cmds.polyCube(w=width, h=height, d=depth, name='bounds_cube')[0]

        # Get the center of the bounding box
        bbox_center = modified_bbox.center

        # Move the cube to the center of the bounding box
        cmds.xform(cube_name, translation=(bbox_center.x, bbox_center.y, bbox_center.z))



    # Collect vertices to select based on the manipulated bounding box
    vertices_to_select = []
    for point, index in points.items():
        # Convert point to MPoint for bounding box check
        mpoint = om.MPoint(point[0], point[1], point[2])
        
        # Check if the point is inside the modified bounding box
        if modified_bbox.contains(mpoint):
            vertex_name = f'{mesh}.vtx[{index}]'
            vertices_to_select.append(vertex_name)

    # Select all matching vertices in one go for consistency
    if vertices_to_select:
        cmds.select(vertices_to_select)




# Example usage:
# Define points (e.g., a list of vertex positions from a mesh in world space)

# # Example usage:
# # Define points (e.g., a list of vertex positions from a mesh in world space)
# select_limbs_from_points(points, limb_type="legs")  # Select leg vertices
def closest_points_on_curve(curve, points):
    # Get the MObject for the curve
    curve_dag_path = get_dag_path(curve)
    curve_fn = om.MFnNurbsCurve(curve_dag_path)
    closest_points = []
    for point in points:
        # Find the closest point on the curve to this vertex position
        closest_points.append(curve_fn.closestPoint(point, space=om.MSpace.kWorld))
    return closest_points

def get_pnt_lists_vector_lengths(from_pts, to_pts):
    lengths = []
    for from_point, to_point in enumerate(from_pts, to_pts):
        print('FROM POINT',from_point)
        vector_from = om.MVector(from_point[0].x, from_point[0].y, from_point[0].z)
        vector_to = om.MVector(to_point[0], to_point[1], to_point[2])
        length_vector = vector_from-vector_to
        lengths.append(length_vector.length())
    return lengths

def sort_points_by_jnt_crv(joints, mesh,  curve):
    joint_data = sort_jnts_in_xy(joints)
    jnts = joint_data['sorted_joints']
    ordered_joint_positions = joint_data['ordered_joint_positions']
    axis_plane = joint_data['axis_plane']
    jnt_chain_dir = joint_data['joint_chain_direction']
    joint_param_dict = {jnt:idx for idx, jnt in enumerate(jnts)}
    bounds_dict={'axis': axis_plane,
                 'axis_bounds_start': ordered_joint_positions[0],
                 'axis_bounds_end': ordered_joint_positions[-1]}
    points_dict=dict()
    points_dict = inside_points_between_bounds(mesh=mesh, axis=axis_plane, curve=curve,
                                               axis_bounds_start=ordered_joint_positions[0],
                                               axis_bounds_end=ordered_joint_positions[-1],
                                               )
    # result map - points_dict
    # {'points', 'point_indices', 'point_normals',
    #  'face_indices', 'normal_jnt_dot_products'}


    mesh_points = [f'{mesh}.vtx[{idx}]' for idx in points_dict['point_indices']]
    mesh_faces = [f'{mesh}.f[{idx}]' for idx in points_dict['face_indices']]
    cmds.select(mesh_points)
    print(len(mesh_points))
    cmds.refresh()
    cmds.pause(sec=1)

    limb_type=''
    if 'x' in axis_plane:limb_type='arms'
    if 'y' in axis_plane:limb_type='legs'
    point_index_dict={}
    for key, value in zip(points_dict['points'], points_dict['point_indices']):
        # Convert the MPoint to a tuple of (x, y, z)
        point_tuple = (round(key.x, 4), round(key.y, 4), round(key.z, 4))
        point_index_dict[point_tuple] = value
    # print("POINTS DICT : ",points_dict['points'])
    # closest_pts = closest_points_on_curve(curve=curve, points=points_dict['points'])
    # vector_lengths = get_pnt_lists_vector_lengths(from_pts=closest_pts,
    #                                               to_pts=points_dict['points'])
    # average_length = statistics.mean(vector_lengths)
    # # statistics.mean(y_vals)  # = 20.11111111111111
    # print(f'Average Length : {average_length}')




    select_limbs_from_points(point_index_dict, mesh=mesh, limb_type='arms')  # Select leg vertices


    # print(points_dict['normal_jnt_dot_products'])

    
    # mfn_mesh = om.MFnMesh(get_dag_path(mesh))
    # vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)



def sort_limbs(joints):
    """
    Splits joints representing arms and legs into sorted lists for left and right arms and legs.
    
    Args:
        joints (list): List of joint names.
        
    Returns:
        tuple: (left_arm, right_arm, left_leg, right_leg), where each is a list of joints ordered 
               from root to end (e.g., shoulder to hand for arms, hip to foot for legs).
    """
    if not joints:
        return [], [], [], []
    
    # Separate joints into left and right based on X position, reversing logic
    left_joints = []
    right_joints = []
    
    for joint in joints:
        x_pos = cmds.xform(joint, q=True, ws=True, t=True)[0]
        # Positive X goes to right, negative X to left
        if x_pos < 0:
            right_joints.append(joint)
        else:
            left_joints.append(joint)
    
    # Calculate the median Y position to distinguish between arms and legs
    y_positions = [cmds.xform(joint, q=True, ws=True, t=True)[1] for joint in joints]
    median_y = sorted(y_positions)[len(y_positions) // 2]
    
    # Function to categorize and sort
    def sort(joint_list, is_arm):
        if is_arm:
            # Sort arms from highest to lowest Y
            return sorted(joint_list, key=lambda j: cmds.xform(j, q=True, ws=True,
                                                               t=True)[1], reverse=True)
        else:
            # Sort legs from highest to lowest Y
            return sorted(joint_list, key=lambda j: cmds.xform(j, q=True, ws=True,
                                                               t=True)[1], reverse=True)
    
    # Separate into arms and legs based on Y position
    l_arm = sort([j for j in left_joints if cmds.xform(j, q=True,ws=True,
                                                       t=True)[1] >= median_y], is_arm=True)
    l_leg = sort([j for j in left_joints if cmds.xform(j, q=True, ws=True,
                                                       t=True)[1] < median_y], is_arm=False)
    r_arm = sort([j for j in right_joints if cmds.xform(j, q=True, ws=True,
                                                        t=True)[1] >= median_y], is_arm=True)
    r_leg = sort([j for j in right_joints if cmds.xform(j, q=True, ws=True,
                                                        t=True)[1] < median_y], is_arm=False)
    
    limb_dict = {'left_arm':l_arm,
                 'right_arm':r_arm,
                 'left_leg':l_leg,
                 'right_leg':r_leg,
                }
    for limb in limb_dict:
        limb_dict[limb] = sort_jnts_bounds(limb_dict[limb])[0]

    print(json.dumps(limb_dict, indent=4))
    return limb_dict


def categorize_joints(joints):
    """
    Categorizes joints into center and limb joints, then further categorizes center joints into torso, neck, and head.
    
    Args:
        joints (list): List of joint names.
        
    Returns:
        dict: Dictionary containing lists of joints categorized as arms, legs, torso, neck, and head.
    """
    if not joints:
        return {
            'left_arm': [], 'right_arm': [], 
            'left_leg': [], 'right_leg': [], 
            'torso': [], 'neck': [], 'head': []
        }
    
    # Separate joints into center and limb joints based on X position proximity to center
    center_joints = []
    limb_joints = []
    
    for joint in joints:
        x_pos = cmds.xform(joint, q=True, ws=True, t=True)[0]
        if abs(x_pos) < 0.01:  # Threshold for "center"
            center_joints.append(joint)
        else:
            limb_joints.append(joint)
    
    # Step 1: Separate limbs into left and right arms and legs
    limb_dict = sort_limbs(limb_joints)
    
    # Step 2: Sort center joints by Y position (height) to determine torso, neck, and head
    center_joints_sorted = sorted(center_joints, key=lambda j: cmds.xform(j, q=True, ws=True, t=True)[1], reverse=True)
    
    torso = []
    neck = None
    head = None
    
    # Categorize center joints into torso, neck, and head
    for joint in center_joints_sorted:
        y_pos = cmds.xform(joint, q=True, ws=True, t=True)[1]
        
        if not neck and limb_dict['left_arm'] and limb_dict['right_arm']:
            # Check if this joint is the neck (first joint above the arms)
            arm_y_position = cmds.xform(limb_dict['left_arm'][0], q=True, ws=True, t=True)[1]
            if y_pos > arm_y_position:
                neck = joint
                continue
        
        if neck and not head:
            # If neck is defined, the next highest joint is the head
            head = joint
            continue
        
        # All other center joints are part of the torso
        torso.append(joint)
    
    # Compile and return the categorized dictionary
    categorized_joints = {
        'left_arm': limb_dict['left_arm'],
        'right_arm': limb_dict['right_arm'],
        'left_leg': limb_dict['left_leg'],
        'right_leg': limb_dict['right_leg'],
        'torso': torso,
        'neck': [neck] if neck else [],
        'head': [head] if head else []
    }
    
    # Output result in JSON format for clarity
    print(json.dumps(categorized_joints, indent=4))
    return categorized_joints

def create_crv_any(self, points, degree=3):
    num_cvs = len(points)
    required_knots = num_cvs + degree - 1
    knots = [i / (required_knots - 1) for i in range(required_knots)]
    curve = cmds.curve(p=points, k=knots, d=degree)
    cmds.rebuildCurve( curve, replaceOriginal=True,
                    #rebuildType=0, endKnots=1, keepControlPoints=False,
                    keepRange=0, keepEndPoints=False, keepTangents=0,
                    spans=6, degree=1, tolerance=0.01)
    return curve

def curve_from_joints(joints):
    joints = sort_jnts_bounds(joints)[0]
    points = []
    for jnt in joints:
        points.append(cmds.xform(jnt, query=True, translate=True))

def get_dag_path(object_name):
    # Utility function to get the DAG path of an object
    selection_list = om.MSelectionList()
    selection_list.add(object_name)
    dag_path = selection_list.getDagPath(0)
    return dag_path


def get_curve_side(curve_name, mesh_name):
    # Get bounding box of the curve
    curve_bbox = cmds.exactWorldBoundingBox(curve_name)
    curve_center_x = (curve_bbox[0] + curve_bbox[3]) / 2  # X-center of the curve bounding box
    
    # Get bounding box of the mesh
    mesh_bbox = cmds.exactWorldBoundingBox(mesh_name)
    mesh_center_x = (mesh_bbox[0] + mesh_bbox[3]) / 2  # X-center of the mesh bounding box

    # Determine side: If the curve center is to the left (-X) of the mesh center, it's on the left; else, right
    side = 'left' if curve_center_x < mesh_center_x else 'right'
    return side, curve_bbox

def find_points_within_bounds(curve_name, mesh_name):
    # Determine side and get the bounding box of the curve
    side, curve_bbox = get_curve_side(curve_name, mesh_name)

    # Set the X limit based on which side the curve is on
    x_limit = curve_bbox[0] if side == 'left' else curve_bbox[3]  # Use min X for left side, max X for right side

    # Get the mesh's DAG path and initialize an iterator for its vertices
    mesh_dag_path = get_dag_path(mesh_name)
    vertex_iter = om.MItMeshVertex(mesh_dag_path)

    within_bounds_indices = []

    # Iterate over each vertex in the mesh
    while not vertex_iter.isDone():
        # Get the vertex position in world space
        vertex_position = vertex_iter.position(om.MSpace.kWorld)

        # Check if the vertex is within the bounding box X limit
        if (side == 'left' and vertex_position.x >= x_limit) or (side == 'right' and vertex_position.x <= x_limit):
            within_bounds_indices.append(vertex_iter.index())  # Store the index if within bounds

        # Move to the next vertex
        vertex_iter.next()

    return within_bounds_indices

########################################## USAGE ##########################################
# curve_name = 'curve1'
# mesh_name = 'pSphere1'
# within_bounds_indices = find_points_within_bounds(curve_name, mesh_name)

# # Create a list to hold the vertex selection strings
# vertex_selection = []

# # Iterate through the returned indices and format them as vertex selection strings
# for index in within_bounds_indices:
#     vertex_selection.append(f'{mesh_name}.vtx[{index}]')

# # Select the vertices using cmds.select
# cmds.select(vertex_selection)

# # Output the selected vertices
# print("Selected vertices:", vertex_selection)
###########################################################################################

def closest_mesh_points_on_curve(curve_name, mesh_name):
    # Get the MObject for the curve
    curve_dag_path = get_dag_path(curve_name)
    curve_fn = om.MFnNurbsCurve(curve_dag_path)

    # Get the MObject for the mesh and create an iterator for its vertices
    mesh_dag_path = get_dag_path(mesh_name)
    vertex_iter = om.MItMeshVertex(mesh_dag_path)

    closest_points = {}

    # Iterate over each vertex in the mesh
    while not vertex_iter.isDone():
        # Get the vertex position
        vertex_position = vertex_iter.position(om.MSpace.kWorld)
        
        # Find the closest point on the curve to this vertex position
        closest_point = curve_fn.closestPoint(vertex_position, space=om.MSpace.kWorld)
        
        # Get the parameter at the closest point on the curve
        param = curve_fn.findParamFromPoint(closest_point, space=om.MSpace.kWorld)
        
        # Store the closest point and parameter for the vertex
        closest_points[vertex_iter.index()] = (closest_point, param)
        
        # Move to the next vertex
        vertex_iter.next()
    
    return closest_points

# # Example usage
# curve_name = 'nurbsCurve1'  # Replace with your curve's name
# mesh = 'mesh'    # Replace with your target point
# closest_point, param = closest_mesh_points_on_curve(curve_name, mesh)
# print(f"Closest point: {closest_point}")
# print(f"Parameter at closest point: {param}")

'''
Long Triangle Arrows
Black Right◅Pointing Pointer: ► (U+25BA)
Black Left◅Pointing Pointer: ◄ (U+25C4)
White Right◅Pointing Pointer: ▻ (U+25BB)
White Left◅Pointing Pointer: ◅ (U+25C5)
Filled and Open Triangle Arrows
Right◅Pointing Small Triangle: ▸ (U+25B8)
Left◅Pointing Small Triangle: ◂ (U+25C2)
Narrow Triangle Arrows
Right Triangle◅Headed Arrow: ⇾ (U+21FE)
Left Triangle◅Headed Arrow: ⇽ (U+21FD)
Vertical Triangle Arrows
Up◅Pointing Small Triangle: ▴ (U+25B4)
Down◅Pointing Small Triangle: ▾ (U+25BE)

'''

class WeightCurve:
    def __init__(self, mesh, joints, dir='-x'):

        self.mesh=mesh
        self.joints=joints
        self.dir=dir
        self.sort_joints()

    def get_side(self):
        self.sorted_joints[0]

    def sort_joints(self):
        '''
        sorts joints based on a direction
        -x dir is ◁○◁○◁○    
        +x dir is ▷○▷○▷○
        -y dir is ↓
        +y dir is ↑
        -z dir forward (depth negs)
        +z dir is backward (depth pos)
        diagonal or more complex directions aren't yet supported.
        '''
        self.sorted_joints = []

    def create_linear_curve_unnormalized(pts, name='linearCurve', parent=None):
        # creates a curve where each point is a numerical parameter starting with a 0 index
        # For example, a curve with seven points will have a 0-6 parameterization.
        if not pts or len(pts) < 2:
            raise ValueError("At least two points are required to create a linear curve.")
        curve = cmds.curve(d=1, p=pts, name=name)  
        if parent and cmds.objExists(parent):
            cmds.parent(curve, parent) 
        return curve

        # # Example usage
        # # Define seven points in 3D space for the curve
        # points = [
        #     (0, 0, 0),
        #     (1, 2, 0),
        #     (2, 4, 0),
        #     (3, 6, 0),
        #     (4, 8, 0),
        #     (5, 10, 0),
        #     (6, 12, 0)
        # ]

        # # Create the curve with a specified name and optional parent (None in this case)
        # curve_name = create_linear_curve(points, name='sevenPointCurve', parent=None)

