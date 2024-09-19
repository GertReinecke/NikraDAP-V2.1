import FreeCAD
import FreeCADGui

from os import path
from PySide import QtCore

import DapToolsMod as DT

from os import path, getcwd
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT
import DapMainMod

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
            "Pixmap": path.join(DT.getDapModulePath(), "Icons", "DAPContainer.png"),
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
    """Handle the screen interface stuff for the containers dialog"""
    #  -------------------------------------------------------------------------
    def __init__(self, containerViewObject):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-__init__\n")
        containerViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, containerViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-doubleClicked\n")
        Document = FreeCADGui.getDocument(containerViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(containerViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the container icon (Icon5n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapContainerClass-getIcon")
        return path.join(DT.getDapModulePath(), "Icons", "DAPContainer.png")
    #  -------------------------------------------------------------------------
    def attach(self, containerViewObject):
        if Debug:
            DT.Mess("ViewProviderDapContainerClass-attach")
        self.containerObject = containerViewObject.Object
        containerViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, containerObject):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-getDisplayModes\n")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-getDefaultDisplayMode\n")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-setDisplayMode\n")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, containerViewObject, mode):
        """Edit the parameters by calling the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapContainerlass-setEdit")
        FreeCADGui.Control.showDialog(TaskPanelDapContainerClass(self.containerObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, containerViewObject, mode):
        """Close the task dialog when we have finished using it"""
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-unsetEdit\n")
        FreeCADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-dumps\n")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            FreeCAD.Console.PrintMessage("ViewProviderDapContainerClass-loads\n")
        if state:
            self.Type = state
        return None
# =============================================================================
class TaskPanelDapContainerClass:
    """Taskpanel for Executing DAP Container User Interface"""
    if Debug:
        DT.Mess("TaskPanelDapContainerClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, containerTaskObject):
        """Run on first instantiation of a TaskPanelDapContainer class"""
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-__init__")

        self.containerTaskObject = containerTaskObject
        containerTaskObject.Proxy = self

        # Load the taskDialog form information
        ui_path = path.join(path.dirname(__file__), "TaskPanels\\TaskPanelDapContainer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # Set the plane of motion
        self.form.planeOfMotionBtn.clicked.connect(self.getPlaneOfMotion_Callback)
        self.form.planeOfMotionName.setText(self.containerTaskObject.movementPlaneNormal.__str__())
    
    def accept(self):
        """Run when we press the OK button"""
        if Debug:
            FreeCAD.Console.PrintMessage("TaskPanelDapContainerClass-accept\n")

        # Update all the stuff by asking for a re-compute
        self.containerTaskObject.recompute()
        FreeCADGui.getDocument(self.containerTaskObject.Document).resetEdit()
    #  -------------------------------------------------------------------------
    def getPlaneOfMotion_Callback(self):
        # First get the selected objects
        selected_objects = FreeCADGui.Selection.getSelectionEx()
        if len(selected_objects) != 1:
            print('There are more than one selected object')
            return

        selected_object = selected_objects[0]
        sub_objects = selected_object.SubObjects
        if len(sub_objects) != 1:
            print('There are more than one selected face, edge, vertex')
            return

        face = sub_objects[0]
        if face.ShapeType != 'Face':
            print('Please select a face')
            return
        
        normal = face.normalAt(0, 0)
        self.form.planeOfMotionName.setText(normal.__str__())
        self.containerTaskObject.movementPlaneNormal = normal
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            FreeCAD.Console.PrintMessage("TaskPanelDapContainerClass-getStandardButtons\n")
        return int(QtGui.QDialogButtonBox.Ok)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapSolverClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapSolverClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
