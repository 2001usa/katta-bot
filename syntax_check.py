
import os
import ast

def check_syntax(start_path):
    print(f"Checking syntax for files in {start_path}...")
    error_count = 0
    file_count = 0
    
    for root, dirs, files in os.walk(start_path):
        if 'venv' in dirs:
            dirs.remove('venv') # Skip venv
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            if file.endswith(".py"):
                file_count += 1
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()
                    ast.parse(source)
                except SyntaxError as e:
                    print(f"SYNTAX ERROR in {full_path}: {e}")
                    error_count += 1
                except Exception as e:
                    print(f"COULD NOT READ {full_path}: {e}")
                    error_count += 1
    
    print(f"\nScanned {file_count} files.")
    if error_count == 0:
        print("No syntax errors found.")
    else:
        print(f"Found {error_count} syntax errors.")

if __name__ == "__main__":
    check_syntax(".")
