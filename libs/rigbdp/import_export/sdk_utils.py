import os, json, re
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
from collections import defaultdict
import rpdecorator
'''
This module has two major purposes.  They are:
1. Export all set driven keys in a maya scene to a json dictionary
2. Import all set driven keys in a maya scene from a json dictionary

Export
There are certain export rules that must be followed:

1. --- all driver nodes must exist before sdk import.
2. --- all driven nodes must exist before sdk import.
3. --- upon export the set driven key anim curve must have both an input 
       and output connection.  If this is not so, the set 
       driven key will not be exported.

For the most part, this is it. I would recommend a somewhat descriptive
naming convention, but it is by no means required.

It is important to note, if a driven connection has multiple drivers, a
blend node is automatically created between the set driven keyframe and
the driven connection. This information will be saved in the json export
dict and will be used to reconstruct the sdk upon reload.


Import
Import rules are much the same as export rules:
1. --- all driver and driven nodes must exist, with the exception of any
       blendWeighted nodes, which will be created if they don't yet exist.

As a side note, it is important to keep in mind the chronological order
of when the sdk is created. Any scripts which create nodes that are used
to drive, or be driven need to have already be run. Any import functions
should be run as late as they can be in any build process they are used in.

'''
def export_to_json(filepath, data, verbose=True):
    # Ensure the directory exists
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write the dictionary to a JSON file
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)  # indent for beauty formatting
    if verbose:print(f'Data exported to {filepath}')

@rpdecorator.undo_chunk
def rename_blend_weighted_nodes(verbose=True)->None:
    # Find all blendWeighted nodes
    blend_weighted_nodes = cmds.ls(type='blendWeighted')
    for node in blend_weighted_nodes:
        if '_' in node: continue # '_'  the node has already been renamed, skip
        
        connections = cmds.listConnections(f'{node}.output',
                                           plugs=True,
                                           skipConversionNodes=True) or []

        # Filter out node editor garbage connections
        connections = [conn for conn in connections
                       if "MayaNodeEditor" not in conn]

        # if no connections remain we can't rename, so skip
        if not connections:continue

        # only the first index, for the sake of readability
        connection = connections[0]

        # derive name from connections
        driven_node, attribute = connection.split('.')[0],connection.split('.')[1]
        new_name = f"{driven_node}_{attribute}_blendWeighted"

        cmds.rename(node, new_name)
        if verbose: print(f"Renamed {node} to {new_name}")

def rename_sdk(sdk, input, output, verbose=True)-> None:

    # we can assume that the key has already been renamed if it has '_' in it
    if '_' in sdk: return sdk
    # if an output/input has an index in it such as:
    # name[1]_sdk
    # we will want naming to be name_1_sdk
    # use re to rename chars '[' --> '_' and ']' --> ''
    input = re.sub(r'\[', '_', input)
    input = re.sub(r'\]', '', input)
    output = re.sub(r'\[', '_', output)
    output = re.sub(r'\]', '', output)

    input_node, input_attr = input.split('.')
    output_node, output_attr = output.split('.')

    new_name = f'{input_node}_{input_attr}_TO_{output_node}_{output_attr}_sdk'
    cmds.rename(sdk, new_name)
    if verbose:print(f'{sdk} renamed to {new_name}')

    return new_name


def get_blend_weighted_in_out(blend_weighted_node, verbose=False) -> dict:

    # we are going to look at both in and out
    # if arg is given as attr, split by '.' and use first index
    if '.' in blend_weighted_node:
        blend_weighted_node = blend_weighted_node.split('.')[0]

    # get the in and out connections
    blend_weighted_input = cmds.listConnections(f'{blend_weighted_node}.input', # positional arg
                                                source=True, 
                                                plugs=True, 
                                                skipConversionNodes=True) or []
    blend_weighted_output = cmds.listConnections(f'{blend_weighted_node}.output', # parg
                                                 destination=True,
                                                 plugs=True, 
                                                 skipConversionNodes=True) or []
    # if either is disconnected we aren't interested anymore
    if not blend_weighted_output or not blend_weighted_input:return None, None
    return_dict = {blend_weighted_node:{'output': blend_weighted_output[0],
                                        'inputs':blend_weighted_input}}
    if verbose: print(json.dumps(return_dict))
    return return_dict

SDK_EXPORT_ATTRS = { 'curve' : {'isStatic', 'isWeighted',
                                'preInfinityType', 'postInfinityType'},
                     'key'   : {'value', 'isBreakdown', 'tangentsLocked',
                                'inTangentType', 'outTangentType'}}


