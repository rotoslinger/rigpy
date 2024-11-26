from maya import cmds
import maya.api.OpenMaya as om


class SegmentRig:
    def __init__(self, start_jnt, end_jnt, rig_parent=None,
                 num_tw_jnts=5, jnt_suffix='tw'):
        '''
        Creates a twist segment joint chain between a start and end joint, with additional
        twist joints for smooth deformation. This setup is commonly used in rigging for
        creating flexible body parts, such as limbs or spines, which need to twist smoothly
        over a range of joints.

        pargs given in order of parent,child - example: arm,elbow or elbow,hand  
        If the component is LeftArm_Seg: LeftArm_Tw00-05 should be parented to LeftArm

        Start to End directions all go in the direction of parent -> child
              ↑  Neck  
        RArm ← → LArm  
              ↓  Spine  
        RLeg  ↓  LLeg  

        creates a start twist joint and n number of twist joints in between.

        :param str start_jnt: Start joint for the twist segment.
        :param str end_jnt: End joint for the twist segment.
        :param str rig_parent: Parent transform for the rig parts of the twist component.
        :param int num_tw_jnts: Number of twist joints to create between start and end. Default 5.
        :param str suffix: Name suffix for each twist joint. Default is 'Tw'.
        '''
        self.start_jnt = start_jnt
        self.end_jnt = end_jnt
        self.rig_parent = rig_parent
        self.num_tw_jnts = num_tw_jnts
        self.jnt_suffix = jnt_suffix

    def run(self):
        self.__generate_lerp_weights()
        self.__create_parent_groups()
        self.__create_joints()
        self.cleanup_objs=[]
        self.tw_ik_handle = self.__no_flip_ik_setup(self.tw_ik_start_jnt, self.tw_ik_end_jnt,
                                            component_parent=self.component_root,
                                            suffix='_0',
                                            ik_type='ikSCsolver')
        self.no_tw_ik_handle = self.__no_flip_ik_setup(self.no_tw_ik_start_jnt, self.no_tw_ik_end_jnt,
                                                component_parent=self.component_root,
                                                suffix='_1',
                                                ik_type='ikRPsolver', do_twist=False)
        # blend rotations for between twists
        self.__blend_rotations(self.tw_buf_children,
                            no_twist_jnt=self.no_tw_ik_start_jnt,
                            twist_jnt=self.tw_ik_start_jnt,
                            weights=[self.wt0, self.wt1])

        # blend rotations for start tw
        self.__blend_rotations([self.start_tw_buf_parent], 
                            no_twist_jnt=self.no_tw_ik_start_jnt,
                            twist_jnt=self.tw_ik_start_jnt,
                            weights=[[1], [.0]])
        # blend rotations for end tw
        self.__blend_rotations([self.end_tw_buf_parent], 
                            no_twist_jnt=self.no_tw_ik_start_jnt,
                            twist_jnt=self.tw_ik_start_jnt,
                            weights=[[0.0], [1.0]])
        
        cmds.pointConstraint(self.start_jnt, self.start_tw_buf_parent, mo=False)
        cmds.pointConstraint(self.end_jnt, self.end_tw_buf_parent, mo=False)

        # Attach chains and handles to start and end
        cmds.parentConstraint(self.start_jnt, self.ik_joints_group, mo=True)
        cmds.parentConstraint(self.end_jnt, self.tw_ik_handle, mo=True)
        cmds.parentConstraint(self.end_jnt, self.no_tw_ik_handle, mo=True)

        self.__setup_stretch(start_jnt=self.tw_ik_start_jnt, end_goal=self.end_jnt,
                        stretch_jnts=self.tw_buf_parents, vector_weights=self.wt1)
        

        self.twist_jnts = [self.start_tw_jnt] + self.between_twist_jnts + [self.end_tw_jnt]
        self.twist_joints_out = []
        for idx, jnt in enumerate(self.twist_jnts):
            bind_jnt = cmds.createNode('joint', parent=self.start_jnt,
                                    name=f'{self.start_jnt}_bind_{self.jnt_suffix}{idx:02}')
            cmds.parentConstraint(jnt, bind_jnt, mo=False)
            self.twist_joints_out.append(bind_jnt)

        # cleanup
        self.__cleanup_rig()

    def __cleanup_rig(self):
        cleanup_objs = [self.tw_ik_handle,
                        self.no_tw_ik_handle,
                        *self.twist_jnts,
                        *self.twist_joints_out,
                        self.ik_joints_group,
                       ]   
        for obj in cleanup_objs:
            cmds.setAttr(f'{obj}.v', 0)

    def connect_global_scale(self, driver):
        cmds.scaleConstraint(driver, self.ik_joints_group, mo=True)

    def __create_parent_groups(self):
        self.component_root = cmds.createNode('transform', name=f'{self.start_jnt}_segment_grp',
                                        parent=self.rig_parent)
        self.ik_joints_group = cmds.createNode('transform', name=f'{self.start_jnt}_segment_ik_chains',
                                        parent=self.component_root)
        cmds.setAttr(f'{self.component_root}.inheritsTransform', 0)

    def __create_joints(self):
        start_orient = self.__clone_jnt(self.start_jnt, 'tmp_jnt_name_DELETEME',
                                    parent=self.component_root, orient_only=True)[1]
        self.start_tw_jnt = cmds.createNode('joint', parent=None,
                                            name=f'{self.start_jnt}_{self.jnt_suffix}{0:02}')
        end_num = self.num_tw_jnts + 1
        self.end_tw_jnt = cmds.createNode('joint', parent=None,
                                            name=f'{self.start_jnt}_{self.jnt_suffix}{end_num:02}')

        cmds.setAttr(f'{self.start_tw_jnt}.jointOrient', *start_orient, type='double3')
        cmds.setAttr(f'{self.end_tw_jnt}.jointOrient', *start_orient, type='double3')
        self.start_tw_jnt = cmds.parent(self.start_tw_jnt, self.component_root)[0]
        self.end_tw_jnt = cmds.parent(self.end_tw_jnt, self.component_root)[0]

        start_tw_buffers = self.create_buffer(self.start_tw_jnt,
                                              parent=self.component_root,
                                              num_buffers=2)
        self.start_tw_buf_parent = start_tw_buffers[0]
        self.start_tw_buf_child = start_tw_buffers[1]

        end_tw_buffers = self.create_buffer(self.end_tw_jnt,
                                              parent=self.component_root,
                                              num_buffers=2)
        self.end_tw_buf_parent = end_tw_buffers[0]
        self.end_tw_buf_child = end_tw_buffers[1]

        # No tw chain
        self.tw_ik_start_jnt = self.__clone_jnt(self.start_jnt,
                                              f'{self.start_jnt}_seg_ik_tw',
                                              start_orient, self.ik_joints_group)[0]
        self.tw_ik_end_jnt = self.__clone_jnt(self.end_jnt,
                                            f'{self.start_jnt}_seg_ik_tw_end', 
                                            start_orient, self.tw_ik_start_jnt)[0]
        self.no_tw_ik_start_jnt = self.__clone_jnt(self.start_jnt,
                                                 f'{self.start_jnt}_seg_ik_no_tw',
                                                 start_orient, self.ik_joints_group)[0]
        self.no_tw_ik_end_jnt = self.__clone_jnt(self.end_jnt,
                                               f'{self.start_jnt}_seg_ik_no_tw_end',
                                               start_orient, self.no_tw_ik_start_jnt)[0]

        self.between_twist_jnts = []
        self.tw_buf_parents = []
        self.tw_buf_children = []

        # NOTE: positioning the joints is taken care of in self.setup_stretch connectAttrs
        for idx in range(self.num_tw_jnts):
            counter = idx + 1
            new_jnt = cmds.createNode('joint', parent=None,
                                    name=f'{self.start_jnt}_{self.jnt_suffix}{counter:02}')
            cmds.setAttr(f'{new_jnt}.jointOrient', *start_orient, type='double3')
            new_jnt = cmds.parent(new_jnt, self.component_root)[0]
            self.between_twist_jnts.append(new_jnt)
            buffers = self.create_buffer(new_jnt, parent=self.component_root, num_buffers=2)
            self.tw_buf_parents.append(buffers[0])
            self.tw_buf_children.append(buffers[1])

    def __generate_lerp_weights(self):
        # Hard coding start and end for now. In the future we may want to give them as args
        # These values normalize the weights between 0-1.
        start=0.0
        end=1.0

        # generic linear interpolate
        # L(t)=(1-t)·a+t·b lerp between two values, a and b, based on interp :param t

        # weight of first influence
        self.wt0 = [(end + (t * (start - end) / (self.num_tw_jnts + 1)))
                    for t in range(1, self.num_tw_jnts + 1)]
        # weight of second influence
        self.wt1 = [end-w for w in self.wt0]

    def __clone_jnt(self, src_jnt, new_jnt_name, orient=None,
                parent=None, orient_only=False) -> tuple: # type str, f3tuple
        '''
        Meant to duplicate joints in place, with more control over how orientation is handled.
        It also returns the orientation for use in other joint creation.
        
        '''
        # important parent arg None at create for orient
        new_jnt = cmds.createNode('joint', name=new_jnt_name, parent=None)
        tmp_cons = cmds.parentConstraint(src_jnt, new_jnt)
        cmds.delete(tmp_cons)
        cmds.makeIdentity(new_jnt, apply=True,
                        rotate=True, scale=True, jointOrient=False)
        if not orient:
            # get while in world.
            orient = cmds.getAttr(f'{new_jnt}.jointOrient')[0]
        if parent: new_jnt = cmds.parent(new_jnt, parent)[0]
        if orient_only:
            cmds.delete(new_jnt)
            return None, orient
        return new_jnt, orient

    def create_crv(self, pnts, name, parent, degree) -> str:
        crv = cmds.curve(p=pnts, d=degree, n=name)
        if parent: crv = cmds.parent(crv, parent)[0]
        return crv

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

    def __blend_rotations(self, tw_jnts, no_twist_jnt, twist_jnt, weights):
        for idx, tw_jnt in enumerate(tw_jnts):
            tmp_cons = cmds.orientConstraint( no_twist_jnt, twist_jnt, tw_jnt ,
                                            maintainOffset=False)
            tw_cons=f'{tw_jnt}_seg_tw_cns{idx:02}'
            cmds.rename(tmp_cons, tw_cons)
            cmds.setAttr(f'{tw_cons}.w0', weights[0][idx])
            cmds.setAttr(f'{tw_cons}.w1', weights[1][idx])
            cmds.setAttr(f'{tw_cons}.interpType', 1)

    def create_space_locator(self, name,parent):
        locator = cmds.createNode('transform', name=name, parent=parent)
        cmds.createNode('locator', parent=locator)
        return locator
    
    def __no_flip_ik_setup(self, start_jnt, end_jnt, component_parent,
                        name=None, suffix ='_no_flip', ik_type = 'ikSCsolver',
                        do_twist=True):
        '''
        Single chain solver to avoid flipping. Avoids need for up vector.
        No flip end used as an orient constraint target for transitional falloff

        :param str start_jnt: only used in naming
        :param str end_jnt: only used to position the handle container
        :param str component_parent: the root parent of the component
        :param list tw_jnts: a list of the twist jnts
        :param list weights: weights to be used as normalized influences in the twist
                             orientConstraint
        '''
        if not name: name=start_jnt

        handle, effector = cmds.ikHandle(startJoint=start_jnt, endEffector=end_jnt,
                                        sol=ik_type, name=f'{name}_seg{suffix}_hdl')
        handle = cmds.parent(handle, component_parent)[0]
        cmds.rename(effector, f'{name}_seg{suffix}_eff')
        effector = f'{name}_seg{suffix}_eff'
        if not do_twist:
            for axis in ['X', 'Y', 'Z']:
                cmds.setAttr(f'{handle}.poleVector{axis}', 0)
                # cmds.setAttr(f'{handle}.poleVector{axis}', lock=True)

        return handle

    def __setup_stretch(self, start_jnt, end_goal, stretch_jnts, vector_weights, name=None):
        '''
        Sets up world-space vector-based stretch joints.

        This stretch technique works only with floating joints in world space.
        Using joints in parent space will result in things not working properly.

        :param str start_jnt: The name of the starting joint for the stretch setup.
        :param str end_goal: The goal position to stretch towards in world space.
        :param list stretch_jnts: A list of joint names that will be stretched.
        :param list vector_weights: The weight representing how far the end joint is from the
                                    start joint - calculated using self.generate_lerp_weights
        :param (str) name: Optional; a custom name for the setup.
        '''
        # collect any missing customization args
        if not name: name = start_jnt

        # translation from matrix for start and end joint
        vec0 = cmds.createNode('translationFromMatrix', name=f'{end_goal}_src_matrix')
        vec1 = cmds.createNode('translationFromMatrix', name=f'{end_goal}_tgt_matrix')
        cmds.connectAttr(f'{start_jnt}.worldMatrix', f'{vec0}.input')
        cmds.connectAttr(f'{end_goal}.worldMatrix', f'{vec1}.input')

        # enter jnt loop
        for idx, jnt in enumerate(stretch_jnts):
            for trn, axis in zip(['tx','ty','tz'],['X','Y','Z']):
                # too much typing, loop through axes
                lerp=cmds.createNode('lerp', name=f'{jnt}_lerp_{trn}')

                # ex: matrix0.outputX  -> lerpTx.input1
                cmds.connectAttr(f'{vec0}.output{axis}', f'{lerp}.input1')
                # ex: matrix1.outputX  -> lerpTx.input2
                cmds.connectAttr(f'{vec1}.output{axis}', f'{lerp}.input2')

                # ex: lerp.output -> joint.tx
                cmds.connectAttr(f'{lerp}.output', f'{jnt}.{trn}')
                # ex: set attr: lerp.weight -> 0.5 == 50% between matrix0 & matrix1)
                cmds.setAttr(f'{lerp}.weight', round(vector_weights[idx], 8))

    def create_buffer(self, obj_to_buffer, parent, num_buffers=3):
        buffers = []
        name_num = list(range(num_buffers))[::-1]
        for idx in range(num_buffers):
            buffer_parent=parent
            if idx > 0:
                buffer_parent = buffers[idx-1]
            buffers.append(cmds.createNode('transform',
                                           name=f'{obj_to_buffer}_bfr{name_num[idx]:02}',
                                           parent=buffer_parent))

        obj_to_buffer = cmds.parent(obj_to_buffer, buffers[-1])
        return buffers
    
    def vec_lerp(self, vec_a, vec_b, lerp_amt=0.5) -> om.MVector:
        '''
        :param om.MVector vec_a: source vector 
        :param om.MVector vec_b: target vector 
        :param float lerp_amt: A float (usually) between 0 and 1 to control the interpolation.
                        Not clamped - so avoid unintentional over/undershooting.
        '''
        return ((vec_a - vec_b) * lerp_amt) + vec_a

    def vec_lerp_multi(self, vec_a, vec_b, lerp_amt_list) -> list:      
        '''
        Performs linear interpolation between two vectors for multiple weights.

        This function calculates interpolated vectors based on a list of lerp amounts,
        allowing for smooth transitions between two source vectors.

        :param om.MVector vec_a: The source vector from which the lerp begins.
        :param om.MVector vec_b: The target vector toward which the lerp proceeds.
        :param list lerp_amt_list: A list of float values, usually between 0 and 1, that control
                                the lerp amount. Values are not clamped, so care should
                                be taken to avoid unintended over/undershooting.
        
        :return: A list of tuples representing the interpolated vectors, each as (tx, ty, tz).
        :rtype: list of (float, float, float)
        '''
        translation_tuples = []
        for lerp_amt in lerp_amt_list:
            # Calculate the interpolated vector
            interpolated_vector = ((vec_b- vec_a) * lerp_amt) + vec_a
            
            # Append the translation as a tuple (x, y, z)
            translation_tuples.append((interpolated_vector.x,
                                       interpolated_vector.y,
                                       interpolated_vector.z))

        return translation_tuples
