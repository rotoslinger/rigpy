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
        self.joint_pairs = []

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

    def get_dependency_node(self, object_name: str) -> om.MObject:
        """
        :param object_name: Name of the object
        :return: MDagPath of the object
        Utility function to get the DAG path of an object.
        """
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        dag_path = selection_list.getDependNode(0)
        return dag_path

    def all_points_in_geom(self, geom):
        geo_type = cmds.objectType(geom)
        if geo_type == 'transform':
            # geom = f'{geom}Shape'
            geo_type = cmds.objectType(f'{geom}Shape')
        if geo_type not in COMPONENT_TYPE_MAP.keys():
            print(textwrap.dedent(f'''\# Warning: Unsupported geometry type: {geo_type}.
            # Please check your use of this function'''))
            return False
        component_type = COMPONENT_TYPE_MAP[geo_type]
        
        # ex: mesh f'{geometry}.vtx[0]' nurbs f'{geometry}.cv[0]' lattice f'{geometry}.pt[0]' 
        points = cmds.ls(f'{geom}.{component_type}[*]', flatten=True)
        point_indices = [int(re.search(r'\[(\d+)\]', p).group(1)) for p in points]

        return points, point_indices

    def get_influence_data(self, joints):
        # get all joint influenced geometry
        all_skinclusters = cmds.ls(type='skinCluster')
        geometries = set()
        skinclusters = set()
        for skin in all_skinclusters:
            influences = cmds.skinCluster(skin, query=True, weightedInfluence=True)
            if not influences:continue
            if not any(joint in influences for joint in joints):continue
            geom = cmds.skinCluster(skin, geometry=True, query=True)[0]
            geometries.add(geom)
            skinclusters.add(skin)

        return list(skinclusters), list(geometries)

    def set_pair_weights(self, joints, geom, skincluster):
        joints, pairs = self.sort_by_hier_dist(joints)
        start_plane = self.get_xform_as_mvector(joints[0])
        end_plane = self.get_xform_as_mvector(joints[-1])

        point_indices = self.all_points_in_geom(geom)[1]

        mfn_mesh = om.MFnMesh(self.get_dag_path(geom))
        point_vectors=[mfn_mesh.getPoint(p, space=om.MSpace.kWorld) for p in point_indices]
        point_vectors = [om.MVector(p.x,p.y,p.z) for p in point_vectors]
        point_indices, point_vectors = self.points_between_startend(point_indices,
                                                                    point_vectors,
                                                                    start_plane,
                                                                    end_plane)
        r_point_names = [f'{geom}.vtx[{idx}]' for idx in point_indices]

        # self.safe_add_influences(joints, skincluster)

        for pair in pairs:
            jnt_start, jnt_end = pair
            joint_start = self.get_xform_as_mvector(jnt_start)
            joint_end = self.get_xform_as_mvector(jnt_end)
            indices, p_vectors = self.points_between_startend(point_indices,
                                                                        point_vectors,
                                                                        joint_start,
                                                                        joint_end)
            wt_start, wt_end = self.mix_values_between(p_vectors, joint_start, joint_end,
                                                       start_inherit_wts=False,
                                                       end_inherit_wts=False,
                                                       decimal_place=False
                                                       )
            point_names = [f'{geom}.vtx[{idx}]' for idx in indices]
            for geo, si, ei in zip(point_names, wt_start, wt_end):
                # same time, to avoid breaking normalization.
                cmds.skinPercent(skincluster, geo, transformValue=[(jnt_start, ei), (jnt_end,si)])
            # self.color_points_start_end(point_names, (wt_start, wt_end))
        return r_point_names

    def safe_add_influences(self, joints, skincluster):
        # safely adds any joints that are currently not in the skincluster
        # If the joint(s) is already in the skin cluster it will not be added
        influences = cmds.skinCluster(skincluster, query=True, influence=True)
        # check if the joints are in the skincluster, if not add them locked, and then unlock them.
        for joint in joints:
            if not joint in influences:
                cmds.skinCluster(skincluster, edit=True, addInfluence=joint, weight=0)

    def distribute_startend_weight(self, start_joint, end_joint, joints):
        # TODO: Look at CW.skinweights_example.py for OpenMaya implementation
        joints = self.sort_by_hier_dist(joints)[0]

        # if any of the start joint weight is in the end joint weight you need to
        # swap with the end joint
        point_names=[]

        # find all points to act on.
        skinclusters, geometries = self.get_influence_data([start_joint, end_joint])
        
        for skin, geo in zip(skinclusters, geometries):
            # because you are distributing weights between start and end joint, any weighting
            # from the start joint on the end joint (elbow to hand) will need to be moved to the
            # second to last joint in the joints list.
            self.safe_add_influences(joints, skin)
            # self.move_skinweights(skin, geo, start_joint, joints[-2])
            point_names+=self.set_pair_weights(joints, geo, skin)


        # if any of the start joint weight is in the end joint weight you need to
        # swap with the second to last joint
        # print(cmds.skinCluster('skinCluster8',  edit = True, selectInfluenceVerts='RightForeArm'))
        # print(cmds.skinCluster('skinCluster8',  query = True, dui = True, selectInfluenceVerts=True))


        # TODO: make sure to get a union of any overlapping weights.
        cmds.select(cl=True)
        print(cmds.skinCluster('skinCluster9',  edit = True, selectInfluenceVerts='RightForeArm'))
        points1 = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        print(cmds.skinCluster('skinCluster9',  edit = True, selectInfluenceVerts='RightHand'))
        points2 = cmds.ls(sl=True, fl=True)
        common_values = list(set(points1) & set(points2))
        
        cmds.select(common_values)
        # print(points)
        # selectInfluenceVerts


        # cmds.select(point_names)
    
    def decompress_slice_indices(self, list_with_slices):
        indices = []

        # Loop through each selection string in the list
        for selection_str in list_with_slices:
            # Find all range patterns or single indices
            matches = re.findall(r'\[(\d+):(\d+)\]|\[(\d+)\]', selection_str)
            
            for match in matches:
                if match[0] and match[1]:  # Range match
                    start, end = int(match[0]), int(match[1])
                    indices.extend(range(start, end))  # Add all indices in the range
                elif match[2]:  # Single index match
                    indices.append(int(match[2]))  # Add the single index
        
        return indices


    # def get_points_in(self, skinCluster, mesh, source_jnt, dest_jnt):
    #     mesh_shape = self.get_dag_path(mesh)


    # def move_skinweights(self, skinCluster, mesh, source_jnt, dest_jnt):
    #     # moves skin weights from one bone to another

    #     mesh_shape = self.get_dag_path(mesh)
    #     # mfn_mesh = om.MFnMesh(self.get_dag_path(mesh))
    #     fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
    #     source_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(source_jnt))
    #     destination_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(dest_jnt))
    #     source_joint = om.MIntArray([source_joint])
    #     destination_joint = om.MIntArray([destination_joint])

    #     # source_joint = self.get_dag_path(source_jnt)
    #     # destination_joint = self.get_dag_path(dest_jnt)

    #     sel_list, weight_list = fnSkinCluster.getPointsAffectedByInfluence(self.get_dag_path(source_jnt))
    #     # sel_list = sel_list.getSelectionStrings()	
    #     # om.MSelectionList
    #     sel_list = list(sel_list.getSelectionStrings())
    #     maya_list= sel_list
    #     if maya_list and 'Body_geo' in maya_list[0]:
    #         cmds.select(maya_list)
    #         print(maya_list)
    #         return
    #     cpnt_indices = self.decompress_slice_indices(sel_list)
    #     print('these are the specific component, indices ', cpnt_indices)
        

        
    #     # cpnt_indices = self.all_points_in_geom(mesh)[1]
    #     # print('these are all indices ', cpnt_indices)

    #     cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    #     om.MFnSingleIndexedComponent(cpnt_list).addElements(cpnt_indices)
    #     print('This is the component list ', cpnt_list)


    #     if not cpnt_list: return


        
    #     skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, source_joint)



    #     zero_weight_list = [0.0] * len(cpnt_indices)
    #     zero_weight_list = om.MDoubleArray(zero_weight_list)

    #     # cpnt_indices = self.all_points_in_geom(mesh)[1]
    #     source_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(source_jnt))
    #     destination_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(dest_jnt))

    #     for idx in cpnt_indices:

    #         cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    #         om.MFnSingleIndexedComponent(cpnt_list).addElement(idx)
    #         weight_val = fnSkinCluster.getWeights(mesh_shape, cpnt_list, source_joint)
    #         fnSkinCluster.setWeights(mesh_shape,
    #                                 cpnt_list,
    #                                 source_joint,
    #                                 0.0,
    #                                 normalize=False)
    #         fnSkinCluster.setWeights(mesh_shape,
    #                                 cpnt_list,
    #                                 destination_joint,
    #                                 1.0,
    #                                 normalize=False)
        


    def move_skinweights(self, skinCluster, mesh, source_jnt, dest_jnt):
        # moves skin weights from one bone to another

        mesh_shape = self.get_dag_path(mesh)
        mfn_mesh = om.MFnMesh(self.get_dag_path(mesh))
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
        source_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(source_jnt))
        destination_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(dest_jnt))
        source_joint = om.MIntArray([source_joint])
        destination_joint = om.MIntArray([destination_joint])

        # source_joint = self.get_dag_path(source_jnt)
        # destination_joint = self.get_dag_path(dest_jnt)

        sel_list, weight_list = fnSkinCluster.getPointsAffectedByInfluence(self.get_dag_path(dest_jnt))
        # sel_list = sel_list.getSelectionStrings()	
        # om.MSelectionList
        sel_list = list(sel_list.getSelectionStrings())
        cpnt_indices = self.decompress_slice_indices(sel_list)
        print('these are the specific component, indices ', cpnt_indices)
        


        cpnt_indices = self.all_points_in_geom(mesh)[1]
        print('these are all indices ', cpnt_indices)

        cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(cpnt_list).addElements(cpnt_indices)


        if not cpnt_list: return


        
        skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, source_joint)



        zero_weight_list = [0.0] * len(cpnt_indices)
        zero_weight_list = om.MDoubleArray(zero_weight_list)

        # cpnt_indices = self.all_points_in_geom(mesh)[1]


        fnSkinCluster.setWeights(mesh_shape,
                                 cpnt_list,
                                 source_joint,
                                 zero_weight_list,
                                 normalize=True)
        fnSkinCluster.setWeights(mesh_shape,
                                 cpnt_list,
                                 destination_joint,
                                 skin_weights,
                                 normalize=True)
        # * shape       (MDagPath) - object being deformed by the skinCluster
        # * components   (MObject) - the components to set weights on
        # * influence        (int) - physical index of a single influence object
        # * weight         (float) - single weight to be applied to all components.
        # * influences (MIntArray) - physical indices of several influence objects.
        # * weights (MDoubleArray) - weights to be used with several influence objects.
        # * normalize       (bool) - if True, normalize weights on other influence objects
        # * returnOldWeights(bool) - if True, return the old weights, otherwise return None


        # remove weights from source_jnt influence with normalize

        # add weights to dest_jnt influence with normalize

        # getWeights(shape, components) -> (MDoubleArray, int)
        # getWeights(shape, components, influence) -> MDoubleArray
        # getWeights(shape, components, influences) -> MDoubleArray
        # setWeights(shape, components, influence, weight, normalize=True, returnOldWeights=False) -> None or MDoubleArray
        # setWeights(shape, components, influences, weights, normalize=True, returnOldWeights=False) -> None or MDoubleArray


    def debug_dict(self, data, indent=0, visited=None, print_dict=False):
        """
        An alternative to json.dumps. Creates a cascading key:value.
        :param dict data: The dictionary to debug.
        :param int indent: Current indentation level.
        :param set visited: Tracks visited objects to prevent circular references.
        :param bool single_line_keys: If True, print nested keys on the same line until the final value.
        """
        visited = visited or set()  # Initialize visited set if None
        output = []  # Initialize an empty list to accumulate the output
        if id(data) in visited:
            output.append(f"{' ' * indent}... (circular reference detected)")
            return '\n'.join(output)
        visited.add(id(data))

        for key, value in data.items():
            if isinstance(value, dict):
                    output.append(f"{' ' * indent}{{{key}:")
                    output.append(self.debug_dict(value, indent + len(key) + 4, visited))
                    output.append(f"{' ' * indent}}}")
            else:
                output.append(f"{' ' * indent}{{{key}: {value}}}")
        r_string = '\n'.join(output)
        if print_dict:print(r_string)

        return r_string


    def is_joint_in_skincluster(self, skincluster, joint):
        # Get all joints (influences) associated with the skinCluster
        influences = cmds.skinCluster(skincluster, query=True, influence=True)
        # Check if the specified joint is in the list of influences
        return joint in influences


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
        return sorted_joints, pairs

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
                                threshold_start=0.1,
                                threshold_end=0.1
                                ) -> tuple[list[int], list[str]]:
        """
        :param list[int] point_indices: List of point names from Maya.    
        :param list[om.MVector] point_indices: List of point names from Maya.
        :param om.MVector start_point: Starting point in world space.
        :param om.MVector to_point: Ending point in world space.
        :return: return_points, return_indices
        :rtype: list[int], list[str]
        """
        if threshold_start:
            # TODO add functionality to retrieve 'blend' points, points that are near the start
            # plane but spill out in both directions so you have an area that you know you
            # need to blend.
            # vector lerp the start point away from itself using by the amount of threshold start
            start_point=((end_point - start_point).normalize() * (-1*threshold_start)) + start_point
            end_point=((start_point - end_point).normalize() * (-1*threshold_end)) + end_point



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

