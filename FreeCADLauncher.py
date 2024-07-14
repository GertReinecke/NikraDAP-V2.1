import os
import subprocess
import signal
import time

def close_freecad():
    """
    Closes any running instance of FreeCAD.
    """
    if os.name == 'nt':  # For Windows
        os.system('taskkill /f /im FreeCAD.exe')
    else:  # For Unix-based systems
        # This will send the SIGTERM signal to gracefully terminate FreeCAD
        os.system('pkill FreeCAD')

def launch_freecad(freecad_path, file_to_open=None):
    """
    Launches a new instance of FreeCAD.
    :param freecad_path: The path to the FreeCAD executable.
    :param file_to_open: Optional, the path to a FreeCAD file to open.
    """
    if file_to_open:
        subprocess.Popen([freecad_path, file_to_open])
    else:
        subprocess.Popen([freecad_path])

# Path to the FreeCAD executable
freecad_path = 'D:\\Universiteit\\MSS 732\\FreeCAD\\bin\\FreeCAD.exe'  # Change this to your FreeCAD executable path

# Optional: Path to the FreeCAD file to open
file_to_open = 'C:\\path\\to\\your\\file.FCStd'  # Change this to your FreeCAD file path if needed

# Step 1: Close FreeCAD
close_freecad()

# Step 2: Wait a moment to ensure FreeCAD is closed
time.sleep(2)

# Step 3: Launch FreeCAD
# launch_freecad(freecad_path, file_to_open)
launch_freecad(freecad_path)