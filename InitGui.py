import FreeCADGui

import os

# =============================================================================
# InitGui.py
# 1. Connects the workbench to FreeCAD and FreeCADGui
# 2. Builds the graphical interface between the workbench and FreeCAD
# 3. Couples the graphical interface of FreeCAD with the functions of the workbench
# =============================================================================

class DapWorkbench21C(Workbench):
    """This class encompasses the whole NikraDAP workbench"""

    #  -------------------------------------------------------------------------
    def __init__(self):
        """Called on startup of FreeCAD"""
        print("DapWorkbenchClass-__init__")

        # Set up the text for the DAP workbench option, the NikraDAP icon, and the tooltip
        self.__class__.Icon = os.path.join(os.getcwd(), "Icons", "Icon1n.png")
        self.__class__.MenuText = "NikraDAP-2.1"
        self.__class__.ToolTip = "Planar multibody dynamics workbench based on Prof. Nikravesh's DAP solver"

    #  -------------------------------------------------------------------------

    def Initialize(self):
        """Called on the first selection of the DapWorkbench
        and couples the main NikraDAP functions to the FreeCAD interface"""
        print("DapWorkbenchClass-Initialize")

        # Define which commands will be called with each command alias
        from DapContainerMod import CommandDapContainerClass
        from DapBodyMod import CommandDapBodyClass
        from DapMaterialMod import CommandDapMaterialClass
        from DapForceMod import CommandDapForceClass
        from DapJointMod import CommandDapJointClass
        from DapSolverMod import CommandDapSolverClass
        from DapAnimationMod import CommandDapAnimationClass

        # Add the command to FreeCAD's list of functions
        FreeCADGui.addCommand("DapContainerAlias", CommandDapContainerClass())
        FreeCADGui.addCommand("DapBodyAlias", CommandDapBodyClass())
        FreeCADGui.addCommand("DapMaterialAlias", CommandDapMaterialClass())
        FreeCADGui.addCommand("DapJointAlias", CommandDapJointClass())
        FreeCADGui.addCommand("DapForceAlias", CommandDapForceClass())
        FreeCADGui.addCommand("DapSolverAlias", CommandDapSolverClass())
        FreeCADGui.addCommand("DapAnimationAlias", CommandDapAnimationClass())

        # Create a toolbar with the DAP commands (Icons)
        self.appendToolbar("NikraDAP Commands", self.MakeCommandList())

        # Create a drop-down menu item for the menu bar
        self.appendMenu("NikraDAP-2.1", self.MakeCommandList())
    #  -------------------------------------------------------------------------

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen
        'recipient'=='View' when mouse is in the VIEW window
        'recipient'=='Tree' when mouse is in the TREE window
        We currently do no use either flag"""
        #print("DapWorkbenchClass-ContextMenu\n")

        # Append the DAP commands to the existing context menu
        self.appendContextMenu("NikraDAP Commands", self.MakeCommandList())
    #  -------------------------------------------------------------------------

    def MakeCommandList(self):
        """Define a list of our aliases for all the DAP main functions"""
        return [
            "DapContainerAlias",
            "Separator",
            "DapBodyAlias",
            "DapMaterialAlias",
            "DapForceAlias",
            "DapJointAlias",
            "Separator",
            "DapSolverAlias",
            "Separator",
            "DapAnimationAlias"
        ]
    #  -------------------------------------------------------------------------

    def Activated(self):
        """Called when the NikraDAP workbench is run"""
    #  -------------------------------------------------------------------------

    def Deactivated(self):
        """This function is executed each time the DAP workbench is stopped"""
    #  -------------------------------------------------------------------------

    def GetClassName(self):
        """This function is mandatory if this is a full FreeCAD workbench
        The returned string should be exactly 'Gui::PythonWorkbench'
        This enables FreeCAD to ensure that the stuff in its 'Mod' folder
        is a valid workbench and not just rubbish"""
        return "Gui::PythonWorkbench"
    # --------------------------------------------------------------------------
    def __str__(self):
        return str(self.__dict__)

# =============================================================================
# Run when FreeCAD detects a workbench folder in its 'Mod' folder
# Add the workbench to the list of workbenches and initialize it
# =============================================================================
FreeCADGui.addWorkbench(DapWorkbench21C())