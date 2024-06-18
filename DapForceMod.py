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

from os import path
#  from math import sin, cos, tan, asin, acos, atan, tanh, degrees, pi
#  import Part
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapForce(name="DapForce"):
    """Create an empty Dap Force Object"""
    if Debug:
        DT.Mess("makeDapForce")
    # Instantiate a DapForce object
    forceObject = CAD.ActiveDocument.addObject("Part::FeaturePython", name)
    DapForceClass(forceObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapForceClass(forceObject.ViewObject)
    return forceObject
# =============================================================================
class CommandDapForceClass:
    """The Dap Force command definition"""
    if Debug:
        DT.Mess("CommandDapForceClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapForceClass-GetResources")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon6n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("DapForceAlias", "Add Force"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("DapForceAlias", "Creates and defines a force for the DAP analysis"),
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out
        Only activate it when there is at least one body defined"""
        if Debug:
            DT.Mess("CommandDapForceClass-IsActive(query)")
        return len(DT.getDictionary("DapBody")) > 0
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Force Selection command is run"""
        if Debug:
            DT.Mess("CommandDapForceClass-Activated")
        # This is where we create a new empty Dap Force object
        DT.getActiveContainerObject().addObject(makeDapForce())
        # Switch on the Dap Force Task Dialog
        CADGui.ActiveDocument.setEdit(CAD.ActiveDocument.ActiveObject.Name)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class DapForceClass:
    if Debug:
        DT.Mess("DapForceClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, forceObject):
        """Initialise an instantiation of a new DAP force object"""
        if Debug:
            DT.Mess("DapForceClass-__init__")
        forceObject.Proxy = self
        self.addPropertiesToObject(forceObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, forceObject):
        if Debug:
            DT.Mess("DapForceClass-onDocumentRestored")
        self.addPropertiesToObject(forceObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, forceObject):
        """Initialise all the properties of the force object"""
        if Debug:
            DT.Mess("DapForceClass-addPropertiesToObject")

        DT.addObjectProperty(forceObject, "actuatorType",         0,            "App::PropertyInteger", "",           "Type of the actuator/force")
        DT.addObjectProperty(forceObject, "newForce",             True,         "App::PropertyBool",    "",           "Flag to show if this is a new or old force definition")

        DT.addObjectProperty(forceObject, "body_I_Name",          "",           "App::PropertyString",  "Bodies",     "Name of the head body")
        DT.addObjectProperty(forceObject, "body_I_Label",         "",           "App::PropertyString",  "Bodies",     "Label of the head body")
        DT.addObjectProperty(forceObject, "body_I_Index",         0,            "App::PropertyInteger", "Bodies",     "Index of the head body in the NumPy array")

        DT.addObjectProperty(forceObject, "point_i_Name",         "",           "App::PropertyString",  "Points",     "Name of the first point of the force")
        DT.addObjectProperty(forceObject, "point_i_Label",        "",           "App::PropertyString",  "Points",     "Label of the first point of the force")
        DT.addObjectProperty(forceObject, "point_i_Index",        0,            "App::PropertyInteger", "Points",     "Index of the first point of the force in the NumPy array")

        DT.addObjectProperty(forceObject, "body_J_Name",          "",           "App::PropertyString",  "Bodies",     "Name of the tail body")
        DT.addObjectProperty(forceObject, "body_J_Label",         "",           "App::PropertyString",  "Bodies",     "Label of the tail body")
        DT.addObjectProperty(forceObject, "body_J_Index",         0,            "App::PropertyInteger", "Bodies",     "Index of the tail body in the NumPy array")

        DT.addObjectProperty(forceObject, "point_j_Name",         "",           "App::PropertyString",  "Points",     "Name of the second point of the force")
        DT.addObjectProperty(forceObject, "point_j_Label",        "",           "App::PropertyString",  "Points",     "Label of the second point of the force")
        DT.addObjectProperty(forceObject, "point_j_Index",        0,            "App::PropertyInteger", "Points",     "Index of the second point of the force in the NumPy array")

        DT.addObjectProperty(forceObject, "Stiffness",            0.0,          "App::PropertyFloat",   "Values",     "Spring Stiffness")
        DT.addObjectProperty(forceObject, "LengthAngle0",         0.0,          "App::PropertyFloat",   "Values",     "Un-deformed Length/Angle")
        DT.addObjectProperty(forceObject, "DampingCoeff",         0.0,          "App::PropertyFloat",   "Values",     "Damping coefficient")
        DT.addObjectProperty(forceObject, "constLocalForce",      CAD.Vector(), "App::PropertyVector",  "Values",     "Constant force in local frame")
        DT.addObjectProperty(forceObject, "constWorldForce",      CAD.Vector(), "App::PropertyVector",  "Values",     "Constant force in x-y frame")
        DT.addObjectProperty(forceObject, "constTorque",          0.0,          "App::PropertyFloat",   "Values",     "Constant torque in x-y frame")
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("DapForceClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("DapForceClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class ViewProviderDapForceClass:
    if Debug:
        DT.Mess("ViewProviderDapForceClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, forceViewObject):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-__init__")
        forceViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, forceViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapForceClass-doubleClicked")
        Document = CADGui.getDocument(forceViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(forceViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the force icon (Icon6n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapForceClass-getIcon")
        return path.join(DT.getDapModulePath(), "icons", "Icon6n.png")
    #  -------------------------------------------------------------------------
    def attach(self, forceViewObject):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-attach")
        self.forceObject = forceViewObject.Object
        forceViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, forceViewObject):
        """Return an empty list of modes when requested"""
        if Debug:
            DT.Mess("ViewProviderDapForceClass-getDisplayModes")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-getDefaultDisplayMode")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-setDisplayMode")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, forceViewObject, mode):
        """Edit the parameters by calling the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapForceClass-setEdit")
        CADGui.Control.showDialog(TaskPanelDapForceClass(self.forceObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, forceViewObject, mode):
        """Terminate the editing via the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapForceClass-unsetEdit")
        CADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("ViewProviderDapForceClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class TaskPanelDapForceClass:
    """Taskpanel for adding a NikraDAP Force"""
    if Debug:
        DT.Mess("TaskPanelDapForceClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, forceTaskObject):
        """Run on first instantiation of a TaskPanelDapForce class"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-__init__")

        self.forceTaskObject = forceTaskObject
        forceTaskObject.Proxy = self

        # Define variables for later use
        # (class variables should preferably be used first in the __init__ block)
        self.pointNameListOneOne = []
        self.pointNameListOneTwo = []
        self.pointNameListTwoOne = []
        self.pointNameListTwoTwo = []
        self.pointLabelListOneOne = []
        self.pointLabelListOneTwo = []
        self.pointLabelListTwoOne = []
        self.pointLabelListTwoTwo = []

        # Load up the task panel layout definition
        uiPath = path.join(path.dirname(__file__), "TaskPanelDapForces.ui")
        self.form = CADGui.PySideUic.loadUi(uiPath)

        # Populate the body object dictionary with body {names : objects}
        self.bodyObjDict = DT.getDictionary("DapBody")

        # Populate the bodyLabels and bodyNames lists
        self.bodyLabels = []
        self.bodyNames = []
        self.bodyObjects = []
        for bodyName in self.bodyObjDict:
            bodyObj = self.bodyObjDict[bodyName]
            self.bodyNames.append(bodyObj.Name)
            self.bodyLabels.append(bodyObj.Name)
            self.bodyObjects.append(self.bodyObjDict[bodyObj.Name])

        # Populate the form from the forceTaskObject
        self.form.linSpringLength.setValue(self.forceTaskObject.LengthAngle0)
        self.form.linSpringStiffness.setValue(self.forceTaskObject.Stiffness)
        self.form.rotSpringAngle.setValue(self.forceTaskObject.LengthAngle0)
        self.form.rotSpringStiffness.setValue(self.forceTaskObject.Stiffness)
        self.form.linSpringDamp.setValue(self.forceTaskObject.DampingCoeff)
        self.form.linSpringDampLength.setValue(self.forceTaskObject.LengthAngle0)
        self.form.linSpringDampStiffness.setValue(self.forceTaskObject.Stiffness)
        self.form.rotSpringDamp.setValue(self.forceTaskObject.DampingCoeff)
        self.form.rotSpringDampAngle.setValue(self.forceTaskObject.LengthAngle0)
        self.form.rotSpringDampStiffness.setValue(self.forceTaskObject.Stiffness)

        # Connect changes in the body choices to the respective Callback functions
        self.form.actuatorCombo.currentIndexChanged.connect(self.actuator_Changed_Callback)
        self.form.body_1B1P.currentIndexChanged.connect(self.body_1B1P_Changed_Callback)
        self.form.body_1B2P.currentIndexChanged.connect(self.body_1B2P_Changed_Callback)
        self.form.body1_2B1P.currentIndexChanged.connect(self.body1_2B1P_Changed_Callback)
        self.form.body2_2B1P.currentIndexChanged.connect(self.body2_2B1P_Changed_Callback)
        self.form.body1_2B2P.currentIndexChanged.connect(self.body1_2B2P_Changed_Callback)
        self.form.body2_2B2P.currentIndexChanged.connect(self.body2_2B2P_Changed_Callback)

        # Connect changes in the point choices to the respective Callback functions
        self.form.point_1B1P.currentIndexChanged.connect(self.point_1B1P_Changed_Callback)
        self.form.point1_1B2P.currentIndexChanged.connect(self.point1_1B2P_Changed_Callback)
        self.form.point2_1B2P.currentIndexChanged.connect(self.point2_1B2P_Changed_Callback)
        self.form.point_2B1P.currentIndexChanged.connect(self.point_2B1P_Changed_Callback)
        self.form.point1_2B2P.currentIndexChanged.connect(self.point1_2B2P_Changed_Callback)
        self.form.point2_2B2P.currentIndexChanged.connect(self.point2_2B2P_Changed_Callback)

        # Set up the body/actuator combo boxes
        self.form.actuatorCombo.clear()
        self.form.actuatorCombo.addItems(DT.FORCE_TYPE)
        self.form.actuatorCombo.setCurrentIndex(forceTaskObject.actuatorType)

        self.form.body_1B1P.clear()
        self.form.body_1B1P.addItems(self.bodyLabels)
        self.form.body_1B1P.setCurrentIndex(forceTaskObject.body_I_Index)

        self.form.body_1B2P.clear()
        self.form.body_1B2P.addItems(self.bodyLabels)
        self.form.body_1B2P.setCurrentIndex(forceTaskObject.body_I_Index)

        self.form.body1_2B1P.clear()
        self.form.body1_2B1P.addItems(self.bodyLabels)
        self.form.body1_2B1P.setCurrentIndex(forceTaskObject.body_I_Index)

        self.form.body2_2B1P.clear()
        self.form.body2_2B1P.addItems(self.bodyLabels)
        self.form.body2_2B1P.setCurrentIndex(forceTaskObject.body_J_Index)

        self.form.body1_2B2P.clear()
        self.form.body1_2B2P.addItems(self.bodyLabels)
        self.form.body1_2B2P.setCurrentIndex(forceTaskObject.body_I_Index)

        self.form.body2_2B2P.clear()
        self.form.body2_2B2P.addItems(self.bodyLabels)
        self.form.body1_2B2P.setCurrentIndex(forceTaskObject.body_J_Index)

        # Copy the state of the gravity vector to the form
        containerObject = DT.getActiveContainerObject()
        if containerObject.gravityVector.x != 0.0 and containerObject.gravityValid is True:
            self.form.gravityX.setChecked(True)
        else:
            self.form.gravityX.setChecked(False)
        if containerObject.gravityVector.y != 0.0 and containerObject.gravityValid is True:
            self.form.gravityY.setChecked(True)
        else:
            self.form.gravityY.setChecked(False)
        if containerObject.gravityVector.z != 0.0 and containerObject.gravityValid is True:
            self.form.gravityZ.setChecked(True)
        else:
            self.form.gravityZ.setChecked(False)

        # Connect changes in the gravity direction to the respective Callback function
        self.form.gravityX.toggled.connect(self.gravityX_Changed_Callback)
        self.form.gravityY.toggled.connect(self.gravityY_Changed_Callback)
        self.form.gravityZ.toggled.connect(self.gravityZ_Changed_Callback)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button - we have finished all the hard work"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-accept")

        # Transfer spring values to the form
        # Actuator type
        # 0-Gravity
        # 1=Linear Spring 2-Rotational Spring
        # 3-Linear Spring Damper 4-Rotational Spring Damper 5-Unilateral Spring Damper
        # 6-Constant Force Local to Body 7-Constant Global Force 8-Constant Torque about a Point
        # 9-Contact Friction 10-Motor 11-Motor with Air Friction
        if self.forceTaskObject.actuatorType == 0:
            pass
        elif self.forceTaskObject.actuatorType == 1:
            self.forceTaskObject.LengthAngle0 = self.form.linSpringLength.value()
            self.forceTaskObject.Stiffness = self.form.linSpringStiffness.value()
        elif self.forceTaskObject.actuatorType == 2:
            self.forceTaskObject.LengthAngle0 = self.form.rotSpringAngle.value()
            self.forceTaskObject.Stiffness = self.form.rotSpringStiffness.value()
        elif self.forceTaskObject.actuatorType == 3:
            self.forceTaskObject.DampingCoeff = self.form.linSpringDamp.value()
            self.forceTaskObject.LengthAngle0 = self.form.linSpringDampLength.value()
            self.forceTaskObject.Stiffness = self.form.linSpringDampStiffness.value()
        elif self.forceTaskObject.actuatorType == 4:
            self.forceTaskObject.DampingCoeff = self.form.rotSpringDamp.value()
            self.forceTaskObject.LengthAngle0 = self.form.rotSpringDampAngle.value()
            self.forceTaskObject.Stiffness = self.form.rotSpringDampStiffness.value()
        elif self.forceTaskObject.actuatorType == 7:
            self.forceTaskObject.constWorldForce = self.form.globalForceMag.value() * CAD.Vector(self.form.globalForceX.value(), self.form.globalForceY.value(), self.form.globalForceZ.value())
        else:
            CAD.Console.PrintError("Code for the selected force is still in development")

        # Switch off the Task panel
        GuiDocument = CADGui.getDocument(self.forceTaskObject.Document)
        GuiDocument.resetEdit()

        # Validate and Clean up Gravity entries if this entry is Gravity
        if self.form.actuatorCombo.currentIndex() == 0:
            containerObject = DT.getActiveContainerObject()
            # Remove the other gravity entry if another one already altered the vector
            if (self.forceTaskObject.newForce is True) and (containerObject.gravityValid is True):
                # We now have two gravity forces
                # Find the first gravity force and remove it
                # the new one will always be after it in the list
                self.forceTaskObject.newForce = False
                forceList = CAD.getDocument(self.forceTaskObject.Document.Name).findObjects(Name="DapForce")
                for forceObj in forceList:
                    if forceObj.actuatorType == 0 and len(forceList) > 1:
                        CAD.ActiveDocument.removeObject(forceObj.Name)
                        break
            # Remove this gravity entry if it is null
            if containerObject.gravityVector == CAD.Vector(0.0, 0.0, 0.0):
                forceList = CAD.getDocument(self.forceTaskObject.Document.Name).findObjects(Name="DapForce")
                if len(forceList) > 0:
                    for forceObj in forceList:
                        if forceObj.actuatorType == 0:
                            CAD.ActiveDocument.removeObject(forceObj.Name)
                            containerObject.gravityValid = False
                            break
            else:
                # All is OK, so validate the gravityVector in the container
                self.forceTaskObject.newForce = False
                containerObject.gravityValid = True
    #  -------------------------------------------------------------------------
    def updateToolTipF(self, ComboName, LabelList):
        bodyString = ""
        for point in LabelList:
            bodyString = bodyString + DT.parsePoint(point) + "\n========\n"
        ComboName.setToolTip(str(bodyString[:-10]))
    #  -------------------------------------------------------------------------
    def body_1B1P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is Changed"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body_1B1P_Changed_Callback")

        # Update the body in the forceTaskObject
        bodyIndex = self.form.body_1B1P.currentIndex()
        self.forceTaskObject.body_I_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_I_Index = bodyIndex

        # Load the new set of point labels, which are in the specified body, into the form
        self.pointNameListOneOne, self.pointLabelListOneOne = DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
        self.updateToolTipF(self.form.body_1B1P, self.pointLabelListOneOne)

        self.updateToolTipF(self.form.point_1B1P, [self.pointLabelListOneOne[0]])
        self.form.point_1B1P.clear()
        self.form.point_1B1P.addItems(self.pointLabelListOneOne)
        self.form.point_1B1P.setCurrentIndex(0)
    #  -------------------------------------------------------------------------
    def body_1B2P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body_1B2P_Changed_Callback")

        # Update the body in the forceTaskObject
        bodyIndex = self.form.body_1B2P.currentIndex()
        self.forceTaskObject.body_I_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_I_Index = bodyIndex

        # Load the new set of point labels, which are in the specified body, into the form
        self.pointNameListOneOne, self.pointLabelListOneOne = DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
        self.updateToolTipF(self.form.body_1B2P, self.pointLabelListOneOne)

        self.updateToolTipF(self.form.point1_1B2P, [self.pointLabelListOneOne[0]])
        self.form.point1_1B2P.clear()
        self.form.point1_1B2P.addItems(self.pointLabelListOneOne)
        self.form.point1_1B2P.setCurrentIndex(0)

        self.pointNameListOneTwo = self.pointNameListOneOne[:]
        self.pointLabelListOneTwo = self.pointLabelListOneOne[:]

        self.updateToolTipF(self.form.point2_1B2P, [self.pointLabelListOneTwo[0]])
        self.form.point2_1B2P.clear()
        self.form.point2_1B2P.addItems(self.pointLabelListOneTwo)
        self.form.point2_1B2P.setCurrentIndex(0)
    #  -------------------------------------------------------------------------
    def body1_2B1P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body1_2B1P_Changed_Callback")

        # Update the body in the forceTaskObject
        bodyIndex = self.form.body1_2B1P.currentIndex()
        self.forceTaskObject.body_I_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_I_Index = bodyIndex

        # Load the new set of point labels, which are in the specified body, into the form
        bodyIndex = self.form.body1_2B1P.currentIndex()
        self.pointNameListOneOne, self.pointLabelListOneOne = DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
        self.updateToolTipF(self.form.body1_2B1P, self.pointLabelListOneOne)

        self.updateToolTipF(self.form.point_2B1P, [self.pointLabelListOneOne[0]])
        self.form.point_2B1P.clear()
        self.form.point_2B1P.addItems(self.pointLabelListOneOne)
        self.form.point_2B1P.setCurrentIndex(0)
    #  -------------------------------------------------------------------------
    def body2_2B1P_Changed_Callback(self):
        """Only update the body in forceTaskObject - there are no points associated with it"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body2_2B1P_Changed_Callback")

        # Update the body tooltip
        self.form.body2_2B1P.setToolTip("")

        # Update the forceTaskObject
        bodyIndex = self.form.body2_2B1P.currentIndex()
        self.forceTaskObject.body_J_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_J_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_J_Index = bodyIndex
    #  -------------------------------------------------------------------------
    def body1_2B2P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is changed"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body1_2B2P_Changed_Callback")

        # Update the body in the forceTaskObject
        bodyIndex = self.form.body1_2B2P.currentIndex()
        self.forceTaskObject.body_I_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_I_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_I_Index = bodyIndex

        # Load the new set of point labels, which are contained in the specified body, into the form
        self.pointNameListOneOne, self.pointLabelListOneOne = DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
        self.updateToolTipF(self.form.body1_2B2P, self.pointLabelListOneOne)

        self.updateToolTipF(self.form.point1_2B2P, [self.pointLabelListOneOne[0]])
        self.form.point1_2B2P.clear()
        self.form.point1_2B2P.addItems(self.pointLabelListOneOne)
        self.form.point1_2B2P.setCurrentIndex(0)
    #  -------------------------------------------------------------------------
    def body2_2B2P_Changed_Callback(self):
        """Populate form with a new list of point labels when a body is _Changed"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-body2_2B2P_Changed_Callback")

        # Update the body in the forceTaskObject
        bodyIndex = self.form.body2_2B2P.currentIndex()
        self.forceTaskObject.body_J_Name = self.bodyNames[bodyIndex]
        self.forceTaskObject.body_J_Label = self.bodyLabels[bodyIndex]
        self.forceTaskObject.body_J_Index = bodyIndex

        # Load the new set of point labels, which are in the specified body, into the form
        self.pointNameListTwoTwo, self.pointLabelListTwoTwo = DT.getPointsFromBodyName(self.bodyNames[bodyIndex], self.bodyObjDict)
        self.updateToolTipF(self.form.body2_2B2P, self.pointLabelListTwoTwo)

        self.updateToolTipF(self.form.point2_2B2P, [self.pointLabelListTwoTwo[0]])
        self.form.point2_2B2P.clear()
        self.form.point2_2B2P.addItems(self.pointLabelListTwoTwo)
        self.form.point2_2B2P.setCurrentIndex(0)
    #  -------------------------------------------------------------------------
    def point_1B1P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point_1B1P_Changed_Callback")

        pointIndex = self.form.point_1B1P.currentIndex()

        if pointIndex != -1:
            # Update the tooltip
            self.form.point_1B1P.setToolTip(str(DT.parsePoint(self.pointLabelListOneOne[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_i_Name = self.pointNameListOneOne[pointIndex]
            self.forceTaskObject.point_i_Label = self.pointLabelListOneOne[pointIndex]
            self.forceTaskObject.point_i_Index = pointIndex
    #  -------------------------------------------------------------------------
    def point1_1B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point1_1B2P_Changed_Callback")

        pointIndex = self.form.point1_1B2P.currentIndex()
        if pointIndex != -1:
            # Update the tooltip
            self.form.point1_1B2P.setToolTip(str(DT.parsePoint(self.pointLabelListOneOne[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_i_Name = self.pointNameListOneOne[pointIndex]
            self.forceTaskObject.point_i_Label = self.pointLabelListOneOne[pointIndex]
            self.forceTaskObject.point_i_Index = pointIndex
    #  -------------------------------------------------------------------------
    def point2_1B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point2_1B2P_Changed_Callback")

        pointIndex = self.form.point2_1B2P.currentIndex()
        if pointIndex != -1:
            # Update the tooltip
            self.form.point2_1B2P.setToolTip(str(DT.parsePoint(self.pointLabelListOneTwo[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_i_Name = self.pointNameListOneTwo[pointIndex]
            self.forceTaskObject.point_i_Label = self.pointLabelListOneTwo[pointIndex]
            self.forceTaskObject.point_i_Index = pointIndex
    #  -------------------------------------------------------------------------
    def point_2B1P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point_2B1P_Changed_Callback")

        pointIndex = self.form.point_2B1P.currentIndex()
        if pointIndex != -1:
            # Update the tooltip
            self.form.point_2B1P.setToolTip(str(DT.parsePoint(self.pointLabelListOneOne[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_i_Name = self.pointNameListOneOne[pointIndex]
            self.forceTaskObject.point_i_Label = self.pointLabelListOneOne[pointIndex]
            self.forceTaskObject.point_i_Index = pointIndex
    #  -------------------------------------------------------------------------
    def point1_2B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point1_2B2P_Changed_Callback")

        pointIndex = self.form.point1_2B2P.currentIndex()
        if pointIndex != -1:
            # Update the tooltip
            self.form.point1_2B2P.setToolTip(str(DT.parsePoint(self.pointLabelListOneOne[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_i_Name = self.pointNameListOneOne[pointIndex]
            self.forceTaskObject.point_i_Label = self.pointLabelListOneOne[pointIndex]
            self.forceTaskObject.point_i_Index = pointIndex
    #  -------------------------------------------------------------------------
    def point2_2B2P_Changed_Callback(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-point2_2B2P_Changed_Callback")

        pointIndex = self.form.point2_2B2P.currentIndex()
        if pointIndex != -1:
            # Update the tooltip
            self.form.point2_2B2P.setToolTip(str(DT.parsePoint(self.pointLabelListTwoTwo[pointIndex])))

            # Update the point in the forceTaskObject
            self.forceTaskObject.point_j_Name = self.pointNameListTwoTwo[pointIndex]
            self.forceTaskObject.point_j_Label = self.pointLabelListTwoTwo[pointIndex]
            self.forceTaskObject.point_j_Index = pointIndex
    #  -------------------------------------------------------------------------
    def gravityX_Changed_Callback(self):
        """The X gravity check box has gone from either checked to unchecked
        or unchecked to checked"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-gravityX_Changed_Callback")
        containerObject = DT.getActiveContainerObject()
        if self.form.gravityX.isChecked():
            # X has been checked, uncheck Y and Z
            self.form.gravityY.setChecked(False)
            self.form.gravityZ.setChecked(False)
            # Set the appropriate gravity vector
            containerObject.gravityVector = CAD.Vector(-9810.0, 0.0, 0.0)
        else:
            containerObject.gravityVector.x = 0.0
        if Debug:
            DT.Mess("Gravity Vector")
            DT.Mess(containerObject.gravityVector)
    #  -------------------------------------------------------------------------
    def gravityY_Changed_Callback(self):
        """The Y gravity check box has gone from either checked to unchecked
        or unchecked to checked"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-gravityY_Changed_Callback")
        containerObject = DT.getActiveContainerObject()
        if self.form.gravityY.isChecked():
            # Y has been checked, uncheck X and Z
            self.form.gravityX.setChecked(False)
            self.form.gravityZ.setChecked(False)
            # Set the appropriate gravity vector
            containerObject.gravityVector = CAD.Vector(0.0, -9810.0, 0.0)
        else:
            containerObject.gravityVector.y = 0.0
        if Debug:
            DT.Mess("Gravity Vector")
            DT.Mess(containerObject.gravityVector)
    #  -------------------------------------------------------------------------
    def gravityZ_Changed_Callback(self):
        """The Z gravity check box has gone from either checked to unchecked
        or unchecked to checked"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-gravityZ_Changed_Callback")
        containerObject = DT.getActiveContainerObject()
        if self.form.gravityZ.isChecked():
            # Z has been checked, uncheck X and Y
            self.form.gravityX.setChecked(False)
            self.form.gravityY.setChecked(False)
            # Set the appropriate gravity vector
            containerObject.gravityVector = CAD.Vector(0.0, 0.0, -9810.0)
        else:
            containerObject.gravityVector.z = 0.0
        if Debug:
            DT.Mess("Gravity Vector")
            DT.Mess(containerObject.gravityVector)
    #  -------------------------------------------------------------------------
    def actuator_Changed_Callback(self):
        """Selects which of the forceData and bodyPointData pages are active,
        and shown/hidden based on the actuator type"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-actuator_Changed_Callback")

        # Actuator type
        # 0-Gravity
        # 1=Linear Spring 2-Rotational Spring
        # 3-Linear Spring Damper 4-Rotational Spring Damper 5-Unilateral Spring Damper
        # 6-Constant Force Local to Body 7-Constant Global Force 8-Constant Torque about a Point
        # 9-Contact Friction 10-Motor 11-Motor with Air Friction

        # Body vs Point page numbers in the Forces form:
        OneBodyTwoPoints = 0
        TwoBodiesOnePoint = 1
        TwoBodiesTwoPoints = 2
        OneBodyOnePoint = 3

        # Set up the combos in the form, depending on the actuator type
        actuatorType = self.form.actuatorCombo.currentIndex()
        self.forceTaskObject.actuatorType = actuatorType

        # The Gravity actuator option - forceData page number is 11
        if actuatorType == 0:
            # Gravity has no bodies and points
            # And it is on page 12 of 12 (forceData page 11)
            self.form.forceData.setCurrentIndex(11)
            self.form.bodyPointData.setHidden(True)
            return

        # After gravity, the forceData page numbers are all one less than actuatorType
        self.form.forceData.setCurrentIndex(actuatorType - 1)

        # Two bodies, two points
        if (actuatorType == 1) or (actuatorType == 3) or (actuatorType == 5):
            self.form.bodyPointData.setCurrentIndex(TwoBodiesTwoPoints)
            self.form.bodyPointData.setHidden(False)

        # One body, two points
        elif actuatorType == 2 or actuatorType == 4 or actuatorType == 6:
            self.form.bodyPointData.setCurrentIndex(OneBodyTwoPoints)
            self.form.bodyPointData.setHidden(False)

        # No bodies or points
        elif actuatorType == 7:
            self.form.bodyPointData.setHidden(True)

        # One body, one point
        elif actuatorType == 8:
            self.form.bodyPointData.setCurrentIndex(OneBodyOnePoint)
            self.form.bodyPointData.setHidden(False)

        # No bodies or points
        elif actuatorType == 9 or actuatorType == 10 or actuatorType == 11:
            self.form.bodyPointData.setHidden(True)
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapForceClass-getStandardButtons")
        return int(QtGui.QDialogButtonBox.Ok)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapForceClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
    def archiveUnusedForceCode(self):
        """
            #     vol1 = 0
            #     vol2 = 0
            #     if forceObject.body_I_Name != "Origin":
            #         vol1 = Document.getObjectsByName(forceObject.body_I_Name)[0].Shape.Volume
            #     if forceObject.body_J_Name != "Origin":
            #         vol2 = Document.getObjectsByName(forceObject.body_J_Name)[0].Shape.Volume
            #     if vol1 + vol2 == 0:
            #         vol1 = 100000
            #     scale = (vol1 + vol2) / 30000

            #     spiral = document.addObject("Part::Spiral", "Spiral")
            #     spiral.Radius = 2 * scale
            #     spiral.Growth = r / 2
            #     spiral.Rotations = 4
            #     spiral.Placement.Base = CAD.Vector(0, 0, 0)

            #     spiralShape = document.getObject("Spiral").Shape
            #     forceObject.Shape = spiralShape

            #     if forceObject.actuatorType == "Rotational Spring":
            #         forceObject.ViewObject.LineColor = 0.0, 0.0, 0.0, 0.0
            #     elif forceObject.actuatorType == "Rotational Spring Damper":
            #         forceObject.ViewObject.LineColor = 0.0, 250.0, 20.0, 0.0

            #     forceObject.Placement.Base = forceIILCS

            #    document.removeObject("Spiral")

            #    springLength = (forceIILCS - forceBLCS).Length
            #    pitch = springLength / 10
            #    radius = springLength / 10
            #    creationAxis = CAD.Vector(0, 0, 1.0)

            #      if springLength > 0:
            #          springDirection = (forceBLCS - forceIILCS).normalize()
            #          angle = degrees(acos(springDirection * creationAxis))
            #          axis = creationAxis.cross(springDirection)
            #          helix = Part.makeHelix(pitch, springLength, radius)
            #         forceObject.Shape = helix
            #         if forceObject.actuatorType == "Spring":
            #             forceObject.ViewObject.LineColor = 0.0, 0.0, 0.0, 0.0
            #         elif forceObject.actuatorType == "Linear Spring Damper":
            #             forceObject.ViewObject.LineColor = 0.0, 250.0, 20.0, 0.0

            #         # First reset the placement in case multiple recomputes are performed
            #         #forceObject.Placement.Base = CAD.Vector(0, 0, 0)
            #         #forceObject.Placement.Rotation = CAD.Rotation(0, 0, 0, 1)
            #         #forceObject.Placement.rotate(CAD.Vector(0, 0, 0), axis, angle)
            #         #forceObject.Placement.translate(forceIILCS)
            #     else:
            #         # An empty shape if the length is zero
            #         forceObject.Shape = Part.Shape()
        """
        return
# =============================================================================
