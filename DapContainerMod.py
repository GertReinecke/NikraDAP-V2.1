import FreeCAD

from os import path
from PySide import QtCore

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapContainer(name="DapContainer"):
    """Create Dap Container FreeCAD group object"""
    if Debug:
        DT.Mess("makeDapContainer")
    containerObject = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    # Instantiate a DapContainer object
    DapContainerClass(containerObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapContainerClass(containerObject.ViewObject)
    return containerObject
# =============================================================================
class CommandDapContainerClass:
    """The Dap Container command definition"""
    if Debug:
        DT.Mess("CommandDapContainerClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapContainerClass-GetResources")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "Icons", "Icon2n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("Dap_Container_alias", "Add Container"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("Dap_Container_alias", "Creates a container for the DAP analysis data."),
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out
        Only activate it if we have an Assembly 4 model to use"""
        if Debug:
            DT.Mess("CommandDapContainerClass-IsActive(query)")
        # Return True if we have an Assembly4 FreeCAD model document which is loaded and Active
        if FreeCAD.ActiveDocument is None:
            FreeCAD.Console.PrintErrorMessage("No active document is loaded into FreeCAD for NikraDAP to use")
            return False

        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, "Type") and obj.Type == 'Assembly':
                return True

        FreeCAD.Console.PrintErrorMessage("No Assembly4 Model found for NikraDAP to use")
        return False
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the create Container command is run by either pressing
        the tool Icon, or running it from one of the available menus.
        We create the DapContainer and set it to be Active"""
        if Debug:
            DT.Mess("CommandDapContainerClass-Activated")
        # This is where we create a new empty Dap Container
        if DT.setActiveContainer(makeDapContainer()) is False:
            FreeCAD.Console.PrintError("Failed to create DAP container")
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class DapContainerClass:
    """The Dap analysis container class"""
    if Debug:
        DT.Mess("DapContainerClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, containerObject):
        """Initialise on entry"""
        if Debug:
            DT.Mess("DapContainerClass-__init__")
        containerObject.Proxy = self
        self.addPropertiesToObject(containerObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, containerObject):
        if Debug:
            DT.Mess("DapContainerClass-onDocumentRestored")
        self.addPropertiesToObject(containerObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, containerObject):
        """Run by '__init__'  and 'onDocumentRestored' to initialise the empty container members"""
        if Debug:
            DT.Mess("DapContainerClass-addPropertiesToObject")

        DT.addObjectProperty(containerObject, "activeContainer",     False,                          "App::PropertyBool",   "", "Flag as Active analysis object in document")
        DT.addObjectProperty(containerObject, "movementPlaneNormal", FreeCAD.Vector(0, 0, 1),            "App::PropertyVector", "", "Defines the movement plane in this NikraDAP run")
        DT.addObjectProperty(containerObject, "gravityVector",       FreeCAD.Vector(0.0, -9810.0, 0.0),  "App::PropertyVector", "", "Gravitational acceleration Components")
        DT.addObjectProperty(containerObject, "gravityValid",        False,                          "App::PropertyBool",   "", "Flag to verify that the gravity Vector is applicable")

        DT.setActiveContainer(containerObject)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("DapContainerClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("DapContainerClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class ViewProviderDapContainerClass:
    """A view provider for the DapContainer container object"""
    if Debug:
        DT.Mess("ViewProviderDapContainerClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, containerViewObject):
        if Debug:
            DT.Mess("ViewProviderDapContainerClass-__init__")
        containerViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, containerViewObject):
        """Set the container to be the active one"""
        if Debug:
            DT.Mess("ViewProviderDapContainerClass-doubleClicked")
        DT.setActiveContainer(containerViewObject.Object)
        return DT.getActiveContainerObject()
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the container icon (Icon2n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapContainer-getIcon")
        return path.join(DT.getDapModulePath(), "Icons", "Icon2n.png")
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================