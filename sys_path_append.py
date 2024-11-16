import sys
import os

# Define the path to the directory where your package is located
package_path = r'C:\Users\harri\Documents\BDP\rigbdp\libs'

# Check if the package path is already in sys.path
if package_path not in sys.path:
    # If not, append it
    sys.path.append(package_path)
