#!/bin/bash

# Get the current user's home directory
USER_HOME="$HOME"

# Path to the maya.env file
MAYA_ENV="$USER_HOME/maya/maya.env"

# Check if the maya.env file exists
if [ -f "$MAYA_ENV" ]; then
    echo "Found maya.env at: $MAYA_ENV"
    # Add an environment variable (example: export MY_LIB_PATH=/path/to/library)
    echo 'MY_LIB_PATH="/path/to/library"' >>"$MAYA_ENV"
    echo "Added MY_LIB_PATH to maya.env"
else
    echo "maya.env file not found in $USER_HOME/maya/"
fi