SDK_EXPORT_ATTRS = ['isStatic', 'isWeighted',
                    'preInfinityType', 'postInfinityType',
                    'value', 'isBreakdown', 'tangentsLocked',
                    'inTangentType', 'outTangentType']

@rpdecorator.undo_chunk
def get_animCurve_info(a_curve):
    # Get the MObject for the animCurve node
    selection_list = om.MSelectionList()
    selection_list.add(a_curve)
    anim_curve_obj = selection_list.getDependNode(0)
    
    # Create an MFnAnimCurve function set to work with the animation curve
    anim_curve_fn = omanim.MFnAnimCurve(anim_curve_obj)
    
    # Retrieve the number of keys
    key_count = anim_curve_fn.numKeys
    if key_count == 0:
        return None  # Return None if there are no keyframes
    
    # First and last keyframe times
    start_time = anim_curve_fn.input(0)
    end_time = anim_curve_fn.input(key_count - 1)
    
    # Get key times and values
    key_times = [anim_curve_fn.input(i) for i in range(key_count)]
    key_values = [anim_curve_fn.value(i) for i in range(key_count)]
    
    # Get tangent types using MFnAnimCurve and tangent weights using cmds.keyTangent
    in_tangent_types = [anim_curve_fn.inTangentType(i) for i in range(key_count)]
    out_tangent_types = [anim_curve_fn.outTangentType(i) for i in range(key_count)]
    
    # Use cmds.keyTangent to query tangent weights for each keyframe
    in_tangent_weights = cmds.keyTangent(a_curve, query=True, inWeight=True)
    out_tangent_weights = cmds.keyTangent(a_curve, query=True, outWeight=True)
    
    # Additional attributes
    pre_infinity_type = anim_curve_fn.preInfinityType
    post_infinity_type = anim_curve_fn.postInfinityType
    is_weighted = anim_curve_fn.isWeighted
    anim_curve_type = anim_curve_fn.animCurveType

    # Construct the result dictionary with Maya attribute names
    anim_curve_data = {
        'animCurve': a_curve,
        'animCurveType': anim_curve_type,
        'minTime': start_time,
        'maxTime': end_time,
        'keyTime': key_times,
        'keyValue': key_values,
        'inTangentType': in_tangent_types,
        'outTangentType': out_tangent_types,
        'inTangentWeight': in_tangent_weights,
        'outTangentWeight': out_tangent_weights,
        'preInfinityType': pre_infinity_type,
        'postInfinityType': post_infinity_type,
        'weighted': is_weighted,
    }

    return anim_curve_data

# # Example usage
# info = get_animCurve_info('L_breast_offset_rotateX')
# if info:
#     print(info)

def get_sdk_data(verbose=False):
    rename_blend_weighted_nodes()
    anim_curves = cmds.ls(typ='animCurve')
    sdk_curves=[]
    sdk_data = {}
    # There may not be any blendWeighted nodes - None for clarity in export dict
    blend_weighted_data = {}
    for a_curve in anim_curves:
        input=f'{a_curve}.input'
        output=f'{a_curve}.output'
        # if the animCurve doesn't in and out connections skip
        sdk_curves.append(a_curve)
        input = cmds.listConnections(a_curve, # positional arg
                                     source=True, 
                                     destination=False, 
                                     plugs=True, 
                                     skipConversionNodes=True) or []
        if not input: continue
        input=input[0]
        output = cmds.listConnections(a_curve, # parg
                                      source=False,
                                      destination=True,
                                      plugs=True,
                                      skipConversionNodes=True) or []
        if not output: continue
        output=output[0]
        final_output = output
        # rename the curves, very important to do before export.
        # user will want to remember to save.
        a_curve = rename_sdk(a_curve,
                             input=input,
                             output=final_output)
        '''
        if it is a blendWeighted node, get its output as the final output.
           it is important to get the blendWeighted in this loop as you only
           want to find bw nodes related to your set driven keys
        '''
        if 'blendWeighted' in cmds.objectType(output):
            blend_input = get_blend_weighted_in_out(output)
            key = None
            if blend_input:
                key = list(blend_input)[0]
            if key and key not in blend_weighted_data.keys():
                blend_weighted_data[key] = blend_input[key]
        a_curve_type = cmds.objectType(a_curve)

        # put all data involved with creating the anim curves into a dictionary.

        # INPUT :  null1.translateX
        # OUTPUT :  null2_scaleY_blendWeighted.input[0]
        # BLEND_OUTPUT :  ['null2.scaleY']
        a_curve_data = get_animCurve_info(a_curve)
        sdk_data[a_curve] = {'input':input,
                                       'output':output,
                                       'obj_type':a_curve_type,
                                       'anim_data':a_curve_data}
    for blend_weighted in blend_weighted_data:
        blend_weighted_data[blend_weighted] = get_blend_weighted_in_out(blend_weighted)[blend_weighted]
    # blend_weighted_data = common_connections(blend_weighted_data)
    sdk_data['blend_weighted_data'] = blend_weighted_data
    if verbose:
        print(json.dumps(sdk_data, indent=4))
    # export_to_json(export_path, sdk_connection_map, verbose=True)
    # print('blend_output_map : ', blend_weighted_data)
    # print('sdk_connection_map : ', sdk_connection_map)
    return sdk_data

