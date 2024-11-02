import json, math

from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

def vec_lerp(vec_a, vec_b, lerp_amt=0.5) -> om.MVector:
    '''
    :param om.MVector vec_a : source vector 
    :param om.MVector vec_b: target vector 
    :param float lerp_amt: A float (usually) between 0 and 1 to control the interpolation.
                     Not clamped - so avoid unintentional over/undershooting.
    '''
    return ((vec_a - vec_b) * lerp_amt) + vec_a


def vec_lerp_multi(vec_a, vec_b, lerp_amt_list):      
    '''
    :param om.MVector vec_a: source
    :param om.MVector vec_b: target
    :param list lerp_amt: vals are floats, (usually) between 0 and 1 to control vector interp.
                          Not clamped - so avoid unintentional over/undershooting.
    '''
    translation_tuples = []

    for lerp_amt in lerp_amt_list:
        # Calculate the interpolated vector
        interpolated_vector = ((vec_b - vec_a) * lerp_amt) + vec_a
        
        # Append the translation as a tuple (x, y, z)
        translation_tuples.append((interpolated_vector.x, interpolated_vector.y, interpolated_vector.z))

    return translation_tuples

def lerp_weights_generator(num_values=5, start=0.0, end=1.0):
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

def clone_jnt(src_jnt, new_jnt_name, orient=None, parent=None) -> tuple: # type str,
    translate = cmds.xform(src_jnt, query=True, worldSpace=True, translation=True)
    if not orient:orient = cmds.getAttr(f'{src_jnt}.jointOrient')[0]

    new_jnt = cmds.createNode('joint', name=new_jnt_name, parent=None)
    cmds.xform(new_jnt, worldSpace=True, translation=translate)
    cmds.setAttr(f'{new_jnt}.jointOrient', *orient, type='double3')
    if parent:cmds.parent(new_jnt, parent)
    # set_jnt_orient(jnt=new_jnt, orient=orient)
    return new_jnt, orient

def create_crv(pnts, name, parent, degree) -> str:
    crv = cmds.curve(p=pnts, d=degree, n=name)
    if parent:cmds.parent(crv, parent)
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


### TODO Class Method ### 


def no_flip_tw_setup(anchor_jnt, no_flip_start_jnt, no_flip_end_jnt, name, component_parent, tw_jnts, weights):
    '''
    :param str anchor_jnt: usually the no twist joint, the start of the transition
    :param str start_jnt: only used in naming
    :param str end_jnt: only used to position the handle container
    :param str component_parent: the root parent of the component
    :param list tw_jnts: a list of the twist jnts
    :param list weights: weights to be used as normalized influences in the twist orientConstraint

    Single chain solver to avoid flipping. Avoids need for up vector.
    No flip end used as an orient constraint target for transitional falloff
    '''

    handle_null = cmds.createNode('transform', name=f'{name}_SegNoFlipNll', parent=component_parent)

    translate = cmds.xform(no_flip_end_jnt, query=True, translation=True, worldSpace=True)
    cmds.xform(handle_null, translation=translate, worldSpace=True)
    cmds.makeIdentity(handle_null, apply=True, translate=True)

    handle, effector = cmds.ikHandle(startJoint=no_flip_start_jnt, endEffector=no_flip_end_jnt,
                                     sol='ikSCsolver', sticky='sticky', name=f'{name}_SegNoFlipHdl')
    cmds.parent(handle, handle_null)
    cmds.rename(effector, f'{name}_SegNoFlipEff')
    effector = f'{name}_SegNoFlipEff'
    for attr in ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']:
        cmds.setAttr(f'{handle}{attr}', lock=True)# avoid accidental movement
        cmds.setAttr(f'{effector}{attr}', lock=True)# avoid accidental movement

    tw_cnsts = []
    for idx, tw_jnt in enumerate(tw_jnts):
        tmp_cons = cmds.orientConstraint(no_flip_end_jnt, anchor_jnt, tw_jnt , skip=['y','z'],
                                         mo=False)
        tw_cons=f'{name}_SegTwCns{idx:02}'
        cmds.rename(tmp_cons, tw_cons)
        print('WEIGHTS 0 : ', weights[0][idx])
        print('WEIGHTS 1 : ', weights[1][idx])
        print('\n')
        print(f'{tw_cons}')


        cmds.setAttr(f'{tw_cons}.w0', weights[0][idx])
        cmds.setAttr(f'{tw_cons}.w1', weights[1][idx])

        # [w0, w1]
        tw_cnsts.append(tw_cons)

        

    return handle_null, handle


