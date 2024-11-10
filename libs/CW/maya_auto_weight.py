import json
import maya.cmds as cmds
import maya.api.OpenMaya as om






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

    # cube_name = 'bounds_cube'
    # if cmds.objExists(cube_name):
    #     cmds.delete(cube_name)

    # width = max_x - min_x  # X-axis difference (length)
    # height = max_y - min_y  # Y-axis difference (width)
    # depth = max_z - min_z  # Z-axis difference (height)
    # print('width : ', width)
    # print('height : ', height)
    # print('depth : ', depth)

    # # Create the poly cube with the correct dimensions
    # cube_name = cmds.polyCube(w=width, h=height, d=depth, name='bounds_cube')[0]

    # # Get the center of the bounding box
    # bbox_center = bbox.center

    # # Move the cube to the center of the bounding box
    # cmds.xform(cube_name, translation=(bbox_center.x, bbox_center.y, bbox_center.z))


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

def sort_points_by_jnt_crv(joints, mesh,  curve):
    joint_data = sort_jnts_in_xy(joints)
    jnts = joint_data['sorted_joints']
    ordered_joint_positions = joint_data['ordered_joint_positions']
    axis_plane = joint_data['axis_plane']
    jnt_chain_dir = joint_data['joint_chain_direction']
    joint_param_dict = {jnt:idx for idx, jnt in enumerate(jnts)}
    # print('jnts : ', jnts)
    # print('ordered_joint_positions : ', ordered_joint_positions)
    # print('axis_plane : ', axis_plane)
    # print('joint_chain_direction : ', jnt_chain_dir)
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
    print(points_dict['points'])


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

