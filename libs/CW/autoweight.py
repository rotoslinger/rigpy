import json
import maya.cmds as cmds
import maya.api.OpenMaya as om

# TODO some of this code should be made more agnostic and moved to a new module called analyze shape
def analyze_and_sort_joints(joints):
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
    primary_axis = 'x' if x_length > y_length else 'y'
    axis_index = 0 if primary_axis == 'x' else 1

    # Determine the side if primary axis is X
    if primary_axis == 'x':
        avg_x_position = sum(x_positions) / len(x_positions)
        side = 'left' if avg_x_position < 0 else 'right'
        
        # Set sort order based on side
        if side == 'left':
            sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True, 
                                                                    ws=True, t=True)[axis_index],
                                                                    reverse=True)
            axis_direction = '-x'  # highest to lowest for left side
        else:
            sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True, 
                                                                    ws=True, t=True)[axis_index])
            axis_direction = '+x'  # lowest to highest for right side
    
    else:  # primary_axis == 'y'
        sorted_joints = sorted(joints, key=lambda j: cmds.xform(j, q=True,
                                                                ws=True, t=True)[axis_index],
                                                                reverse=True)
        axis_direction = '-y'  # always highest to lowest for Y axis

    return sorted_joints, primary_axis, axis_direction

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
        limb_dict[limb] = analyze_and_sort_joints(limb_dict[limb])[0]

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
    joints = analyze_and_sort_joints(joints)[0]
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
        
