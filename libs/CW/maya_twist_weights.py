import json, statistics, re, math
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
        self.joint_name = joints
        
    
    def get_dag_path(self, object_name: str) -> om.MDagPath:
        '''
        Utility function to get the DAG path of an object.
        :param object_name: Name of the object
        :return: MDagPath of the object
        '''
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        dag_path = selection_list.getDagPath(0)
        return dag_path

    
    def get_xform_as_mvector(self, object_name: str) -> om.MVector:
        """
        Retrieve the translation of an object as an MVector.
        Do not loop: non-performant for vertex lists, should only be used for debugging
        :return: MVector of the object's translation
        """
        
        return om.MVector(cmds.xform(object_name, query=True, translation=True, worldSpace=True))
    
    
    def set_skin_weights(self, object_name):
        '''
        look at CW.skinweights_example.py for help with implementation
        '''

    
    def get_dag_path(self, object_name:str)->om.MDagPath:
        # Utility function to get the DAG path of an object
        selection_list = om.MSelectionList()
        selection_list.add(object_name)
        dag_path = selection_list.getDagPath(0)
        return dag_path
    
    
    def get_xform_as_mvector(self, object_name:str)->om.MVector:
        """
        Retrieve the translation of an object as an MVector.
        Do not loop: non-performant for vertex lists, should only be used for debugging
        """
        return om.MVector(cmds.xform(object_name, query=True, translation=True, worldSpace=True))
    

    def get_xform_as_mpoint(self, object_name:str)->om.MPoint:
        """
        Retrieve the translation of an object as an MVector.
        Do not loop: non-performant for vertex lists, should only be used for debugging
        """
        return om.MPoint(cmds.xform(object_name, query=True, translation=True, worldSpace=True))
    
    
    def point_direction_from_projection(self, 
                                        plane_direction:om.MVector,
                                        plane_center:om.MVector,
                                        point:om.MVector)->om.MVector:
        """
        Projects a point onto an infinite plane defined by two transforms, from_plane and to_plane.
        Then get a directional vector from the point to where it was projected on the plain
        Return the directional vector

        :param om.MVector from_plane: Must be normalized. The source plane direction.
        :param om.MVector to_plane: The target plane transform.
        :param om.MVector point: The point is an MVector that is usually derived from an MPoint
                                This function is usually run in a loop, so generating an MVector
                                when given a point would be non-performant.  Better to do it in a
                                list comprehension on a list of MPoints outside this function and then
                                pass it in as an arg.
        :return: The projected point as an MVector.
        :rtype: om.MVector
        """
        # Get the world-space positions of the from_plane and to_plane
            
        # # Calculate the direction from the from_plane to the to_plane
        # plane_direction = to_point - from_point
        
        # # Normalize the direction to get the plane's normal
        # plane_direction.normalize()

        # Project the point onto the plane along the normal direction
        point_to_plane = point - plane_center
        dot_product = point_to_plane * plane_direction

        # Project the point onto the plane
        # Move the point to the plane and remove any perpendicular deviation with dot product
        # Steps:
        # 1. find the vector length from the point to the plane center.
        # 2. if there is any perpendicular to that movement, remove by subtracting the
        #    dot_product·plane_direction from the point
        #projected point = point-(dotProd·planeDir)

        projected_point = point - dot_product * plane_direction
        
        directional_vector = point - projected_point
        directional_vector.normalize()
        
        return directional_vector
    
    
    def is_point_between_points(self, points, from_point, to_point):
        # get all points between two vectors

        if type(points) != list:
            points = [points]
        
        # Create a normalized vector from and vector to
        # These are directional vectors that are 'aiming' at one another.
        # from_point = get_xform_as_mvector(from_point)
        # to_point = get_xform_as_mvector(to_point)
        
        # Calculate the direction from the from_plane to the to_plane
        plane_direction = to_point - from_point
        
        # Normalize the direction to get the plane's normal
        plane_direction.normalize()

        vector_from = to_point - from_point
        vector_from.normalize()
        vector_to = from_point - to_point
        vector_to.normalize()

        return_points = []

        for point in points:
            # find the directional vector from the point to the from_plane representing an infinite plane

            # project the point to the to_plane
            # then create a directional vector from this point to where it was projected
            
            projected_point_from = self.point_direction_from_projection(plane_direction, from_point,  point)
            dot_product_from = projected_point_from * vector_from

            # print(f'The projected dot product of {point} from_plane : ', dot_product_from)

            # find the directional vector from the point to the to_plane representing an infinite plane

            # creates a point's directional vector by projecting to from_plane
            projected_point_to = self.point_direction_from_projection(plane_direction, to_point,  point)
            dot_product_to = projected_point_to * vector_to

            # print('The projected dot product of point_01 to_plane : ', dot_product_to)

            # if the point is between, both of the dot products will either 1.0 or .99999
            # if either are below 0 they are not between
            # if they are 0 they are on a plane, technically not between, but we will treat them as such
            if dot_product_from >= 0 and dot_product_to >= 0:
                return_points.append(point)

        # print('POINTS BEING RETURNED: ', return_points)
        # cmds.select(return_points)
        # return_points
        return return_points

    
    def point_indices_between_points(self,
                                     mfn_mesh:om.MFnMesh,
                                     point_indices:list[str],
                                     from_point:om.MVector,
                                     to_point:om.MVector) -> tuple[list[int], list[str]]:
        """
        :param list[str] point_indices: List of point names from Maya.
                        ``` ['maya_object.vtx[0]','maya_object.vtx[1]']
                        ```
                        
        :param om.MVector from_point: Starting point in world space.
        :param om.MVector to_point: Ending point in world space.
        :return:
        :rtype: list[int], list[str]
        """

        # # get the geom for the MFn geom obj
        # maya_object = maya_cmds_points[0].split('.')[0]
        
        # # Check object type to determine which MFn geom type you will be searching through.
        # # Reference --- 'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'
        # geom = cmds.listRelatives(maya_object,shapes=True)
        # obj_type = cmds.objectType(geom)
        # if obj_type not in COMPONENT_TYPE_MAP.keys():
        #     print(f'# Warning: Unsupported geometry type: {obj_type}. Please check your use of this function')
        #     return False
        # component_type = COMPONENT_TYPE_MAP[obj_type]
        # # TODO: Future implementation for MFnLattice, MFnNurbsCurve, MFnNurbsSurface functionality
        # #       will need to loop through vtx, cv, pt, using MFnLattice MFnNurbsCurve MFnNurbsSurface
        # # NOTE: for now I am hard coding component_type to be vtx because that is all the weighting we
        # #       need at this time.
        # component_type='vtx'

        # point_indices = [int(re.search(r'\[(\d+)\]', p).group(1)) for p in maya_cmds_points]
        # mfn_mesh = om.MFnMesh(self.get_dag_path(maya_object))
        point_vectors=[mfn_mesh.getPoint(p, space=om.MSpace.kWorld) for p in point_indices]
        point_vectors = [om.MVector(p.x,p.y,p.z) for p in point_vectors]
        
        # Calculate the direction of the from_plane to the to_plane
        direction = to_point - from_point
        
        # Normalize the direction to get the plane's normal
        direction.normalize()

        vector_from = to_point - from_point
        vector_from.normalize()
        vector_to = from_point - to_point
        vector_to.normalize()

        return_points = []
        return_indices = []
        for idx, point in zip(point_indices, point_vectors):
            # find the location of the point in relation to the from & to infinite planes
            # Project the point to the to_plane, create directional vector from point to projection
            projected_point_from = self.point_direction_from_projection(direction, from_point, point)
            # This will tell us if the point is outside of the from_point plane
            dot_product_from = projected_point_from * vector_from

            # Project the point to the from_plane, create directional vector from point to projection
            projected_point_to = self.point_direction_from_projection(direction, to_point,  point)
            # This will tell us if the point is outside of the from_point plane
            dot_product_to = projected_point_to * vector_to

            # if the point is between, both of the dot products will either 1.0 or .99999
            # if either are below 0 they are not between
            # if they are 0 they are on a plane, technically not between, but we will treat them as such
            if dot_product_from >= 0 and dot_product_to >= 0:
                return_points.append(point)
                return_indices.append(idx)
            # XXX: FOR DEBUG ONLY, this will cause a massive speed bottleneck! MAKE SURE TO DELETE
            # print(f'The projected dot product of {point} from_plane : ', dot_product_from)
            # print('The projected dot product of point_01 to_plane : ', dot_product_to)
            # XXX: FOR DEBUG ONLY, this will cause a massive speed bottleneck! MAKE SURE TO DELETE

        # Send it back to maya.cmd form
        # maya_point_objects = [f'{maya_object}.{component_type}[{idx}]' for idx in return_indices]
        return return_indices, point_vectors

    
    def create_rotation_from_objects(self, source_object, target_object):
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
        cmds.xform(source_object,rotation=(math.degrees(euler_rotation[0]),
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
        self.create_rotation_from_objects(source_object=from_plane, target_object=to_plane)
        self.create_rotation_from_objects(source_object=to_plane, target_object=from_plane)

        point_01 = self.get_xform_as_mvector(point_01)
        point_02 = self.get_xform_as_mvector(point_02)
        from_plane = self.get_xform_as_mvector(from_plane)
        to_plane = self.get_xform_as_mvector(to_plane)
        (to_plane)

        return point_01,point_02, from_plane, to_plane

    def mix_values_by_distance(self, 
                               point_indices: list[int],
                               from_point: om.MVector,
                               to_point: om.MVector,
                               from_inherit_wts: bool | list[float]=False,
                               to_inherit_wts: bool | list[float]=False,
                               val_start=0.0,
                               val_end=1.0):
        '''
        creates a paired weight normalization between two points.
        Run on a list that has been sorted and or culled
        It is assumed that this will be used after point lists have been created based on some
        arbitrary rule (distance, bounds, etc). 
        '''
    
    def color_points(self, points:list[str],
                     color_start:tuple[float,float,float] =(1, 0, 0),
                     color_end:tuple[float,float,float] =(0, 0, 1)):
        mesh = 'point_01'
        color_set = 'colorSet1'  # Name of the color set

        # mix_weights = mix_values_by_distance()
        vals_srt, vals_end = [0.1,0.2,0.3,1], [0.9,0.9,0.7,.0]

        # XXX: vals for ref
        col_srt = (1, 0, 0)
        col_end =  (0, 0, 1)

        # make 'em floats
        col_srt = (float(col_srt[0]), float(col_srt[1]), float(col_srt[2]))
        col_end = (float(col_end[0]), float(col_end[1]), float(col_end[2]))

        color_mult_srt = [(col_srt[0]*vals, col_srt[0]*vals, col_srt[0]*vals) for vals in vals_srt]
        color_mult_end = [(col_end[0]*vals, col_end[0]*vals, col_end[0]*vals) for vals in vals_end]

        # mix the final colors
        final_colors = [(cs[0]+ ce[0], cs[1]+ ce[1], cs[2]+ ce[2])
                       for cs, ce in zip(color_mult_srt, color_mult_end)]

        rgb_color = (0, 0, 1)  # RGB color values
        # blue = (0, 0, 1)  # RGB color values

        for point, color in zip(points, final_colors):
            # relative flag false will not set by adding
            cmds.polyColorPerVertex(point, rgb=color, alpha=1, relative=False) 

    
    def debug_find_points_between(self, points=[], do_test_objs=False):



        point_01, point_02, from_plane, to_plane = self.create_debug_objs()

        if points and 'vtx' in points[0]:
            # get the geom for the MFn geom obj
            maya_object = points[0].split('.')[0]
            # get the indices
            point_indices = [int(re.search(r'\[(\d+)\]', p).group(1)) for p in points]

            # Check object type to determine which MFn geom type you will be searching through.
            # Reference --- 'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt'
            geom = cmds.listRelatives(maya_object,shapes=True)
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
            mfn_mesh = om.MFnMesh(self.get_dag_path(maya_object))


            # point_indices = [int(re.search(r'\[(\d+)\]', p).group(1)) for p in points]
            mesh = points[0].split('.')[0]
            
            # mfn_mesh = om.MFnMesh(get_dag_path(mesh))
            # points=[mfn_mesh.getPoint(p, space=om.MSpace.kObject) for p in point_indices]
            # points = [om.MVector(p.x,p.y,p.z) for p in points]

            # first, find the point indices between.
            idx_list, point_vectors = self.point_indices_between_points(mfn_mesh, point_indices, from_plane, to_plane)
            print('vtx_indices_between', idx_list)
            point_names = [f'{mesh}.vtx[{idx}]' for idx in idx_list]
            cmds.select(point_names)
            
        if do_test_objs:
            point_indices = [0,1]
            points_as_vectors = [point_01, point_02]
            point_names = ['point_01', 'point_02']

            for name, vector in zip(point_names, points_as_vectors):
                sel_point = self.is_point_between_points(vector, from_plane, to_plane)
                if sel_point:
                    print(f'{name} is between the planes')



    # if point_01 in points:
    #     for vector in points:
    #         sel_point = is_point_between_points(vector, from_plane, to_plane)
    #         if sel_point:
    #             print(f'{vector} is between the planes')

twist_weights = Weights()
twist_weights.debug_find_points_between(do_test_objs=True)
points = ['point_01.vtx[0]', 'point_01.vtx[1]', 'point_01.vtx[2]', 'point_01.vtx[3]', 'point_01.vtx[4]', 'point_01.vtx[5]', 'point_01.vtx[6]', 'point_01.vtx[7]', 'point_01.vtx[8]', 'point_01.vtx[9]', 'point_01.vtx[10]', 'point_01.vtx[11]', 'point_01.vtx[12]', 'point_01.vtx[13]', 'point_01.vtx[14]', 'point_01.vtx[15]', 'point_01.vtx[16]', 'point_01.vtx[17]', 'point_01.vtx[18]', 'point_01.vtx[19]', 'point_01.vtx[20]', 'point_01.vtx[21]', 'point_01.vtx[22]', 'point_01.vtx[23]', 'point_01.vtx[24]', 'point_01.vtx[25]', 'point_01.vtx[26]', 'point_01.vtx[27]', 'point_01.vtx[28]', 'point_01.vtx[29]', 'point_01.vtx[30]', 'point_01.vtx[31]', 'point_01.vtx[32]', 'point_01.vtx[33]', 'point_01.vtx[34]', 'point_01.vtx[35]', 'point_01.vtx[36]', 'point_01.vtx[37]', 'point_01.vtx[38]', 'point_01.vtx[39]', 'point_01.vtx[40]', 'point_01.vtx[41]', 'point_01.vtx[42]', 'point_01.vtx[43]', 'point_01.vtx[44]', 'point_01.vtx[45]', 'point_01.vtx[46]', 'point_01.vtx[47]', 'point_01.vtx[48]', 'point_01.vtx[49]', 'point_01.vtx[50]', 'point_01.vtx[51]', 'point_01.vtx[52]', 'point_01.vtx[53]', 'point_01.vtx[54]', 'point_01.vtx[55]', 'point_01.vtx[56]', 'point_01.vtx[57]', 'point_01.vtx[58]', 'point_01.vtx[59]', 'point_01.vtx[60]', 'point_01.vtx[61]', 'point_01.vtx[62]', 'point_01.vtx[63]', 'point_01.vtx[64]', 'point_01.vtx[65]', 'point_01.vtx[66]', 'point_01.vtx[67]', 'point_01.vtx[68]', 'point_01.vtx[69]', 'point_01.vtx[70]', 'point_01.vtx[71]', 'point_01.vtx[72]', 'point_01.vtx[73]', 'point_01.vtx[74]', 'point_01.vtx[75]', 'point_01.vtx[76]', 'point_01.vtx[77]', 'point_01.vtx[78]', 'point_01.vtx[79]', 'point_01.vtx[80]', 'point_01.vtx[81]', 'point_01.vtx[82]', 'point_01.vtx[83]', 'point_01.vtx[84]', 'point_01.vtx[85]', 'point_01.vtx[86]', 'point_01.vtx[87]', 'point_01.vtx[88]', 'point_01.vtx[89]', 'point_01.vtx[90]', 'point_01.vtx[91]', 'point_01.vtx[92]', 'point_01.vtx[93]', 'point_01.vtx[94]', 'point_01.vtx[95]', 'point_01.vtx[96]', 'point_01.vtx[97]', 'point_01.vtx[98]', 'point_01.vtx[99]', 'point_01.vtx[100]', 'point_01.vtx[101]', 'point_01.vtx[102]', 'point_01.vtx[103]', 'point_01.vtx[104]', 'point_01.vtx[105]', 'point_01.vtx[106]', 'point_01.vtx[107]', 'point_01.vtx[108]', 'point_01.vtx[109]', 'point_01.vtx[110]', 'point_01.vtx[111]', 'point_01.vtx[112]', 'point_01.vtx[113]', 'point_01.vtx[114]', 'point_01.vtx[115]', 'point_01.vtx[116]', 'point_01.vtx[117]', 'point_01.vtx[118]', 'point_01.vtx[119]', 'point_01.vtx[120]', 'point_01.vtx[121]', 'point_01.vtx[122]', 'point_01.vtx[123]', 'point_01.vtx[124]', 'point_01.vtx[125]', 'point_01.vtx[126]', 'point_01.vtx[127]', 'point_01.vtx[128]', 'point_01.vtx[129]', 'point_01.vtx[130]', 'point_01.vtx[131]', 'point_01.vtx[132]', 'point_01.vtx[133]', 'point_01.vtx[134]', 'point_01.vtx[135]', 'point_01.vtx[136]', 'point_01.vtx[137]', 'point_01.vtx[138]', 'point_01.vtx[139]', 'point_01.vtx[140]', 'point_01.vtx[141]', 'point_01.vtx[142]', 'point_01.vtx[143]', 'point_01.vtx[144]', 'point_01.vtx[145]', 'point_01.vtx[146]', 'point_01.vtx[147]', 'point_01.vtx[148]', 'point_01.vtx[149]', 'point_01.vtx[150]', 'point_01.vtx[151]', 'point_01.vtx[152]', 'point_01.vtx[153]', 'point_01.vtx[154]', 'point_01.vtx[155]', 'point_01.vtx[156]', 'point_01.vtx[157]', 'point_01.vtx[158]', 'point_01.vtx[159]', 'point_01.vtx[160]', 'point_01.vtx[161]', 'point_01.vtx[162]', 'point_01.vtx[163]', 'point_01.vtx[164]', 'point_01.vtx[165]', 'point_01.vtx[166]', 'point_01.vtx[167]', 'point_01.vtx[168]', 'point_01.vtx[169]', 'point_01.vtx[170]', 'point_01.vtx[171]', 'point_01.vtx[172]', 'point_01.vtx[173]', 'point_01.vtx[174]', 'point_01.vtx[175]', 'point_01.vtx[176]', 'point_01.vtx[177]', 'point_01.vtx[178]', 'point_01.vtx[179]', 'point_01.vtx[180]', 'point_01.vtx[181]', 'point_01.vtx[182]', 'point_01.vtx[183]', 'point_01.vtx[184]', 'point_01.vtx[185]', 'point_01.vtx[186]', 'point_01.vtx[187]', 'point_01.vtx[188]', 'point_01.vtx[189]', 'point_01.vtx[190]', 'point_01.vtx[191]', 'point_01.vtx[192]', 'point_01.vtx[193]', 'point_01.vtx[194]', 'point_01.vtx[195]', 'point_01.vtx[196]', 'point_01.vtx[197]', 'point_01.vtx[198]', 'point_01.vtx[199]', 'point_01.vtx[200]', 'point_01.vtx[201]', 'point_01.vtx[202]', 'point_01.vtx[203]', 'point_01.vtx[204]', 'point_01.vtx[205]', 'point_01.vtx[206]', 'point_01.vtx[207]', 'point_01.vtx[208]', 'point_01.vtx[209]', 'point_01.vtx[210]', 'point_01.vtx[211]', 'point_01.vtx[212]', 'point_01.vtx[213]', 'point_01.vtx[214]', 'point_01.vtx[215]', 'point_01.vtx[216]', 'point_01.vtx[217]', 'point_01.vtx[218]', 'point_01.vtx[219]', 'point_01.vtx[220]', 'point_01.vtx[221]', 'point_01.vtx[222]', 'point_01.vtx[223]', 'point_01.vtx[224]', 'point_01.vtx[225]', 'point_01.vtx[226]', 'point_01.vtx[227]', 'point_01.vtx[228]', 'point_01.vtx[229]', 'point_01.vtx[230]', 'point_01.vtx[231]', 'point_01.vtx[232]', 'point_01.vtx[233]', 'point_01.vtx[234]', 'point_01.vtx[235]', 'point_01.vtx[236]', 'point_01.vtx[237]', 'point_01.vtx[238]', 'point_01.vtx[239]', 'point_01.vtx[240]', 'point_01.vtx[241]', 'point_01.vtx[242]', 'point_01.vtx[243]', 'point_01.vtx[244]', 'point_01.vtx[245]', 'point_01.vtx[246]', 'point_01.vtx[247]', 'point_01.vtx[248]', 'point_01.vtx[249]', 'point_01.vtx[250]', 'point_01.vtx[251]', 'point_01.vtx[252]', 'point_01.vtx[253]', 'point_01.vtx[254]', 'point_01.vtx[255]', 'point_01.vtx[256]', 'point_01.vtx[257]', 'point_01.vtx[258]', 'point_01.vtx[259]', 'point_01.vtx[260]', 'point_01.vtx[261]', 'point_01.vtx[262]', 'point_01.vtx[263]', 'point_01.vtx[264]', 'point_01.vtx[265]', 'point_01.vtx[266]', 'point_01.vtx[267]', 'point_01.vtx[268]', 'point_01.vtx[269]', 'point_01.vtx[270]', 'point_01.vtx[271]', 'point_01.vtx[272]', 'point_01.vtx[273]', 'point_01.vtx[274]', 'point_01.vtx[275]', 'point_01.vtx[276]', 'point_01.vtx[277]', 'point_01.vtx[278]', 'point_01.vtx[279]', 'point_01.vtx[280]', 'point_01.vtx[281]', 'point_01.vtx[282]', 'point_01.vtx[283]', 'point_01.vtx[284]', 'point_01.vtx[285]', 'point_01.vtx[286]', 'point_01.vtx[287]', 'point_01.vtx[288]', 'point_01.vtx[289]', 'point_01.vtx[290]', 'point_01.vtx[291]', 'point_01.vtx[292]', 'point_01.vtx[293]', 'point_01.vtx[294]', 'point_01.vtx[295]', 'point_01.vtx[296]', 'point_01.vtx[297]', 'point_01.vtx[298]', 'point_01.vtx[299]', 'point_01.vtx[300]', 'point_01.vtx[301]', 'point_01.vtx[302]', 'point_01.vtx[303]', 'point_01.vtx[304]', 'point_01.vtx[305]', 'point_01.vtx[306]', 'point_01.vtx[307]', 'point_01.vtx[308]', 'point_01.vtx[309]', 'point_01.vtx[310]', 'point_01.vtx[311]', 'point_01.vtx[312]', 'point_01.vtx[313]', 'point_01.vtx[314]', 'point_01.vtx[315]', 'point_01.vtx[316]', 'point_01.vtx[317]', 'point_01.vtx[318]', 'point_01.vtx[319]', 'point_01.vtx[320]', 'point_01.vtx[321]', 'point_01.vtx[322]', 'point_01.vtx[323]', 'point_01.vtx[324]', 'point_01.vtx[325]', 'point_01.vtx[326]', 'point_01.vtx[327]', 'point_01.vtx[328]', 'point_01.vtx[329]', 'point_01.vtx[330]', 'point_01.vtx[331]', 'point_01.vtx[332]', 'point_01.vtx[333]', 'point_01.vtx[334]', 'point_01.vtx[335]', 'point_01.vtx[336]', 'point_01.vtx[337]', 'point_01.vtx[338]', 'point_01.vtx[339]', 'point_01.vtx[340]', 'point_01.vtx[341]', 'point_01.vtx[342]', 'point_01.vtx[343]', 'point_01.vtx[344]', 'point_01.vtx[345]', 'point_01.vtx[346]', 'point_01.vtx[347]', 'point_01.vtx[348]', 'point_01.vtx[349]', 'point_01.vtx[350]', 'point_01.vtx[351]', 'point_01.vtx[352]', 'point_01.vtx[353]', 'point_01.vtx[354]', 'point_01.vtx[355]', 'point_01.vtx[356]', 'point_01.vtx[357]', 'point_01.vtx[358]', 'point_01.vtx[359]', 'point_01.vtx[360]', 'point_01.vtx[361]', 'point_01.vtx[362]', 'point_01.vtx[363]', 'point_01.vtx[364]', 'point_01.vtx[365]', 'point_01.vtx[366]', 'point_01.vtx[367]', 'point_01.vtx[368]', 'point_01.vtx[369]', 'point_01.vtx[370]', 'point_01.vtx[371]', 'point_01.vtx[372]', 'point_01.vtx[373]', 'point_01.vtx[374]', 'point_01.vtx[375]', 'point_01.vtx[376]', 'point_01.vtx[377]', 'point_01.vtx[378]', 'point_01.vtx[379]', 'point_01.vtx[380]', 'point_01.vtx[381]']
twist_weights.debug_find_points_between(points, do_test_objs=True)
#print('worked!')



