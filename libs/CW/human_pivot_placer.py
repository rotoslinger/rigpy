import maya.api.OpenMaya as om
import maya.cmds as cmds

def snap_joint_to_nearest_point_on_surface(mesh_name, joint_name):
    """
    Snaps a joint to the nearest point on the mesh surface using OpenMaya 2.0.

    Args:
        joint_name (str): The name of the joint to move.
        mesh_name (str): The name of the mesh to find the nearest point on its surface.
    """
    # Get the position of the joint using cmds.xform and convert it to an MPoint
    joint_position_tuple = cmds.xform(joint_name, query=True, worldSpace=True, translation=True)
    joint_position = om.MPoint(joint_position_tuple[0], joint_position_tuple[1], joint_position_tuple[2])

    # Get the selection list for the mesh
    selection_list = om.MSelectionList()
    selection_list.add(mesh_name)

    # Get the MObject for the mesh
    mesh_obj = selection_list.getDagPath(0)
    print('before')

    # Create MFnMesh for the mesh
    mesh_fn = om.MFnMesh(mesh_obj)

    print('after')
    # Use getClosestPoint to find the closest point on the mesh's surface

    closest_point, face_id = mesh_fn.getClosestPoint(joint_position, om.MSpace.kWorld)

    from_vec = om.MVector(joint_position)
    to_vec = om.MVector(closest_point)
    

    print(f"Snapped {joint_name} to closest point on surface at {closest_point}") 

def average_normal(normals):
    # Initialize a zero vector to store the sum of the normals
    sum_normal = om.MFloatVector(0.0, 0.0, 0.0)

    # Sum all the normals in the list
    for normal in normals:
        sum_normal += normal

    # Normalize the resulting vector to get the average normal
    normalized_normal = sum_normal.normal()  # Normalize the vector
    
    # Convert MFloatVector to MVector
    average_normal = om.MVector(normalized_normal)

    return average_normal


