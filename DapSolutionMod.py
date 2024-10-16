import FreeCAD
import FreeCADGui

from os import path, getcwd
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT
import DapMainMod

Debug = False

planeOfMotion2 = []

# =============================================================================
def makeDapSolution(name="DapSolution"):
    """Create a Dap Solver object"""
    if Debug:
        DT.Mess("makeDapSolution")
    solutionObject = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    # Instantiate a DapSolution object
    DapSolutionClass(solutionObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapSolutionClass(solutionObject.ViewObject)
    return solutionObject
# =============================================================================
class DapSolutionClass:
    if Debug:
        DT.Mess("DapSolutionClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solutionObject):
        """Initialise on instantiation of a new DAP solver object"""
        if Debug:
            DT.Mess("DapSolutionClass-__init__")
        solutionObject.Proxy = self
        
        self.addPropertiesToObject(solutionObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, solutionObject):
        if Debug:
            DT.Mess("DapSolutionClass-onDocumentRestored")
        self.addPropertiesToObject(solutionObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, solutionObject):
        """Initialise all the properties of the solver object"""
        if Debug:
            DT.Mess("DapSolutionClass-addPropertiesToObject")
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("DapSolutionClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("DapSolutionClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class ViewProviderDapSolutionClass:
    if Debug:
        DT.Mess("ViewProviderDapSolutionClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverViewObject):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-__init__")
        solverViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, solverViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-doubleClicked")
        Document = FreeCADGui.getDocument(solverViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(solverViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the solver icon (Icon7n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-getIcon")
        return path.join(DT.getDapModulePath(), "Icons", "DapSolution.png")
    #  -------------------------------------------------------------------------
    def attach(self, solverViewObject):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-attach")
        self.solutionObject = solverViewObject.Object
        solverViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, obj):
        """Return an empty list of modes when requested"""
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-getDisplayModes")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-getDefaultDisplayMode")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-setDisplayMode")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, solverViewObject, mode):
        """Edit the parameters by switching on the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-setEdit")
        FreeCADGui.Control.showDialog(TaskPanelDapSolutionClass(self.solutionObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, viewobj, mode):
        """Shut down the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-unsetEdit")
        FreeCADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("ViewProviderDapSolutionClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class TaskPanelDapSolutionClass:
    """Taskpanel for Executing DAP Solver User Interface"""
    if Debug:
        DT.Mess("TaskPanelDapSolutionClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverTaskObject):
        """Run on first instantiation of a TaskPanelDapSolution class"""
        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-__init__")

        self.solverTaskObject = solverTaskObject
        solverTaskObject.Proxy = self

        # Get the directory name to store results in
        if solverTaskObject.Directory == "":
            solverTaskObject.Directory = getcwd()

        # Load the taskDialog form information
        ui_path = path.join(path.dirname(__file__), "TaskPanels", "TaskPanelDapSolution.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # Set up actions on the solver button and fileDirectory browser
        self.form.solveButton.clicked.connect(self.solveButtonClicked_Callback)
        self.form.browseFileDirectory.clicked.connect(self.getFolderDirectory_Callback)

        # Set the time in the form
        self.form.endTime.setValue(solverTaskObject.TimeLength)
        self.form.reportingTime.setValue(solverTaskObject.DeltaTime)

        # Set the file name and directory
        self.form.outputDirectory.setText(solverTaskObject.Directory)
        self.form.outputFileName.setText(solverTaskObject.FileName)

        # Grey out the output data check boxes
        self.form.outputAnimOnly.toggled.connect(self.outputAnimOnlyCheckboxChanged_Callback)
        self.form.outputAnimOnly.setChecked(False)
        self.form.outputAnimOnly.setChecked(True)

        # Set the accuracy in the form
        self.Accuracy = 5
        self.form.Accuracy.setValue(self.Accuracy)
        self.form.Accuracy.valueChanged.connect(self.accuracyChanged_Callback)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button"""

        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-accept")

        # Save the settings to the object
        self.solverTaskObject.TimeLength = self.form.endTime.value()

        # Recompute document to update view provider based on the shapes
        self.solverTaskObject.recompute()

        # Close the dialog
        Document = FreeCADGui.getDocument(self.solverTaskObject.Document)
        Document.resetEdit()

        #  Recompute document to update view provider based on the shapes
        solverDocName = str(self.solverTaskObject.Document.Name)
        FreeCAD.getDocument(solverDocName).recompute()
    #  -------------------------------------------------------------------------
    def outputAnimOnlyCheckboxChanged_Callback(self):
        if self.form.outputAnimOnly.isChecked():
            self.form.outputFileLabel.setDisabled(True)
            self.form.outputFileName.setDisabled(True)
            self.form.browseFileDirectory.setDisabled(True)
            self.form.outputDirectoryLabel.setDisabled(True)
            self.form.outputDirectory.setDisabled(True)
        else:
            self.form.outputFileLabel.setEnabled(True)
            self.form.outputFileName.setEnabled(True)
            self.form.browseFileDirectory.setEnabled(True)
            self.form.outputDirectoryLabel.setEnabled(True)
            self.form.outputDirectory.setEnabled(True)
            self.Accuracy = 9
            self.form.Accuracy.setValue(self.Accuracy)
    #  -------------------------------------------------------------------------
    def solveButtonClicked_Callback(self):
        """Call the MainSolve() method in the DapMainC class"""

        # Update the settings of the solver objects from the task panel
        self.solverTaskObject.TimeLength = self.form.endTime.value()
        self.solverTaskObject.DeltaTime = self.form.reportingTime.value()

        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-solveButtonClicked_Callback")

        # Change the solve button to red with 'Solving' on it
        self.form.solveButton.setDisabled(True)
        self.form.solveButton.setText("Solving")
        self.form.solveButton.repaint()
        self.form.solveButton.update()

        # Instantiate the DapMainC class and run the solver
        self.DapMainC_Instance = DapMainMod.DapMainC(
                    self.solverTaskObject.TimeLength,
                    self.solverTaskObject.DeltaTime,
                    self.Accuracy,
                    self.form.correctInitial.isChecked()
                )
        
        if self.DapMainC_Instance.initialised is True:
            self.DapMainC_Instance.MainSolve()

        self.form.solveButton.setText("Solve")
        self.form.solveButton.setEnabled(True)

    def getFolderDirectory_Callback(self):
        """Request the directory where the .csv result files will be written"""
        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-getFolderDirectory_Callback")
        self.solverTaskObject.Directory = QtGui.QFileDialog.getExistingDirectory()
        self.form.outputDirectory.setText(self.solverTaskObject.Directory)
    #  -------------------------------------------------------------------------
    def accuracyChanged_Callback(self):
        """Change the accuracy setting when slider has been adjusted"""
        self.Accuracy = self.form.Accuracy.value()
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-getStandardButtons")
        return int(QtGui.QDialogButtonBox.Ok)
        
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapSolutionClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================