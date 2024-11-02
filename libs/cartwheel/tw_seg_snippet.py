import maya.cmds as cmds



from maya import cmds
import maya.api.OpenMaya as om

def vec_lerp(vec_a, vec_b, lerp_amt=0.5) -> om.MVector:
    '''
    ::param vec_a (om2.MVector): source
    ::param vec_b (om2.MVector): target
    ::param lerp_amt: A float (usually) between 0 and 1 to control the interpolation.
                     Not clamped - so avoid unintentional over/undershooting.
    '''
    return ((vec_a - vec_b) * lerp_amt) + vec_a


def vec_lerp_multi(vec_a, vec_b, lerp_amt_list):      
    '''
    ::param vec_a (om2.MVector): source
    ::param vec_b (om2.MVector): target
    ::param lerp_amt: (list): vals are floats, (usually) between 0 and 1 to control vector interp.
                     Not clamped - so avoid unintentional over/undershooting.
    '''
    translation_tuples = []

    for lerp_amt in lerp_amt_list:
        # Calculate the interpolated vector
        interpolated_vector = ((vec_b - vec_a) * lerp_amt) + vec_a
        
        # Append the translation as a tuple (x, y, z)
        translation_tuples.append((interpolated_vector.x, interpolated_vector.y, interpolated_vector.z))

    return translation_tuples

def vector_lerp_weights(num_values, start=0.0, end=1.0):
    # generic linear interpolate
    # L(t)=(1-t)·a+t·b lerp between two values, a and b, based on interp :param t
    return [(start + (t * (end - start) / (num_values + 1))) for t in range(1, num_values + 1)]


def clone_jnt(src_jnt, new_jnt_name, parent=None) -> tuple: # type str,
    translate = cmds.xform(src_jnt, query=True, worldSpace=True, translation=True)
    orient = cmds.getAttr(f'{src_jnt}.jointOrient')[0]

    new_jnt = cmds.createNode('joint', name=new_jnt_name, parent=parent)

    cmds.xform(new_jnt, worldSpace=True, translation=translate)
    cmds.setAttr(f'{src_jnt}.jointOrient', *orient, type='double3')

    # set_jnt_orient(jnt=new_jnt, orient=orient)
    return new_jnt, orient

def create_crv(pnts, name, parent, degree) -> str:
    crv = cmds.curve(p=pnts, d=degree, n=name)
    if parent:cmds.parent(crv, parent)
    return crv 

def create_normalized_curve(points, degree=3):
    num_cvs = len(points)
    required_knots = num_cvs + degree - 1
    knots = [i / (required_knots - 1) for i in range(required_knots)]
    curve = cmds.curve(p=points, k=knots, d=degree)
    return curve




def create_twist_segment(start_joint, end_joint, parent, num_tw_jnts=5, suffix='Tw',) -> tuple:
    # pargs given in order of parent,child - example: arm,elbow || elbow,hand
    # twist segment : start jnt, end jnt, and n number of tw between the two.
    # hier : StartJnt->Tw00->Tw01->Tw02->Tw03->Tw05->EndJnt
    # return (tuple) : list of jnts, list of floats
    vec_start = cmds.xform(start_joint, query=True, worldSpace=True, translation=True)
    vec_end = cmds.xform(end_joint, query=True, worldSpace=True, translation=True)
    vec_start = om.MVector(vec_start)
    vec_end = om.MVector(vec_end)

    vec_wts = vector_lerp_weights(num_values=num_tw_jnts)
    translations = vec_lerp_multi(vec_start, vec_end, vec_wts)

    crv_seg_linear = create_crv(pnts=[vec_start,vec_end], name=f'{start_joint}_LineCrv', degree=1, parent=parent) 
    crv_seg_nurbs = create_crv(pnts=[vec_start, *translations, vec_end], name=f'{start_joint}_ShaperCrv', degree=1, parent=parent) 
    create_normalized_curve([vec_start, *translations, vec_end])
    seg_start, start_orient = clone_jnt(start_joint, f'{start_joint}_SegStart', parent)
    

    vec_wts = vector_lerp_weights(num_values=num_tw_jnts)
    translations = vec_lerp_multi(vec_start, vec_end, vec_wts)
    
    out_joints = {'seg_start_jnt':seg_start,
                  'seg_end':'',
                  'tw_jnts':[],
                  'vector_weights':vec_wts}
    
    for idx in range(num_tw_jnts):
        new_jnt = cmds.createNode('joint', parent=None, name=f'{start_joint}_{suffix}{idx:02}')
        cmds.xform(new_jnt, worldSpace=True, translation=translations[idx])
        cmds.setAttr(f'{new_jnt}.jointOrient', *start_orient, type='double3')
        cmds.parent(new_jnt, seg_start)
        out_joints['tw_jnts'].append(new_jnt)

    # Adding at the end purely for outliner ordering clarity
    # This order is not necessary for functionality
    seg_end = clone_jnt(end_joint, f'{start_joint}_SegEnd', seg_start)[0]
    out_joints['seg_end'] = seg_end

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
    P1 = (-handle_lengths[0], y_points[0])  # Control point 1 influenced by handle length to the left
    P2 = (0, y_points[1])  # Control point 2 at the midpoint
    P3 = (handle_lengths[1], y_points[1])  # Control point 3 influenced by handle length to the right
    P4 = (handle_lengths[2], y_points[2])  # End point

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

