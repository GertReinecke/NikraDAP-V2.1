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
# *       #### Nikra-DAP FreeCAD WorkBench Revision 2.0 (c) 2023: ####           *
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
# * Copyright (c) 2023 Cecil Churms <churms@gmail.com>                           *
# * Copyright (c) 2023 Lukas du Plessis (UP) <lukas.duplessis@up.ac.za>          *
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

from os import path
import math
import Part
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapJoint(name="DapJoint"):
    """Create an empty Dap Joint Object"""
    if Debug:
        DT.Mess("makeDapJoint")
    jointObject = CAD.ActiveDocument.addObject("Part::FeaturePython", name)
    # Instantiate a DapJoint object
    DapJointClass(jointObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapJointClass(jointObject.ViewObject)
    return jointObject
# ==============================================================================
def initComboInFormF(ComboName, LabelList, index):
    ComboName.clear()
    comboLabels = ['Undefined'] + LabelList.copy()
    ComboName.addItems(comboLabels)
    ComboName.setCurrentIndex(index + 1)
#  -------------------------------------------------------------------------
def updateToolTipF(ComboName, LabelList):
    bodyString = ""
    for point in LabelList:
        if point != 'Undefined' or len(LabelList) == 1:
            bodyString = bodyString + DT.parsePoint(point) + "\n========\n"
    ComboName.setToolTip(str(bodyString[:-10]))
# ==============================================================================
class CommandDapJointClass:
    """The Dap Joint command definition"""
    if Debug:
        DT.Mess("CommandDapJointClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapJointClass-GetResourcesC")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon4n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("DapJointAlias", "Add Joint"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("DapJointAlias", "Creates and defines a joint for the DAP analysis."),
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out.
        Only activate it when there are at least two bodies defined"""
        if Debug:
            DT.Mess("CommandDapJointClass-IsActive(query)")
        return len(DT.getDictionary("DapBody")) > 1
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Dap Joint command is run"""
        if Debug:
            DT.Mess("CommandDapJointClass-Activated")
        # This is where we create a new empty Dap joint object
        DT.getActiveContainerObject().addObject(makeDapJoint())
        # Switch on the Dap Joint Task Dialog
        CADGui.ActiveDocument.setEdit(CAD.ActiveDocument.ActiveObject.Name)
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("CommandDapJointClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("CommandDapJointClass-__setstate__")
# ==============================================================================
class DapJointClass:
    if Debug:
        DT.Mess("DapJointClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, jointObject):
        """Initialise an instantiation of a new DAP Joint object"""
        if Debug:
            DT.Mess("DapJointClass-__init__")
        jointObject.Proxy = self
        self.addPropertiesToObject(jointObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, jointObject):
        if Debug:
            DT.Mess("DapJointClass-onDocumentRestored")
        self.addPropertiesToObject(jointObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, jointObject):
        """Initialise all the properties of the joint object"""
        if Debug:
            DT.Mess("DapJointClass-addPropertiesToObject")

        DT.addObjectProperty(jointObject, "JointType", -1, "App::PropertyInteger", "Joint", "Type of Joint")
        DT.addObjectProperty(jointObject, "JointNumber", 0, "App::PropertyInteger", "Joint", "Number of this joint")
        DT.addObjectProperty(jointObject, "fixDof", False, "App::PropertyBool", "Joint", "Fix the Degrees of Freedom")

        DT.addObjectProperty(jointObject, "body_I_Name", "", "App::PropertyString", "Points", "Name of Body at A of Joint")
        DT.addObjectProperty(jointObject, "body_I_Label", "", "App::PropertyString", "Points", "Label of Body at A of Joint")
        DT.addObjectProperty(jointObject, "body_I_Index", -1, "App::PropertyInteger", "Points", "Index of the head body in the NumPy array")

        DT.addObjectProperty(jointObject, "body_J_Name", "", "App::PropertyString", "Points", "Name of Body at B of Joint")
        DT.addObjectProperty(jointObject, "body_J_Label", "", "App::PropertyString", "Points", "Label of Body at B of Joint")
        DT.addObjectProperty(jointObject, "body_J_Index", -1, "App::PropertyInteger", "Points", "Index of the tail body in the NumPy array")

        DT.addObjectProperty(jointObject, "point_I_i_Name", "", "App::PropertyString", "Points", "Name of Point at head of joint")
        DT.addObjectProperty(jointObject, "point_I_i_Label", "", "App::PropertyString", "Points", "Label of Point at head of joint")
        DT.addObjectProperty(jointObject, "point_I_i_Index", -1, "App::PropertyInteger", "Points", "Index of the head point in the NumPy array")

        DT.addObjectProperty(jointObject, "point_I_j_Name", "", "App::PropertyString", "Points", "Name of Point at head of 2nd unit vector")
        DT.addObjectProperty(jointObject, "point_I_j_Label", "", "App::PropertyString", "Points", "Label of Point at head of 2nd unit vector")
        DT.addObjectProperty(jointObject, "point_I_j_Index", -1, "App::PropertyInteger", "Points", "Index of the head point of the 2nd unit vector in the NumPy array")

        DT.addObjectProperty(jointObject, "point_J_i_Name", "", "App::PropertyString", "Points", "Name of Point at tail of joint")
        DT.addObjectProperty(jointObject, "point_J_i_Label", "", "App::PropertyString", "Points", "Label of Point at tail of joint")
        DT.addObjectProperty(jointObject, "point_J_i_Index", -1, "App::PropertyInteger", "Points", "Index of the tail point in the NumPy array")

        DT.addObjectProperty(jointObject, "point_J_j_Name", "", "App::PropertyString", "Points", "Name of Point at tail of 2nd unit vector")
        DT.addObjectProperty(jointObject, "point_J_j_Label", "", "App::PropertyString", "Points", "Label of Point at tail of 2nd unit vector")
        DT.addObjectProperty(jointObject, "point_J_j_Index", -1, "App::PropertyInteger", "Points", "Index of the tail point of the 2nd unit vector in the NumPy array")

        DT.addObjectProperty(jointObject, "FunctClass", "", "App::PropertyPythonObject", "Driver", "A machine which is set up to generate a driver function")
        DT.addObjectProperty(jointObject, "FunctType", -1, "App::PropertyInteger", "Driver", "Analytical function type")
        DT.addObjectProperty(jointObject, "Coeff0", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c0'")
        DT.addObjectProperty(jointObject, "Coeff1", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c1'")
        DT.addObjectProperty(jointObject, "Coeff2", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c2'")
        DT.addObjectProperty(jointObject, "Coeff3", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c3'")
        DT.addObjectProperty(jointObject, "Coeff4", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c4'")
        DT.addObjectProperty(jointObject, "Coeff5", 0.0, "App::PropertyFloat", "Driver", "Drive Function coefficient 'c5'")

        DT.addObjectProperty(jointObject, "startTimeDriveFunc", 0.0, "App::PropertyFloat", "Driver", "Drive Function Start time")
        DT.addObjectProperty(jointObject, "endTimeDriveFunc", 0.0, "App::PropertyFloat", "Driver", "Drive Function End time")
        DT.addObjectProperty(jointObject, "startValueDriveFunc", 0.0, "App::PropertyFloat", "Driver", "Drive Func value at start")
        DT.addObjectProperty(jointObject, "endValueDriveFunc", 0.0, "App::PropertyFloat", "Driver", "Drive Func value at end")
        DT.addObjectProperty(jointObject, "endDerivativeDriveFunc", 0.0, "App::PropertyFloat", "Driver", "Drive Func derivative at end")
        DT.addObjectProperty(jointObject, "lengthLink", 0.0, "App::PropertyFloat", "Starting Values", "Link length")
        DT.addObjectProperty(jointObject, "Radius", 0.0, "App::PropertyFloat", "Starting Values", "Disc Radius")
        DT.addObjectProperty(jointObject, "world0", CAD.Vector(), "App::PropertyVector", "Starting Values",  "Initial condition for disc")
        DT.addObjectProperty(jointObject, "phi0", 0.0, "App::PropertyFloat", "Starting Values", "Initial condition for disc")
        DT.addObjectProperty(jointObject, "d0", CAD.Vector(), "App::PropertyVector", "Starting Values", "Initial condition (Rigid)")

        DT.addObjectProperty(jointObject, "nMovBodies", -1, "App::PropertyInteger", "Bodies & constraints", "Number of moving bodies involved")
        DT.addObjectProperty(jointObject, "mConstraints", -1, "App::PropertyInteger", "Bodies & constraints", "Number of rows (constraints)")
        DT.addObjectProperty(jointObject, "rowStart", -1, "App::PropertyInteger", "Bodies & constraints", "Row starting index")
        DT.addObjectProperty(jointObject, "rowEnd", -1, "App::PropertyInteger", "Bodies & constraints", "Row ending index")
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("DapJointClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("DapJointClass-__setstate__")
#  =============================================================================
class ViewProviderDapJointClass:
    if Debug:
        DT.Mess("ViewProviderDapJointClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, jointViewObject):
        if Debug:
            DT.Mess("ViewProviderDapJointClass-__init__")
        jointViewObject.Proxy = self
        self.jointObject = jointViewObject.Object
    #  -------------------------------------------------------------------------
    def doubleClicked(self, jointViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapJointClass-doubleClicked")
        Document = CADGui.getDocument(jointViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(jointViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the joint icon (Icon4n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapJointClass-getIcon")
        return path.join(DT.getDapModulePath(), "icons", "Icon4n.png")
    #  -------------------------------------------------------------------------
    def attach(self, jointViewObject):
        if Debug:
            DT.Mess("ViewProviderDapJointClass-attach")
        self.jointObject = jointViewObject.Object
        jointViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, jointViewObject):
        """Return an empty list of modes when requested"""
        if Debug:
            DT.Mess("ViewProviderDapJointClass-getDisplayModes")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            DT.Mess("ViewProviderDapJointClass-getDefaultDisplayMode")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            DT.Mess("ViewProviderDapJointClass-setDisplayMode")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, jointViewObject, mode):
        """Edit the parameters by calling the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapJointClass-setEdit")
        CADGui.Control.showDialog(TaskPanelDapJointClass(self.jointObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, jointViewObject, mode):
        """We have finished with the task dialog so close it"""
        if Debug:
            DT.Mess("ViewProviderDapJointClass-unsetEdit")
        CADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("ViewProviderDapJointClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("ViewProviderDapJoint-__setstate__")
# ==============================================================================
class TaskPanelDapJointClass:
    """Task panel for editing DAP Joints"""
    if Debug:
        DT.Mess("TaskPanelDapJointClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, jointTaskObject):
        """Run on first instantiation of a TaskPanelJoint class"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-__init__")

        self.jointTaskObject = jointTaskObject
        jointTaskObject.Proxy = self

        # Initialise some class instances which we will use later        
        self.pointNameListFirstBody = []
        self.pointLabelListFirstBody = []
        self.pointNameListSecondBody = []
        self.pointLabelListSecondBody = []

        # Load up the Task panel dialog definition file
        ui_path = path.join(path.dirname(__file__), "TaskPanelDapJoints.ui")
        self.form = CADGui.PySideUic.loadUi(ui_path)

        # Populate the body object dictionary with body {names : objects}
        self.bodyObjDict = DT.getDictionary("DapBody")

        # Make up the lists of possible body names and labels and their objects to ensure ordering
        self.bodyNames = []
        self.bodyLabels = []
        self.bodyObjects = []
        for bodyName in self.bodyObjDict:
            bodyObj = self.bodyObjDict[bodyName]
            self.bodyNames.append(bodyObj.Name)
            self.bodyLabels.append(bodyObj.Label)
            self.bodyObjects.append(bodyObj)

        # Connect changes to the respective Callback functions
        self.form.jointType.currentIndexChanged.connect(self.jointType_Changed_Callback)


        self.form.body_1B1P.currentIndexChanged.connect(self.body_1B1P_Changed_Callback)
        self.form.body_1B2P.currentIndexChanged.connect(self.body_1B2P_Changed_Callback)
        self.form.body1_2B2P.currentIndexChanged.connect(self.body1_2B2P_Changed_Callback)
        self.form.body2_2B2P.currentIndexChanged.connect(self.body2_2B2P_Changed_Callback)
        self.form.body1_2B3P.currentIndexChanged.connect(self.body1_2B3P_Changed_Callback)
        self.form.body2_2B3P.currentIndexChanged.connect(self.body2_2B3P_Changed_Callback)
        self.form.body1_2B4P.currentIndexChanged.connect(self.body1_2B4P_Changed_Callback)
        self.form.body2_2B4P.currentIndexChanged.connect(self.body2_2B4P_Changed_Callback)
        self.form.bodyDisc.currentIndexChanged.connect(self.bodyDisc_Changed_Callback)

        self.form.point_1B1P.currentIndexChanged.connect(self.point_1B1P_Changed_Callback)
        self.form.vectorHead_1B2P.currentIndexChanged.connect(self.vectorHead_1B2P_Changed_Callback)
        self.form.vectorTail_1B2P.currentIndexChanged.connect(self.vectorTail_1B2P_Changed_Callback)
        self.form.point1_2B2P.currentIndexChanged.connect(self.point1_2B2P_Changed_Callback)
        self.form.point2_2B2P.currentIndexChanged.connect(self.point2_2B2P_Changed_Callback)
        self.form.vectorHead_2B3P.currentIndexChanged.connect(self.vectorHead_2B3P_Changed_Callback)
        self.form.vectorTail_2B3P.currentIndexChanged.connect(self.vectorTail_2B3P_Changed_Callback)
        self.form.point_2B3P.currentIndexChanged.connect(self.point_2B3P_Changed_Callback)
        self.form.vector1Head_2B4P.currentIndexChanged.connect(self.vector1Head_2B4P_Changed_Callback)
        self.form.vector1Tail_2B4P.currentIndexChanged.connect(self.vector1Tail_2B4P_Changed_Callback)
        self.form.vector2Head_2B4P.currentIndexChanged.connect(self.vector2Head_2B4P_Changed_Callback)
        self.form.vector2Tail_2B4P.currentIndexChanged.connect(self.vector2Tail_2B4P_Changed_Callback)

        self.form.pointDiscCentre.currentIndexChanged.connect(self.pointDiscCentre_Changed_Callback)
        self.form.pointDiscRim.currentIndexChanged.connect(self.pointDiscRim_Changed_Callback)


        self.form.withDriver.toggled.connect(self.withDriver_Changed_Callback)
        self.form.radioButtonA.toggled.connect(self.radioA_Changed_Callback)
        self.form.radioButtonB.toggled.connect(self.radioB_Changed_Callback)
        self.form.radioButtonC.toggled.connect(self.radioC_Changed_Callback)
        self.form.radioButtonD.toggled.connect(self.radioD_Changed_Callback)
        self.form.radioButtonE.toggled.connect(self.radioE_Changed_Callback)
        self.form.radioButtonF.toggled.connect(self.radioF_Changed_Callback)

        # Set the joint type combo box up according to the jointObject
        self.form.jointType.clear()
        jointTypeCombo = ['Undefined'] + DT.JOINT_TYPE
        self.form.jointType.addItems(jointTypeCombo)
        self.form.jointType.setCurrentIndex(jointTaskObject.JointType + 1)

        # Initialise the withDriver checkbox and the a radio button
        self.form.radioButtonA.setChecked(True)
        self.form.withDriver.setChecked(False)
        self.form.withDriver.setEnabled(True)
        self.jointTaskObject.FunctType = -1

        # Activate the functions definition pages only if we have a Driven-Revolute or Driven-Translation joint
        '''if jointTaskObject.JointType == DT.JOINT_TYPE_DICTIONARY["Driven-Revolute"] or \
                jointTaskObject.JointType == DT.JOINT_TYPE_DICTIONARY["Driven-Translation"]:
            self.showAllEquationsF()
        else:
            self.greyAllEquationsF()'''

        # Copy over the current driver function parameters to the form in case we need them
        self.parmsToFormF()

        # Make the jointTaskObject "Observed" when the cursor is on it / it is selected
        CADGui.Selection.addObserver(jointTaskObject)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-accept")

        formJointType = self.form.jointType.currentIndex() - 1
        if formJointType == DT.JOINT_TYPE_DICTIONARY["Revolute"] or \
                formJointType == DT.JOINT_TYPE_DICTIONARY["Revolute-Revolute"] or \
                formJointType == DT.JOINT_TYPE_DICTIONARY["Rigid"]:
            self.jointTaskObject.point_I_j_Name = ""
            self.jointTaskObject.point_I_j_Label = ""
            self.jointTaskObject.point_I_j_Index = -1
            self.jointTaskObject.point_J_j_Name = ""
            self.jointTaskObject.point_J_j_Label = ""
            self.jointTaskObject.point_J_j_Index = -1
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Translation"]:
            pass
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Translation-Revolute"]:
            self.jointTaskObject.point_J_j_Name = ""
            self.jointTaskObject.point_J_j_Label = ""
            self.jointTaskObject.point_J_j_Index = -1
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Disc"]:
            self.jointTaskObject.point_J_i_Name = ""
            self.jointTaskObject.point_J_i_Label = ""
            self.jointTaskObject.point_J_i_Index = -1
            self.jointTaskObject.point_J_j_Name = ""
            self.jointTaskObject.point_J_j_Label = ""
            self.jointTaskObject.point_J_j_Index = -1

        # Switch off the Task panel
        GuiDocument = CADGui.getDocument(self.jointTaskObject.Document)
        GuiDocument.resetEdit()
    #  -------------------------------------------------------------------------
    def hideAllEquationsF(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-hideAllEquations")

        self.form.allRadioButtons.setEnabled(False)
        self.form.funcCoeff.setHidden(True)

        # The html image of the equations does not grey out when we set them hidden
        # So we have two copies of each, the one normal and the one grey
        # and we switch between the two when we enable/disable the functions
        self.form.funcAequationGrey.setVisible(True)
        self.form.funcAequation.setHidden(True)
        self.form.funcBequationGrey.setVisible(True)
        self.form.funcBequation.setHidden(True)
        self.form.funcCequationGrey.setVisible(True)
        self.form.funcCequation.setHidden(True)
        self.form.funcDequationGrey.setVisible(True)
        self.form.funcDequation.setHidden(True)
        self.form.funcEequationGrey.setVisible(True)
        self.form.funcEequation.setHidden(True)
        self.form.funcFequationGrey.setVisible(True)
        self.form.funcFequation.setHidden(True)
    #  -------------------------------------------------------------------------
    def showAllEquationsF(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-showAllEquationsF")

        self.form.allRadioButtons.setEnabled(True)
        self.form.funcCoeff.setEnabled(True)
        self.form.funcCoeff.setVisible(True)

        # The html image of the equations does not grey out when we set them hidden
        # So we have two copies of each, the one normal and the one grey
        # and we switch between the two when we enable/disable the functions
        self.form.funcAequationGrey.setHidden(True)
        self.form.funcAequation.setVisible(True)
        self.form.funcBequationGrey.setHidden(True)
        self.form.funcBequation.setVisible(True)
        self.form.funcCequationGrey.setHidden(True)
        self.form.funcCequation.setVisible(True)
        self.form.funcDequationGrey.setHidden(True)
        self.form.funcDequation.setVisible(True)
        self.form.funcEequationGrey.setHidden(True)
        self.form.funcEequation.setVisible(True)
        self.form.funcFequationGrey.setHidden(True)
        self.form.funcFequation.setVisible(True)
    #  -------------------------------------------------------------------------
    def parmsToFormF(self):
        """Transfer the applicable parameters from the joint object to the applicable page in the form"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-parmsToFormF")

        # Function type a
        self.form.FuncACoeff0.setValue(self.jointTaskObject.Coeff0)
        self.form.FuncACoeff1.setValue(self.jointTaskObject.Coeff1)
        self.form.FuncACoeff2.setValue(self.jointTaskObject.Coeff2)
        self.form.FuncAendTime.setValue(self.jointTaskObject.endTimeDriveFunc)

        # Function type b
        self.form.FuncBstartTime.setValue(self.jointTaskObject.startTimeDriveFunc)
        self.form.FuncBendTime.setValue(self.jointTaskObject.endTimeDriveFunc)
        self.form.FuncBstartValue.setValue(self.jointTaskObject.startValueDriveFunc)
        self.form.FuncBendValue.setValue(self.jointTaskObject.endValueDriveFunc)

        # Function type c
        self.form.FuncCstartTime.setValue(self.jointTaskObject.startTimeDriveFunc)
        self.form.FuncCendTime.setValue(self.jointTaskObject.endTimeDriveFunc)
        self.form.FuncCstartValue.setValue(self.jointTaskObject.startValueDriveFunc)
        self.form.FuncCendDeriv.setValue(self.jointTaskObject.endDerivativeDriveFunc)

        # Function type d
        self.form.FuncDCoeff0.setValue(self.jointTaskObject.Coeff0)
        self.form.FuncDCoeff1.setValue(self.jointTaskObject.Coeff1)
        self.form.FuncDCoeff2.setValue(self.jointTaskObject.Coeff2)
        self.form.FuncDCoeff3.setValue(self.jointTaskObject.Coeff3)
        self.form.FuncDCoeff4.setValue(self.jointTaskObject.Coeff4)
        self.form.FuncDstartTime.setValue(self.jointTaskObject.startTimeDriveFunc)
        self.form.FuncDendTime.setValue(self.jointTaskObject.endTimeDriveFunc)

        # Function type e
        self.form.FuncFCoeff0.setValue(self.jointTaskObject.Coeff0)
        self.form.FuncFCoeff1.setValue(self.jointTaskObject.Coeff1)
        self.form.FuncFCoeff2.setValue(self.jointTaskObject.Coeff2)
        self.form.FuncFCoeff3.setValue(self.jointTaskObject.Coeff3)
        self.form.FuncFCoeff4.setValue(self.jointTaskObject.Coeff4)
        self.form.FuncFCoeff5.setValue(self.jointTaskObject.Coeff5)
        self.form.FuncFstartTime.setValue(self.jointTaskObject.startTimeDriveFunc)
        self.form.FuncFendTime.setValue(self.jointTaskObject.endTimeDriveFunc)

        # Function type f
        self.form.FuncFCoeff0.setValue(self.jointTaskObject.Coeff0)
        self.form.FuncFCoeff1.setValue(self.jointTaskObject.Coeff1)
        self.form.FuncFCoeff2.setValue(self.jointTaskObject.Coeff2)
        self.form.FuncFCoeff3.setValue(self.jointTaskObject.Coeff3)
        self.form.FuncFCoeff4.setValue(self.jointTaskObject.Coeff4)
        self.form.FuncFCoeff5.setValue(self.jointTaskObject.Coeff5)
        self.form.FuncFstartTime.setValue(self.jointTaskObject.startTimeDriveFunc)
        self.form.FuncFendTime.setValue(self.jointTaskObject.endTimeDriveFunc)
    #  -------------------------------------------------------------------------
    def withDriver_Changed_Callback(self):
        if self.form.withDriver.isChecked() == False:
            self.jointTaskObject.FunctType = -1
            self.hideAllEquationsF()
        else:
            self.showAllEquationsF()
            if self.form.radioButtonA.isChecked():
                self.jointTaskObject.FunctType = 0
            elif self.form.radioButtonB.isChecked():
                self.jointTaskObject.FunctType = 1
            elif self.form.radioButtonC.isChecked():
                self.jointTaskObject.FunctType = 2
            elif self.form.radioButtonD.isChecked():
                self.jointTaskObject.FunctType = 3
            elif self.form.radioButtonE.isChecked():
                self.jointTaskObject.FunctType = 4
            elif self.form.radioButtonF.isChecked():
                self.jointTaskObject.FunctType = 5
    #  -------------------------------------------------------------------------
    def driveFunc_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-driveFunc_Changed_Callback")

        # Set the current page of the funcCoeff stacked widget
        self.form.funcCoeff.setEnabled(True)
        self.showAllEquationsF()
    #  -------------------------------------------------------------------------
    def jointType_Changed_Callback(self):
        """When we have _Changed the joint movement type"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-jointType_Changed_Callback")

        formJointType = self.form.jointType.currentIndex() - 1
        self.jointTaskObject.JointType = formJointType

        # Set up which page of body definition we must see
        # Pages in the joint dialog
        # 0 - 2Bodies 2Points [rev rev-rev rigid]
        # 1 - 2Bodies 4Points [trans]
        # 2 - 2Bodies 3Points [trans-rev]
        # 3 - 1Body 1Point [driven-rev]
        # 4 - 1Body 2Points [driven-trans]
        # 5 - Body Disc [disc]
        # 6 - expansion
        #   And whether the driven function stuff is available
        #   And populate the body combo boxes in the applicable page
        if formJointType == DT.JOINT_TYPE_DICTIONARY["Revolute"] or \
                formJointType == DT.JOINT_TYPE_DICTIONARY["Revolute-Revolute"] or \
                formJointType == DT.JOINT_TYPE_DICTIONARY["Rigid"]:
            initComboInFormF(self.form.body1_2B2P, self.bodyLabels, -1)
            initComboInFormF(self.form.body2_2B2P, self.bodyLabels, -1)
            self.form.definitionWidget.setCurrentIndex(0)
            self.hideAllEquationsF()
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Translation"]:
            initComboInFormF(self.form.body1_2B4P, self.bodyLabels, -1)
            initComboInFormF(self.form.body2_2B4P, self.bodyLabels, -1)
            self.form.definitionWidget.setCurrentIndex(1)
            self.hideAllEquationsF()
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Translation-Revolute"]:
            initComboInFormF(self.form.body1_2B3P, self.bodyLabels, -1)
            initComboInFormF(self.form.body2_2B3P, self.bodyLabels, -1)
            self.form.definitionWidget.setCurrentIndex(2)
            self.hideAllEquationsF()
        elif formJointType == DT.JOINT_TYPE_DICTIONARY["Disc"]:
            initComboInFormF(self.form.bodyDisc, self.bodyLabels, -1)
            self.form.definitionWidget.setCurrentIndex(5)
            self.hideAllEquationsF()
    #  -------------------------------------------------------------------------
    def body_1B1P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body_1B1P_Changed_Callback")

        bodyIndex = self.form.body_1B1P.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.body_1B1P, ['Undefined'])
            initComboInFormF(self.form.point_1B1P, ['Undefined'], -1)
            updateToolTipF(self.form.point_1B1P, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body_1B1P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.point_1B1P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.point_1B1P, self.pointLabelListFirstBody)
    #  -------------------------------------------------------------------------
    def point_1B1P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-point_1B1P_Changed_Callback")

        pointIndex = self.form.point_1B1P.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.point_1B1P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.point_1B1P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def body_1B2P_Changed_Callback(self):
        """In the case of unit vectors, the joint point is the tail of the vector
        and the other point, the head"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body_1B2P_Changed_Callback")

        bodyIndex = self.form.body_1B2P.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.body_1B2P, ['Undefined'])
            initComboInFormF(self.form.vectorHead_1B2P, ['Undefined'], -1)
            updateToolTipF(self.form.vectorHead_1B2P, ['Undefined'])
            initComboInFormF(self.form.vectorTail_1B2P, ['Undefined'], -1)
            updateToolTipF(self.form.vectorTail_1B2P, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body_1B2P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vectorHead_1B2P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vectorHead_1B2P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vectorTail_1B2P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vectorTail_1B2P, self.pointLabelListFirstBody)
    #  ------------------------------------------------------------------------
    def vectorTail_1B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vectorHead_1B2P_Changed_Callback")

        pointIndex = self.form.vectorTail_1B2P.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.vectorTail_1B2P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vectorTail_1B2P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def vectorHead_1B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vectorTail_1B2P_Changed_Callback")

        pointIndex = self.form.vectorHead_1B2P.currentIndex() - 1
        self.jointTaskObject.point_I_j_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_j_Name = ""
            self.jointTaskObject.point_I_j_Label = ""
            updateToolTipF(self.form.vectorHead_1B2P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_j_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_j_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vectorHead_1B2P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def body1_2B2P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is Changed"""
        if Debug:
            DT.Mess("TaskPanelDapjointClass-body1_2B2P_Changed_Callback")

        bodyIndex = self.form.body1_2B2P.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.body1_2B2P, ['Undefined'])
            initComboInFormF(self.form.point1_2B2P, ['Undefined'], -1)
            updateToolTipF(self.form.point1_2B2P, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body1_2B2P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.point1_2B2P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.point1_2B2P, self.pointLabelListFirstBody)
    # --------------------------------------------------------------------------
    def body2_2B2P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is Changed"""
        if Debug:
            DT.Mess("TaskPanelDapjointClass-body2_2B2P_Changed_Callback")

        bodyIndex = self.form.body2_2B2P.currentIndex() - 1
        self.jointTaskObject.body_J_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_J_Name = ""
            self.jointTaskObject.body_J_Label = ""
            updateToolTipF(self.form.body2_2B2P, ['Undefined'])
            initComboInFormF(self.form.point2_2B2P, ['Undefined'], -1)
            updateToolTipF(self.form.point2_2B2P, ['Undefined'])
        else:
            self.pointNameListSecondBody, self.pointLabelListSecondBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_J_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_J_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body2_2B2P, self.pointLabelListSecondBody)
            initComboInFormF(self.form.point2_2B2P, self.pointLabelListSecondBody, -1)
            updateToolTipF(self.form.point2_2B2P, self.pointLabelListSecondBody)
    #  -------------------------------------------------------------------------
    def point1_2B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-point1_2B2P_Changed_Callback")

        pointIndex = self.form.point1_2B2P.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.point1_2B2P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.point1_2B2P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def point2_2B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-point2_2B2P_Changed_Callback")

        pointIndex = self.form.point2_2B2P.currentIndex() - 1
        self.jointTaskObject.point_J_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_J_i_Name = ""
            self.jointTaskObject.point_J_i_Label = ""
            updateToolTipF(self.form.point2_2B2P, ['Undefined'])
        else:
            self.jointTaskObject.point_J_i_Name = self.pointNameListSecondBody[pointIndex]
            self.jointTaskObject.point_J_i_Label = self.pointLabelListSecondBody[pointIndex]
            updateToolTipF(self.form.point2_2B2P, [self.pointLabelListSecondBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def body1_2B3P_Changed_Callback(self):
        """The Body2 combo box in the Translation joint page current index has _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body1_2B3P_Changed_Callback")

        bodyIndex = self.form.body1_2B3P.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.body1_2B3P, ['Undefined'])
            initComboInFormF(self.form.vectorHead_2B3P, ['Undefined'], -1)
            updateToolTipF(self.form.vectorHead_2B3P, ['Undefined'])
            initComboInFormF(self.form.vectorTail_2B3P, ['Undefined'], -1)
            updateToolTipF(self.form.vectorTail_2B3P, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body1_2B3P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vectorHead_2B3P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vectorHead_2B3P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vectorTail_2B3P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vectorTail_2B3P, self.pointLabelListFirstBody)
    #  -------------------------------------------------------------------------
    def body2_2B3P_Changed_Callback(self):
        """The Body II Revolute combo box current index has _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body2_2B3P_Changed_Callback")

        bodyIndex = self.form.body2_2B3P.currentIndex() - 1
        self.jointTaskObject.body_J_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_J_Name = ""
            self.jointTaskObject.body_J_Label = ""
            updateToolTipF(self.form.body2_2B3P, ['Undefined'])
            initComboInFormF(self.form.point_2B3P, ['Undefined'], -1)
            updateToolTipF(self.form.point_2B3P, ['Undefined'])
        else:
            self.pointNameListSecondBody, self.pointLabelListSecondBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_J_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_J_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body2_2B3P, self.pointLabelListSecondBody)
            initComboInFormF(self.form.point_2B3P, self.pointLabelListSecondBody, -1)
            updateToolTipF(self.form.point_2B3P, self.pointLabelListSecondBody)
    #  -------------------------------------------------------------------------
    def vectorTail_2B3P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vectorHead_2B3P_Changed_Callback")

        pointIndex = self.form.vectorTail_2B3P.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.vectorTail_2B3P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vectorTail_2B3P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def vectorHead_2B3P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vectorTail_2B3P_Changed_Callback")

        pointIndex = self.form.vectorHead_2B3P.currentIndex() - 1
        self.jointTaskObject.point_I_j_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_j_Name = ""
            self.jointTaskObject.point_I_j_Label = ""
            updateToolTipF(self.form.vectorHead_2B3P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_j_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_j_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vectorHead_2B3P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def point_2B3P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-point_2B3P_Changed_Callback")

        pointIndex = self.form.point_2B3P.currentIndex() - 1
        self.jointTaskObject.point_J_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_J_i_Name = ""
            self.jointTaskObject.point_J_i_Label = ""
            updateToolTipF(self.form.point_2B3P, ['Undefined'])
        else:
            self.jointTaskObject.point_J_i_Name = self.pointNameListSecondBody[pointIndex]
            self.jointTaskObject.point_J_i_Label = self.pointLabelListSecondBody[pointIndex]
            updateToolTipF(self.form.point_2B3P, [self.pointLabelListSecondBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def body1_2B4P_Changed_Callback(self):
        """The Body1 Translation combo box in the Translation joint page current index has _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body1_2B4P_Changed_Callback")

        bodyIndex = self.form.body1_2B4P.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.body1_2B4P, ['Undefined'])
            initComboInFormF(self.form.vector1Head_2B4P, ['Undefined'], -1)
            updateToolTipF(self.form.vector1Head_2B4P, ['Undefined'])
            initComboInFormF(self.form.vector1Tail_2B4P, ['Undefined'], -1)
            updateToolTipF(self.form.vector1Tail_2B4P, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body1_2B4P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vector1Head_2B4P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vector1Head_2B4P, self.pointLabelListFirstBody)
            initComboInFormF(self.form.vector1Tail_2B4P, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.vector1Tail_2B4P, self.pointLabelListFirstBody)
    #  -------------------------------------------------------------------------
    def body2_2B4P_Changed_Callback(self):
        """The Body2 combo box in the Translation joint page current index has _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-body2_2B4P_Changed_Callback")

        bodyIndex = self.form.body2_2B4P.currentIndex() - 1
        self.jointTaskObject.body_J_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_J_Name = ""
            self.jointTaskObject.body_J_Label = ""
            updateToolTipF(self.form.body2_2B4P, ['Undefined'])
            initComboInFormF(self.form.vector2Head_2B4P, ['Undefined'], -1)
            updateToolTipF(self.form.vector2Head_2B4P, ['Undefined'])
            initComboInFormF(self.form.vector2Tail_2B4P, ['Undefined'], -1)
            updateToolTipF(self.form.vector2Tail_2B4P, ['Undefined'])
        else:
            self.pointNameListSecondBody, self.pointLabelListSecondBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_J_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_J_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.body2_2B4P, self.pointLabelListSecondBody)
            initComboInFormF(self.form.vector2Head_2B4P, self.pointLabelListSecondBody, -1)
            updateToolTipF(self.form.vector2Head_2B4P, self.pointLabelListSecondBody)
            initComboInFormF(self.form.vector2Tail_2B4P, self.pointLabelListSecondBody, -1)
            updateToolTipF(self.form.vector2Tail_2B4P, self.pointLabelListSecondBody)
    #  -------------------------------------------------------------------------
    def vector1Tail_2B4P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vector1Head_2B4P_Changed_Callback")

        pointIndex = self.form.vector1Tail_2B4P.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.vector1Tail_2B4P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vector1Tail_2B4P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def vector1Head_2B4P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vector1Tail_2B4P_Changed_Callback")

        pointIndex = self.form.vector1Head_2B4P.currentIndex() - 1
        self.jointTaskObject.point_I_j_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_j_Name = ""
            self.jointTaskObject.point_I_j_Label = ""
            updateToolTipF(self.form.vector1Head_2B4P, ['Undefined'])
        else:
            self.jointTaskObject.point_I_j_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_j_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.vector1Head_2B4P, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def vector2Tail_2B4P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vector2Head_2B4P_Changed_Callback")

        pointIndex = self.form.vector2Tail_2B4P.currentIndex() - 1
        self.jointTaskObject.point_J_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_J_i_Name = ""
            self.jointTaskObject.point_J_i_Label = ""
            updateToolTipF(self.form.vector2Tail_2B4P, ['Undefined'])
        else:
            self.jointTaskObject.point_J_i_Name = self.pointNameListSecondBody[pointIndex]
            self.jointTaskObject.point_J_i_Label = self.pointLabelListSecondBody[pointIndex]
            updateToolTipF(self.form.vector2Tail_2B4P, [self.pointLabelListSecondBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def vector2Head_2B4P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-vector2Tail_2B4P_Changed_Callback")

        pointIndex = self.form.vector2Head_2B4P.currentIndex() - 1
        self.jointTaskObject.point_J_j_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_J_j_Name = ""
            self.jointTaskObject.point_J_j_Label = ""
            updateToolTipF(self.form.vector2Head_2B4P, ['Undefined'])
        else:
            self.jointTaskObject.point_J_j_Name = self.pointNameListSecondBody[pointIndex]
            self.jointTaskObject.point_J_j_Label = self.pointLabelListSecondBody[pointIndex]
            updateToolTipF(self.form.vector2Head_2B4P, [self.pointLabelListSecondBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def bodyDisc_Changed_Callback(self):
        """The Body Disc combo box in the Disc joint page current index has _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-bodyDisc_Changed_Callback")

        bodyIndex = self.form.bodyDisc.currentIndex() - 1
        self.jointTaskObject.body_I_Index = bodyIndex
        if bodyIndex == -1:
            self.jointTaskObject.body_I_Name = ""
            self.jointTaskObject.body_I_Label = ""
            updateToolTipF(self.form.bodyDisc, ['Undefined'])
            initComboInFormF(self.form.pointDiscCentre, ['Undefined'], -1)
            updateToolTipF(self.form.pointDiscCentre, ['Undefined'])
            initComboInFormF(self.form.pointDiscRim, ['Undefined'], -1)
            updateToolTipF(self.form.pointDiscRim, ['Undefined'])
        else:
            self.pointNameListFirstBody, self.pointLabelListFirstBody = \
                DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
            self.jointTaskObject.body_I_Name = self.bodyNames[bodyIndex]
            self.jointTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
            updateToolTipF(self.form.bodyDisc, self.pointLabelListFirstBody)
            initComboInFormF(self.form.pointDiscCentre, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.pointDiscCentre, self.pointLabelListFirstBody)
            initComboInFormF(self.form.pointDiscRim, self.pointLabelListFirstBody, -1)
            updateToolTipF(self.form.pointDiscRim, self.pointLabelListFirstBody)
    #  -------------------------------------------------------------------------
    def pointDiscCentre_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-pointDiscCentre_Changed_Callback")

        pointIndex = self.form.pointDiscCentre.currentIndex() - 1
        self.jointTaskObject.point_I_i_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_i_Name = ""
            self.jointTaskObject.point_I_i_Label = ""
            updateToolTipF(self.form.pointDiscCentre, ['Undefined'])
        else:
            self.jointTaskObject.point_I_i_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_i_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.pointDiscCentre, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def pointDiscRim_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-pointDiscRim_Changed_Callback")

        pointIndex = self.form.pointDiscRim.currentIndex() - 1
        self.jointTaskObject.point_I_j_Index = pointIndex
        if pointIndex == -1:
            self.jointTaskObject.point_I_j_Name = ""
            self.jointTaskObject.point_I_j_Label = ""
            updateToolTipF(self.form.pointDiscRim, ['Undefined'])
        else:
            self.jointTaskObject.point_I_j_Name = self.pointNameListFirstBody[pointIndex]
            self.jointTaskObject.point_I_j_Label = self.pointLabelListFirstBody[pointIndex]
            updateToolTipF(self.form.pointDiscRim, [self.pointLabelListFirstBody[pointIndex]])
    #  -------------------------------------------------------------------------
    def radioA_Changed_Callback(self):
        if self.form.radioButtonA.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(0)
            self.jointTaskObject.FunctType = 0
    #  -------------------------------------------------------------------------
    def radioB_Changed_Callback(self):
        if self.form.radioButtonB.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(1)
            self.jointTaskObject.FunctType = 1
    #  -------------------------------------------------------------------------
    def radioC_Changed_Callback(self):
        if self.form.radioButtonC.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(2)
            self.jointTaskObject.FunctType = 2
    #  -------------------------------------------------------------------------
    def radioD_Changed_Callback(self):
        if self.form.radioButtonD.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(3)
            self.jointTaskObject.FunctType = 3
    #  -------------------------------------------------------------------------
    def radioE_Changed_Callback(self):
        if self.form.radioButtonE.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(4)
            self.jointTaskObject.FunctType = 4
    #  -------------------------------------------------------------------------
    def radioF_Changed_Callback(self):
        if self.form.radioButtonF.isChecked():
            self.showAllEquationsF()
            self.form.funcCoeff.setCurrentIndex(5)
            self.jointTaskObject.FunctType = 5
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapJointClass-getStandardButtons")
        return int(QtGui.QDialogButtonBox.Ok)
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("TaskPanelDapJointClass-__setstate__")
# ==============================================================================
'''elif formJointType == DT.JOINT_TYPE_DICTIONARY["Driven-Revolute"]:
    self.jointTaskObject.point_I_j_Name = ""
    self.jointTaskObject.point_I_j_Label = ""
    self.jointTaskObject.point_I_j_Index = -1
    self.jointTaskObject.point_J_i_Name = ""
    self.jointTaskObject.point_J_i_Label = ""
    self.jointTaskObject.point_J_i_Index = -1
    self.jointTaskObject.point_J_j_Name = ""
    self.jointTaskObject.point_J_j_Label = ""
    self.jointTaskObject.point_J_j_Index = -1
elif formJointType == DT.JOINT_TYPE_DICTIONARY["Driven-Translation"]:
    self.jointTaskObject.point_J_i_Name = ""
    self.jointTaskObject.point_J_i_Label = ""
    self.jointTaskObject.point_J_i_Index = -1
    self.jointTaskObject.point_J_j_Name = ""
    self.jointTaskObject.point_J_j_Label = ""
    self.jointTaskObject.point_J_j_Index = -1'''
'''elif formJointType == DT.JOINT_TYPE_DICTIONARY["Driven-Revolute"]:
    initComboInFormF(self.form.body_1B1P, self.bodyLabels, -1)
    self.form.definitionWidget.setCurrentIndex(3)
    self.showAllEquationsF()
    self.radioA_Changed_Callback()
    self.radioB_Changed_Callback()
    self.radioC_Changed_Callback()
    self.radioD_Changed_Callback()
    self.radioE_Changed_Callback()
    self.radioF_Changed_Callback()
elif formJointType == DT.JOINT_TYPE_DICTIONARY["Driven-Translation"]:
    initComboInFormF(self.form.body_1B2P, self.bodyLabels, -1)
    self.form.definitionWidget.setCurrentIndex(4)
    self.showAllEquationsF()
    self.radioA_Changed_Callback()
    self.radioB_Changed_Callback()
    self.radioC_Changed_Callback()
    self.radioD_Changed_Callback()
    self.radioE_Changed_Callback()
    self.radioF_Changed_Callback()'''
