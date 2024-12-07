# builtins
import traceback
from functools import wraps

# to only be run within the maya application
# --- fails silently
try:
    # third party
    import maya.cmds as cmds
    from maya import mel

    # for use within maya
    def sel_restore(func):
        """
        A decorator to save the current selection, run a function, and restore the selection afterward.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the current selection
            original_selection = cmds.ls(selection=True)

            try:
                # Run the decorated function
                return func(*args, **kwargs)
            finally:
                # Restore the original selection
                if original_selection:
                    cmds.select(original_selection)
                else:
                    cmds.select(clear=True)  # Clear selection if original was empty
        return wrapper
    
    def return_created_nodes(func):
        """
        This function is to return nodes created by a maya command that doesn't return anything
        
        It does this by:
        1. find all nodes before function runs
        2. run function
        3. find all nodes after the function runs
        4. find the nodes that were not in the first list - these are the created nodes
        5. return the newly created nodes

        """
        def wrapper(*args, **kwargs):
            # Get the current list of all nodes in the scene before running the function
            all_nodes_before = cmds.ls(long=True)
            
            # Run the function
            result = func(*args, **kwargs)
            
            # Get the list of all nodes after running the function
            all_nodes_after = cmds.ls(long=True)
            
            # Find the difference between nodes before and after
            created_nodes = list(set(all_nodes_after) - set(all_nodes_before))
            
            return created_nodes  # Return the list of created nodes
        
        return wrapper


    def undo_chunk(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cmds.undoInfo(state=True, openChunk=True)
            result = func(*args, **kwargs)
            cmds.undoInfo(state=True, closeChunk=True)
            return result
        return wrapper

    def undo_ignore(func):
        # Ignores undo just for the decorated method
        @wraps(func)
        def wrapper(*args, **kwargs):
            cmds.undoInfo(stateWithoutFlush = False)
            result = func(*args, **kwargs)
            cmds.undoInfo(stateWithoutFlush = True)
            return result
        return wrapper

    def suppress_warnings(func):
        # Ignores undo just for the decorated method
        @wraps(func)
        def wrapper(*args, **kwargs):
            cmds.scriptEditorInfo(suppressWarnings=True)
            result = func(*args, **kwargs)
            cmds.scriptEditorInfo(suppressWarnings=False)
            return result
        return wrapper

    # creating a new poseInterpolator always selects it, so you will want to restore sel afterward
    @sel_restore
    def suppress_pose_editor(func):
        """
        A decorator to save the current selection, run a function, and restore the selection afterward.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # will create the poseInterpolator without warning
            # -1 - the dialog should pop up;
            #  0 - the dialog should not pop up, and not create neutral pose when driver are controlled
            #  1 - the dialog should not pop up, and create neutral pose when driver are controlled

            # find out what the global value is
            # set the nuetral to not be created, and suppress the dialogue (we will set later)
            mel.eval('$gCreateNeutralPoseWhenControlled=0;')

            try:
                # Run the decorated function
                return func(*args, **kwargs)
            finally:
                # this is the maya default, so I am going to 
                mel.eval(f'$gCreateNeutralPoseWhenControlled={-1};')
        return wrapper
except:
    pass
def print_bookends(func):
    """
    Decorator to print bookend lines before and after the output of the function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('\n###############################################################################################')
        func(*args, **kwargs)
        print('###############################################################################################\n')
    return wrapper

def auto_wrapper(method):
    """Wrapper to log method calls and catch errors with traceback."""
    def wrapped(*args, **kwargs):
        try:
            print(f"Calling: {method.__name__}")
            result = method(*args, **kwargs)
            print(f"Completed: {method.__name__}")
            return result
        except Exception as e:
            print(f"Error in {method.__name__}: {e}")
            traceback.print_exc()
            raise  # Re-raise the exception to propagate it if needed
    return wrapped

# Dynamically wrap all methods
def wrap_methods(cls):
    for attr_name in dir(cls):
        attr_value = getattr(cls, attr_name)
        if callable(attr_value) and not attr_name.startswith("__"):
            setattr(cls, attr_name, auto_wrapper(attr_value))
    return cls