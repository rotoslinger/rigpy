from importlib import reload
from rigbdp.build import build_pathing
reload(build_pathing)

# Create character directory structure
# --- Character directories to assist in build automation

char_name = 'ally'
dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
created_dirs = build_pathing.create_char_structure(char_name=char_name, dir_to_char=dir_to_char)   # char_name, dir_to_char, new_version, input_extension='.ma',
