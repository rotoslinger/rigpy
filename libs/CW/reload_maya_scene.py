from maya import mel
def load_maya_scene():
    mel.eval('file -f -options "v=0;"  -ignoreVersion  -typ "mayaAscii" -o "C:/Users/harri/Documents/cartwheel/working_files/running_jump02_with_end.ma";addRecentFile("C:/Users/harri/Documents/cartwheel/working_files/running_jump02_with_end.ma", "mayaAscii");')
