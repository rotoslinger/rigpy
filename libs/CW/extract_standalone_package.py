import ast
import inspect
'''
def extract_function_and_dependencies(file_path, function_name):
    # Read the source code from the file
    with open(file_path, 'r') as file:
        source_code = file.read()

    # Parse the source code
    tree = ast.parse(source_code)

    def find_dependencies(node, dependencies=set()):
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                dependencies.add(child.func.id)
            elif isinstance(child, ast.ImportFrom) or isinstance(child, ast.Import):
                for name in child.names:
                    dependencies.add(name.name)
        return dependencies

    function_code = ""
    imports_code = []
    dependencies_code = []
    dependencies = set()
    
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            function_code = ast.get_source_segment(source_code, node)
            dependencies = find_dependencies(node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports_code.append(ast.get_source_segment(source_code, node))
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in dependencies:
            dependencies_code.append(ast.get_source_segment(source_code, node))

    extracted_code = "\n".join(imports_code + dependencies_code + [function_code])

    return extracted_code
'''

def extract_function_with_dependencies(module, function_name):
    # Step 1: Get the module source code
    module_code = inspect.getsource(module)
    
    # Step 2: Parse the module code with AST
    tree = ast.parse(module_code)
    
    # Store imports, dependencies, and the target function code
    imports = []
    dependencies_code = []
    target_function_code = None
    
    # Helper function to find all called functions and dependencies
    def find_dependencies(node, dependencies=set()):
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                dependencies.add(child.func.id)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(module_code, child))
        return dependencies

    # Step 3: Traverse the AST to find the target function and dependencies
    dependencies = set()
    for node in tree.body:
        # Collect imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.get_source_segment(module_code, node))
        
        # Find the target function
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            target_function_code = ast.get_source_segment(module_code, node)
            dependencies = find_dependencies(node)
        
        # Collect code for dependencies in the same module
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in dependencies:
            dependencies_code.append(ast.get_source_segment(module_code, node))
    
    # Step 4: Combine everything into the final extracted code
    extracted_code = "\n".join(set(imports)) + "\n" + "\n".join(dependencies_code) + "\n" + (target_function_code or "")
    return extracted_code

# Example usage with an imported module
from CW import test  # Replace with the actual module name

# Extract code for a function named 'target_function'
extracted_code = extract_function_with_dependencies(test, 'test')

# Write to a new file
with open('extracted_function.py', 'w') as f:
    f.write(extracted_code)