# Mapping from animCurveType enum values to string node types
ANIM_CURVE_TYPE_MAP = {
    0: 'animCurveTA',  # Time to Angular
    1: 'animCurveTL',  # Time to Linear
    2: 'animCurveTT',  # Time to Time
    3: 'animCurveTU',  # Time to Unitless
    4: 'animCurveUA',  # Unitless to Angular
    5: 'animCurveUL',  # Unitless to Linear
    6: 'animCurveUT',  # Unitless to Time
    7: 'animCurveUU',  # Unitless to Unitless
}

def export_sdks(filepath):
    sdk_data = get_sdk_data()
    export_to_json(filepath, sdk_data, verbose=True)



def rebuild_anim_curve(anim_curve, anim_data):
    # Get MObject from anim_curve
    selection_list = om.MSelectionList()
    selection_list.add(anim_curve)
    anim_curve_obj = selection_list.getDependNode(0)
    
    # Create MFnAnimCurve function set
    anim_curve_fn = omanim.MFnAnimCurve(anim_curve_obj)
    
    # Set pre and post infinity types
    anim_curve_fn.setPreInfinityType(anim_data['preInfinityType'])
    anim_curve_fn.setPostInfinityType(anim_data['postInfinityType'])
    
    # Set weighted state
    anim_curve_fn.setIsWeighted(anim_data['weighted'])
    
    # Add keys and set tangents
    for i, (time, value) in enumerate(zip(anim_data['keyTime'], anim_data['keyValue'])):
        anim_curve_fn.addKey(time, value)
        anim_curve_fn.setInTangentType(i, anim_data['inTangentType'][i])
        anim_curve_fn.setOutTangentType(i, anim_data['outTangentType'][i])
        
        # Set tangent weights if the curve is weighted
        if anim_data['weighted']:
            anim_curve_fn.setTangentWeight(i, anim_data['inTangentWeight'][i], True)  # in tangent
            anim_curve_fn.setTangentWeight(i, anim_data['outTangentWeight'][i], False)  # out tangent


