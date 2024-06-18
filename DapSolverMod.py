# ********************************************************************************
# *                                                                              *
# *   This program is free software; you can redistribute it and/or modify       *
# *   it under the terms of the GNU Lesser General Public License (LGPL)         *
# *   as published by the Free Software Foundation; either version 3 of          *
# *   the License, or (at your option) any later version.                        *
# *   for detail see the LICENCE text file.                                      *
# *                                                                              *
# *   This program is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of             *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       *
# *   See the GNU Lesser General Public License for more details.                *
# *                                                                              *
# *   You should have received a copy of the GNU Lesser General Public           *
# *   License along with this program; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston,                      *
# *   MA 02111-1307, USA                                                         *
# *_____________________________________________________________________________ *
# *                                                                              *
# *        ##########################################################            *
# *       #### Nikra-DAP FreeCAD WorkBench Revision 2.1 (c) 2024: ####           *
# *        ##########################################################            *
# *                                                                              *
# *                     Authors of this workbench:                               *
# *                   Cecil Churms <churms@gmail.com>                            *
# *             Lukas du Plessis (UP) <lukas.duplessis@up.ac.za>                 *
# *                                                                              *
# *               This file is a sizeable expansion of the:                      *
# *                "Nikra-DAP-Rev-1" workbench for FreeCAD                       *
# *        with increased functionality and inherent code documentation          *
# *                  by means of expanded variable naming                        *
# *                                                                              *
# *     Which in turn, is based on the MATLAB code Complementary to              *
# *                  Chapters 7 and 8 of the textbook:                           *
# *                                                                              *
# *                     "PLANAR MULTIBODY DYNAMICS                               *
# *         Formulation, Programming with MATLAB, and Applications"              *
# *                          Second Edition                                      *
# *                         by P.E. Nikravesh                                    *
# *                          CRC Press, 2018                                     *
# *                                                                              *
# *     Authors of Rev-1:                                                        *
# *            Alfred Bogaers (EX-MENTE) <alfred.bogaers@ex-mente.co.za>         *
# *            Lukas du Plessis (UP) <lukas.duplessis@up.ac.za>                  *
# *            Dewald Hattingh (UP) <u17082006@tuks.co.za>                       *
# *            Varnu Govender (UP) <govender.v@tuks.co.za>                       *
# *                                                                              *
# * Copyright (c) 2024 Cecil Churms <churms@gmail.com>                           *
# * Copyright (c) 2024 Lukas du Plessis (UP) <lukas.duplessis@up.ac.za>          *
# * Copyright (c) 2022 Alfred Bogaers (EX-MENTE) <alfred.bogaers@ex-mente.co.za> *
# * Copyright (c) 2022 Dewald Hattingh (UP) <u17082006@tuks.co.za>               *
# * Copyright (c) 2022 Varnu Govender (UP) <govender.v@tuks.co.za>               *
# *                                                                              *
# *             Please refer to the Documentation and README for                 *
# *         more information regarding this WorkBench and its usage              *
# *                                                                              *
# ********************************************************************************
import FreeCAD as CAD
import FreeCADGui as CADGui

from os import path, getcwd
from math import sin, cos, tan, asin, acos, atan2, pi
import Part
import time
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT
import DapMainMod

