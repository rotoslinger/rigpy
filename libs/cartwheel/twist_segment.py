import json, math

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
        interpolated_vector = ((vec_b - vec_a) * lerp_amt) + vec_a
        
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
    w0 = [(start + (t * (end - start) / (num_values + 1))) for t in range(1, num_values + 1)]
    # weight of second influence
    w1 = [end-w for w in w0]
    return w0,w1


### TODO REMOVE ###
# get/setAttr will probably suffice, but leaving in for now
def get_jnt_orient(jnt):
    selection = om.MSelectionList()
    selection.add(jnt)
    joint_dag_path = selection.getDagPath(0)
    joint_fn = oma.MFnIkJoint(joint_dag_path)
    joint_orient = joint_fn.orientation()
    return joint_orient

def set_jnt_orient(jnt, orient):
    selection = om.MSelectionList()
    selection.add(jnt)
    joint_dag_path = selection.getDagPath(0)
    joint_fn = oma.MFnIkJoint(joint_dag_path)
    joint_orient = joint_fn.setOrientation(orient)
    return joint_orient
### TODO REMOVE ###


def clone_jnt(src_jnt, new_jnt_name, orient=None, parent=None) -> tuple: # type str, f3tuple
    '''
    Meant to avoid cmds.duplicate - this func gives users more control
    over how the orientation is handled. It also returns said orientation.
    
    :param str src_jnt: The source joint to clone.
    :param str new_jnt_name: The name for the new joint.
    :param str orient: Optional; the orientation for the new joint.
    :param str parent: Optional; the parent joint for the new joint.
    :return: A tuple of the new joint name and its orientation.
    :rtype: tuple
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

### TODO Class Method ### 
def no_flip_ik_setup(start_jnt, end_jnt, name,
                     component_parent, suffix ='_no_flip', ik_type = 'ikSCsolver') -> tuple:
    '''
    Single chain solver to avoid flipping. Avoids need for up vector.
    No flip end used as an orient constraint target for transitional falloff

    :param str start_jnt: only used in naming
    :param str end_jnt: only used to position the handle container
    :param str component_parent: the root parent of the component
    :param list tw_jnts: a list of the twist jnts
    :param list weights: weights to be used as normalized influences in the twist orientConstraint

    '''
    handle_null = cmds.createNode('transform', name=f'{name}_seg{suffix}_null', parent=component_parent)

    translate = cmds.xform(end_jnt, query=True, translation=True, worldSpace=True)
    cmds.xform(handle_null, translation=translate, worldSpace=True)
    cmds.makeIdentity(handle_null, apply=True, translate=True)

    handle, effector = cmds.ikHandle(startJoint=start_jnt, endEffector=end_jnt,
                                     sol=ik_type, sticky='sticky', name=f'{name}_seg{suffix}_hdl')
    handle = cmds.parent(handle, handle_null)[0]
    cmds.rename(effector, f'{name}_seg{suffix}_eff')
    effector = f'{name}_seg{suffix}_eff'
    for attr in ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']:
        cmds.setAttr(f'{handle}{attr}', lock=True)# avoid accidental movement
        cmds.setAttr(f'{effector}{attr}', lock=True)# avoid accidental movement

    return handle_null, handle


def setup_bend_bow():
    '''
    placeholder func for creating a sline ik to give bend bow functionality
    '''


def setup_stretch(start_jnt, end_goal, stretch_jnts, wt1,
                  no_flip_orient_jnt=None, name=None) -> None:
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
    if not no_flip_orient_jnt: no_flip_orient_jnt = start_jnt

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

            # # orient constrain to ik
            # cns=cmds.orientConstraint(no_flip_orient_jnt, jnt, 
            #                             skip = 'x', maintainOffset=False)


### TODO Class Method ###
# this code here will work best in a class and should be converted 
# whether in whole or in part.
def create_twist_segment(start_bind_jnt, end_bind_jnt,
                         end_attach=None, rig_parent=None,
                         no_tw_jnt=True, num_tw_jnts=5, suffix='Tw', 
                         create_shaper_jnts=False,
                         debug=True) -> dict:
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
    :param str end_attach: Optional end attachment point for the segment.
                           If None, defaults to end_bind_jnt
    :param str rig_parent: Parent transform for the rig parts of the twist component.
    :param bool no_tw_jnt: If True, includes a no-twist joint at the start. Default is True.
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
    translations = vec_lerp_multi(vec_start, vec_end, wt0)
    
    component_root = cmds.createNode('transform', name=f'{start_bind_jnt}_segment_rig',
                                     parent=rig_parent)

    # Primary chain start
    seg_start_jnt, start_orient = clone_jnt(start_bind_jnt, f'{start_bind_jnt}_seg_start',
                                            parent=component_root)
    
    # No flip chain
    tw_ik_start_jnt = clone_jnt(seg_start_jnt, f'{start_bind_jnt}_seg_ik_tw_start',
                                  start_orient, seg_start_jnt)[0]
    tw_ik_end_jnt = clone_jnt(end_bind_jnt, f'{start_bind_jnt}_seg_ik_tw_end', 
                                start_orient, tw_ik_start_jnt)[0]
    
    no_twist_ik_start_jnt = clone_jnt(seg_start_jnt, f'{start_bind_jnt}_seg_no_tw_start',
                                  start_orient, seg_start_jnt)[0]
    no_tw_ik_end_jnt = clone_jnt(end_bind_jnt, f'{start_bind_jnt}_seg_no_tw_end', 
                                start_orient, no_twist_ik_start_jnt)[0]

    no_tw_shldr_jnt=None
    no_tw_jnt=cmds.listRelatives(start_bind_jnt, parent=True)
    if no_tw_jnt: no_tw_jnt = no_tw_jnt[0]
    if not no_tw_jnt: no_tw_jnt = start_bind_jnt

    if no_tw_jnt:
        no_tw_shldr_jnt = clone_jnt(start_bind_jnt, f'{start_bind_jnt}_seg_start_jnt',
                                    start_orient, component_root)[0]

        ### TODO FLIP TEST ###
        # # make sure to test flipping with single channel orient constraint
        cmds.orientConstraint(no_tw_jnt, no_tw_shldr_jnt, skip=['y', 'z'], mo=True)
        ### TODO FLIP TEST ###
    

    twist_jnts=[]
    for idx in range(num_tw_jnts):
        new_jnt = cmds.createNode('joint', parent=None,
                                  name=f'{start_bind_jnt}_{suffix}{idx:02}')
        cmds.xform(new_jnt, worldSpace=True, translation=translations[idx])
        cmds.setAttr(f'{new_jnt}.jointOrient', *start_orient, type='double3')

        new_jnt=cmds.parent(new_jnt, component_root)[0]

        twist_jnts.append(new_jnt)

    # create the no flip setup
    tw_ik_null_cons=''
    if not end_attach: end_attach = end_bind_jnt

    tw_ik_null, tw_ik_handle = no_flip_ik_setup(tw_ik_start_jnt, tw_ik_end_jnt,
                                                name=start_bind_jnt,
                                                component_parent=seg_start_jnt,
                                                suffix ='_tw',
                                                ik_type='ikSCsolver')
    no_tw_ik_null, no_tw_ik_handle = no_flip_ik_setup(no_twist_ik_start_jnt, no_tw_ik_end_jnt,
                                                      name=start_bind_jnt,
                                                      component_parent=seg_start_jnt,
                                                      suffix ='_no_tw',
                                                      ik_type='ikRPsolver')

    # fallback to end_bind_jnt if end_attach is not specified
    if not end_attach: end_attach = end_bind_jnt
    tw_ik_null_cons = cmds.parentConstraint(end_attach, tw_ik_null, mo=True)
    no_tw_ik_null_cons = cmds.pointConstraint(end_attach, no_tw_ik_null, mo=True)

    blend_rotations(twist_jnts,
                    no_twist_jnt=no_twist_ik_start_jnt,
                    twist_jnt=tw_ik_start_jnt,
                    weights=[wt0,wt1])

    setup_stretch(start_jnt=tw_ik_start_jnt, end_goal=end_attach,
                  stretch_jnts=twist_jnts, wt1=wt1, no_flip_orient_jnt=tw_ik_start_jnt,)

    
    shaper_jnts = []
    if create_shaper_jnts:
        jnts_to_clone = [seg_start_jnt, *twist_jnts, end_bind_jnt]
        for idx, jnt in enumerate(jnts_to_clone):
            no_tw_jnt = seg_start_jnt
            if idx > 0: no_tw_jnt = shaper_jnts[idx-1]
            shaper_jnts.append(clone_jnt(jnt, f'{start_bind_jnt}_shaper_jnt{idx:02}',
                                         start_orient, no_tw_jnt)[0])
        # create bend bow ik spline
        setup_bend_bow()
    ### TODO REVALUATE ###
    # may not need
    # crv_seg_linear = create_crv(pnts=[vec_start,vec_end],name=f'{start_joint}_LineCrv',
    #                             degree=1, parent=component_parent) 
    # crv_seg_nurbs = create_crv(pnts=[vec_start, *translations, vec_end],
    #                            name=f'{start_joint}_ShaperCrv',
    #                            degree=1, parent=component_parent) 
    # create_normalized_curve([vec_start, *translations, vec_end])
    ### TODO REVALUATE ###

    # return map:
    tw_map = {'segment_chain':[seg_start_jnt],
            'no_flip_parts': {'chain':[tw_ik_start_jnt, tw_ik_end_jnt],
                            'tw_ik':[tw_ik_null,tw_ik_handle],
                            'no_tw_ik':[no_tw_ik_null,no_tw_ik_handle],
                            'handle_null_cons':tw_ik_null_cons},
            'shaper_chain':shaper_jnts,
            'tw_jnts':twist_jnts,                
            'infl_weight_linear':[wt0,wt1]}
    ### TODO REMOVE ###
    #if debug: print(json.dumps(out_joints, indent=4))
    ### TODO REMOVE ###

    return tw_map


def jnt_shaper_curve_attach():

    '''
        This will need extremely thorough testing to make sure flipping does not happen.


        drive the shaper curve with the linear curve by creating a wire deformer
            wire deformer = linear curve -> shaper curve
        attach a 2 point linear curve to the start and end joints
            start.worldMatrix -> translationFromMatrix_start -> crv.controlPoints[0]
            end.worldMatrix -> translationFromMatrix_end -> crv.controlPoints[1]
        for each tw jnts
            turn off inherit transform
            remove inverse scale from parent
            add scale from parent? probably a good idea


    '''



# # Example call
# twist_segment.create_twist_segment(start_joint='LeftArm',
#                                    end_joint='LeftForeArm',
#                                    parent=None,
#                                    num_tw_jnts=5, suffix='Tw',)

r'''