def snap_joint_to_nearest_point_on_surface(mesh_name, joint_name):
    """
    Snaps a joint to the nearest point on the mesh surface using OpenMaya 2.0.
    Finds all intersections from the joint to the mesh and calculates an average intersection point.
    Then, adjusts the joint position based on mesh volume.

    Args:
        joint_name (str): The name of the joint to move.
        mesh_name (str): The name of the mesh to find the nearest point on its surface.
    """
    # Get the position of the joint using cmds.xform and convert it to an MPoint
    joint_position_tuple = cmds.xform(joint_name, query=True, worldSpace=True, translation=True)
    joint_position = om.MPoint(joint_position_tuple[0], joint_position_tuple[1], joint_position_tuple[2])

    # Convert MPoint to MFloatPoint
    joint_position_float = om.MFloatPoint(joint_position.x, joint_position.y, joint_position.z)

    # Get the selection list for the mesh
    selection_list = om.MSelectionList()
    selection_list.add(mesh_name)

    # Get the MObject for the mesh
    mesh_obj = selection_list.getDagPath(0)

    # Create MFnMesh for the mesh
    mesh_fn = om.MFnMesh(mesh_obj)

    # Use getClosestPoint to find the closest point on the mesh's surface
    closest_point, face_id = mesh_fn.getClosestPoint(joint_position, om.MSpace.kWorld)

    # Define the ray source (joint position) and ray direction (from joint to closest point)
    ray_direction = om.MVector(closest_point - joint_position)

    # Convert MVector to MFloatVector
    ray_direction_float = om.MFloatVector(ray_direction.x, ray_direction.y, ray_direction.z)

    # Max distance to check (can be a larger value depending on the mesh size)
    max_param = 1000.0
    test_both_directions = False
    tolerance = 1e-6  # Small tolerance for intersection calculations

    # Find all intersections between the ray and the mesh
    hit_points, hit_ray_params, hit_faces, hit_triangles, hit_bary1s, hit_bary2s = mesh_fn.allIntersections(
        joint_position_float,          # raySource (converted to MFloatPoint)
        ray_direction_float,           # rayDirection (converted to MFloatVector)
        om.MSpace.kWorld,              # space (world space)
        max_param,                     # maxParam
        test_both_directions,          # testBothDirections
        tolerance=tolerance            # tolerance (optional)
    )

    if hit_points:
        # Calculate the average of all hit points
        total_hit = len(hit_points)
        average_point = om.MPoint(0, 0, 0)

        for hit in hit_points:
            # Convert MFloatPoint to MPoint for addition
            average_point += om.MPoint(hit.x, hit.y, hit.z)

        average_point /= total_hit

        # Convert the average point to an MVector before setting the joint's translation
        average_point_vector = om.MVector(average_point.x, average_point.y, average_point.z)

        cmds.xform(joint_name, worldSpace=True, translation=(average_point.x, average_point.y, average_point.z))


        # Using the average_point, send a ray out in the y, -y get first intersection for both axes. then average the two points. move the joint to the center
        # then do the same for z, -z 
        # do several iterations to make sure the joint is well and truly centered.

        # and the z, -z, get the first intersection for


        # Using the average_point, send a ray out in the y, -y and the z, -z, get the first intersection

        # Move the joint to the average point

        selection_list = om.MSelectionList()
        selection_list.add(joint_name)



        # # Get the MObject for the mesh
        # joint_fn = selection_list.getDagPath(0)

        # joint_fn = om.MFnTransform(selection_list.getDagPath(0))
        # joint_fn.setTranslation(average_point_vector, om.MSpace.kWorld)

        # print(f"Snapped joint {joint_name} to average point {average_point}")

        # Now, adjust the joint based on surface normals in Z and Y directions

        # print(hit_faces)

        # for i in range(len(hit_faces)):
        #     # Get the normal of the hit face
        #     face_normal = mesh_fn.getFaceVertexNormals(hit_faces[i], om.MSpace.kWorld)
        #     normal_vector = average_normal(face_normal)
        #     print('FACE NORMAL ', normal_vector)

        #     # We use the face normal to adjust the joint's position based on Z and Y axes
        #     # normal_vector = om.MVector(face_normal)

        #     # Move joint to center of the mesh volume by adjusting with normals in Z and Y
        #     joint_position += normal_vector * 0.1  # Adjust with a small factor, modify as needed
        #     cmds.xform(joint_name, worldSpace=True, translation=(joint_position.x, joint_position.y, joint_position.z))

        # Convert the adjusted joint position to an MVector and set it
        # joint_fn.setTranslation(joint_position, om.MSpace.kWorld)
        # print(f"Adjusted joint {joint_name} to mesh volume center.")
    else:
        print("No intersections found.")


def test_intersections_in_direction(joint, mesh_fn, joint_position_float, direction = (0,1,0)):
        direction = om.MFloatVector(direction, direction, direction)
        # inverse_direction = om.MFloatVector(-1*direction[0], -1*direction[1], -1*direction[2])
        max_param = 10000.0
        test_both_directions = False
        tolerance = 1e-6  # Small tolerance for intersection calculations

        hit_points, hit_ray_params, hit_faces, hit_triangles, hit_bary1s, hit_bary2s = mesh_fn.allIntersections(
        joint_position_float,           # raySource (converted to MFloatPoint)
        direction,                     # rayDirection (converted to MFloatVector)
        om.MSpace.kWorld,              # space (world space)
        max_param,                     # maxParam
        True,                          # testBothDirections
        tolerance=tolerance            # tolerance (optional)
        )

        total_hit = len(hit_points)
        average_point = om.MPoint(0, 0, 0)

        for hit in hit_points:
            # Convert MFloatPoint to MPoint for addition
            average_point += om.MPoint(hit.x, hit.y, hit.z)

        average_point /= total_hit

        average_point_vector = om.MVector(average_point.x, average_point.y, average_point.z)

        cmds.xform(joint, worldSpace=True, translation=(average_point.x, average_point.y, average_point.z))
