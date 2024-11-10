import maya.cmds as cmds
import maya.api.OpenMaya as om
from itertools import product

def chunk_mesh_bounding_box(mesh_name, chunk_count, chunk_direction='vertical', debug=False):
    """
    Subdivide a mesh's bounding box into even chunks, either vertically or horizontally, and collect points inside each chunk.

    Args:
        mesh_name (str): The name of the mesh to chunk.
        chunk_count (int): The number of chunks to create. If odd, 1 will be added to make it even.
        chunk_direction (str): Direction of chunking, either 'vertical' or 'horizontal'. Default is 'vertical'.
        debug (bool): If True, creates poly cubes representing the bounding box chunks.

    Returns:
        dict: A dictionary with chunk details including the points inside each chunk.
    """

    # Ensure chunk_count is an even number
    if chunk_count < 2:
        cmds.error("chunk_count cannot be less than 2.")
    if chunk_count % 2 != 0:
        chunk_count += 1  # Make chunk_count even if it is odd
    
    # Get the exact world bounding box of the mesh
    min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(mesh_name)
    
    # Calculate width, height, and depth based on Maya's axes
    width = max_x - min_x  # X-axis difference (length)
    height = max_y - min_y  # Y-axis difference (width)
    depth = max_z - min_z  # Z-axis difference (height)

    # Determine the chunk size and the axis to subdivide based on the direction
    chunk_size = None
    if chunk_direction == 'vertical':  # Subdivide along X-axis (height)
        chunk_size = width / chunk_count
    elif chunk_direction == 'horizontal':  # Subdivide along Y-axis (width)
        chunk_size = height / chunk_count
    else:
        cmds.error("Invalid chunk_direction. Must be 'vertical' or 'horizontal'.")
    
    # Create the list to store bounding boxes of the chunks
    chunk_bboxes = []
    chunk_details = {}

    # Create a Mesh function set to access mesh geometry
    selection_list = om.MSelectionList()
    selection_list.add(mesh_name)
    mesh_dag_path = selection_list.getDagPath(0)
    mfn_mesh = om.MFnMesh(mesh_dag_path)

    # Iterate over chunks
    for index in range(chunk_count):
        # Calculate the min and max for each chunk based on its position
        if chunk_direction == 'vertical':  # Vertical chunking, divide by X-axis
            chunk_min_x = min_x + index * chunk_size
            chunk_max_x = chunk_min_x + chunk_size
            chunk_min_y = min_y
            chunk_max_y = max_y
            chunk_min_z = min_z
            chunk_max_z = max_z
        elif chunk_direction == 'horizontal':  # Horizontal chunking, divide by Y-axis
            chunk_min_x = min_x
            chunk_max_x = max_x
            chunk_min_y = min_y + index * chunk_size
            chunk_max_y = chunk_min_y + chunk_size
            chunk_min_z = min_z
            chunk_max_z = max_z
        
        # Create an empty bounding box
        chunk_bbox = om.MBoundingBox()
        
        # Expand the bounding box using the min and max points
        chunk_bbox.expand(om.MPoint(chunk_min_x, chunk_min_y, chunk_min_z))
        chunk_bbox.expand(om.MPoint(chunk_max_x, chunk_max_y, chunk_max_z))
        
        chunk_bboxes.append(chunk_bbox)
        
        # In debug mode, create poly cubes to represent each chunk
        chunk_name = f'chunk{index:02}'
        if cmds.objExists(chunk_name): cmds.delete(chunk_name)

        if debug:
            cube = cmds.polyCube(w=chunk_bbox.width, h=chunk_bbox.height, d=chunk_bbox.depth, name=chunk_name)[0]
            cmds.move(chunk_bbox.center.x, chunk_bbox.center.y, chunk_bbox.center.z, cube)
            cmds.setAttr(f"{cube}.overrideEnabled", 1)
            cmds.setAttr(f"{cube}.overrideColor", 17)  # Optional: set color for debug (green)

        # Create point_index dictionary for points within this chunk
        point_index = {}
        maya_verts = []
        points = []
        # Get mesh vertices and iterate through them
        mfn_mesh.getPoints(om.MSpace.kWorld)
        vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)

        for idx, point in enumerate(vertex_array):
            points.append((round(point.x, 4), round(point.x, 4), round(point.x, 4)))
            point_position = point
            point_x, point_y, point_z = point_position.x, point_position.y, point_position.z

            # Check if the point lies within the chunk's bounding box using inside() method
            point = om.MPoint(point_x, point_y, point_z)
            if chunk_bbox.contains(point):
                # Add the vertex index and its Maya vertex string
                point_index[idx] = point
                maya_verts.append(f"{mesh_name}.vtx[{idx}]")

        # Create dictionary entry for the chunk details
        chunk_details[f'chunk{index:02}'] = {
            'chunk_direction': chunk_direction,
            'points': points,
            'indices': list(point_index.keys()),  # Using indices as integer values
            'maya_verts': maya_verts  # Maya vertex selection strings
        }

    return chunk_details