# cmds.file('C:/Users/harri/Documents/cartwheel/working_files/running_jump02.ma',
#           force=True,
#           options="v=0;",
#           ignoreVersion=True,
#           type="mayaAscii",
#           open=True)


joints = ['jointtg', 'sfd', 'fgbf', 'joint5', 'joint2', 'sgv', 'joint4', 'cv']



# twist_weights.debug_find_points_between(do_test_objs=True)
all_points = ['point_04.vtx[0]', 'point_04.vtx[1]', 'point_04.vtx[2]', 'point_04.vtx[3]', 'point_04.vtx[4]', 'point_04.vtx[5]', 'point_04.vtx[6]', 'point_04.vtx[7]', 'point_04.vtx[8]', 'point_04.vtx[9]', 'point_04.vtx[10]', 'point_04.vtx[11]', 'point_04.vtx[12]', 'point_04.vtx[13]', 'point_04.vtx[14]', 'point_04.vtx[15]', 'point_04.vtx[16]', 'point_04.vtx[17]', 'point_04.vtx[18]', 'point_04.vtx[19]', 'point_04.vtx[20]', 'point_04.vtx[21]', 'point_04.vtx[22]', 'point_04.vtx[23]', 'point_04.vtx[24]', 'point_04.vtx[25]', 'point_04.vtx[26]', 'point_04.vtx[27]', 'point_04.vtx[28]', 'point_04.vtx[29]', 'point_04.vtx[30]', 'point_04.vtx[31]', 'point_04.vtx[32]', 'point_04.vtx[33]', 'point_04.vtx[34]', 'point_04.vtx[35]', 'point_04.vtx[36]', 'point_04.vtx[37]', 'point_04.vtx[38]', 'point_04.vtx[39]', 'point_04.vtx[40]', 'point_04.vtx[41]', 'point_04.vtx[42]', 'point_04.vtx[43]', 'point_04.vtx[44]', 'point_04.vtx[45]', 'point_04.vtx[46]', 'point_04.vtx[47]', 'point_04.vtx[48]', 'point_04.vtx[49]', 'point_04.vtx[50]', 'point_04.vtx[51]', 'point_04.vtx[52]', 'point_04.vtx[53]']
joints = ['jointtg', 'sfd', 'fgbf', 'joint5', 'joint2', 'sgv', 'joint4', 'cv']
joints = ['RightArm','RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05', 'RightForeArm']
joints = ['RightArm_out_bind_tw00', 'RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05', 'RightArm', 'RightForeArm', 'RightForeArm_out_bind_tw00', 'RightForeArm_out_bind_tw01', 'RightForeArm_out_bind_tw02', 'RightForeArm_out_bind_tw03', 'RightForeArm_out_bind_tw04', 'RightForeArm_out_bind_tw05', 'RightHand']

# distribute_joints = ['RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05' ]

twist_weights = Weights()
twist_weights.joints = joints
# twist_weights.set_pair_weights(joints=joints, geom='point_04', skincluster='skinCluster1')
up_arm_jnts = ['RightArm','RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05', 'RightForeArm']
lo_arm_jnts = ['RightForeArm', 'RightForeArm_out_bind_tw01', 'RightForeArm_out_bind_tw02', 'RightForeArm_out_bind_tw03', 'RightForeArm_out_bind_tw04', 'RightForeArm_out_bind_tw05', 'RightHand']

twist_weights.distribute_startend_weight(start_joint='RightArm',end_joint='RightForeArm',joints=up_arm_jnts)
twist_weights.distribute_startend_weight(start_joint='RightForeArm',end_joint='RightHand',joints=lo_arm_jnts)

# Example of using the function
# Assuming debug_dict is defined in your class

# NOTE: Add a threshold attribute to the points between and another to the mix
# this simply increases the vector distance by a small amount.
# POINTS BETWEEN Threshold start, threshold end.
# test by selecting so you can see what different values do.
# same for mix values

# Inherit weights!!!
# inherit