twist segment, prototype that has a start jnt, end jnt, and n number of tw between the two.

Hier looks like : StartJnt->Tw00->Tw01->Tw02->Tw03->Tw05->EndJnt  (all parented to StartJnt).

Twist count isn't limited but defaults to 5.

StartJnt, EndJnt are parentConstrained to  LeftArm, LeftForeArm.

As the arm jnts move or rotate you get twist and stretch between.

You don't have to worry about multiple IK/FK joint chains because these could be constrained to your skin joints.

The idea is that it doesn't interfere with any structural rigging

goes along for the ride without creating any dependencies or complicating any IK/FK switching.

'''


def bezier_curve_with_symmetric_handles(y_points, handle_lengths, num_samples):
    """
    Generate points for a cubic Bézier curve with symmetric handles.

    Parameters:
    - y_points: list of three floats [y0, y1, y2] for the control points.
    - handle_lengths: list of three floats [h0, h1, h2] for the handle lengths.
    - num_samples: int - The number of output points along the curve.

    Returns:
    - bezier_points: List of tuples representing the points on the Bézier curve.
    """
    # Control points for the cubic Bézier spline
    P0 = (0, y_points[0])  # Starting point
    P1 = (handle_lengths[0], y_points[0])  # Control point 1 influenced by handle length
    P2 = (handle_lengths[1], y_points[1])  # Control point 2 at the midpoint
    P3 = (handle_lengths[2], y_points[2])  # Control point 3 influenced by handle length
    P4 = (2 * handle_lengths[2], y_points[2])  # End point

    bezier_points = []

    # Calculate points along the cubic Bézier curve
    for t in range(num_samples + 1):
        t /= num_samples
        
        # Cubic Bézier formula
        x = (1 - t) ** 4 * P0[0] + \
            4 * (1 - t) ** 3 * t * P1[0] + \
            6 * (1 - t) ** 2 * t ** 2 * P2[0] + \
            4 * (1 - t) * t ** 3 * P3[0] + \
            t ** 4 * P4[0]
        
        y = (1 - t) ** 4 * P0[1] + \
            4 * (1 - t) ** 3 * t * P1[1] + \
            6 * (1 - t) ** 2 * t ** 2 * P2[1] + \
            4 * (1 - t) * t ** 3 * P3[1] + \
            t ** 4 * P4[1]
        
        bezier_points.append((x, y))
    
    return bezier_points

# Print the resulting points
# Example usage
def print_b_spline(w0, scale_length=50):
    max_val = max(w0)
    scale_factor = scale_length / max_val

    for value in w0:
        num_hashes = int(value * scale_factor)
        print('#' * num_hashes)



# usage
# bezier_points = bezier_curve_with_symmetric_handles(y_coords=[0,1,0], handle_lengths=[0,1,0], num_samples=10)
# y =[y[0] for y in bezier_points]
# print(y)
# # Generate and print the bell curve
# print_b_spline(y)
