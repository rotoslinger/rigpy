import os, shutil


def copy_files_with_newer_timestamps(source_dir, destination_dir, 
                                     ignore_types=['.pyc', '.bak', '__pycache__',
                                                   'DS_Store', '.git', 'gitignore',
                                                   'vscode']):
    """
    Copy all files from source_dir to destination_dir recursively.
    Only copy files with newer timestamps or if they don't exist in the destination.

    :param source_dir: The source directory to copy files from.
    :param destination_dir: The destination directory to copy files to.
    :param ignore_types: List of file and directory types to ignore.
    """
    # Normalize paths
    source_dir = os.path.normpath(source_dir)
    destination_dir = os.path.normpath(destination_dir)

    # Check if source directory exists
    if not os.path.isdir(source_dir):
        print(f'The source directory "{source_dir}" does not exist or is not a directory.')
        return

    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    updated_files = []  # List to keep track of updated files

    # Iterate over the files and directories in the source directory
    for item in os.listdir(source_dir):
        source_path = os.path.join(source_dir, item)
        destination_path = os.path.join(destination_dir, item)

        # Check if the item should be ignored
        if any(item.endswith(ext) or item == ext for ext in ignore_types):
            continue  # Skip ignored files and directories

        # If the item is a file
        if os.path.isfile(source_path):
            # If the file does not exist in the destination or if the source file is newer
            if not os.path.exists(destination_path) or os.path.getmtime(source_path) > os.path.getmtime(destination_path):
                shutil.copy2(source_path, destination_path)  # Copy file with metadata
                updated_files.append(source_path)  # Track updated file

        # If the item is a directory, recursively copy (optional)
        elif os.path.isdir(source_path):
            # If the directory does not exist in the destination, copy it
            if not os.path.exists(destination_path):
                shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
                updated_files.append(source_path)  # Track updated directory
            else:
                # Recursively call the function for existing directories
                copy_files_with_newer_timestamps(source_path, destination_path, ignore_types)

    # Print summary of updated files
    if updated_files:
        print("Updated files and directories:")
        for updated in updated_files:
            print(f'- {updated}')
# Example usage:
# copy_files_with_newer_timestamps('/path/to/source', '/path/to/destination', ignore_types=['.git', '.tmp'])

####################################### Usage ########################################
# source_directory = 'path/to/source/directory'
# destination_directory = 'path/to/destination/directory'
# copy_files_with_newer_timestamps(source_directory, destination_directory)
######################################################################################
repo_path = os.path.dirname(os.path.realpath(__file__))
copy_files_with_newer_timestamps(repo_path, r'C:\Users\harri\Desktop\staging_py_libs')


# copy_files_with_newer_timestamps(repo_path, r'\show\BDPUser\rig')
