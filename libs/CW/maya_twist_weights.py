import re, time, math, json, textwrap, itertools, statistics
import sys
import os

from typing import List, Tuple, Union

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim

COMPONENT_TYPE_MAP = {'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'}

class Weights:
    def __init__(self,
                 object_names: str ='',
                 skin_cluster: str='',
                 joints: list[str]= ['']):
        """
        :param object_name: The object to set the skin weights for
        :param skin_cluster: The skin cluster node affecting the object
        :param joints: The list of joints to assign weights to
        """
        self.object_names = object_names
        self.skin_cluster = skin_cluster
        self.joints = joints

    def get_dag_path(self, object_name: str) -> om.MDagPath:
        """
        :param object_name: Name of the object
        :return: MDagPath of the object
        Utility function to get the DAG path of an object.
        """
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        dag_path = selection_list.getDagPath(0)
        return dag_path
    
    def set_skin_weights(self):
        # TODO: Look at CW.skinweights_example.py for OpenMaya implementation
        self.sort_by_hier_dist(self.joints)
        skin_data = self.get_existing_joint_weight_data(self.joints)
        format_key = lambda key: (' ' * (len(key) + 3))
        print(self.debug_dict(skin_data))

    def debug_dict(self, data, indent=0, visited=None, single_line_keys=True):
        """
        Debug and inspect dictionaries with nested structure.

        :param dict data: The dictionary to debug.
        :param int indent: Current indentation level.
        :param set visited: Tracks visited objects to prevent circular references.
        :param bool single_line_keys: If True, print nested keys on the same line until the final value.
        """
        visited = visited or set()  # Initialize visited set if None
        if id(data) in visited:
            print(f"{' ' * indent}... (circular reference detected)")
            return
        visited.add(id(data))

        for key, value in data.items():
            if isinstance(value, dict):
                if single_line_keys:
                    print(f"{{{key}: ", end="")
                    self.debug_dict(value, indent + len(key) + 4, visited, single_line_keys)
                else:
                    print(f"{' ' * indent}{{{key}:")
                    self.debug_dict(value, indent + len(key) + 4, visited, single_line_keys)
                    print(f"{' ' * indent}}}")
            else:
                if single_line_keys:
                    if list(data.keys()).index(key) == 0:
                        print(f"  {key}: {value}")

                    # Final key-value pair aligned with indentation
                    else:
                        print(f"{' ' * indent}{key}: {value}")
                else:
                    print(f"{' ' * indent}{{{key}: {value}}}")

    def is_joint_in_skincluster(self, skincluster, joint):
        # Get all joints (influences) associated with the skinCluster
        influences = cmds.skinCluster(skincluster, query=True, influence=True)
        # Check if the specified joint is in the list of influences
        return joint in influences

    def get_joint_influenced_points(self, skincluster, joint):
        # If the joint isn't in the skincluster, return None
        if not self.is_joint_in_skincluster(skincluster, joint): return None

        # Get all components influenced by the skinCluster
        geometry = cmds.skinCluster(skincluster, query=True, geometry=True)[0]
        
        COMPONENT_TYPE_MAP = {'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'}
        geo_type = cmds.objectType(geometry)
        if geo_type not in COMPONENT_TYPE_MAP.keys():
            print(textwrap.dedent(f'''\# Warning: Unsupported geometry type: {geo_type}.
            # Please check your use of this function'''))
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
        return {'geometry': geometry,
                'indices': indices,
                'points': influenced_pts,
                'weights': weights}
    # ########################################## Usage example ###########################################
    # skin_cluster = 'skinCluster10'  # Replace with your skinCluster name
    # joint = 'RightArm'  # Replace with the joint you are checking
    # result = get_joint_influenced_points(skin_cluster, joint)
    # ####################################################################################################

    def get_existing_joint_weight_data(self, joints, mesh_only=True):
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
                if not self.is_joint_in_skincluster(skincluster, joint):continue
                
                # Get the points influenced by this joint and their weights
                point_weights = self.get_joint_influenced_points(skincluster, joint)
                if not point_weights['points']:continue  # Skip if there are no influenced points/weights
                # influencing_skinclusters.append(skincluster)
                # for key in point_weights:
                #     print(f'{key}: {point_weights[key]}')
                return_dict[joint] =  {f'{skincluster}': point_weights}

        return return_dict

    def sort_by_hier_dist(self, xforms:str, parent_check=True):
        """
        Classify joints and sort them by distance to the start joint in descending order.
        :param list joint_names: List of Maya joint names.
        :return: A tuple with:
            - Dict of start, mid, and end joints.
            - Dict of all joints sorted by distance to start.
        :rtype: tuple(dict, dict)
        """
        start = ''
        # assumes xforms are hierarchal, and part of the same chain.
        # if the parent is not in the joints, it is the start.
        # all other xforms must be descendants of start.
        if parent_check:
            for xform in xforms:
                parent = cmds.listRelatives(xform, parent=True)
                if not parent in xforms:
                    start=xform
                    break
            # make sure the start is at the start of the lsit
            xforms.remove(start)
            xforms.insert(0, start)
        # Assuming self.get_xform_as_mvector is a method to get the position of a joint as an MVector
        xform_vectors = [self.get_xform_as_mvector(joint) for joint in xforms]
        
        # Assume the first joint is the start
        start_joint = xforms[0]
        s_vec = xform_vectors[0]

        # Calculate distances from the start joint
        distances = [ (xf, (s_vec - v).length())for xf, v in zip(xforms[1:], xform_vectors[1:])]

        # NOTE: dict sorting lambda pattern
        # a_list = [('a', 3), ('b', 1), ('c', 2)]
        # s_list = sorted(a_list, key=lambda x: x[1])
        # output : [('b', 1), ('c', 2), ('a', 3)]

        # Sort joints by distance to start (ascending order)
        sorted_joints = [start_joint] + [xf for xf, _ in sorted(distances, key=lambda x: x[1])]

        # get start end pairs for linear blends between xforms ex: [(1, 2), (2, 3), (3, 4), (4, 5)]
        pairs = [(sorted_joints[i], sorted_joints[i+1]) for i in range(len(sorted_joints) - 1)]

        # print('distances : ', distances)
        # print(pairs)
        # print(sorted_joints)
        self.joints=sorted_joints
        return sorted_joints

    def find_mid_in_appendage(self, xforms):
        # a helper the find the middle joint in an arm or a leg.
        # must be given an upper arm, lower arm, and end joint using any
        # there can be any number of joints between, assumes they don't
        # have children. Combinations must be a pattern similar to one 
        # of the following:
        # leg, knee, foot || arm, elbow, hand
        # Finds the one joint that has both a parent and a child in the joint chain
        # great for twist joints.
        middle = ''
        for xform in xforms:
            parent = cmds.listRelatives(xform, parent=True)
            children = cmds.listRelatives(xform, children=True)
            # if not parent in joint_names:
            #     continue
            if parent:
                parent = [p for p in parent if p in xforms]
            if children:
                children = [c for c in children if c in xforms]
            if parent and children:
                middle = xform
        print('middle : ', middle)

    def get_xform_as_mpoint(self, object_name:str)->om.MPoint:
        """
        Retrieve the translation of an object as an MVector.
        Do not loop: non-performant for vertex lists, should only be used for debugging
        """
        return om.MPoint(cmds.xform(object_name, query=True, translation=True, worldSpace=True))

    def get_xform_as_mvector(self, object_name: str) -> om.MVector:
        """
        Retrieve the translation of an object as an MVector.
        Do not loop: non-performant for vertex lists, should only be used for debugging
        :return: MVector of the object's translation
        """
        return om.MVector(cmds.xform(object_name, query=True, translation=True, worldSpace=True))

    def project_point_to_plane(self, point, plane_center, plane_normal):
        '''
        Projects a point vector onto an infinite plane defined by two vectors
        Use this point to get a normalized directional vector from the source point.

        :param om.MVector from_plane: Must be normalized. The source plane direction.
        :param om.MVector to_plane: The target plane transform.
        :param om.MVector point: the vector being projected, the normalized direction
        :return: The projected point as an MVector.
        :rtype: om.MVector

        Move the point to the plane center then remove any perpendicular deviation with dot product
        Steps:
        1. find the vector from the source point to the plane center.
        2. if there is any perpendicular to that movement, remove by subtracting the
           dot_product * plane_normal from the point
        3. projected point = point-(dotProd·planeDir)
        4. Get the projected vector's reflection direction by subtracting it from the source point.
        5. Normalize the direction
        '''
        point_to_plane = point - plane_center #-------------------1.
        dot_product = point_to_plane * plane_normal #-------------2.
        projected_point = point - dot_product * plane_normal #----3.
        directional_vector = point - projected_point #------------4.
        directional_vector.normalize() #--------------------------5.

        return projected_point,  directional_vector
    
    
    def points_between_startend(self,
                                point_indices:list[int],
                                point_vectors:list[om.MVector],
                                start_point:om.MVector,
                                end_point:om.MVector,
                                ) -> tuple[list[int], list[str]]:
        """
        :param list[int] point_indices: List of point names from Maya.    
        :param list[om.MVector] point_indices: List of point names from Maya.
        :param om.MVector start_point: Starting point in world space.
        :param om.MVector to_point: Ending point in world space.
        :return: return_points, return_indices
        :rtype: list[int], list[str]
        """
        # Calculate the direction of the from_plane to the to_plane
        direction = end_point - start_point
        
        # Normalize the direction to get the plane's normal
        direction.normalize()

        vector_from = end_point - start_point
        vector_from.normalize()
        vector_to = start_point - end_point
        vector_to.normalize()

        # important to return as a pair these are both of these have to match in order! 
        return_indices = []
        return_point_vectors = []
        
        for idx, point in zip(point_indices, point_vectors):
            # direction of the start point in relation to the start & end infinite planes
            direction_start = self.project_point_to_plane(point, start_point, direction)[1]
            # Dot product to determine whether outside of the start_point plane
            dot_product_start = direction_start * vector_from

            # direction of the end point in relation to the start & end infinite planes
            direction_end = self.project_point_to_plane(point, end_point, direction)[1]
            # Dot product to determine whether outside of the end_point plane
            dot_product_end = direction_end * vector_to

            # to avoid near 0 values
            dot_product_start = round(dot_product_start, 1)
            dot_product_end = round(dot_product_end, 1)

            # if the point is between, both of the dot products will either 1.0 or .9999
            # if either are below 0 they are not between
            # if they are 0 they are on a plane, technically not between, but we will treat them as such
            if dot_product_start >= 0 and dot_product_end >= 0:
                return_indices.append(idx)
                return_point_vectors.append(point)

            # XXX: FOR DEBUG ONLY, this will cause a massive speed bottleneck! MAKE SURE TO DELETE
            # print(f'The projected dot product of {point} from_plane : ', dot_product_from)
            # print('The projected dot product of point_01 to_plane : ', dot_product_to)
            # XXX: FOR DEBUG ONLY, this will cause a massive speed bottleneck! MAKE SURE TO DELETE

        # Send it back to maya.cmd form
        # maya_point_objects = [f'{maya_object}.{component_type}[{idx}]' for idx in return_indices]
        return return_indices, return_point_vectors

    def mix_values_between(self, point_vectors, start_point, end_point,
                           # If given get the difference (from_inherit_wts-to_wts)
                           start_inherit_wts: bool | list[float]=False,
                           # If given get the difference (to_inherit_wts-from_wts)
                           end_inherit_wts: bool | list[float]=False, 
                           decimal_place: int | bool=5):
        start_weights=[]
        end_weights=[]

        total_length = (start_point-end_point).length()


        plane_srt_center = start_point
        plane_srt_normal = end_point - start_point
        plane_srt_normal.normalize()


        for point in point_vectors:
            proj_p_srt = self.project_point_to_plane(point, plane_srt_center, plane_srt_normal)[0]
            # possible TODO
            # should we worry about dividing by 0, or rounding the weight values?
            # cmds.skinPercent(weights, pruneWeights=0.0001) could be fine to handle rounding...
            srt_pnt_length = (point-proj_p_srt).length()
            start_weights.append(srt_pnt_length/total_length)

        end_weights = [1-wt for wt in start_weights]

        if decimal_place and type(decimal_place) == int :
            # points can drift when world movement is 5 or more figures.
            # rounding, in combination with maya.cmds.skinWeights flags pruneWeights & normalize
            # can help to avoid these issues.
            start_weights = [round(sw, decimal_place) for sw in start_weights]
            end_weights = [round(ew, decimal_place) for ew in end_weights]

        return start_weights, end_weights


    def debug_project_point_to_plane(self, obj_to_project, start_obj, end_obj):
        point_vector = self.get_xform_as_mvector(obj_to_project)
        start_vector = self.get_xform_as_mvector(start_obj)
        end_vector = self.get_xform_as_mvector(end_obj)
        
        plane_center = start_vector
        plane_normal = end_vector - start_vector
        plane_normal.normalize()

        projected_point =self.project_point_to_plane(point_vector, plane_center, plane_normal)[0]


        self.debug_rotation_from_vectors(source_object=start_obj, target_object=end_obj)
        self.debug_rotation_from_vectors(source_object=end_obj, target_object=start_obj)

        cmds.xform(obj_to_project, worldSpace=True,
                   translation=(projected_point.x,
                                projected_point.y,
                                projected_point.z))


    def debug_rotation_from_vectors(self, source_object, target_object):
        """
        Calculates and applies the rotation to the source object to aim at the target object.
        
        :param str source_object: The object that will be rotated.
        :param str target_object: The object that the source object will aim at.
        """
        # Get the positions of the source and target objects
        source_position = self.get_xform_as_mvector(source_object)
        target_position = self.get_xform_as_mvector(target_object)
        
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
        cmds.xform(source_object, rotation=(math.degrees(euler_rotation[0]),
                                            math.degrees(euler_rotation[1]),
                                            math.degrees(euler_rotation[2])), worldSpace=True)

    
    def create_debug_prim(self, name, cube_or_sphere=True, position=(0, 0, 0)):
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
    
    def create_debug_plane(self, name, position):
        # Create the polyplane
        if not cmds.objExists(name):
            name = cmds.polyPlane(name=name, width=5, height=5, subdivisionsX=1, subdivisionsY=1, axis=[1,0,0])[0]

            # Move the plane to the source position
            cmds.xform(name, worldSpace=True, translation=(position))

            # Turn on the normal display for visualizing the face normal
            cmds.polyOptions(name, displayNormal=True)
            cmds.select(name)
            cmds.ToggleFaceNormalDisplay(name)

    
    def create_debug_objs(self,):
        point_01 = self.create_debug_prim("point_01", cube_or_sphere=False, position=(5, 2, 0))  # Example, can be replaced by pSphere creation
        point_02 = self.create_debug_prim("point_02", cube_or_sphere=False, position=(15, 0, 0))

        from_plane = "plane_from"
        to_plane = "plane_to"
        
        self.create_debug_plane(from_plane, position=(0, 0, 0))
        self.create_debug_plane(to_plane, position=(10, 0, 0))
        
        # Rotate the plane to point towards the target (Only used to visually debug)
        self.debug_rotation_from_vectors(source_object=from_plane, target_object=to_plane)
        self.debug_rotation_from_vectors(source_object=to_plane, target_object=from_plane)

        point_01 = self.get_xform_as_mvector(point_01)
        point_02 = self.get_xform_as_mvector(point_02)
        from_plane = self.get_xform_as_mvector(from_plane)
        to_plane = self.get_xform_as_mvector(to_plane)
        (to_plane)

        return point_01,point_02, from_plane, to_plane
        
    def debug_project_point_to_plane(self, obj_to_project, start_obj, end_obj):
        point_vector = self.get_xform_as_mvector(obj_to_project)
        start_vector = self.get_xform_as_mvector(start_obj)
        end_vector = self.get_xform_as_mvector(end_obj)

        plane_center = start_vector
        plane_normal = end_vector - start_vector
        plane_normal.normalize()

        projected_point =self.project_point_to_plane(point_vector, plane_center, plane_normal)[0]

        # projected_point = from_vector#self.project_point_to_plane(point_vector, from_vector, plane_normal)

        self.debug_rotation_from_vectors(source_object=start_obj, target_object=end_obj)
        self.debug_rotation_from_vectors(source_object=end_obj, target_object=start_obj)

        cmds.xform(obj_to_project, worldSpace=True,
                   translation=(projected_point.x,
                                projected_point.y,
                                projected_point.z))
        
    def color_points_start_end(self,
                               points,
                               weight_val_pairs,
                               color_start= (1, 0, 0),
                               color_end= (0, 0, 1)):
        """
        :param list[str] points: List of point names
        :param list[float], list[float] weight_val_pairs: Tuple containing two lists of floats: start and end weights 
        :param (float, float, float) color_start: Color for the start point (default is red) 
        :param (float, float, float) color_end: Color for the end point (default is blue)
        Colors points from start to end based on weight values.
        """
        # to help visualize weight normalization

        mesh = 'point_01'
        color_set = 'colorSet1'  # Name of the color set

        # mix_weights = mix_values_by_distance()
        vals_srt, vals_end = weight_val_pairs

        # XXX: vals for ref
        col_srt = (1, 0, 0)
        col_end =  (0, 0, 1)
        col_srt = color_start
        col_end = color_end

        # make 'em floats
        col_srt = (float(col_srt[0]), float(col_srt[1]), float(col_srt[2]))
        col_end = (float(col_end[0]), float(col_end[1]), float(col_end[2]))
        print('color_mult_srt : ', col_srt)


        color_mult_srt = [(col_srt[0] * vals, col_srt[1] * vals, col_srt[2] * vals) for vals in vals_srt]
        color_mult_end = [(col_end[0]*vals, col_end[1]*vals, col_end[2]*vals) for vals in vals_end]
        print('color_mult_srt : ', color_mult_srt)

        # mix the final colors
        final_colors = [(cs[0]+ ce[0], cs[1]+ ce[1], cs[2]+ ce[2])
                       for cs, ce in zip(color_mult_srt, color_mult_end)]

        rgb_color = (0, 0, 1)  # RGB color values
        # blue = (0, 0, 1)  # RGB color values

        for point, color in zip(points, final_colors):
            # relative flag false will not set by adding
            cmds.polyColorPerVertex(point, rgb=color, alpha=1, relative=False)

    def debug_find_points_between(self, points=[], do_test_objs=False):

        point_01, point_02, start_plane, end_plane = self.create_debug_objs()

        if points and 'vtx' in points[0]:
            # get the geom for the MFn geom obj
            mesh = points[0].split('.')[0]
            # get the indices
            point_indices = [int(re.search(r'\[(\d+)\]', p).group(1)) for p in points]

            # Check object type to determine which MFn geom type you will be searching through.
            # Reference --- 'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'
            geom = cmds.listRelatives(mesh,shapes=True)[0]
            print(geom)
            obj_type = cmds.objectType(geom)
            if obj_type not in COMPONENT_TYPE_MAP.keys():
                print(f'# Warning: Unsupported geometry type: {obj_type}. Please check your use of this function')
                return False
            component_type = COMPONENT_TYPE_MAP[obj_type]
            # TODO: Future implementation for MFnLattice, MFnNurbsCurve, MFnNurbsSurface functionality
            #       will need to loop through vtx, cv, pt, using MFnLattice MFnNurbsCurve MFnNurbsSurface
            # NOTE: for now I am hard coding component_type to be vtx because that is all the weighting we
            #       need at this time.
            component_type='vtx'
            mfn_mesh = om.MFnMesh(self.get_dag_path(mesh))
            point_vectors=[mfn_mesh.getPoint(p, space=om.MSpace.kWorld) for p in point_indices]
            point_vectors = [om.MVector(p.x,p.y,p.z) for p in point_vectors]

            # first, find the point indices between.
            idx_list, point_vectors = self.points_between_startend(point_indices,
                                                                        point_vectors, 
                                                                        start_plane, end_plane)
            srt_wts, end_wts = self.mix_values_by_distance(point_vectors, start_plane, end_plane,
                                                           start_inherit_wts=False,
                                                           end_inherit_wts=False,
                                                           # decimal_place=False
                                                           )
            print(srt_wts)
            print(end_wts)
            print('NORMALIZATION TEST : ', [(swt + ewt) for swt, ewt in zip(srt_wts, end_wts)])
            # print('vtx_indices_between', idx_list)
            point_names = [f'{mesh}.vtx[{idx}]' for idx in idx_list]
            self.color_points_start_end(point_names, (srt_wts, end_wts))

            cmds.select(point_names)
            
        if do_test_objs:
            point_indices = [0,1]
            points_as_vectors = [point_01, point_02]
            point_names = ['point_01', 'point_02']

            for name, vector in zip(point_names, points_as_vectors):
                sel_point = self.points_between_startend(point_indices, vector, start_plane, end_plane)
                if sel_point:
                    print(f'{name} is between the planes')

    # middle = ''
    # for joint in joint_names:
    #     parent = cmds.listRelatives(joint, parent=True)
    #     children = cmds.listRelatives(joint, children=True)
    #     # if not parent in joint_names:
    #     #     continue
    #     if parent:
    #         parent = [p for p in parent if p in joint_names]
    #     if children:
    #         children = [c for c in children if c in joint_names]
    #     if parent and children:
    #         middle = joint