### TODO Class Method ###
def create_twist_segment(start_joint, end_joint,
                         component_parent=None, twist_parent=None,
                         num_tw_jnts=5, suffix='Tw', no_tw_jnt=True,
                         create_shaper_jnts=False,
                         debug=True) -> list:
    '''
    unintuitive args -
    @:param component_parent: Twist Segment Component parent.
    @:param tw_parent: this will be the influencing skeleton.
    @:param tw_parent: this will be the influencing skeleton.

    pargs given in order of parent,child - example: arm,elbow || elbow,hand
    If the component is LeftArm_Seg: LeftArm_Tw00-05 should be parented to LeftArm

    twist segment : start jnt, end jnt, and n number of tw between the two.
    hier : StartJnt->Tw00->Tw01->Tw02->Tw03->Tw05->EndJnt
    return (tuple) : list of jnts
    '''
    vec_start = cmds.xform(start_joint, query=True, worldSpace=True, translation=True)
    vec_end = cmds.xform(end_joint, query=True, worldSpace=True, translation=True)
    vec_start = om.MVector(vec_start)
    vec_end = om.MVector(vec_end)
    
    w0,w1 = lerp_weights_generator(num_values=num_tw_jnts)
    translations = vec_lerp_multi(vec_start, vec_end, w0)
    
    # Primary chain start
    seg_start_jnt, start_orient = clone_jnt(start_joint, f'{start_joint}_SegStart', component_parent)


    # No flip chain
    no_flip_start_jnt = clone_jnt(seg_start_jnt, f'{start_joint}_SegNoFlipStart', start_orient, seg_start_jnt)[0]
    no_flip_end_jnt = clone_jnt(end_joint, f'{start_joint}_SegNoFlipEnd', start_orient, no_flip_start_jnt)[0]

    no_tw_shldr_jnt=None
    if no_tw_jnt:
        no_tw_shldr_jnt = clone_jnt(start_joint, f'{start_joint}_SegStart', start_orient, component_parent)[0]
        ### TODO REMOVE ###
        if debug: cmds.parent(no_tw_shldr_jnt, no_flip_start_jnt)
        if not debug: cmds.parent(no_tw_shldr_jnt, twist_parent)
        ### TODO REMOVE ###
        parent=cmds.listRelatives(start_joint, parent=True)
        if parent:
            ### TODO make sure to test flipping with single channel orient constraint ###
            cmds.orientConstraint(parent, no_tw_jnt, skip=['y', 'z'], mo=True)
    if not no_tw_jnt:
        no_tw_shldr_jnt = seg_start_jnt


    ### TODO REMOVE ###
    dbg_chain_start=''
    dbg_chain_end=''
    if debug:
        dbg_chain_start = clone_jnt(seg_start_jnt, f'{start_joint}_SegDbgStart', start_orient, seg_start_jnt)[0]
        dbg_chain_end = clone_jnt(end_joint, f'{start_joint}_SegDbgEnd', start_orient, dbg_chain_start)[0]
    ### TODO REMOVE ###


    tw_jnts=[]
    for idx in range(num_tw_jnts):
        new_jnt = cmds.createNode('joint', parent=None, name=f'{start_joint}_{suffix}{idx:02}')
        cmds.xform(new_jnt, worldSpace=True, translation=translations[idx])
        cmds.setAttr(f'{new_jnt}.jointOrient', *start_orient, type='double3')

        ### TODO REMOVE ###
        if debug: cmds.parent(new_jnt, dbg_chain_start)
        if not debug: cmds.parent(new_jnt, twist_parent)
        ### TODO REMOVE ###

        ### TODO UNCOMMENT ###
        #cmds.parent(new_jnt, twist_parent)
        ### TODO UNCOMMENT ###

        tw_jnts.append(new_jnt)

    ### TODO REVALUATE ###
    #Adding at the end purely for outliner ordering clarity
    #This order is not necessary for functionality
    #seg_end_jnt = clone_jnt(end_joint, f'{start_joint}_SegEnd', start_orient, seg_start_jnt)[0]
    #seg_end_jnt = clone_jnt(end_joint, f'{start_joint}_SegEnd', start_orient, seg_start_jnt)[0]
    ### TODO REVALUATE ###

    # create the no flip setup
    handle_null, handle = no_flip_tw_setup(no_tw_shldr_jnt, no_flip_start_jnt, no_flip_end_jnt,
                                        name=start_joint, component_parent=seg_start_jnt,
                                        tw_jnts=tw_jnts, weights=[w0,w1])

    shaper_jnts = []
    if create_shaper_jnts:
        jnts_to_clone = [seg_start_jnt, *tw_jnts, end_joint]
        for idx, jnt in enumerate(jnts_to_clone):
            parent = seg_start_jnt
            if idx > 0: parent = shaper_jnts[idx-1]
            shaper_jnts.append(clone_jnt(jnt, f'{start_joint}ShaperJnt{idx:02}', start_orient, parent)[0])

    ### TODO REVALUATE ###
    # may not need
    #crv_seg_linear = create_crv(pnts=[vec_start,vec_end], name=f'{start_joint}_LineCrv', degree=1, parent=component_parent) 
    #crv_seg_nurbs = create_crv(pnts=[vec_start, *translations, vec_end], name=f'{start_joint}_ShaperCrv', degree=1, parent=component_parent) 
    #create_normalized_curve([vec_start, *translations, vec_end])
    ### TODO REVALUATE ###

    # return map:
    # out_joints = {'segment_chain':[seg_start_jnt,seg_end_jnt],
    out_joints = {'segment_chain':[seg_start_jnt],
                  'no_flip_parts': {'chain':[no_flip_start_jnt, no_flip_end_jnt],
                                    'ik_handle_null':handle_null,
                                    'ik_handle_null':handle},
                  'shaper_chain':shaper_jnts,
                  'tw_jnts':tw_jnts,                
                  'infl_weight_linear':[w0,w1]}

    #if debug: print(json.dumps(out_joints, indent=4))

    return out_joints




def tw_jnts():
    '''
    rpSolver ik handle for no flip.
    Constrain jnt Rx to start_jnt/end-effector
    Use vec_wts & 1-vec_wts as the w0 and w1.
    '''




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
