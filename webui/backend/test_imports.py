import sys
import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '../../'))
sys.path.append(project_root)

try:
    import penplotter.img2sketch as img2sketch
    import penplotter.imageUtils as imageUtils
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