@rpdecorator.undo_chunk
def import_sdks(filepath, verbose=True):
    '''
    1. create blendWeighted nodes, name based on key
    2. connect them to their output attrs, based on ['output'] val
    3. create sdk animCurves, name based on key
    4. create keyframes on animcurves based on 
    4. connect their inputs, based on
    5. loop through blendWeighted dictionary and connect sdks.
    '''
    with open(filepath, 'r') as f:
        sdk_connection_map = json.load(f)

    #blend_weighted_data = sdk_connection_map['blend_weighted_data']
    blend_weighted_data = sdk_connection_map.pop('blend_weighted_data', None)
    
    # Blend Weighted Creation
    # must check nodes do not already exist
    # output here, anim curve connections later
    for bw_node in blend_weighted_data:
        if not cmds.objExists(bw_node):
            cmds.createNode('blendWeighted', name=bw_node)
        cmds.connectAttr(f'{bw_node}.output', blend_weighted_data[bw_node]['output'], force=True)


    # Curve Creation
    # must check nodes do not already exist
    anim_curve_data = sdk_connection_map
    for anim_curve in anim_curve_data:
        if not cmds.objExists(anim_curve):
            cmds.createNode(anim_curve_data[anim_curve]['obj_type'], name=anim_curve)
        if (cmds.objExists(anim_curve_data[anim_curve]['input']) and cmds.objExists(f'{anim_curve}.input')):
            cmds.connectAttr(anim_curve_data[anim_curve]['input'], f'{anim_curve}.input', force=True)
        if (cmds.objExists(f'{anim_curve}.output') and cmds.objExists(anim_curve_data[anim_curve]['output'])):
            cmds.connectAttr(f'{anim_curve}.output', anim_curve_data[anim_curve]['output'],force=True)
        print('ANIM CURVE : ', anim_curve)
        anim_data = anim_curve_data[anim_curve]['anim_data']
        rebuild_anim_curve(anim_curve, anim_data)

        

    # "R_clavicle_ctrl_rotateZ_TO_R_breast_offset_translateZ_blendWeighted_input_2_sdk": {
    #     "input": "R_clavicle_ctrl.rotateZ",
    #     "output": "R_breast_offset_translateZ_blendWeighted.input[2]",
    #     "obj_type": "animCurveUL",
    #     "anim_data": {
    #         "animCurve": "R_clavicle_ctrl_rotateZ_TO_R_breast_offset_translateZ_blendWeighted_input_2_sdk",
    #         "animCurveType": 5,
    #         "minTime": -50.0,
    #         "maxTime": 50.0,
    #         "keyTime": [
    #             -50.0,
    #             0.0,
    #             50.0
    #         ],
    #         "keyValue": [
    #             -0.54,
    #             0.0,
    #             1.036
    #         ],
    #         "inTangentType": [
    #             1,
    #             1,
    #             1
    #         ],
    #         "outTangentType": [
    #             1,
    #             1,
    #             1
    #         ],
    #         "inTangentWeight": [
    #             1.0,
    #             1.0,
    #             1.0
    #         ],
    #         "outTangentWeight": [
    #             1.0,
    #             1.0,
    #             1.0
    #         ],
    #         "preInfinityType": 0,
    #         "postInfinityType": 0,
    #         "weighted": false
    #     }
    # },


    # "R_clavicle_ctrl_rotateZ_TO_R_breast_offset_translateZ_blendWeighted_input_2_sdk": {
    #     "input": "R_clavicle_ctrl.rotateZ",
    #     "output": "R_breast_offset_translateZ_blendWeighted.input[2]",
    #     "obj_type": "animCurveUL",
    #     "anim_data": {
    #         "animCurve": "R_clavicle_ctrl_rotateZ_TO_R_breast_offset_translateZ_blendWeighted_input_2_sdk",

    #     "R_breast_offset_translateZ_blendWeighted": {
    #         "output": "R_breast_offset",
    #         "inputs": [
    #             "R_breast_offset_translateZ",
    #             "R_clavicle_ctrl_rotateY_to_R_breast_offset_translateZ_blendWeighted_input_1_sdk",
    #             "R_clavicle_ctrl_rotateZ_to_R_breast_offset_translateZ_blendWeighted_input_2_sdk"
    #         ]
    #     }
    # }

    # Unpack 

    # # Unpack all animCurveData
    # anim_curve_type = ANIM_CURVE_TYPE_MAP.get(sdk_connection_map['animCurveType'],
    #                                           'animCurveUA')  # Default Unitless
    
    # anim_curve = cmds.createNode(anim_curve_type)




def import_anim_curve_EXAMPLE(filepath):
    with open(filepath, 'r') as f:
        anim_curve_data = json.load(f)

    # Get the correct node type from the mapping
    anim_curve_type = ANIM_CURVE_TYPE_MAP.get(anim_curve_data['animCurveType'],
                                              'animCurveUA')  # Default Unitless
    
    # Create the animation curve node
    anim_curve = cmds.createNode(anim_curve_type)

    # Create MFnAnimCurve function set
    anim_curve_fn = omanim.MFnAnimCurve(om.MSelectionList().add(anim_curve))
    anim_curve_fn = anim_curve_fn.getDependNode(0)

    # Set the animation curve attributes
    for i, (time, value) in enumerate(zip(anim_curve_data['keyTime'],
                                          anim_curve_data['keyValue'])):
        anim_curve_fn.addKey(time, value)
        anim_curve_fn.setInTangentType(i, anim_curve_data['inTangentType'][i])
        anim_curve_fn.setOutTangentType(i, anim_curve_data['outTangentType'][i])
        
        # Set tangent weights if the curve is weighted
        if anim_curve_data['weighted']:
            cmds.keyTangent(anim_curve, edit=True,
                            inWeight=anim_curve_data['inTangentWeight'][i],
                            outWeight=anim_curve_data['outTangentWeight'][i])

    # Set pre and post infinity types
    anim_curve_fn.preInfinityType = anim_curve_data['preInfinityType']
    anim_curve_fn.postInfinityType = anim_curve_data['postInfinityType']
    
    # Set weighted state
    anim_curve_fn.isWeighted = anim_curve_data['weighted']

    print(f'Animation curve imported: {anim_curve_data["animCurve"]}')

# # Example usage
# import_path = '/path/to/exported_curve.json'
# import_anim_curve(import_path)



def get_sdk_final_input(a_curve):
    input = cmds.setDrivenKeyframe(a_curve)
    output = cmds.setDrivenKeyframe(a_curve)
    




