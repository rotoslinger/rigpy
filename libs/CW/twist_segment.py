import json, math

from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma


import json
import math

from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma


def vec_lerp(vec_a, vec_b, lerp_amt=0.5) -> om.MVector:
    '''
    :param om.MVector vec_a: source vector 
    :param om.MVector vec_b: target vector 
    :param float lerp_amt: A float (usually) between 0 and 1 to control the interpolation.
                     Not clamped - so avoid unintentional over/undershooting.
    '''
    return ((vec_a - vec_b) * lerp_amt) + vec_a


def vec_lerp_multi(vec_a, vec_b, lerp_amt_list) -> list:      
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
        translation_tuples.append((interpolated_vector.x, interpolated_vector.y, interpolated_vector.z))

    return translation_tuples

def generate_lerp_weights(num_values=5, start=0.0, end=1.0) -> tuple:
    '''
    Generates linear interpolation weights between two values.

    Calculates lerp weights between a specified start and end value. The weights
    are normalized for the use of transitional rotation, stretching, and shaping.

    :param int num_values: Number of weights to generate. Default is 5.
    :param float start: The starting value for the interpolation. Default is 0.0.
    :param float end: The ending value for the interpolation. Default is 1.0.
    
    :return: A tuple containing two lists of weights; 
             the first, weights moving away from the start value, toward the end 
             the second, weights moving away from the end value, toward the start
    :rtype: (list, list)
    '''
    # TODO this is usually going to be normalized between 0-1 - may want to remove args

    # generic linear interpolate
    # L(t)=(1-t)·a+t·b lerp between two values, a and b, based on interp :param t

    # weight of first influence
    w0 = [(end + (t * (start - end) / (num_values + 1))) for t in range(1, num_values + 1)]
    # weight of second influence
    w1 = [end-w for w in w0]
    return w0,w1