Debug = False
# =============================================================================
def makeDapSolver(name="DapSolver"):
    """Create a Dap Solver object"""
    if Debug:
        DT.Mess("makeDapSolver")
    solverObject = CAD.ActiveDocument.addObject("Part::FeaturePython", name)
    # Instantiate a DapSolver object
    DapSolverClass(solverObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapSolverClass(solverObject.ViewObject)
    return solverObject
# =============================================================================
class CommandDapSolverClass:
    """The Dap Solver command definition"""
    if Debug:
        DT.Mess("CommandDapSolverClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapSolverClass-GetResources")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon7n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("Dap_Solver_alias", "Run the analysis"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("Dap_Solver_alias", "Run the analysis."),
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out"""
        if Debug:
            DT.Mess("CommandDapSolverClass-IsActive(query)")
        return (DT.getActiveContainerObject() is not None) and (DT.getMaterialObject() is not None)
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Solver command is run"""
        if Debug:
            DT.Mess("CommandDapSolverClass-Activated")
        # Re-use the old solver object if it exists
        activeContainer = DT.getActiveContainerObject()
        for groupMember in activeContainer.Group:
            if "DapSolver" in groupMember.Name:
                solverObject = groupMember
                CADGui.ActiveDocument.setEdit(solverObject.Name)
                return
        # Otherwise create a new solver object
        DT.getActiveContainerObject().addObject(makeDapSolver())
        CADGui.ActiveDocument.setEdit(CAD.ActiveDocument.ActiveObject.Name)
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
class DapSolverClass:
    if Debug:
        DT.Mess("DapSolverClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverObject):
        """Initialise on instantiation of a new DAP solver object"""
        if Debug:
            DT.Mess("DapSolverClass-__init__")
        solverObject.Proxy = self
        self.addPropertiesToObject(solverObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, solverObject):
        if Debug:
            DT.Mess("DapSolverClass-onDocumentRestored")
        self.addPropertiesToObject(solverObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, solverObject):
        """Initialise all the properties of the solver object"""
        if Debug:
            DT.Mess("DapSolverClass-addPropertiesToObject")

        DT.addObjectProperty(solverObject, "FileName",        "",    "App::PropertyString",     "", "FileName to save data under")
        DT.addObjectProperty(solverObject, "Directory",       "",    "App::PropertyString",     "", "Directory to save data")
        DT.addObjectProperty(solverObject, "TimeLength",      10.0,  "App::PropertyFloat",      "", "Length of the Analysis")
        DT.addObjectProperty(solverObject, "DeltaTime",       0.01,  "App::PropertyFloat",      "", "Length of time steps")
        DT.addObjectProperty(solverObject, "DapResultsValid", False, "App::PropertyBool",       "", "")
        DT.addObjectProperty(solverObject, "BodyNames",       [],    "App::PropertyStringList", "", "")
        DT.addObjectProperty(solverObject, "BodyCoG",         [],    "App::PropertyVectorList", "", "")
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("DapSolverClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("DapSolverClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class ViewProviderDapSolverClass:
    if Debug:
        DT.Mess("ViewProviderDapSolverClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverViewObject):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-__init__")
        solverViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, solverViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-doubleClicked")
        Document = CADGui.getDocument(solverViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(solverViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the solver icon (Icon7n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-getIcon")
        return path.join(DT.getDapModulePath(), "icons", "Icon7n.png")
    #  -------------------------------------------------------------------------
    def attach(self, solverViewObject):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-attach")
        self.solverObject = solverViewObject.Object
        solverViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, obj):
        """Return an empty list of modes when requested"""
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-getDisplayModes")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-getDefaultDisplayMode")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-setDisplayMode")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, solverViewObject, mode):
        """Edit the parameters by switching on the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-setEdit")
        CADGui.Control.showDialog(TaskPanelDapSolverClass(self.solverObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, viewobj, mode):
        """Shut down the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-unsetEdit")
        CADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("ViewProviderDapSolverClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class TaskPanelDapSolverClass:
    """Taskpanel for Executing DAP Solver User Interface"""
    if Debug:
        DT.Mess("TaskPanelDapSolverClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverTaskObject):
        """Run on first instantiation of a TaskPanelDapSolver class"""
        if Debug:
            DT.Mess("TaskPanelDapSolverClass-__init__")

        self.solverTaskObject = solverTaskObject
        solverTaskObject.Proxy = self

        # Get the directory name to store results in
        if solverTaskObject.Directory == "":
            solverTaskObject.Directory = getcwd()

        # Load the taskDialog form information
        ui_path = path.join(path.dirname(__file__), "TaskPanelDapSolver.ui")
        self.form = CADGui.PySideUic.loadUi(ui_path)

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
            DT.Mess("TaskPanelDapSolverClass-accept")

        # Close the dialog
        Document = CADGui.getDocument(self.solverTaskObject.Document)
        Document.resetEdit()

        #  Recompute document to update view provider based on the shapes
        solverDocName = str(self.solverTaskObject.Document.Name)
        CAD.getDocument(solverDocName).recompute()
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

        if Debug:
            DT.Mess("TaskPanelDapSolverClass-solveButtonClicked_Callback")

        # Change the solve button to red with 'Solving' on it
        self.form.solveButton.setDisabled(True)
        self.form.solveButton.setText("Solving")
        # Do some arithmetic to allow the repaint to happen
        # before the frame becomes unresponsive due to the big maths
        self.form.solveButton.repaint()
        self.form.solveButton.update()
        t = 0.0
        for f in range(1000000):
            t += f/10.0
        self.form.solveButton.repaint()
        self.form.solveButton.update()

        self.solverTaskObject.Directory = self.form.outputDirectory.text()
        if self.form.outputAnimOnly.isChecked():
            self.solverTaskObject.FileName = "-"
        else:
            self.solverTaskObject.FileName = self.form.outputFileName.text()

        self.solverTaskObject.TimeLength = self.form.endTime.value()
        self.solverTaskObject.DeltaTime = self.form.reportingTime.value()

        # Instantiate the DapMainC class and run the solver
        self.DapMainC_Instance = DapMainMod.DapMainC(self.solverTaskObject.TimeLength,
                                                     self.solverTaskObject.DeltaTime,
                                                     self.Accuracy,
                                                     self.form.correctInitial.isChecked())
        if self.DapMainC_Instance.initialised is True:
            self.DapMainC_Instance.MainSolve()

        # Return the solve button to green with 'Solve' on it
        self.form.solveButton.setText("Solve")
        self.form.solveButton.setEnabled(True)
        # We end here after the solving has been completed
        # and will wait for the OK button to be clicked
    #  -------------------------------------------------------------------------
    def getFolderDirectory_Callback(self):
        """Request the directory where the .csv result files will be written"""
        if Debug:
            DT.Mess("TaskPanelDapSolverClass-getFolderDirectory_Callback")
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
            DT.Mess("TaskPanelDapSolverClass-getStandardButtons")
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
