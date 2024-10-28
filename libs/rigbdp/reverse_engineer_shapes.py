import maya.cmds as cmds
import maya.mel as mel

def SHAPESImportBlendShapeSetup(node):
    # List keyable and locked attributes
    attr = cmds.listAttr(node, multi=True, keyable=True, locked=True)
    
    if attr:
        attr.pop(0)  # Remove the first item from the list

    # Check if optionVar exists for SHAPESRestoreShapeWeights
    if not mel.eval('optionVar -ex "SHAPESRestoreShapeWeights"'):
        return

    # Path to the import directory
    import_path = "C:/Users/harri/Documents/BDP/mirroring/mirror"

    # Check if the directory exists
    if not mel.eval(f'filetest -d "{import_path}"'):
        return

    # Retrieve the weight list from the optionVar
    weight_list_string = mel.eval('optionVar -q "SHAPESRestoreShapeWeights"')
    weight_list = weight_list_string.split(',')

    targets = []
    prefix = ""
    
    for weight in weight_list:
        items = weight.split('_')
        prefix = items[0]
        items.pop(0)
        targets.append('_'.join(items))

    # Iterate over targets and attributes
    for target in targets:
        for i in range(len(attr)):
            if target == attr[i]:
                file_name = f"{import_path}/{prefix}_{target}.bsw"
                
                try:
                    with open(file_name, 'r') as file:
                        file_line = file.readline()
                        
                        while file_line:
                            values = file_line.split(' ')
                            val = float(values[1])
                            cmds.setAttr(f"{node}.it[0].itg[{i}].tw[{values[0]}]", val)
                            file_line = file.readline()
                except IOError:
                    print(f"Failed to open file: {file_name}")

    # Remove the SHAPESRestoreShapeWeights optionVar
    mel.eval('optionVar -rm "SHAPESRestoreShapeWeights"')

# Global variables to hold the last curve names
SHAPESImportLastCurveUL = ''
SHAPESImportLastCurveUA = ''
SHAPESImportLastCurveUU = ''

def SHAPESImportGetLastCurve(init):
    global SHAPESImportLastCurveUL, SHAPESImportLastCurveUA, SHAPESImportLastCurveUU
    
    lastCurveUL = ''
    lastCurveUA = ''
    lastCurveUU = ''
    
    curves = cmds.ls(type="animCurve")
    
    for c in curves:
        if mel.eval(f'gmatch "{c}" "animCurveUL*"'):
            lastCurveUL = c
        elif mel.eval(f'gmatch "{c}" "animCurveUA*"'):
            lastCurveUA = c
        elif mel.eval(f'gmatch "{c}" "animCurveUU*"'):
            lastCurveUU = c

    if init == 1:
        SHAPESImportLastCurveUL = lastCurveUL
        SHAPESImportLastCurveUA = lastCurveUA
        SHAPESImportLastCurveUU = lastCurveUU
        return ""

    if lastCurveUL != SHAPESImportLastCurveUL:
        SHAPESImportLastCurveUL = lastCurveUL
        return lastCurveUL
    elif lastCurveUA != SHAPESImportLastCurveUA:
        SHAPESImportLastCurveUA = lastCurveUA
        return lastCurveUA
    elif lastCurveUU != SHAPESImportLastCurveUU:
        SHAPESImportLastCurveUU = lastCurveUU
        return lastCurveUU
    else:
        return ""

def SHAPES_getNamespace(name):
    try:
        cmds.select(f"*:{name}")
    except RuntimeError:
        return ""
    
    sel = cmds.ls(sl=True)
    if not sel:
        return ""
    
    items = sel[0].split(':')
    items.pop(-1)
    
    namespace = ":".join(items) + ":"
    return namespace

def SHAPES_setEmptyTargetData(bsNode, id, pos):
    comp = mel.eval(f'getAttr {bsNode}.it[0].itg[{id}].iti[{pos}].ict')
    
    if not comp:
        cmds.setAttr(f"{bsNode}.it[0].itg[{id}].iti[{pos}].ict", type="componentList", *["vtx[0]"])
        cmds.setAttr(f"{bsNode}.it[0].itg[{id}].iti[{pos}].ipt", type="pointArray", *[1, 0, 0, 0, 1])
