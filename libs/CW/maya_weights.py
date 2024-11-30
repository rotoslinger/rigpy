import re, math, textwrap, inspect

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim

# TODO: entry point for future implementation.
#       Supported needed for weighting MFnLattice, MFnNurbsCurve, MFnNurbsSurface
#       Use cmds.objectType to determine the point attribute name (vtx, cv, pt)
# Currently, only 'mesh' is fully supported.
COMPONENT_TYPE_MAP = {'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'}

class Weights:
    """
    A utility class for manipulating weights.
    
    :Methods of interest:
    ```
    self.distribute_startend_weight # - Entry point for distributing existing weight
                                    #   between twist joints
    self.set_pair_weights # - distribute weights of a start influence over a list of joint
                          #   pairs
    self.mix_values_between # - calculates weights between a start and end vector
    self.points_between_startend # - given a list of points and two vectors, create 2 
                                 #   infinite planes and find points that fall between.
    ```
    :Methods:
    ```
    self.distribute_startend_weight
    self.set_pair_weights
    self.mix_values_between
    self.get_dag_path
    self.get_dependency_node
    self.extract_point_indices
    self.get_maya_points
    self.select_points_between_startend
    self.all_points_in_geom
    self.get_influence_data
    self.gather_weighted_indices
    self.safe_add_influences
    self.get_influenced_points
    self.get_joint_weights
    self.get_joint_weight_by_idx
    self.get_joint_allweights
    self.move_maya_skinweights
    self.point_weight_intersection
    self.point_weight_intersects
    self.unpack_sliced_indices
    self.unpack_sliced_strings
    self.debug_dict
    self.is_joint_in_skincluster
    self.sorted_pair_by_dist
    self.find_mid_in_appendage
    self.get_xform_as_mpoint
    self.get_xform_as_mvector
    self.project_point_to_plane
    self.points_between_startend
    self.move_to_plane_projection
    self.aim_rotation
    self.list_methods
    self.create_debug_prim
    self.create_debug_plane
    self.create_debug_objs
    self.color_points_start_end
    ```
    """
    def __init__(self):
        ...

    def distribute_twist_weights(self, start_joint: str,
                                 end_joint: str, twist_joints: list[str]) -> None:
        """
        Distribute skin weights between a start joint and an end joint across a list of
        intermediate joints.

        :param str start_joint: The name of the starting joint in the weight distribution.
        :param str end_joint: The name of the ending joint in the weight distribution.
        :param list[str] twist_joints: A list of joints between which the weights will be
                                       distributed. The list should include start_joint.
        :return: None
        """
        twist_joints = self.sorted_pair_by_dist(twist_joints)[0]

        skinclusters, geometries = self.get_influence_data([start_joint, end_joint])
        
        for skin, geo in zip(skinclusters, geometries):
            self.safe_add_influences(twist_joints, skin)

            # because you are distributing weights between start and end joint, any weighting
            # from the start joint on the end joint (elbow to hand) will need to be moved to the
            # second to last joint in the joints list.
            tmp_pts = self.point_weight_intersection([start_joint, end_joint], skin, geo)
            if tmp_pts:
                self.move_maya_skinweights(skin, geo, tmp_pts, start_joint, twist_joints[-1])
            
            self.set_pair_weights([start_joint] + twist_joints, geo, skin)

    def set_pair_weights(self, joints: list[str], geom: str, skincluster: str, 
                        use_existing_wts: bool = False) -> None:
        """
        Distribute skin weights between joint pairs based on point position between pairs.
        Multiplies existing weights by a volumetric linear gradient from method mix_values_between
        

        :param list[str] joints: Joints to define weight distribution along a gradient.
        :param str geom: Geometry whose weights are being modified.
        :param str skincluster: SkinCluster controlling the geometry.
        :param bool use_existing_wts: Use only points already weighted by joints. Default is False.

        :return: List of point names processed (e.g., 'vtx[0]').
        :rtype: list[str]
        """
        # it is very important to remember that due to weight normalization, you will only want to
        # distribute the weights from the start joint
        # end joint weights will automatically get distributed as the start weights are multiplied
        # by the gradient distribution, so they will not wipe out the end weights.
    
        weight_joint = joints[0]

        joints, pairs = self.sorted_pair_by_dist(joints)
        start_plane = self.get_xform_as_mvector(joints[0])
        end_plane = self.get_xform_as_mvector(joints[-1])

        point_indices = self.all_points_in_geom(geom)[1]
        if use_existing_wts:
            point_indices= self.gather_weighted_indices(joints, skincluster)[1]


        mfn_mesh = om.MFnMesh(self.get_dag_path(geom))
        point_vectors=[mfn_mesh.getPoint(p, space=om.MSpace.kWorld) for p in point_indices]
        point_vectors = [om.MVector(p.x,p.y,p.z) for p in point_vectors]
        point_indices, point_vectors = self.points_between_startend(point_indices,
                                                                    point_vectors,
                                                                    start_plane,
                                                                    end_plane)

        for pair in pairs:
            jnt_start, jnt_end = pair
            pair_start = self.get_xform_as_mvector(jnt_start)
            pair_end = self.get_xform_as_mvector(jnt_end)
            indices, p_vectors = self.points_between_startend(point_indices,
                                                            point_vectors,
                                                            pair_start,
                                                            pair_end)
            if not indices: continue
            inherit_wts = []
            inherit_wts = self.get_joint_weight_by_idx(skincluster, geom, 
                                                                weight_joint, indices)

            wt_start, wt_end = self.mix_values_between(p_vectors, pair_start, pair_end,
                                                    inherited_weights=inherit_wts,
                                                    decimal_place=False
                                                    )

            point_names = [f'{geom}.vtx[{i}]' for i in indices]

            for maya_pt, s_wt, e_wt in zip(point_names, wt_start, wt_end):
                if s_wt < .05 and e_wt < .05: continue
                # set weights on start and end at the same time, to avoid breaking normalization.
                cmds.skinPercent(skincluster, maya_pt, transformValue=[(jnt_start, e_wt), 
                                                                       (jnt_end, s_wt)])

    def mix_values_between(self, point_vectors:list[om.MVector], start_point:om.MVector,
                           end_point:om.MVector, inherited_weights: list[float] = [],
                           decimal_place: int | bool = 5) -> tuple[list[float], list[float]]:
        """
        Computes start and end weights for points along a line between two points.

        :param list[om.MVector] point_vectors: A list of points (as MVector) to calculate weights for.
        :param om.MVector start_point: The starting point of the line.
        :param om.MVector end_point: The ending point of the line.
        :param list inherited_weights: Optional list of weights to multiply the results by, 
                                       scaling the computed weights for each point.
        :param int | bool decimal_place: Number of decimal places to round weights. 
                                         Set False to skip rounding.

        :return: start_weights, end_weights (lists of start and end weights for the given points)
        :rtype: tuple[list[float], list[float]]
        """

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

        # Normalize by getting the inverse start_weights
        end_weights = [1-wt for wt in start_weights]

        if inherited_weights:
            start_weights = [(strt_wt * inh_wt) for strt_wt, inh_wt in zip(start_weights,
                                                                        inherited_weights)]
            end_weights = [(end_wt * inh_wt) for end_wt, inh_wt in zip(end_weights,
                                                                    inherited_weights)]


        if decimal_place and type(decimal_place) == int :
            # points can drift when world movement is 5 or more figures.
            # rounding, in combination with maya.cmds.skinWeights flags pruneWeights & normalize
            # can help to avoid these issues.
            start_weights = [round(sw, decimal_place) for sw in start_weights]
            end_weights = [round(ew, decimal_place) for ew in end_weights]

        return start_weights, end_weights

    def get_dag_path(self, object_name: str) -> om.MDagPath:
        """
        Utility function to get the dag path of an object.

        :param str object_name: Name of the object
        :return: MDagPath of the object
        :rtype: om.MDagPath
        """
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        dag_path = selection_list.getDagPath(0)
        return dag_path

    def get_dependency_node(self, object_name: str) -> om.MObject:
        """
        Utility function to get a dependency node as an MObject.

        :param object_name: Name of the object
        :return: MDagPath of the object
        :rtype: om.MDagPath
        """
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        node = selection_list.getDependNode(0)
        return node

    def extract_point_indices(self, points: list[str]) -> list[int]:
        """
        Extract numerical indices from a list of point names.

        :param list[str] points: A list of point names, each containing an index in square brackets
                                 (e.g., 'point[3]').
        :return: A list of integers representing the extracted indices.
        :rtype: list[int]
        """
        return [int(re.search(r'\[(\d+)\]', p).group(1)) for p in points]
    
    def get_maya_points(self, geo, indices):
        if cmds.objectType(geo) == 'transform':
            geo = cmds.listRelatives(geo, shapes=True, children=True, noIntermediate=True)[0]
        geo_type = cmds.objectType(geo)
        component_type = COMPONENT_TYPE_MAP[geo_type]

        maya_points = [f'{geo}.{component_type}[{idx}]' for idx in indices]
        return maya_points
    
    def select_points_between_startend(self, geo: str, start: str, end: str) -> None:
        """
        Select points on a geometry that lie between the start and end positions.
        This is a visual debug utility.  It does not return any information, but allows you to 
        preview which points fall between two objects.
        
        See Weights.points_between_startend for useful returns

        :param str geo: The name of the geometry to query.
        :param str start: The name of the start point or locator, converted to an MVector.
        :param str end: The name of the end point or locator, converted to an MVector.
        :return: None
        """
        start = self.get_xform_as_mvector(start)
        end = self.get_xform_as_mvector(end)
        indices = self.all_points_in_geom(geo)[1]
        mfn_mesh = om.MFnMesh(self.get_dag_path(geo))
        point_vectors=[mfn_mesh.getPoint(p, space=om.MSpace.kWorld) for p in indices]
        point_vectors = [om.MVector(p.x,p.y,p.z) for p in point_vectors]

        indices, _ = self.points_between_startend(indices,
                                                  point_vectors,
                                                  start,
                                                  end)
        points = self.get_maya_points(geo, indices)
        cmds.select(points)

    def all_points_in_geom(self, geom: str) -> tuple[list[str], list[int]] | bool:
        """
        Retrieve all points and their indices from a geometry. Uses a COMPONENT_TYPE_MAP dict to
        classify the component type (vtx, cv, pt).

        :param str geom: The name of the geometry (e.g., a mesh, NURBS surface, or lattice).
        :return: A tuple containing a list of point names (e.g., vertices, CVs, lattice points) 
                and their corresponding indices. Returns False if the geometry type is unsupported.
        :rtype: tuple[list[str], list[int]] | bool
        """
        geo_type = cmds.objectType(geom)
        if geo_type == 'transform':
            shape = cmds.listRelatives(geom, shapes=True, noIntermediate=True, children=True)
            if not cmds.about(batch=True) and not shape:
                print(f'# Warning: no shapes were found under transform {geom}')
                return False
            geo_type = cmds.objectType(shape[0])
        # TODO: Incorporate this functionality into methods that only support type 'mesh'
        if geo_type not in COMPONENT_TYPE_MAP.keys():
            if not cmds.about(batch=True):
                print(textwrap.dedent(f'''# Warning: Unsupported geometry type: {geo_type}.
                # Please check your use of this function'''))
            return False
        component_type = COMPONENT_TYPE_MAP[geo_type]
        
        # Example:
        # mesh -> f'{geometry}.vtx[0]', NURBS -> f'{geometry}.cv[0]', lattice -> f'{geometry}.pt[0]' 
        points = cmds.ls(f'{geom}.{component_type}[*]', flatten=True)
        point_indices = self.extract_point_indices(points)

        return points, point_indices

    def get_influence_data(self, joints: list[str]) -> tuple[list[str], list[str]]:
        """
        Retrieve skinClusters and their associated geometries influenced by the specified joints.

        :param list[str] joints: A list of joint names to check for influence.
        :return: Tuple:
                       - A list of skinCluster names that include the specified joints as influences
                       - A list of geometries associated with those skinClusters.
        :rtype: tuple[list[str], list[str]]
        """
        # get all joint influenced geometry
        all_skinclusters = cmds.ls(type='skinCluster')
        geometries = []
        skinclusters = []
        for skin in all_skinclusters:
            influences = cmds.skinCluster(skin, query=True, weightedInfluence=True)
            if not influences:continue
            if not any(joint in influences for joint in joints):continue
            geom = cmds.skinCluster(skin, geometry=True, query=True)[0]
            geometries.append(geom)
            skinclusters.append(skin)

        return skinclusters, geometries

    def gather_weighted_indices(self, joints: list[str], skincluster: str) -> tuple[list[str],
                                                                                    list[int]]:
        """
        Collect all points and their indices influenced by the specified joints in a skinCluster.
        Using set class to avoid duplicate entries.

        :param list[str] joints: A list of joint names to query for influenced points.
        :param str skincluster: The name of the skinCluster to query.
        :return: Tuple:
                       - A list of point names influenced by the specified joints.
                       - A list of indices of those points.

        :rtype: tuple[list[str], list[int]]
        """
        all_points=set()
        all_indices=set()
        for joint in joints:
            pt, pt_idx = self.get_influenced_points(joint, skincluster)
            all_points.add(pt)
            all_indices.add(pt_idx)
        return list(all_points), list(all_indices)
    
    def safe_add_influences(self, joints:list[str], skincluster:str):
        # safely adds any joints that are currently not in the skincluster
        # If the joint(s) is already in the skin cluster it will not be added
        influences = cmds.skinCluster(skincluster, query=True, influence=True)
        # check if the joints are in the skincluster, if not add them locked, and then unlock them.
        for joint in joints:
            if not joint in influences:
                cmds.skinCluster(skincluster, edit=True, addInfluence=joint, weight=0)


    def get_influenced_points(self, skinCluster: str, joint: str) -> tuple[list[str], list[int]]:
        """
        Retrieves the points and their indices influenced by a specific joint.

        :param str skinCluster: The name of the skinCluster node.
        :param str joint: The name of the joint to query for influences.

        :return: Tuple of influenced points and their corresponding indices.
        :rtype: tuple[list[str], list[int]]
        """  
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))    
        sliced_strings = fnSkinCluster.getPointsAffectedByInfluence(self.get_dag_path(joint))[0]
        sliced_strings = list(sliced_strings.getSelectionStrings())
        points = self.unpack_sliced_strings(sliced_strings)
        indices = self.extract_point_indices(points)

        return points, indices

    def get_sparse_joint_weights(self, skinCluster: str, mesh: str, joint: str) -> list[float]:
        """
        Returns a sparse list of weights for the specified joint on the given mesh.

        Note that this list only includes points with non-zero weights, making 
        per-point lookups unsafe because indexing may not be properly ordered. 
        For a complete list of all indices, use the method 'get_joint_allweights'.

        :param str skinCluster: The name of the skinCluster node.
        :param str mesh: The name of the mesh geometry.
        :param str joint: The name of the joint to query for weights.
        :return: A list of weights corresponding to the influenced points of the joint.
        :rtype: list[float]
        """
        # Turn the point list into an integer list, then convert it to type kMeshVertComponent 
        cpnt_indices = self.get_influenced_points(skinCluster, joint)[1]
        cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(cpnt_list).addElements(cpnt_indices)
        # if for some reason the list isn't created, or fails, you won't want to move forward.
        if not cpnt_list: return

        # convert all maya data into OpenMaya data
        mesh_shape = self.get_dag_path(mesh)
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
        joint_index= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(joint))
        # joint_index = om.MIntArray([joint_index])
    
        # get weights, set back an empty weight list for the weights that will be moved
        skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, joint_index)
        skin_weights = list(skin_weights)
        return skin_weights

    def get_joint_weight_by_idx(self, skinCluster: str,
                                mesh: str, joint: str, indices: list[int]) -> list[float]:
        """
        Returns a non-sparse list of weight values for the specified joint on the given mesh.

        This method provides a list that is safe for 'wildcard-type' point index lookups, 
        containing a weight value for every vertex in the mesh.

        :param str skinCluster: The name of the skinCluster node.
        :param str mesh: The name of the mesh geometry.
        :param str joint: The name of the joint to query for weights.
        :param list[int] indices: A list of integer indices for the vertices to query.
        :return: A list of weights corresponding to the specified indices of the joint.
        :rtype: list[float]
        """
        # the list returned by this method contains a weight value for every vertex in the mesh.
        # the result is a list that is safe for 'wildcard-type' point index lookups.

        # Convert list of integers it to type kMeshVertComponent 
        cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(cpnt_list).addElements(indices)
        # if for some reason the list isn't created, or fails, you won't want to move forward.
        if not cpnt_list: return

        # convert all maya data into OpenMaya data
        mesh_shape = self.get_dag_path(mesh)
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
        joint_index= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(joint))
        # joint_index = om.MIntArray([joint_index])
    
        # get weights, set back an empty weight list for the weights that will be moved
        skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, joint_index)
        skin_weights = list(skin_weights)
        return skin_weights

    def get_joint_allweights(self, skinCluster: str, mesh: str,
                             joint: str, round_amt: int | bool = False) -> list[float]:
        """
        Returns a non-sparse list of weight values for every vertex in the specified mesh.

        This method provides a complete list of weights that is safe for 'wildcard-type'
        point index lookups.

        :param str skinCluster: The name of the skinCluster node.
        :param str mesh: The name of the mesh geometry.
        :param str joint: The name of the joint to query for weights.
        :param int | bool round_amt: If specified, the weights will be rounded to this
                                    number of decimal places.
        :return: A list of weights corresponding to every vertex in the mesh for the joint.
        :rtype: list[float]
        """
        # Push back a sequential list of integers the same amount as the vertex count 
        cpnt_indices = [i for i in range(cmds.polyEvaluate(mesh, vertex=True))]
        # Convert list of integers to type kMeshVertComponent 
        cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(cpnt_list).addElements(cpnt_indices)
        # if for some reason the list isn't created, or fails, you won't want to move forward.
        if not cpnt_list: return

        # convert all maya data into OpenMaya data
        mesh_shape = self.get_dag_path(mesh)
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
        joint_index= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(joint))
    
        # get weights, set back an empty weight list for the weights that will be moved
        skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, joint_index)
        skin_weights = list(skin_weights)
        if round_amt:
            skin_weights = [round(sw, round_amt) for sw in skin_weights]
        return skin_weights

    def move_maya_skinweights(self, skinCluster: str, mesh: str,
                              points: list[str], src_jnt: str, dst_jnt: str) -> None:
        """
        Moves skin weights from one joint to another for specified points in a mesh.

        This method first sets the weights of the source joint to zero for the given points
        and then assigns the original weights to the destination joint, normalizing the weights 
        only at the end to prevent unintended influence shifts.

        :param str skinCluster: The name of the skinCluster node.
        :param str mesh: The name of the mesh geometry.
        :param list[str] points: The list of point names (vertices) to move weights for.
        :param str src_jnt: The name of the source joint from which weights will be moved.
        :param str dst_jnt: The name of the destination joint to which weights will be assigned.
        :return: None
        """
        # Turn the point list into an integer list, then convert it to type kMeshVertComponent 
        cpnt_indices = self.extract_point_indices(points)
        cpnt_list = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(cpnt_list).addElements(cpnt_indices)
        # if for some reason the list isn't created, or fails, you won't want to move forward.
        if not cpnt_list: return

        # convert all maya data into OpenMaya data
        mesh_shape = self.get_dag_path(mesh)
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))
        source_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(src_jnt))
        destination_joint= fnSkinCluster.indexForInfluenceObject(self.get_dag_path(dst_jnt))
        source_joint = om.MIntArray([source_joint])
        destination_joint = om.MIntArray([destination_joint])
        
        # get weights, set back an empty weight list for the weights that will be moved
        skin_weights = fnSkinCluster.getWeights(mesh_shape, cpnt_list, source_joint)
        zero_weight_list = [0.0] * len(cpnt_indices)
        zero_weight_list = om.MDoubleArray(zero_weight_list)

        # You only want to normalize at the end. 
        # Normalizing when setting weights to 0.0 will push the influences to some other bone.
        # We want them to go to the bone in step 2
        # step 1
        fnSkinCluster.setWeights(mesh_shape,
                                cpnt_list,
                                source_joint,
                                zero_weight_list,
                                normalize=False)
        # only normalize when you move the weights.
        # step 2
        fnSkinCluster.setWeights(mesh_shape,
                                cpnt_list,
                                destination_joint,
                                skin_weights,
                                normalize=True)

    def point_weight_intersection(self, joints: list[str], skinCluster: str,
                                  geo: str, threshold: float = 0.09) -> list[str]:
        """
        Finds the intersection of points weighted to all specified joints in the given skinCluster.

        Only points with a non-zero weight value above the specified threshold will be considered.

        :param list[str] joints: List of joint names to check for weight intersections.
        :param str skinCluster: The name of the skinCluster node.
        :param str geo: The name of the geometry to analyze.
        :param float threshold: The minimum weight value for a point to be included. The sweet spot
                                seems to be 0.09.  Weights smaller than 0.09 don't seem to have
                                much visible influence. They may also be unintended, caused by
                                over-sensitive weight normalization. By default, weights in maya
                                usually have 
        :return: A list of point names that are influenced by all joints above the threshold.
        :rtype: list[str]
        """
        # finds intersection of points weighted to all joints in joints arg.
        # points must have a non-zero weight val to be considered.
        all_points = []

        for joint in joints:
            weights = self.get_joint_allweights(skinCluster, geo, joint, round_amt=4)
            weights = [idx for idx, w in enumerate(weights) if w > threshold]
            all_points.append(weights)

        all_points = list(set(all_points[0]).intersection(*map(set, all_points[1:])))

        all_points=self.get_maya_points(geo, all_points)
        return all_points

    def point_weight_intersects(self, joints, skinCluster):
        # finds intersection of points weighted to all joints in joints arg.
        # points must have a non-zero weight val to be considered.
        fnSkinCluster = omAnim.MFnSkinCluster(self.get_dependency_node(skinCluster))    
        all_points = []

        for joint in joints:
            sliced_strings = fnSkinCluster.getPointsAffectedByInfluence(self.get_dag_path(joint))[0]
            sliced_strings = list(sliced_strings.getSelectionStrings())
            all_points.append(self.unpack_sliced_strings(sliced_strings))
        all_points = list(set(all_points[0]).intersection(*map(set, all_points[1:])))

        return all_points

    def unpack_sliced_indices(self, list_with_slices: list[str]) -> list[int]:
        '''
        Decompresses a list of Maya indexed component strings into individual components.

        :param list[str] list_with_slices: List of strings in Maya slice format
                                           e.g., ['polygon[0:2]', 'polygon[4]']
        :return: List of expanded indexed components e.g., [0, 1, 2, 4]
        :rtype: list[int]
        '''
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

    def unpack_sliced_strings(self, list_with_slices:list[str]) -> list[str]:
        '''
        Decompresses a list of Maya indexed component strings into individual components.

        :param list_with_slices: List of strings in Maya slice format
                                 e.g., 'polygon[0:2]', 'polygon[4]'
        :return: List of expanded indexed components 
                 e.g., ['polygon[0]', 'polygon[1]', 'polygon[2]', 'polygon[4]']).
        :rtype: list[str]
        '''
        indices = []

        for selection_str in list_with_slices:
            # Extract the base component name (e.g., "polygon")
            base = re.match(r'^\D+', selection_str).group(0)

            # Find all slice patterns or single indices
            matches = re.findall(r'\[(\d+):(\d+)\]|\[(\d+)\]', selection_str)

            for match in matches:
                if match[0] and match[1]:  # Range match
                    start, end = int(match[0]), int(match[1])
                    indices.extend(f'{base}{i}]' for i in range(start, end + 1))  # Include end index
                elif match[2]:  # Single index match
                    indices.append(f'{base}{int(match[2])}]')  # Add the single index

        return indices

    def debug_dict(self, data, indent=0, visited=None, print_dict=False):
        """
        An alternative to json.dumps. Creates a cascading key:value. Makes nested dictionaries
        easier to read for debugging. It is especially useful for dictionaries within dictionaries
        that have many keys and long lists/dictionaries.

        :param dict data: The dictionary to debug.
        :param int indent: Current indentation level.
        :param set visited: Tracks visited objects to prevent circular references.
        :param bool single_line_keys: If True, print nested keys on the same line until the
                                      final value.

        :return: a string with cascading key:value
        :rtype: LiteralString
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
        
        if not cmds.about(batch=True) and print_dict:print(r_string)

        return r_string

    def is_joint_in_skincluster(self, skincluster, joint):
        # Get all joints (influences) associated with the skinCluster
        # Check if the specified joint is in the list of influences
        return joint in cmds.skinCluster(skincluster, query=True, influence=True)

    def sorted_pair_by_dist(self, xform_names:list[str], parent_check=True):
        """
        Classify xforms and sort them by distance to the start xform in ascending distance.
        If parent_check is false assume the first xform in the list is the parent.

        :param list[str] xform_names: List of Maya object names.
        :param bool parent_check: List of Maya objects.
        :return: Tuple: list of sorted xforms, list tuple pairs of [xform, next xform]
        :rtype: tuple[list[str], list[tuple[str, str]]]
        """
        start = ''
        if parent_check:
            '''
            parent_check logic:
            - assumes xforms are hierarchal, and part of the same chain.
            - finds parents for all xforms, compares parents with the list of joints, if the parent
              is not in the list of xforms then it is the start xform
            - get distances by creating a vector for each xform to start, then get length/magnitude
            - sort distances,
            '''
            for xform in xform_names:
                parent = cmds.listRelatives(xform, parent=True)
                if not parent in xform_names:
                    start=xform
                    break
            # make sure the start is at the start of the list
            xform_names.remove(start)
            xform_names.insert(0, start)
        # Assuming self.get_xform_as_mvector is a method to get the position of a joint as an MVector
        xform_vectors = [self.get_xform_as_mvector(joint) for joint in xform_names]
        
        # Assume the first joint is the start
        start_joint = xform_names[0]
        strt_vec = xform_vectors[0]

        # Calculate distances from the start joint
        # Creates list of tuples paired in this format:
        # list[(str, float)] which is [(xform_name, distance_to_start)]
        distances = [ (xform, (strt_vec - v).length())for xform, v in zip(xform_names[1:],
                                                                       xform_vectors[1:])]

        # NOTE: Sorts transforms by distance to start (ascending order)
        # While less readable, the O(n) of the following list comp is significantly lower than a
        # nested for loop comparison.

        # This makes it perfect for future per point comparisons.
        # Also a great way to avoid dict sorting by key association
        # a_list = [('a', 3), ('b', 1), ('c', 2)]
        # s_list = sorted(a_list, key=lambda x: x[1])
        # output : [('b', 1), ('c', 2), ('a', 3)]

        # TODO : future implementation for per point comparisons:
        sorted_joints = [start_joint] + [xf for xf,_ in sorted(distances, key=lambda pair: pair[1])]

        # get start end pairs for linear blends between xforms ex: [(1, 2), (2, 3), (3, 4), (4, 5)]
        pairs = [(sorted_joints[i], sorted_joints[i+1]) for i in range(len(sorted_joints) - 1)]

        return sorted_joints, pairs

    def find_mid_in_appendage(self, xforms:list[str])->str:
        # A helper to find the middle joint in an arm or a leg. Can have any number of xforms
        # between. Arg xforms list can be given in any order.
        # Finds the one joint that has both a parent and a child in the joint chain
        # great for twist joints.
        middle = ''
        for xform in xforms:
            parent = cmds.listRelatives(xform, parent=True)
            children = cmds.listRelatives(xform, children=True)
            if parent:
                parent = [p for p in parent if p in xforms]
            if children:
                children = [c for c in children if c in xforms]
            if parent and children:
                middle = xform
        return middle

    def get_xform_as_mpoint(self, object_name:str)->om.MPoint:
        """
        Retrieve the translation of an object as an MPoint.
        Non-performant - Should not be called from within a loop on a per point basis
                         (use om.MFnMesh.getPoint() to retrieve on a per point basis)

        :param str object_name:
        :return: the object's translation as an MPoint
        :rtype: om.MPoint
        """
        return om.MPoint(cmds.xform(object_name, query=True, translation=True, worldSpace=True))

    def get_xform_as_mvector(self, object_name: str) -> om.MVector:
        """
        Retrieve the translation of an object as an MVector.
        Non-performant - Should not be called from within a loop on a per point basis.
                         Instead use om.MFnMesh.getPoint's x,y,z to create and retrieve on a per
                         point basis.

        :param str object_name:
        :return: the object's translation as an MVector
        :rtype: om.MVector
        """
        position = cmds.xform(object_name, query=True, translation=True, worldSpace=True)
        return om.MVector(position[0], position[1], position[2])

    def project_point_to_plane(self, point:om.MVector,
                               plane_center:om.MVector,
                               plane_normal:om.MVector) -> tuple[om.MVector,
                                                                 om.MVector]:
        '''
        Projects a point vector onto an infinite plane defined by two vectors
        Use this point to get a normalized directional vector from the source point.

        :param om.MVector point: Must be normalized. The source plane direction.
        :param om.MVector plane_center: The target plane transform.
        :param om.MVector plane_normal: the vector being projected, the normalized direction
        :return: The projected point, the directional vector (point - projected point).
        :rtype: tuple[om.MVector, om.MVector]

        Move the point to the plane center then remove any perpendicular deviation with dot product
        Steps:
        1. Find the vector from the source point to the plane center.
        2. If there is any perpendicular to that movement, remove by subtracting the
           dot_product * plane_normal from the point
        3. Projected point = point-(dotProd·planeDir)
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
                                point_indices: list[int],
                                point_vectors: list[om.MVector],
                                start_point: om.MVector,
                                end_point: om.MVector,
                                threshold_start=0.1,
                                threshold_end=0.1
                                ) -> tuple[list[int], list[om.MVector]]:
        """
        Identify and return points that lie between the specified start and end points based on their
        projection onto the defined infinite planes created by these points.

        :param list[int] point_indices: Indices of the points in point_vectors being compared.
                                        This list will be filtered and returned. It is not used
                                        in any calculations.
        :param list[om.MVector] point_vectors: List of MVector instances representing point
                                               positions in world space.
        :param om.MVector start_point: Starting point in world space.
        :param om.MVector end_point: Ending point in world space.
        :param float threshold_start: Distance threshold from the start point, affecting the start
                                      plane projection. Default is 0.1.
        :param float threshold_end: Distance threshold from the end point, affecting the end plane
                                    projection. Default is 0.1.
        :return: A tuple containing:
            - list[int]: Indices of the points that lie between the start and end points.
            - list[om.MVector]: Points that lie between the start and end points based on their
                                projections onto the defined planes.
        :rtype: tuple[list[int], list[om.MVector]]
        """
        if threshold_start:
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
            # if they are 0 they are on a plane, technically not between, but we will treat
            # them as such
            if dot_product_start >= 0 and dot_product_end >= 0:
                return_indices.append(idx)
                return_point_vectors.append(point)

        return return_indices, return_point_vectors

    def move_to_plane_projection(self, obj_to_project, start_obj, end_obj, orient_startend=False):
        point_vector = self.get_xform_as_mvector(obj_to_project)
        start_vector = self.get_xform_as_mvector(start_obj)
        end_vector = self.get_xform_as_mvector(end_obj)
        
        plane_center = start_vector
        plane_normal = end_vector - start_vector
        plane_normal.normalize()

        projected_point =self.project_point_to_plane(point_vector, plane_center, plane_normal)[0]

        if orient_startend:
            self.aim_rotation(source_object=start_obj, target_object=end_obj)
            self.aim_rotation(source_object=end_obj, target_object=start_obj)

        cmds.xform(obj_to_project, worldSpace=True,
                   translation=(projected_point.x,
                                projected_point.y,
                                projected_point.z))

    def aim_rotation(self, source_object, target_object):
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
        
    def list_methods(self):
        """
        Returns a dictionary of all methods defined in the class with their descriptions.
        """
        methods = []
        for name, member in self.__class__.__dict__.items():
            if inspect.isfunction(member):
                methods.append((name))
        instance_methods = [f'self.{method}' for method in methods]
        if not cmds.about(batch=True):
            [print(method) for method in instance_methods]
        return instance_methods

    def create_debug_prim(self, name, cube_or_sphere=True, position=(0, 0, 0)):
        """
        creates primitives that can be used to visualize points.
        
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
        self.aim_rotation(source_object=from_plane, target_object=to_plane)
        self.aim_rotation(source_object=to_plane, target_object=from_plane)

        point_01 = self.get_xform_as_mvector(point_01)
        point_02 = self.get_xform_as_mvector(point_02)
        from_plane = self.get_xform_as_mvector(from_plane)
        to_plane = self.get_xform_as_mvector(to_plane)
        (to_plane)

        return point_01,point_02, from_plane, to_plane
            
    def color_points_start_end(self,
                               points,
                               weight_val_pairs,
                               color_start= (1, 0, 0),
                               color_end= (0, 0, 1)):
        """
        Colors points from start to end based on weight values to help visualize/debug weighting and
        weight normalization
        :param list[str] points: List of point names
        :param tuple[list[float], list[float]] weight_val_pairs: Tuple containing two lists of
                                                                 floats: start and end weights 
        :param (float, float, float) color_start: Color for the start point (default is red) 
        :param (float, float, float) color_end: Color for the end point (default is blue)
        """
        # to help visualize weight normalization

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


        color_mult_srt = [(col_srt[0] * vals, col_srt[1] * vals, col_srt[2] * vals) for vals in vals_srt]
        color_mult_end = [(col_end[0]*vals, col_end[1]*vals, col_end[2]*vals) for vals in vals_end]

        # mix the final colors
        final_colors = [(cs[0]+ ce[0], cs[1]+ ce[1], cs[2]+ ce[2])
                       for cs, ce in zip(color_mult_srt, color_mult_end)]

        for point, color in zip(points, final_colors):
            # relative flag false will not set by adding
            cmds.polyColorPerVertex(point, rgb=color, alpha=1, relative=False)
            