# Example usage
y_coords = [0, 2, 0]            # Y coordinates for control points
handle_lengths = [1, 1, 1]      # Lengths for the symmetric handles
num_samples = 20                 # Number of points to generate

bezier_points = bezier_curve_with_symmetric_handles(y_coords, handle_lengths, num_samples)

# Print the resulting points
print(bezier_points)

# Visualize the Bézier output
def print_bezier_curve(bezier_points, scale_length=30):
    y_values = [y for _, y in bezier_points]
    max_val = max(y_values) if y_values else 1  # Prevent division by zero
    scale_factor = scale_length / max_val

    for value in y_values:
        num_hashes = int(value * scale_factor)
        print('#' * num_hashes)

# Visualizing the Bézier curve
print_bezier_curve(bezier_points)







def rig_arm_split(ik_jnts, tw_jnts, bind_jnt, split_arm_jnt, side, skel_parent, arm_clusters_grp, elbow_clusters_grp):
    from_point = cmds.xform(ik_jnts[0], q=True, ws=True, t=True)
    to_point = cmds.xform(ik_jnts[1], q=True, ws=True, t=True)

    arm_curve = cmds.curve(name=f'{side}_arm_CRV', d=1, p=(from_point, to_point))
    cmds.setAttr(f'{arm_curve}.inheritsTransform', 0)
    cmds.parent(arm_curve, skel_parent)
    cmds.setAttr(f'{arm_curve}.v', 0)

    arm_from_grp = cmds.createNode('transform', name=f'{side}_armFrom_GRP', parent=skel_parent)
    arm_from_loc = cmds.spaceLocator(name=f'{side}_armFrom_LOC')[0]
    cmds.parent(arm_from_loc, arm_from_grp)
    cmds.move(from_point[0], from_point[1], from_point[2], arm_from_grp, ws=True)

    arm_from_cls = cmds.cluster(f'{arm_curve}.cv[0]', name=f'{side}_armFrom_CLS', wn=(arm_from_loc, arm_from_loc), bindState=True)
    arm_from_cls_handle = arm_from_cls[1]  # Assign the cluster handle directly
    cmds.rename('clusterHandleShape', f'{side}_armFrom_CLSShape')

    arm_to_grp = cmds.createNode('transform', name=f'{side}_armTo_GRP', parent=skel_parent)
    arm_to_loc = cmds.spaceLocator(name=f'{side}_armTo_LOC')[0]
    cmds.parent(arm_to_loc, arm_to_grp)
    cmds.move(to_point[0], to_point[1], to_point[2], arm_to_grp, ws=True)

    arm_to_cls = cmds.cluster(f'{arm_curve}.cv[1]', name=f'{side}_armTo_CLS', wn=(arm_to_loc, arm_to_loc), bindState=True)
    arm_to_cls_handle = arm_to_cls[1]  # Assign the cluster handle directly
    cmds.rename('clusterHandleShape', f'{side}_armTo_CLSShape')

    ik_handle = cmds.ikHandle(sj=bind_jnt, ee=split_arm_jnt, sol='ikSplineSolver', c=arm_curve, name=f'{side}_armIKSpine_IKH')[0]

    cmds.setAttr(f'{ik_handle}.dTwistControlEnable', 1)
    cmds.setAttr(f'{ik_handle}.dWorldUpType', 4)
    cmds.setAttr(f'{ik_handle}.dWorldUpVectorY', 0)
    cmds.setAttr(f'{ik_handle}.dWorldUpVectorEndY', 0)
    cmds.setAttr(f'{ik_handle}.dWorldUpVectorZ', 1)
    cmds.setAttr(f'{ik_handle}.dWorldUpVectorEndZ', 1)
    cmds.setAttr(f'{ik_handle}.dWorldUpAxis', 3)

    # Connect world matrices for world up vectors
    cmds.connectAttr(f'{arm_from_cls_handle}.worldMatrix[0]', f'{ik_handle}.dWorldUpMatrix', f=True)
    cmds.connectAttr(f'{arm_to_cls_handle}.worldMatrix[0]', f'{ik_handle}.dWorldUpMatrixEnd', f=True)

    cmds.parent(arm_clusters_grp[1], ik_handle)
    cmds.parent(elbow_clusters_grp[0], bind_jnt)
    cmds.parent(elbow_clusters_grp[1], ik_handle)

    cmds.setAttr(f'{arm_clusters_grp[0]}.v', 0)
    cmds.setAttr(f'{elbow_clusters_grp[0]}.v', 0)
    cmds.setAttr(f'{arm_clusters_grp[1]}.v', 0)
    cmds.setAttr(f'{elbow_clusters_grp[1]}.v', 0)
    cmds.setAttr(f'{arm_curve}.v', 0)

# Usage
# Call the function with specific parameters for the arm rigging
rig_arm_split(ik_jnts, tw_jnts, bind_jnt, split_arm_jnt, 'L', skel_parent, arm_clusters_grp, elbow_clusters_grp)
