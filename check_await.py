
import os
import ast

def find_missing_awaits(start_path):
    print(f"Scanning for missing 'await' in {start_path}...")
    issues_found = 0
    
    # List of known async DB functions (ending in _base)
    # Ideally we'd parse bot_base.py to get these, but ending in _base is our convention.
    
    for root, dirs, files in os.walk(start_path):
        if 'venv' in dirs: dirs.remove('venv')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()
                    
                    tree = ast.parse(source)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            func_name = ""
                            if isinstance(node.func, ast.Name):
                                func_name = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                func_name = node.func.attr
                            
                            # Check if it matches our convention
                            if func_name.endswith("_base"):
                                # It's a database call. Check if it's awaited.
                                # The parent node in the AST should be an Await.
                                # However, ast.walk doesn't give parents easily.
                                # So we look at the line in the source.
                                
                                # Simpler approach: check if the node is wrapped in an Await node check?
                                # Actually, walking the tree is top-down. 
                                pass

                except Exception as e:
                    pass

    # Better approach with simple line text scan to be robust against AST complexity for a quick check
    # We look for "func_base(" that is NOT preceded by "await "
    
    import re
    
    for root, dirs, files in os.walk(start_path):
         if 'venv' in dirs: dirs.remove('venv')
         if '__pycache__' in dirs: dirs.remove('__pycache__')
         
         for file in files:
            if file.endswith(".py") and file != "bot_base.py": # Skip defining file
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # Regex to find function calls ending in _base(
                    # and check if 'await' is missing before it
                    
                    # Matches things like:  x = func_base(
                    # But NOT: x = await func_base(
                    # AND NOT: def func_base( (definition)
                    # AND NOT: async def func_base(
                    
                    # We ignore definitions
                    if "def " in line:
                        continue
                        
                    matches = re.finditer(r'\b(\w+_base)\s*\(', line)
                    for match in matches:
                        func_name = match.group(1)
                        # Check context before the match
                        preceding_text = line[:match.start()]
                        
                        if "await" not in preceding_text:
                            # Edge case: maybe it's `return asyncio.to_thread(func_base_sync...)`?
                            # But we renamed those to _sync. So direct _base calls MUST be awaited.
                            
                            print(f"Missing await? File: {os.path.relpath(full_path)} Line: {i+1}")
                            print(f"   Code: {line.strip()}")
                            issues_found += 1

    if issues_found == 0:
        print("No missing awaits found for *_base functions.")
    else:
        print(f"Found potential missing awaits.")

if __name__ == "__main__":
    find_missing_awaits(".")