'''
chunk_dict = chunk_mesh_bounding_box('full_body', chunk_count=4, chunk_direction='vertical', debug=True)
print(chunk_dict)
'''
import maya.cmds as cmds
import maya.api.OpenMaya as om

def subdivide_by_chunk(mesh_name, num_vertical_chunks, num_horizontal_chunks, vertical=True, horizontal=False, reverse_vertical_chunks=True, debug=False):
    """
    Subdivide a mesh's bounding box into even chunks, either vertically or horizontally, or both to create a grid of chunks.
    
    Args:
        mesh_name (str): The name of the mesh to chunk.
        num_vertical_chunks (int): The number of vertical chunks.
        num_horizontal_chunks (int): The number of horizontal chunks.
        vertical (bool): If True, chunk along the vertical (X-axis).
        horizontal (bool): If True, chunk along the horizontal (Y-axis).
        debug (bool): If True, creates poly cubes representing the bounding box chunks.
    
    Returns:
        dict: A dictionary with chunk details including the points inside each chunk.
    """
    # Ensure both num_vertical_chunks and num_horizontal_chunks are even numbers
    if num_vertical_chunks < 2 or num_horizontal_chunks < 2:
        cmds.error("num_vertical_chunks and num_horizontal_chunks cannot be less than 2.")
    if num_vertical_chunks % 2 != 0:
        num_vertical_chunks += 1  # Make num_vertical_chunks even if it is odd
    if num_horizontal_chunks % 2 != 0:
        num_horizontal_chunks += 1  # Make num_horizontal_chunks even if it is odd

    # Get the exact world bounding box of the mesh
    min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(mesh_name)
    
    # Calculate width, height, and depth based on Maya's axes
    width = max_x - min_x  # X-axis difference (length)
    height = max_y - min_y  # Y-axis difference (width)
    depth = max_z - min_z  # Z-axis difference (height)

    # Determine the chunk sizes based on vertical and horizontal parameters
    chunk_size_vertical = width / num_vertical_chunks if vertical else None
    chunk_size_horizontal = height / num_horizontal_chunks if horizontal else None

    # Create the list to store bounding boxes of the chunks
    chunk_details = {}

    # Create a Mesh function set to access mesh geometry
    selection_list = om.MSelectionList()
    selection_list.add(mesh_name)
    mesh_dag_path = selection_list.getDagPath(0)
    mfn_mesh = om.MFnMesh(mesh_dag_path)

    # Iterate over chunks
    chunk_index = 0
    for v_index, h_index in product(range(num_vertical_chunks), range(num_horizontal_chunks)):
        # Calculate the min and max for each chunk based on its position
        chunk_min_x = min_x + (v_index * chunk_size_vertical if vertical else 0)
        chunk_max_x = chunk_min_x + (chunk_size_vertical if vertical else width)
        chunk_min_y = min_y + (h_index * chunk_size_horizontal if horizontal else 0)
        chunk_max_y = chunk_min_y + (chunk_size_horizontal if horizontal else height)
        chunk_min_z = min_z
        chunk_max_z = max_z

        # Initialize a new bounding box for the current chunk
        chunk_bbox = om.MBoundingBox()
        chunk_bbox.expand(om.MPoint(chunk_min_x, chunk_min_y, chunk_min_z))
        chunk_bbox.expand(om.MPoint(chunk_max_x, chunk_max_y, chunk_max_z))
        
        # In debug mode, create poly cubes to represent each chunk
        chunk_name = f'chunk{chunk_index:02}'
        if cmds.objExists(chunk_name): cmds.delete(chunk_name)

        if debug:
            cube = cmds.polyCube(w=chunk_bbox.width, h=chunk_bbox.height,
                                d=chunk_bbox.depth, name=chunk_name)[0]
            cmds.move(chunk_bbox.center.x, chunk_bbox.center.y, chunk_bbox.center.z, cube)
            cmds.setAttr(f"{cube}.overrideEnabled", 1)
            cmds.setAttr(f"{cube}.overrideColor", 17)  # Optional: set color for debug (green)

        # Create point_index dictionary for points within this chunk
        point_index = {}
        maya_verts = []
        points = []

        # Get mesh vertices and iterate through them
        vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)

        for idx, point in enumerate(vertex_array):
            point_position = om.MPoint(point.x, point.y, point.z)

            # Check if the point lies within the chunk's bounding box
            if chunk_bbox.contains(point_position):
                points.append((round(point.x, 4), round(point.y, 4), round(point.z, 4)))
                point_index[idx] = point
                maya_verts.append(f"{mesh_name}.vtx[{idx}]")

        # Only add chunks that contain points
        if point_index:
            # Create dictionary entry for the chunk details
            chunk_details[f'chunk{chunk_index:02}'] = {
                'chunk_center_x': chunk_bbox.center.x,
                'points': points,
                'indices': list(point_index.keys()),  # Using indices as integer values
                'maya_verts': maya_verts  # Maya vertex selection strings
            }

        chunk_index += 1

    # Create the mirrored chunks dictionary
    mirrored_chunks = {'left': {}, 'right': {}}

    for chunk_name, chunk_info in chunk_details.items():
        # Assign chunks to 'left' or 'right' based on the chunk's center X coordinate
        if chunk_info['chunk_center_x'] > 0:  # Positive X direction (left)
            mirrored_chunks['left'][chunk_name] = chunk_info
        else:  # Negative X direction (right)
            mirrored_chunks['right'][chunk_name] = chunk_info
    print('working')
    # Sort the chunks by their X-center values
    mirrored_chunks['left'] = {k: v for k, v in sorted(mirrored_chunks['left'].items(),
                                                       key=lambda item: item[1]['chunk_center_x'],
                                                       reverse=reverse_vertical_chunks)}
    mirrored_chunks['right'] = {k: v for k, v in sorted(mirrored_chunks['right'].items(),
                                                        key=lambda item: item[1]['chunk_center_x'],
                                                        reverse=not reverse_vertical_chunks)}

    return chunk_details, mirrored_chunks