def clone_jnt(src_jnt, new_jnt_name, orient=None,
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

def create_crv(pnts, name, parent, degree) -> str:
    crv = cmds.curve(p=pnts, d=degree, n=name)
    if parent: crv = cmds.parent(crv, parent)[0]
    return crv 

def create_crv_any(points, degree=3):
    num_cvs = len(points)
    required_knots = num_cvs + degree - 1
    knots = [i / (required_knots - 1) for i in range(required_knots)]
    curve = cmds.curve(p=points, k=knots, d=degree)
    cmds.rebuildCurve( curve, replaceOriginal=True,
                      #rebuildType=0, endKnots=1, keepControlPoints=False,
                      keepRange=0, keepEndPoints=False, keepTangents=0,
                      spans=6, degree=1, tolerance=0.01)
    return curve

def blend_rotations(tw_jnts, no_twist_jnt, twist_jnt, weights) -> list: # returns list of constraints
    tw_cnsts = []
    for idx, tw_jnt in enumerate(tw_jnts):
        tmp_cons = cmds.orientConstraint( no_twist_jnt, twist_jnt, tw_jnt ,#skip=['y','z'],
                                         maintainOffset=True)
        tw_cons=f'{tw_jnt}_seg_tw_cns{idx:02}'
        cmds.rename(tmp_cons, tw_cons)
        cmds.setAttr(f'{tw_cons}.w0', weights[0][idx])
        cmds.setAttr(f'{tw_cons}.w1', weights[1][idx])
        cmds.setAttr(f'{tw_cons}.interpType', 1)
        tw_cnsts.append(tw_cons)

def create_space_locator(name,parent):
    locator = cmds.createNode('transform', name=name, parent=parent)
    cmds.createNode('locator', parent=locator)
    return locator

### TODO Class Method ### 
def no_flip_ik_setup(start_jnt, end_jnt, component_parent,
                     name=None, suffix ='_no_flip', ik_type = 'ikSCsolver', do_twist=True) -> tuple:
    '''
    Single chain solver to avoid flipping. Avoids need for up vector.
    No flip end used as an orient constraint target for transitional falloff

    :param str start_jnt: only used in naming
    :param str end_jnt: only used to position the handle container
    :param str component_parent: the root parent of the component
    :param list tw_jnts: a list of the twist jnts
    :param list weights: weights to be used as normalized influences in the twist orientConstraint

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
            cmds.setAttr(f'{handle}.poleVector{axis}', lock=True)

    return handle


def setup_stretch(start_jnt, end_goal, stretch_jnts, wt1, name=None) -> None:
    '''
    Sets up world-space vector-based stretch joints.

    This stretch technique works only with floating joints in world space.
    Using joints in parent space will result in things not working properly.

    :param (str) start_jnt: The name of the starting joint for the stretch setup.
    :param (str) end_goal: The goal position to stretch towards in world space.
    :param (list) stretch_jnts: A list of joint names that will be stretched.
    :param (float) w1: The weight representing how far the end joint is from the start joint, 
                       calculated using generate_lerp_weights.
    :param (str) no_flip_orient_jnt: Optional; the joint used as a stable twist goal 
                                       for ry and rz orientation. If not specified, 
                                       the start joint will be used for orientation.
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
            cmds.setAttr(f'{lerp}.weight', round(wt1[idx], 8))


def create_buffer(obj_to_buffer, parent, num_buffers=3):
    buffers = []
    name_num = list(range(num_buffers))[::-1]
    for idx in range(num_buffers):
        buffer_parent=parent
        if idx > 0:
            buffer_parent = buffers[idx-1]
        buffers.append(cmds.createNode('transform', name=f'{obj_to_buffer}_bfr{name_num[idx]:02}', parent=buffer_parent))

    obj_to_buffer = cmds.parent(obj_to_buffer, buffers[-1])
    return buffers


### TODO Class Method ###
# this code here will work best in a class and should be converted 
# whether in whole or in part.
def create_twist_segment(start_bind_jnt, end_bind_jnt, rig_parent=None,
                         num_tw_jnts=5, suffix='Tw') -> dict:
    '''
    Creates a twist segment joint chain between a start and end joint, with additional
    twist joints for smooth deformation. This setup is commonly used in rigging for
    creating flexible body parts, such as limbs or spines, which need to twist smoothly
    over a range of joints.

    pargs given in order of parent,child - example: arm,elbow or elbow,hand  
    If the component is LeftArm_Seg: LeftArm_Tw00-05 should be parented to LeftArm

    Start to End directions all go in the parent-> child direction
          ↑  Neck  
    RArm ← → LArm  
          ↓  Spine  
    RLeg  ↓  LLeg  

    Structure:
    - Twist segment: start joint, end joint, and n number of twist joints in between.
    - Hierarchy: StartJnt-> Tw00-> Tw01-> Tw02-> Tw03-> Tw04 -> EndJnt.
    - No-flip and shaper joint options for additional control.
    - Debug mode includes additional joints for testing.

    :param str start_bind_jnt: Start joint for the twist segment.
    :param str end_bind_jnt: End joint for the twist segment.
    :param str end_bind_jnt: Optional end attachment point for the segment.
                           If None, defaults to end_bind_jnt
    :param str rig_parent: Parent transform for the rig parts of the twist component.
    :param str no_tw_parent: The parent of the start_bind_jnt if you want a no twist setup
                                 No twist setup means that the first jnt will not twist, but will
                                 pick up the ry, rz rotations.
                                 Defaults to start_bind_jnt if no arg given.
    :param int num_tw_jnts: Number of twist joints to create between start and end. Default is 5.
    :param str suffix: Name suffix for each twist joint. Default is 'Tw'.
    :param bool create_shaper_jnts: If True, adds extra joints for shape control.
    :param bool debug: Enables debug output and structure for testing. Default is True.

    :return:
        dict: Contains lists of created joints:
            - 'segment_chain': Main twist segment chain.
            - 'no_flip_parts': Components for the no-flip setup, including `ik_handle_null` and chain.
            - 'shaper_chain': Extra joints for shaping.
            - 'tw_jnts': Intermediate twist joints.
            - 'infl_weight_linear': Linear influence weights.
    '''

    vec_start = cmds.xform(start_bind_jnt, query=True, worldSpace=True, translation=True)
    vec_end = cmds.xform(end_bind_jnt, query=True, worldSpace=True, translation=True)
    vec_start = om.MVector(vec_start)
    vec_end = om.MVector(vec_end)
    
    wt0,wt1 = generate_lerp_weights(num_values=num_tw_jnts)
    
    component_root = cmds.createNode('transform', name=f'{start_bind_jnt}_segment_rig',
                                     parent=rig_parent)
    twist_ik_grp = cmds.createNode('transform', name=f'{start_bind_jnt}_segment_ik_chains',
                                     parent=component_root)


    # Primary chain start
    start_orient = clone_jnt(start_bind_jnt, 'tmp_jnt_name_DELETEME',
                                            parent=component_root, orient_only=True)[1]
    start_tw_jnt = cmds.createNode('joint', parent=None,
                            name=f'{start_bind_jnt}_{suffix}{0:02}')
    
    cmds.setAttr(f'{start_tw_jnt}.jointOrient', *start_orient, type='double3')
    start_tw_jnt=cmds.parent(start_tw_jnt, component_root)[0]

    start_tw_buffers = create_buffer(start_tw_jnt, parent=component_root, num_buffers=2)

    # No tw chain
    tw_ik_start_jnt = clone_jnt(start_bind_jnt, f'{start_bind_jnt}_seg_ik_tw',
                                  start_orient, twist_ik_grp)[0]
    tw_ik_end_jnt = clone_jnt(end_bind_jnt, f'{start_bind_jnt}_seg_ik_tw_end', 
                                start_orient, tw_ik_start_jnt)[0]
    no_tw_ik_start_jnt = clone_jnt(start_bind_jnt, f'{start_bind_jnt}_seg_ik_no_tw',
                                  start_orient, twist_ik_grp)[0]
    no_tw_ik_end_jnt = clone_jnt(end_bind_jnt, f'{start_bind_jnt}_seg_ik_no_tw_end', 
                                start_orient, no_tw_ik_start_jnt)[0]

    twist_jnts=[]
    tw_buf_parents=[]
    tw_buf_children=[]
    # NOTE: positioning the joints is taken care of in setup_stretch() below
    for idx in range(num_tw_jnts):
        counter=idx+1
        new_jnt = cmds.createNode('joint', parent=None,
                                  name=f'{start_bind_jnt}_{suffix}{counter:02}')
        cmds.setAttr(f'{new_jnt}.jointOrient', *start_orient, type='double3')
        new_jnt=cmds.parent(new_jnt, component_root)[0]
        twist_jnts.append(new_jnt)
        buffers = create_buffer(new_jnt, parent=component_root, num_buffers=2)
        tw_buf_parents.append(buffers[0])
        tw_buf_children.append(buffers[1])

    # create the no flip setup
    tw_ik_handle = no_flip_ik_setup(tw_ik_start_jnt, tw_ik_end_jnt,
                                  component_parent=component_root,
                                  suffix ='_0',
                                  ik_type = 'ikSCsolver')
    no_tw_ik_handle = no_flip_ik_setup(no_tw_ik_start_jnt, no_tw_ik_end_jnt,
                                        component_parent=component_root,
                                        suffix ='_1',
                                        ik_type = 'ikRPsolver', do_twist=False)

    blend_rotations(tw_buf_children,
                    no_twist_jnt=no_tw_ik_start_jnt,
                    twist_jnt=tw_ik_start_jnt,
                    weights=[wt0, wt1])

    # # No tw setup
    blend_rotations([start_tw_buffers[0]],
                    no_twist_jnt=no_tw_ik_start_jnt,
                    twist_jnt=tw_ik_start_jnt,
                    weights=[[1],[.0]])
    cmds.pointConstraint(start_bind_jnt, start_tw_buffers[0] ,mo=False)

    # Attach chains and handles to start and end
    cmds.parentConstraint(start_bind_jnt, twist_ik_grp, mo=True)
    cmds.parentConstraint(end_bind_jnt, tw_ik_handle, mo=True)
    cmds.parentConstraint(end_bind_jnt, no_tw_ik_handle, mo=True)

    setup_stretch(start_jnt=tw_ik_start_jnt, end_goal=end_bind_jnt,
                  stretch_jnts=tw_buf_parents, wt1=wt1,)
    

    all_twist_jnts = [start_tw_jnt] + twist_jnts
    tw_bind_jnts = []
    for idx, jnt in enumerate(all_twist_jnts):
        bind_jnt=cmds.createNode('joint', parent=start_bind_jnt,
                                            name=f'{start_bind_jnt}_bind_{suffix}{idx:02}')
        cmds.parentConstraint(jnt, bind_jnt, mo=False)
        tw_bind_jnts.append(bind_jnt)
        cmds.setAttr(f'{bind_jnt}.displayLocalAxis', 1)
