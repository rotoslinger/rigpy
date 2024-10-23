#!/bin/bash

# Detect the operating system and set the path separator
if [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
   # Windows-like environments
   path_sep="\\"
else
   # Linux/macOS/Unix-like systems
   path_sep="/"
fi

# Example of using the separator
full_path="path${path_sep}to${path_sep}file"
echo "The constructed path is: $full_path"

# Specify the module directory relative to the script's directory
MODULE_DIR="$(dirname "$0")${path_sep}refreshlibs.py" # Set your module directory here

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
   echo "Usage: $0 <src_dir> <dest_dir>"
   exit 1
fi

# Assign arguments to variables
SOURCE_DIR="$1"
DESTINATION_DIR="$2"

# Call the Python script to copy files with newer timestamps
python3 - <<EOF
import sys
import os

# Add module directory to sys.path if it's not already present
if os.path.abspath('${MODULE_DIR}') not in sys.path:
    sys.path.append(os.path.abspath('${MODULE_DIR}'))

from file import copy_files_with_newer_timestamps

# Call the function with the provided source and destination directories
copy_files_with_newer_timestamps('${SOURCE_DIR}', '${DESTINATION_DIR}')
EOF

# Usage examples
cat <<EOF
Usage examples:
1. To copy files from '/home/user/source' to '/home/user/destination':
   updatelibs.sh /home/user/source /home/user/destination

2. To copy files from the current directory's 'libs' folder to a 'backup' folder:
   updatelibs.sh ./libs ./backup

3. To copy files from a relative path to an absolute path:
   updatelibs.sh ./my_files /home/user/documents/my_files_backup

Make sure to replace '<src_dir>' and '<dest_dir>' with the actual paths you want to use.
EOF