########################################## Usage example ###########################################
# from importlib import reload
# from CW import voxel_based_analysis
# reload(voxel_based_analysis)
# import time
# num_vert_chunk=34
# mirrored_chunk_dict = voxel_based_analysis.subdivide_by_chunk('full_body',
#                                                               num_vertical_chunks=num_vert_chunk,
#                                                               num_horizontal_chunks=2,
#                                                               vertical=True,
#                                                               horizontal=False,
#                                                               reverse_vertical_chunks=True,
#                                                               debug=False)[1]
# iter_id=0
# max_iter=num_vert_chunk
# high = 30
# low = max_iter-high
# cmds.select(cl=True)
# print('finding arms...')
# for key_left, key_right in zip(mirrored_chunk_dict['left'], mirrored_chunk_dict['right']):
#     if iter_id > high-low:
#         continue
#     print('...')
#     cmds.select(mirrored_chunk_dict['left'][key_left]['maya_verts'], add=True)
#     cmds.select(mirrored_chunk_dict['right'][key_right]['maya_verts'], add=True)
#     cmds.refresh()
#     iter_id+=1
#     time.sleep(.05)
# print('intersected body...')
# cmds.refresh()
# time.sleep(1)
# cmds.select(cl=True)
# mirrored_chunk_dict = voxel_based_analysis.subdivide_by_chunk('full_body',
#                                                               num_vertical_chunks=24,
#                                                               num_horizontal_chunks=2,
#                                                               vertical=True,
#                                                               horizontal=False,
#                                                               reverse_vertical_chunks=False,
#                                                               debug=False)[1]
# print('finding body...')
# iter_id=0
# for key_left, key_right in zip(mirrored_chunk_dict['left'], mirrored_chunk_dict['right']):
#     if iter_id > low:
#         continue
#     print('...')

