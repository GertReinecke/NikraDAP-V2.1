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
from FreeCAD.Plot import Plot

class TaskPanelDapSolutionClass:
    """Taskpanel for Executing DAP Solver User Interface"""
    if Debug:
        DT.Mess("TaskPanelDapSolutionClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solutionTaskObject):
        """Run on first instantiation of a TaskPanelDapSolution class"""
        self.solutionTaskObject = solutionTaskObject
        solutionTaskObject.Proxy = self
        # Load the taskDialog form information
        ui_path = path.join(path.dirname(__file__), "TaskPanels", "TaskPanelDapSolution.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # Polulate the combo box with the list of properties, for the x axis
        data_properties = [prop for prop in solutionTaskObject.PropertiesList if solutionTaskObject.getGroupOfProperty(prop) == "Data"]
        self.form.cmbXAxis.addItems(data_properties)
        if "Time" in data_properties:
            time_index = data_properties.index("Time")
            self.form.cmbXAxis.setCurrentIndex(time_index)

        # Populate the Y-axis QListWidget with checkable items
        for prop in data_properties:
            item = QtGui.QListWidgetItem(prop)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)  # Set the initial state to unchecked
            self.form.lwYAxis.addItem(item)

        # Create a plot figure
        Plot.figure('DAPSolution Plot')
        
        self.form.cmbXAxis.currentIndexChanged.connect(self.graphChange_Callback)
        self.form.lwYAxis.itemChanged.connect(self.graphChange_Callback)

        self.form.chXAuto.stateChanged.connect(self.graphChange_Callback)
        self.form.chYAuto.stateChanged.connect(self.graphChange_Callback)

        self.form.edtXMin.textChanged.connect(self.graphChange_Callback)
        self.form.edtXMax.textChanged.connect(self.graphChange_Callback)
        self.form.edtYMin.textChanged.connect(self.graphChange_Callback)
        self.form.edtYMax.textChanged.connect(self.graphChange_Callback)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button"""
        # Close the plotting
        Plot.closePlot()

        Document = FreeCADGui.getDocument(self.solutionTaskObject.Document)
        Document.resetEdit()

    def graphChange_Callback(self):
        """Change the accuracy setting when slider has been adjusted"""
        plt = Plot.getPlot()

        if not plt: # Ensure there is a plot object
            Plot.figure('DAPSolution Plot')
            plt = Plot.getPlot()

            if not plt:
                return

        # Get the data
        x_label = self.form.cmbXAxis.currentText()
        x_values = self.solutionTaskObject.getPropertyByName(x_label)

        y_values = []
        for i in range(self.form.lwYAxis.count()):
            item = self.form.lwYAxis.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                y_values.append(item.text())

        #plt.title("Title")
        ax = plt.axes
        ax.cla()
        plt.update()

        ax.set_xlabel(x_label)
        
        y_label = ""
        for y in y_values:
            y_values = self.solutionTaskObject.getPropertyByName(y)
            ax.plot(x_values, y_values, label=y)
            y_label = f"{y_label}{y} "
        ax.set_ylabel(y_label)
        
        # Get the handles and labels for the legend
        handles, labels = ax.get_legend_handles_labels()
        # Only add a legend if there are labels
        if labels:
            ax.legend()

        # Adjust the axis limits
        if self.form.chXAuto.checkState() == False:
            try:
                ax.set_xlim(float(self.form.edtXMin.text()), float(self.form.edtXMax.text()))
            except:
                pass

        if self.form.chYAuto.checkState() == False:
            try:
                ax.set_ylim(float(self.form.edtYMin.text()), float(self.form.edtYMax.text()))
            except:
                pass

        plt.update()

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