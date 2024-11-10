import maya.cmds as cmds
import maya.api.OpenMaya as om

r'''
Note on the term shapes:
In this writing the term *shapes will be used to describe both 2-d and 3-d shapes, whether
anomalous clouds of volume, polygonal faces, points, sparse voxel octrees, solids, or any other
kind of agnostic data that can be used to describe shape and form.

Note on the term loco-pedal:
Loco-pedal will be used as a general term to describe moving creatures. While it isn't a formal
term it is derived from the Latin words 'loco' meaning 'place', and "pedalis" meaning 'of the foot'.
While this writing focuses on biped and quadruped mesh analysis, it may be possible to use similar
analyses on other types creature as long as they have a somewhat distinguishable torso, and
n-number of appendages (within reason).

The scope of this writing will not cover facial shape analysis, or finger digit analysis, only
head, torso, arm, hand, leg, and foot disambiguation.

vertical, horizontal, and depth based segmenting of meshes, points, or shapes of any kind can help
to narrow down and isolate volumes.

As some of the code provided can work on ambiguous point clouds data, much greater fine tuning is
possible with surfaces. Ray intersections that take face normals into account will also be covered.
From this data you can find points points on the surface, but you can distinguish whether a point is
inside of a mesh. This can be crucial when attempting to place a joint, or pivot point inside of a
mesh, as mammals pivot from the inside out during self driven movement.


To give a bit of background, there are many ways to procedurally analyze shapes for automatic
recognition. Thankfully we have many rules, as well as some assumptions:
1. Analysis can be focused on searching for loco-pedal creatures.
2. Loco-pedal creatures, are assumed to be somewhat symmetrical.
3. Bipedal and quadrupedal creatures can be distinguished by their torso bounds and appendage
   direction. In more detail:
   a. Bipedal creatures have a torso that is vertical
   b. Bipedal arms, being in t-pose, run along the x translation axis
   c. Quadrupedal torsos are horizontal.
   d. Quadrupedal torso depth can be assumed to be longer than it is tall
   e. Quadrupeds will have 4 branching volumes going in the -y direction.
   f. Quadrupeds appendage bounding boxes will usually have a greater height than either width
      or depth
3. Bipedal creatures must be in t-pose.
    a. Their arms are horizontal, and legs vertical
    b. Legs/arms are assumed to be longer than they are thick
    c. Torso, like a leg, is vertical. Confusion with a leg can be avoided by considering several
       factors:
       i. Torso is usually thicker than either leg.
       ii. Torso has a center volume that crosses the y/z plane (points falling in both -x, +x 
           regions)
       iii. An infinite ray running along the x axis will intersect the torso 2 times, legs will
            be intersected 4 times. Torso cross-section see diagram below:
            key:
            ray          = --->
            intersection = *
                                     Biped Torso
                                       -x | +x
                                          |     
                                     _____|_____
                                    |     |     |
                                    |     |     |
                                    |_____|_____|
                            ________|_____|_____|__________
                            ________      |     |__________
                                    |     |     |
                                    |     |     |
            infinite ray in x ---->*|--------->*|---->
                                    |     |     |
                                    |_____|_____|
                                    |  |     |  |
                                    |  |     |  |
            infinite ray in x ---->*| *|--->*| *|--->
3. Quadrupedal creatures will have 4 appendages. Their center 
    These appendages can be  have a bounding box that is
   usually taller than it is thick.
3. We can assume that appendages will be longer than their thickness
4. We can assume that appendages will be 
4. We can assume that torso, or 'trunk' is wider than legs

The first step to organic, pedal creature recognition
                            biped
                        _____________
                        |           |
                        |           |
                ________|___________|__________
                ________            |__________
                        |           |
                        |           |
infinite ray in x ---->*|--------->*|---->
                        |           |
                        |  _______  |
                        |  |     |  |
                        |  |     |  |
infinite ray in x ---->*| *|--->*| *|--->





'''