joints = ['jointtg', 'sfd', 'fgbf', 'joint5', 'joint2', 'sgv', 'joint4', 'cv']


twist_weights = Weights()
twist_weights.joints = joints
twist_weights.sort_by_hier_dist(joints)
twist_weights.set_skin_weights()

# twist_weights.debug_find_points_between(do_test_objs=True)
points = ['point_04.vtx[0]', 'point_04.vtx[1]', 'point_04.vtx[2]', 'point_04.vtx[3]', 'point_04.vtx[4]', 'point_04.vtx[5]', 'point_04.vtx[6]', 'point_04.vtx[7]', 'point_04.vtx[8]', 'point_04.vtx[9]', 'point_04.vtx[10]', 'point_04.vtx[11]', 'point_04.vtx[12]', 'point_04.vtx[13]', 'point_04.vtx[14]', 'point_04.vtx[15]', 'point_04.vtx[16]', 'point_04.vtx[17]', 'point_04.vtx[18]', 'point_04.vtx[19]', 'point_04.vtx[20]', 'point_04.vtx[21]', 'point_04.vtx[22]', 'point_04.vtx[23]', 'point_04.vtx[24]', 'point_04.vtx[25]', 'point_04.vtx[26]', 'point_04.vtx[27]', 'point_04.vtx[28]', 'point_04.vtx[29]', 'point_04.vtx[30]', 'point_04.vtx[31]', 'point_04.vtx[32]', 'point_04.vtx[33]', 'point_04.vtx[34]', 'point_04.vtx[35]', 'point_04.vtx[36]', 'point_04.vtx[37]', 'point_04.vtx[38]', 'point_04.vtx[39]', 'point_04.vtx[40]', 'point_04.vtx[41]', 'point_04.vtx[42]', 'point_04.vtx[43]', 'point_04.vtx[44]', 'point_04.vtx[45]', 'point_04.vtx[46]', 'point_04.vtx[47]', 'point_04.vtx[48]', 'point_04.vtx[49]', 'point_04.vtx[50]', 'point_04.vtx[51]', 'point_04.vtx[52]', 'point_04.vtx[53]']
joints = ['jointtg', 'sfd', 'fgbf', 'joint5', 'joint2', 'sgv', 'joint4', 'cv']

# twist_weights.debug_find_points_between(points, do_test_objs=False)



#twist_weights.debug_project_point_to_plane()

# twist_weights.debug_project_point_to_plane('point_01', 'plane_from', 'plane_from')