#     cmds.select(mirrored_chunk_dict['left'][key_left]['maya_verts'], add=True)
#     cmds.select(mirrored_chunk_dict['right'][key_right]['maya_verts'], add=True)
#     cmds.refresh()
#     iter_id+=1
#     time.sleep(.05)
####################################################################################################

'''

# def subdivide_by_chunk(mesh_name, num_vertical_chunks, num_horizontal_chunks, vertical=True, horizontal=False, debug=False):
#     """
#     Subdivide a mesh's bounding box into even chunks, either vertically or horizontally, or both to create a grid of chunks.
    
#     Args:
#         mesh_name (str): The name of the mesh to chunk.
#         num_vertical_chunks (int): The number of vertical chunks.
#         num_horizontal_chunks (int): The number of horizontal chunks.
#         vertical (bool): If True, chunk along the vertical (X-axis).
#         horizontal (bool): If True, chunk along the horizontal (Y-axis).
#         debug (bool): If True, creates poly cubes representing the bounding box chunks.
    
#     Returns:
#         dict: A dictionary with chunk details including the points inside each chunk.
#     """
#     # Ensure both num_vertical_chunks and num_horizontal_chunks are even numbers
#     if num_vertical_chunks < 2 or num_horizontal_chunks < 2:
#         cmds.error("num_vertical_chunks and num_horizontal_chunks cannot be less than 2.")
#     if num_vertical_chunks % 2 != 0:
#         num_vertical_chunks += 1  # Make num_vertical_chunks even if it is odd
#     if num_horizontal_chunks % 2 != 0:
#         num_horizontal_chunks += 1  # Make num_horizontal_chunks even if it is odd

#     # Get the exact world bounding box of the mesh
#     min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(mesh_name)
    
#     # Calculate width, height, and depth based on Maya's axes
#     width = max_x - min_x  # X-axis difference (length)
#     height = max_y - min_y  # Y-axis difference (width)
#     depth = max_z - min_z  # Z-axis difference (height)

#     # Determine the chunk sizes based on vertical and horizontal parameters
#     chunk_size_vertical = width / num_vertical_chunks if vertical else None
#     chunk_size_horizontal = height / num_horizontal_chunks if horizontal else None

#     # Create the list to store bounding boxes of the chunks
#     chunk_bboxes = []
#     chunk_details = {}

#     # Create a Mesh function set to access mesh geometry
#     selection_list = om.MSelectionList()
#     selection_list.add(mesh_name)
#     mesh_dag_path = selection_list.getDagPath(0)
#     mfn_mesh = om.MFnMesh(mesh_dag_path)

#     # Iterate over chunks
#     chunk_index = 0
#     for v_index in range(num_vertical_chunks):
#         for h_index in range(num_horizontal_chunks):
#             # Calculate the min and max for each chunk based on its position
#             chunk_min_x = min_x + (v_index * chunk_size_vertical if vertical else 0)
#             chunk_max_x = chunk_min_x + (chunk_size_vertical if vertical else width)
#             chunk_min_y = min_y + (h_index * chunk_size_horizontal if horizontal else 0)
#             chunk_max_y = chunk_min_y + (chunk_size_horizontal if horizontal else height)
#             chunk_min_z = min_z
#             chunk_max_z = max_z

#             # Create an empty bounding box
#             chunk_bbox = om.MBoundingBox()
            
#             # Expand the bounding box using the min and max points
#             chunk_bbox.expand(om.MPoint(chunk_min_x, chunk_min_y, chunk_min_z))
#             chunk_bbox.expand(om.MPoint(chunk_max_x, chunk_max_y, chunk_max_z))
            
#             chunk_bboxes.append(chunk_bbox)
            
#             # In debug mode, create poly cubes to represent each chunk
#             chunk_name = f'chunk{chunk_index:02}'
#             if cmds.objExists(chunk_name): cmds.delete(chunk_name)

#             if debug:
#                 cube = cmds.polyCube(w=chunk_bbox.width, h=chunk_bbox.height, d=chunk_bbox.depth, name=chunk_name)[0]
#                 cmds.move(chunk_bbox.center.x, chunk_bbox.center.y, chunk_bbox.center.z, cube)
#                 cmds.setAttr(f"{cube}.overrideEnabled", 1)
#                 cmds.setAttr(f"{cube}.overrideColor", 17)  # Optional: set color for debug (green)

#             # Create point_index dictionary for points within this chunk
#             point_index = {}
#             maya_verts = []
#             points = []
#             # Get mesh vertices and iterate through them
#             mfn_mesh.getPoints(om.MSpace.kWorld)
#             vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)

#             for idx, point in enumerate(vertex_array):
#                 points.append((round(point.x, 4), round(point.y, 4), round(point.z, 4)))
#                 point_position = point
#                 point_x, point_y, point_z = point_position.x, point_position.y, point_position.z

#                 # Check if the point lies within the chunk's bounding box using inside() method
#                 point = om.MPoint(point_x, point_y, point_z)
#                 if chunk_bbox.contains(point):
#                     # Add the vertex index and its Maya vertex string
#                     point_index[idx] = point
#                     maya_verts.append(f"{mesh_name}.vtx[{idx}]")

#             # Create dictionary entry for the chunk details
#             chunk_details[f'chunk{chunk_index:02}'] = {
#                 'chunk_direction': {'vertical': vertical, 'horizontal': horizontal},
#                 'points': points,
#                 'indices': list(point_index.keys()),  # Using indices as integer values
#                 'maya_verts': maya_verts  # Maya vertex selection strings
#             }

#             chunk_index += 1

#     return chunk_details

# def voxel_mesh_mirrored(mesh_name, num_vertical_chunks, num_horizontal_chunks, vertical=True, horizontal=False, debug=False):
#     """
#     Subdivide a mesh's bounding box into even chunks, either vertically or horizontally, or both to create a grid of chunks.
    
#     Args:
#         mesh_name (str): The name of the mesh to chunk.
#         num_vertical_chunks (int): The number of vertical chunks.
#         num_horizontal_chunks (int): The number of horizontal chunks.
#         vertical (bool): If True, chunk along the vertical (X-axis).
#         horizontal (bool): If True, chunk along the horizontal (Y-axis).
#         debug (bool): If True, creates poly cubes representing the bounding box chunks.
    
#     Returns:
#         dict: A dictionary with chunk details including the points inside each chunk.
#     """
#     # Ensure both num_vertical_chunks and num_horizontal_chunks are even numbers
#     if num_vertical_chunks < 2 or num_horizontal_chunks < 2:
#         cmds.error("num_vertical_chunks and num_horizontal_chunks cannot be less than 2.")
#     if num_vertical_chunks % 2 != 0:
#         num_vertical_chunks += 1  # Make num_vertical_chunks even if it is odd
#     if num_horizontal_chunks % 2 != 0:
#         num_horizontal_chunks += 1  # Make num_horizontal_chunks even if it is odd

#     # Get the exact world bounding box of the mesh
#     min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(mesh_name)
    
#     # Calculate width, height, and depth based on Maya's axes
#     width = max_x - min_x  # X-axis difference (length)
#     height = max_y - min_y  # Y-axis difference (width)
#     depth = max_z - min_z  # Z-axis difference (height)

#     # Determine the chunk sizes based on vertical and horizontal parameters
#     chunk_size_vertical = width / num_vertical_chunks if vertical else None
#     chunk_size_horizontal = height / num_horizontal_chunks if horizontal else None

#     # Create the list to store bounding boxes of the chunks
#     chunk_bboxes = []
#     chunk_details = {}

#     # Create a Mesh function set to access mesh geometry
#     selection_list = om.MSelectionList()
#     selection_list.add(mesh_name)
#     mesh_dag_path = selection_list.getDagPath(0)
#     mfn_mesh = om.MFnMesh(mesh_dag_path)

#     # Iterate over chunks
#     chunk_index = 0
#     for v_index in range(num_vertical_chunks):
#         for h_index in range(num_horizontal_chunks):
#             # Calculate the min and max for each chunk based on its position
#             chunk_min_x = min_x + (v_index * chunk_size_vertical if vertical else 0)
#             chunk_max_x = chunk_min_x + (chunk_size_vertical if vertical else width)
#             chunk_min_y = min_y + (h_index * chunk_size_horizontal if horizontal else 0)
#             chunk_max_y = chunk_min_y + (chunk_size_horizontal if horizontal else height)
#             chunk_min_z = min_z
#             chunk_max_z = max_z

#             # Create an empty bounding box
#             chunk_bbox = om.MBoundingBox()
            
#             # Expand the bounding box using the min and max points
#             chunk_bbox.expand(om.MPoint(chunk_min_x, chunk_min_y, chunk_min_z))
#             chunk_bbox.expand(om.MPoint(chunk_max_x, chunk_max_y, chunk_max_z))
            
#             chunk_bboxes.append(chunk_bbox)
            
#             # In debug mode, create poly cubes to represent each chunk
#             chunk_name = f'chunk{chunk_index:02}'
#             if cmds.objExists(chunk_name): cmds.delete(chunk_name)

#             if debug:
#                 cube = cmds.polyCube(w=chunk_bbox.width, h=chunk_bbox.height, d=chunk_bbox.depth, name=chunk_name)[0]
#                 cmds.move(chunk_bbox.center.x, chunk_bbox.center.y, chunk_bbox.center.z, cube)
#                 cmds.setAttr(f"{cube}.overrideEnabled", 1)
#                 cmds.setAttr(f"{cube}.overrideColor", 17)  # Optional: set color for debug (green)

#             # Create point_index dictionary for points within this chunk
#             point_index = {}
#             maya_verts = []
#             points = []
#             # Get mesh vertices and iterate through them
#             mfn_mesh.getPoints(om.MSpace.kWorld)
#             vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)

#             for idx, point in enumerate(vertex_array):
#                 points.append((round(point.x, 4), round(point.y, 4), round(point.z, 4)))
#                 point_position = point
#                 point_x, point_y, point_z = point_position.x, point_position.y, point_position.z

#                 # Check if the point lies within the chunk's bounding box using inside() method
#                 point = om.MPoint(point_x, point_y, point_z)
#                 if chunk_bbox.contains(point):
#                     # Add the vertex index and its Maya vertex string
#                     point_index[idx] = point
#                     maya_verts.append(f"{mesh_name}.vtx[{idx}]")

#             # Only add chunks that contain points
#             if point_index:
#                 # Create dictionary entry for the chunk details
#                 chunk_details[f'chunk{chunk_index:02}'] = {
#                     'chunk_direction': {'vertical': vertical, 'horizontal': horizontal},
#                     'points': points,
#                     'indices': list(point_index.keys()),  # Using indices as integer values
#                     'maya_verts': maya_verts  # Maya vertex selection strings
#                 }

#             chunk_index += 1

#     # Create the mirrored chunks dictionary
#     mirrored_chunks = {'left': {}, 'right': {}}

    
#     for chunk_name, chunk_info in chunk_details.items():
#         # Get the chunk center (X, Y, Z)
#         chunk_center = chunk_info['chunk_direction']
#         chunk_center_x = chunk_center['vertical'] * (chunk_bbox.center.x if vertical else 0) + (chunk_bbox.center.x if horizontal else 0)
        
#         if chunk_center_x > 0:  # Positive X direction (left)
#             mirrored_chunks['left'][chunk_name] = chunk_info
#         else:  # Negative X direction (right)
#             mirrored_chunks['right'][chunk_name] = chunk_info

#     # Sort the chunks by their X-center values
#     mirrored_chunks['left'] = {k: v for k, v in sorted(mirrored_chunks['left'].items(), key=lambda item: item[1]['chunk_direction']['vertical'], reverse=False)}
#     mirrored_chunks['right'] = {k: v for k, v in sorted(mirrored_chunks['right'].items(), key=lambda item: item[1]['chunk_direction']['vertical'], reverse=True)}

#     return chunk_details, mirrored_chunks


# '''
# chunk_dict, mirrored_dict = chunk_mesh_bounding_box('full_body', num_vertical_chunks=4, num_horizontal_chunks=3, vertical=True, horizontal=True, debug=True)
# print(chunk_dict)
# print(mirrored_dict)
# '''
