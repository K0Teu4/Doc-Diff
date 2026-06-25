import subprocess
import sys
import os

"""
Build script for PyInstaller.
Usage: python build.py

Creates:
- dist/docdiff.exe  (GUI, no console window)
- dist/docdiff-cli.exe (CLI, with console)
"""

def run_pyinstaller():
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Common args
    common = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        # Include templates and static files
        "--add-data", f"{os.path.join(project_root, 'docdiff', 'webapp', 'templates')}:docdiff/webapp/templates",
        "--add-data", f"{os.path.join(project_root, 'docdiff', 'webapp', 'static')}:docdiff/webapp/static",
    ]
    
    # GUI version (no console)
    gui_args = common + [
        "--name", "docdiff",
        "--windowed",
        "--icon", "NONE",
        os.path.join(project_root, "main.py"),
    ]
    
    print("Building docdiff.exe (GUI, no console)...")
    result = subprocess.run(gui_args, cwd=project_root)
    if result.returncode != 0:
        print("GUI build failed!")
        return result.returncode
    
    # CLI version (with console)
    cli_args = common + [
        "--name", "docdiff-cli",
        "--console",
        "--icon", "NONE",
        os.path.join(project_root, "docdiff", "cli.py"),
    ]
    
    print("Building docdiff-cli.exe (CLI, with console)...")
    result = subprocess.run(cli_args, cwd=project_root)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_pyinstaller())