class MeshAnalyzer:
    def __init__(self, mesh_name):
        # Persistent attributes to store results across methods
        self.sorted_vertices = None
        self.mesh = mesh_name
        self.primary_axis = None
        self.axis_direction = None
        self.limb_dict = None
        self.categorized_vertices = None
        self.vertex_positions = None
        self.all_vertices = None

    def get_mesh_vertices(self):
        """
        Retrieves vertex positions and indices from the given mesh.
        
        Args:
            mesh_name (str): The name of the mesh to retrieve vertices from.
        
        Returns:
            dict: A dictionary where keys are the vertex indices and values are the MPoint positions in world space.
        """
        # Ensure the mesh exists in the scene
        if not cmds.objExists(self.mesh):
            raise RuntimeError(f"Mesh object '{self.mesh}' does not exist in the scene.")
        
        # Create a selection list and add the mesh to it
        sel = om.MSelectionList()
        sel.add(mesh_name)

        # Get the DAG path for the mesh
        dag_path = sel.getDagPath(0)

        # Create the MFnMesh function set to access the mesh data
        mfn_mesh = om.MFnMesh(dag_path)

        # Get all vertex positions (in world space) directly from getPoints
        vertex_array = mfn_mesh.getPoints(space=om.MSpace.kWorld)

        # Create a dictionary where keys are vertex indices and values are MPoint objects
        vertex_dict = {i: vertex_array[i] for i in range(len(vertex_array))}

        return vertex_dict

    def analyze_and_sort_vertices(self):
        """
        Analyze a cloud of vertices to determine if it is longer along the X or Y axis.
        Sorts the vertices based on the primary axis and determines the axis direction.

        Args:
            vertices (list): List of vertex positions.

        Returns:
            tuple: (sorted_vertices, primary_axis, axis_direction), where:
                - sorted_vertices (list): List of vertices ordered by position along the primary axis.
                - primary_axis (str): The primary axis ('x' or 'y') based on the longest dimension.
                - axis_direction (str): Direction ('+' or '-') based on the orientation of the sorted vertices.
        """
        if not self.vertex_positions:
            return [], None, None

        # Extract X and Y positions from the vertex positions dictionary
        x_positions = [v[0] for v in self.vertex_positions.values()]
        y_positions = [v[1] for v in self.vertex_positions.values()]

        # Calculate the lengths along X and Y axes
        x_length = max(x_positions) - min(x_positions)
        y_length = max(y_positions) - min(y_positions)

        # Determine the primary axis (the axis with the greatest length)
        primary_axis = 'x' if x_length > y_length else 'y'
        axis_index = 0 if primary_axis == 'x' else 1

        # Sorting based on the primary axis
        if primary_axis == 'x':
            avg_x_position = sum(x_positions) / len(x_positions)
            side = 'left' if avg_x_position < 0 else 'right'

            # Sort vertices by the X position
            sorted_vertices = sorted(self.vertex_positions.items(), key=lambda item: item[1][axis_index], reverse=(side == 'left'))
            axis_direction = '-x' if side == 'left' else '+x'
        else:
            # Sort vertices by the Y position
            sorted_vertices = sorted(self.vertex_positions.items(), key=lambda item: item[1][axis_index], reverse=True)
            axis_direction = '-y'

        # Extract the sorted indices
        sorted_indices = [item[0] for item in sorted_vertices]
        sorted_vertex_positions = [item[1] for item in sorted_vertices]
        # Store the sorted result and axis direction
        self.sorted_vertices = sorted_indices
        self.primary_axis = primary_axis
        self.axis_direction = axis_direction

        sorted_points = {'verts':sorted_vertex_positions,
                         'indices':sorted_indices}

        return sorted_points, primary_axis, axis_direction

    def sort_limbs(self):
        """
        Splits vertices representing arms and legs into sorted lists for left and right sides.

        Args:
            vertices (list): List of vertex positions.

        Returns:
            dict: Dictionary with lists of vertices ordered for 'left_arm', 'right_arm', 'left_leg', 'right_leg'.
        """
        if not self.vertex_positions:
            return {'left_arm': [], 'right_arm': [], 'left_leg': [], 'right_leg': []}

        # Split vertices into left and right based on X position
        left_vertices = [i for i, v in self.vertex_positions.items() if v[0] < 0]
        right_vertices = [i for i, v in self.vertex_positions.items() if v[0] >= 0]

        # Sort vertices by Y position
        y_positions = [v[1] for v in self.vertex_positions.values()]
        median_y = sorted(y_positions)[len(y_positions) // 2]

        def sort(vertex_list, is_arm):
            return sorted(vertex_list, key=lambda i: self.vertex_positions[i][1], reverse=True)

        # Sort limbs based on Y positions
        l_arm = sort([i for i in left_vertices if self.vertex_positions[i][1] >= median_y], is_arm=True)
        l_leg = sort([i for i in left_vertices if self.vertex_positions[i][1] < median_y], is_arm=False)
        r_arm = sort([i for i in right_vertices if self.vertex_positions[i][1] >= median_y], is_arm=True)
        r_leg = sort([i for i in right_vertices if self.vertex_positions[i][1] < median_y], is_arm=False)

        # Create the dictionary with sorted limbs
        limb_dict = {
            'left_arm': l_arm,
            'right_arm': r_arm,
            'left_leg': l_leg,
            'right_leg': r_leg
        }

        # Analyze and sort each limb further if needed
        for limb in limb_dict:
            limb_dict[limb] = self.analyze_and_sort_vertices()[0]

        self.limb_dict = limb_dict

        return limb_dict

    def categorize_vertices(self):
        """
        Categorizes vertices into left and right based on their X position.
        Also categorizes center vertices into torso, neck, and head.

        Args:
            mesh_name (str): Name of the mesh to analyze.

        Returns:
            dict: Dictionary containing categorized vertices for left_arm, right_arm, left_leg,
                right_leg, torso, neck, and head, each with indices and positions.
        """
        # Get all vertex positions (in world space)
        self.all_vertices = self.get_mesh_vertices()
        self.vertex_positions = {i: (v.x, v.y, v.z) for i, v in self.all_vertices.items()}

        # Categorizing vertices into left and right based on their X position
        left_vertices = [i for i, v in self.all_vertices.items() if v.x < 0]
        right_vertices = [i for i, v in self.all_vertices.items() if v.x >= 0]

        # Create a dictionary with the categorized vertices
        categorized_vertices = {
            'left': left_vertices,
            'right': right_vertices
        }

        # Sort and categorize limbs (arms and legs)
        self.sort_limbs()
        # Categorizing center vertices into torso, neck, and head
        center_vertices = [v for i, v in self.all_vertices.items() if abs(v.x) < 0.01]
        center_vertices_sorted = sorted(center_vertices, key=lambda v: v.y, reverse=True)

        torso, neck, head = [], None, None


        # REFERENCE: limb dict map
        # limb_dict[limb] = {'verts':sorted_vertex_positions,
        #                    'indices':sorted_indices}
        arm_y_position = self.limb_dict['left_arm']['verts'][0][1] if self.limb_dict['left_arm'] else 0

        for v in center_vertices_sorted:
            if not neck and self.limb_dict['left_arm'] and self.limb_dict['right_arm'] and v.y > arm_y_position:
                neck = v
            elif neck and not head:
                head = v
            else:
                torso.append(v)

        tmp_vertex_positions = [self.vertex_positions[i] for i in self.vertex_positions]
        print("tmp_vertex_positions : ", tmp_vertex_positions)

        print("self.vertex_positions : ", self.vertex_positions)
        # print("self.vertex_positions : ", self.vertex_positions)
        torso = [(t.x, t.y, t.z) for t in torso]
        torso = [(t.x, t.y, t.z) for t in torso]
        print("TORSO : ", torso)

        categorized_vertices.update({
            'left_arm': {
                'point_positions': [self.vertex_positions[i] for i in self.limb_dict['left_arm']['indices']],  # Use indices to get positions
                'point_index': self.limb_dict['left_arm']['indices']
            },
            'right_arm': {
                'point_positions': [self.vertex_positions[i] for i in self.limb_dict['right_arm']['indices']],
                'point_index': self.limb_dict['right_arm']['indices']
            },
            'left_leg': {
                'point_positions': [self.vertex_positions[i] for i in self.limb_dict['left_leg']['indices']],
                'point_index': self.limb_dict['left_leg']['indices']
            },
            'right_leg': {
                'point_positions': [self.vertex_positions[i] for i in self.limb_dict['right_leg']['indices']],
                'point_index': self.limb_dict['right_leg']['indices']
            },
            'torso': {
                'point_positions': [self.vertex_positions[i] for i in torso],
                'point_index': torso
            },
            'neck': {
                'point_positions': [self.vertex_positions[i] for i in [self.vertex_positions.index(neck)]] if neck else [],
                'point_index': [self.vertex_positions.index(neck)] if neck else []
            },
            'head': {
                'point_positions': [self.vertex_positions[i] for i in [self.vertex_positions.index(head)]] if head else [],
                'point_index': [self.vertex_positions.index(head)] if head else []
            }
        }
        )

        self.categorized_vertices = categorized_vertices

    def select_vertices(self, body_part):
        """
        Select vertices based on the specified body part.

        Args:
            mesh_name (str): Name of the mesh.
            body_part (str): The body part to select (e.g., 'left_arm', 'torso').
        """
        # Select vertices based on body part
        if body_part not in self.categorized_vertices:
            print(f"Body part {body_part} not found.")
            return

        body_part_data = self.categorized_vertices[body_part]
        vertex_indices = body_part_data['point_index']

        if vertex_indices:
            selection = [f'{self.mesh_name}.vtx[{idx}]' for idx in vertex_indices]
            cmds.select(selection, replace=True)
        else:
            print(f"No vertices found for {body_part}.")


mesh_name = 'jsh_base_body_geo'

# Create an instance of MeshAnalyzer
mesh_analysis = MeshAnalyzer(mesh_name=mesh_name)

# Categorize vertices
mesh_analysis.categorize_vertices()

# Access categorized vertices
print('Categorized Vertices:', mesh_analysis.categorized_vertices)

# Example: Select vertices for the left arm
left_arm_indices = mesh_analysis.categorized_vertices['left_arm']['indices']
cmds.select([f'{mesh_name}.vtx[{idx}]' for idx in left_arm_indices], replace=True)

# Example: Select vertices for the torso
torso_indices = mesh_analysis.categorized_vertices['torso']['indices']
cmds.select([f'{mesh_name}.vtx[{idx}]' for idx in torso_indices], replace=True)

# Example: Print positions for left arm and torso
left_arm_positions = mesh_analysis.categorized_vertices['left_arm']['positions']
torso_positions = mesh_analysis.categorized_vertices['torso']['positions']

print('Left Arm Positions:', left_arm_positions)
print('Torso Positions:', torso_positions)
