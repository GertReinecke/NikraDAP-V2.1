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
import math
import Part
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapBody(name="DapBody"):
    """Create an empty Dap Body object"""
    if Debug:
        DT.Mess("makeDapBody")
    bodyObject = CAD.ActiveDocument.addObject("Part::FeaturePython", name)
    # Instantiate a DapBody object
    DapBodyClass(bodyObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapBodyClass(bodyObject.ViewObject)
    return bodyObject
# ==============================================================================
class CommandDapBodyClass:
    """The Dap body command definition"""
    if Debug:
        DT.Mess("CommandDapBodyClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapBodyClass-GetResources")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon3n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("DapBodyAlias", "Add Body"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("DapBodyAlias", "Creates and defines a body for the DAP analysis."), }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out
        Only activate it when there is at least a container defined"""
        if Debug:
            DT.Mess("CommandDapBodyClass-IsActive(query)")
        return DT.getActiveContainerObject() is not None
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Body Selection command is run"""
        if Debug:
            DT.Mess("CommandDapBodyClass-Activated")
        # This is where we create a new empty Dap Body object
        DT.getActiveContainerObject().addObject(makeDapBody())
        # Switch on the Dap Body Task Dialog
        CADGui.ActiveDocument.setEdit(CAD.ActiveDocument.ActiveObject.Name)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("CommandDapBody-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("CommandDapBodyClass-loads")
        if state:
            self.Type = state
        return None
# ==============================================================================
class DapBodyClass:
    if Debug:
        DT.Mess("DapBodyClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, bodyObject):
        """Initialise an instantiation of a new DAP body object"""
        if Debug:
            DT.Mess("DapBodyClass-__init__")
        bodyObject.Proxy = self
        self.addPropertiesToObject(bodyObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, bodyObject):
        if Debug:
            DT.Mess("DapBodyClass-onDocumentRestored")
        self.addPropertiesToObject(bodyObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, bodyObject):
        """Initialise the properties on instantiation of a new body object or on Document Restored
        All the sub-part bodies [including the main body] are included in the point lists as extra points
        All points/bodies are local and relative to world placement above"""
        if Debug:
            DT.Mess("DapBodyClass-addPropertiesToObject")

        DT.addObjectProperty(bodyObject, "ass4SolidsNames",  [],              "App::PropertyStringList", "Body",      "Names of Assembly 4 Solid Parts comprising this body")
        DT.addObjectProperty(bodyObject, "ass4SolidsLabels", [],              "App::PropertyStringList", "Body",      "Labels of Assembly 4 Solid Parts comprising this body")

        DT.addObjectProperty(bodyObject, "Mass",             1.0,             "App::PropertyFloat",      "Body",      "Mass")
        DT.addObjectProperty(bodyObject, "centreOfGravity",  CAD.Vector(),    "App::PropertyVector",     "Body",      "Centre of gravity")
        DT.addObjectProperty(bodyObject, "weightVector",     CAD.Vector(),    "App::PropertyVector",     "Body",      "Weight as a force vector")
        DT.addObjectProperty(bodyObject, "momentInertia",    1.0,             "App::PropertyFloat",      "Body",      "Moment of inertia")

        DT.addObjectProperty(bodyObject, "world",            CAD.Placement(), "App::PropertyPlacement",  "X Y Z Phi", "Body LCS relative to origin")
        DT.addObjectProperty(bodyObject, "worldDot",         CAD.Vector(),    "App::PropertyVector",     "X Y Z Phi", "Time derivative of x y z")
        DT.addObjectProperty(bodyObject, "phiDot",           0.0,             "App::PropertyFloat",      "X Y Z Phi", "Angular velocity of phi")

        DT.addObjectProperty(bodyObject, "pointNames",       [],              "App::PropertyStringList", "Points",    "List of Point names associated with this body")
        DT.addObjectProperty(bodyObject, "pointLabels",      [],              "App::PropertyStringList", "Points",    "List of Point labels associated with this body")
        DT.addObjectProperty(bodyObject, "pointLocals",      [],              "App::PropertyVectorList", "Points",    "Vectors relative to local LCS")
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("DapBodyClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("DapBodyClass-loads")
        if state:
            self.Type = state
        return None
# ==============================================================================
class ViewProviderDapBodyClass:
    """A class which handles all the gui overheads"""
    if Debug:
        DT.Mess("ViewProviderDapBodyClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, bodyViewObject):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-__init__")
        bodyViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, bodyViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-doubleClicked")
        Document = CADGui.getDocument(bodyViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(bodyViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the body icon (Icon3n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-getIcon")
        return path.join(DT.getDapModulePath(), "icons", "Icon3n.png")
    #  -------------------------------------------------------------------------
    def attach(self, bodyViewObject):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-attach")
        self.bodyObject = bodyViewObject.Object
        bodyViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, bodyViewObject):
        """Return an empty list of modes when requested"""
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-getDisplayModes")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-getDefaultDisplayMode")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-setDisplayMode")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, bodyViewObject, mode):
        """Edit the parameters by calling the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-setEdit")
        CADGui.Control.showDialog(TaskPanelDapBodyClass(bodyViewObject.Object))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, bodyViewObject, mode):
        """We have finished with the task dialog so close it"""
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-unsetEdit")
        CADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("ViewProviderDapBodyClass-loads")
        if state:
            self.Type = state
        return None
# ==============================================================================
class TaskPanelDapBodyClass:
    """Task panel for adding and editing DAP Bodies"""
    if Debug:
        DT.Mess("TaskPanelDapBodyClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, bodyTaskObject):
        """Run on first instantiation of a TaskPanelDapBody class
        or when the body is re-built on loading of saved model etc.
        [Called explicitly by FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-__init__")

        # Remember stuff to refer to later
        self.bodyTaskObject = bodyTaskObject
        self.taskDocName = CAD.getDocument(self.bodyTaskObject.Document.Name)
        self.bodyTaskObject.Proxy = self
        
        # Set up the form used to create the dialog box
        ui_path = path.join(path.dirname(__file__), "TaskPanelDapBodies.ui")
        self.form = CADGui.PySideUic.loadUi(ui_path)

        # Signal that we only allow non-moving(ground) body for the first body
        Prefix = '<html><head/><body><p align="center"><span style="font-weight:600;">'
        Suffix = '</span></p></body></html>'
        if bodyTaskObject.Name == "DapBody":
            self.form.movingStationary.setText(Prefix+"Stationary"+Suffix)
            self.form.velocityGroup.setDisabled(True)
        else:
            self.form.movingStationary.setText(Prefix+"Moving"+Suffix)
            self.form.velocityGroup.setEnabled(True)

        # Give the body a nice transparent blue colour
        self.bodyTaskObject.ViewObject.Transparency = 20
        self.bodyTaskObject.ViewObject.ShapeColor = (0.5, 0.5, 1.0, 1.0)
        CADGui.Selection.addObserver(self.bodyTaskObject)

        # --------------------------------------------------------
        # Set up the movement plane normal stuff in the dialog box
        # --------------------------------------------------------
        # Fetch the movementPlaneNormal vector from the container and
        # normalize the LARGEST coordinate to 1
        # (i.e. it is easier to visualise [0, 1, 1] instead of [0, 0.707, 0.707]
        # or [1, 1, 1] instead of [0.577, 0.577, 0.577])
        self.movementPlaneNormal = DT.getActiveContainerObject().movementPlaneNormal
        maxCoordinate = 1
        if self.movementPlaneNormal.Length == 0:
            CAD.Console.PrintError("The plane normal vector is the null vector - this should never occur\n")
        else:
            if abs(self.movementPlaneNormal.x) > abs(self.movementPlaneNormal.y):
                if abs(self.movementPlaneNormal.x) > abs(self.movementPlaneNormal.z):
                    maxCoordinate = abs(self.movementPlaneNormal.x)
                else:
                    maxCoordinate = abs(self.movementPlaneNormal.z)
            else:
                if abs(self.movementPlaneNormal.y) > abs(self.movementPlaneNormal.z):
                    maxCoordinate = abs(self.movementPlaneNormal.y)
                else:
                    maxCoordinate = abs(self.movementPlaneNormal.z)
        self.movementPlaneNormal /= maxCoordinate

        # Tick the checkboxes where the Plane Normal has a non-zero value
        self.form.planeX.setChecked(abs(self.movementPlaneNormal.x) > 1e-6)
        self.form.planeY.setChecked(abs(self.movementPlaneNormal.y) > 1e-6)
        self.form.planeZ.setChecked(abs(self.movementPlaneNormal.z) > 1e-6)

        # Transfer the X/Y/Z plane normal coordinates to the form
        self.form.planeXdeci.setValue(self.movementPlaneNormal.x)
        self.form.planeYdeci.setValue(self.movementPlaneNormal.y)
        self.form.planeZdeci.setValue(self.movementPlaneNormal.z)
        
        # Temporarily disable changing to an alternative movement plane - see note in PlaneNormal_Callback
        # Set the Define Plane tick box as un-ticked
        self.form.definePlaneNormal.setChecked(False)
        self.form.definePlaneNormal.setEnabled(False)
        self.form.definePlaneNormalLabel.setEnabled(False)
        self.form.planeX.setEnabled(False)
        self.form.planeY.setEnabled(False)
        self.form.planeZ.setEnabled(False)
        self.form.planeXdeci.setEnabled(False)
        self.form.planeYdeci.setEnabled(False)
        self.form.planeZdeci.setEnabled(False)

        # Clean things up to reflect what we have changed
        self.PlaneNormal_Callback()
        
        # -----------------------------
        # Set up the assembly 4 objects
        # -----------------------------
        # Get any existing list of ass4Solids in this body
        self.ass4SolidsNames = self.bodyTaskObject.ass4SolidsNames
        self.ass4SolidsLabels = self.bodyTaskObject.ass4SolidsLabels

        # Get the list of ALL possible ass4Solids in the entire assembly
        self.modelAss4SolidsNames, self.modelAss4SolidsLabels, self.modelAss4SolidObjectsList = DT.getAllSolidsLists()
            
        # Set up the model ass4Solids list in the combo selection box
        self.form.partLabel.clear()
        self.form.partLabel.addItems(self.modelAss4SolidsLabels)
        self.form.partLabel.setCurrentIndex(0)
        self.selectedAss4SolidsToFormF()

        # Populate the form with velocities
        self.velocitiesToFormX_Callback()
        self.velocitiesToFormY_Callback()
        self.velocitiesToFormZ_Callback()
        self.angularVelToFormVal_Callback()

        # Set the Radians and m/s radio buttons as the default
        self.form.radians.setChecked(True)
        self.form.mms.setChecked(True)

        # --------------------------------------------------------
        # Set up the callback functions for various things changed
        # --------------------------------------------------------
        self.form.buttonRemovePart.clicked.connect(self.buttonRemovePart_Callback)
        self.form.buttonAddPart.clicked.connect(self.buttonAddPart_Callback)
        self.form.partsList.currentRowChanged.connect(self.partsListRowChanged_Callback)
        self.form.planeX.toggled.connect(self.PlaneNormal_Callback)
        self.form.planeY.toggled.connect(self.PlaneNormal_Callback)
        self.form.planeZ.toggled.connect(self.PlaneNormal_Callback)
        self.form.planeXdeci.valueChanged.connect(self.PlaneNormal_Callback)
        self.form.planeYdeci.valueChanged.connect(self.PlaneNormal_Callback)
        self.form.planeZdeci.valueChanged.connect(self.PlaneNormal_Callback)
        self.form.definePlaneNormal.toggled.connect(self.PlaneNormal_Callback)

        self.form.velocityX.valueChanged.connect(self.velocitiesFromFormX_Callback)
        self.form.velocityY.valueChanged.connect(self.velocitiesFromFormY_Callback)
        self.form.velocityZ.valueChanged.connect(self.velocitiesFromFormZ_Callback)
        self.form.angularVelocity.valueChanged.connect(self.angularVelFromFormVal_Callback)

        self.form.mms.toggled.connect(self.velocitiesToFormX_Callback)
        self.form.mms.toggled.connect(self.velocitiesToFormY_Callback)
        self.form.mms.toggled.connect(self.velocitiesToFormZ_Callback)
        self.form.ms.toggled.connect(self.velocitiesToFormX_Callback)
        self.form.ms.toggled.connect(self.velocitiesToFormY_Callback)
        self.form.ms.toggled.connect(self.velocitiesToFormZ_Callback)
        self.form.degrees.toggled.connect(self.angularVelToFormVal_Callback)
        self.form.radians.toggled.connect(self.angularVelToFormVal_Callback)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button - we have finished all the hard work
           now transfer it into the DAP body object"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-accept")

        # Refuse to 'OK' if no part references have been defined
        if len(self.ass4SolidsLabels) == 0:
            CAD.Console.PrintError("No Parts have been added to this body\n")
            CAD.Console.PrintError("First add at least one Part to this body\n")
            CAD.Console.PrintError("        or alternatively:\n")
            CAD.Console.PrintError("add any part to it, 'OK' the body,\n")
            CAD.Console.PrintError("and then delete it from the DapContainer tree\n\n")
            return

        # Store the velocities into the bodyTaskObject
        self.velocitiesFromFormX_Callback()
        self.velocitiesFromFormY_Callback()
        self.velocitiesFromFormZ_Callback()
        self.angularVelFromFormVal_Callback()

        # Store the normalised plane Normal into the container object
        # If it is still undefined (zero vector) then set plane normal to z
        if self.movementPlaneNormal == CAD.Vector(0, 0, 0):
            self.movementPlaneNormal.z = 1.0
        self.movementPlaneNormal /= self.movementPlaneNormal.Length
        DT.getActiveContainerObject().movementPlaneNormal = self.movementPlaneNormal

        # Run through the sub-parts and add all Shapes into a ShapeList
        ShapeList = []
        for ass4Solids in self.ass4SolidsNames:
            solidObject = self.taskDocName.findObjects(Name="^" + ass4Solids + "$")[0]
            # Put all the referenced shapes into a list
            ShapeList.append(solidObject.Shape)

        # Start off with an empty shape
        self.bodyTaskObject.Shape = Part.Shape()
        # Replace empty shape with a new compound one
        if len(ShapeList) > 0:
            # Make a Part.Compound shape out of all the Referenced shapes in the list
            CompoundShape = Part.makeCompound(ShapeList)
            if CompoundShape is not None:
                # Store this compound shape into the body object
                self.bodyTaskObject.Shape = CompoundShape
            else:
                # Otherwise flag that no object has a shape
                CAD.Console.PrintError("Compound Body has no shape - this should not occur\n")

        # Transfer the names and labels to the bodyTaskObject
        self.bodyTaskObject.ass4SolidsNames = self.ass4SolidsNames
        self.bodyTaskObject.ass4SolidsLabels = self.ass4SolidsLabels

        # Save the information to the point lists
        pointNames = []
        pointLabels = []
        pointLocals = []

        # Get the info for the main (first) Assembly-4 Solid in the DapBody
        mainSolidObject = self.taskDocName.findObjects(Name="^" + self.ass4SolidsNames[0] + "$")[0]

        # Save this world body PLACEMENT in the body object -
        # POA_O is P-lacement from O-rigin to body A LCS in world (O-rigin) coordinates
        POA_O = mainSolidObject.Placement
        self.bodyTaskObject.world = POA_O

        # Process all POINTS belonging to the main Solid (Solid A)
        # VAa_A is the local V-ector from solid A to point 'a' in solid A local coordinates
        for mainPoint in mainSolidObject.Group:
            if hasattr(mainPoint, 'MapMode') and not \
                    ('Wire' in str(mainPoint.Shape)) and not \
                    ('Sketch' in str(mainPoint.Name)):
                pointNames.append(
                    mainSolidObject.Name + "-{" + mainPoint.Name + "}")  # the name of the associated point
                pointLabels.append(
                    mainSolidObject.Label + "-{" + mainPoint.Label + "}")  # the label of the associated point
                VAa_A = CAD.Vector(mainPoint.Placement.Base)
                pointLocals.append(VAa_A)

                if Debug:
                    DT.MessNoLF("Local vector from " + mainSolidObject.Label +
                                " to point " + mainPoint.Label +
                                " in " + mainSolidObject.Label + " coordinates: ")
                    DT.PrintVec(VAa_A)

        # Now convert all other solids (i.e. from 1 onward) and their points into points relative to the solid A LCS
        if len(self.ass4SolidsNames) > 1:
            for assIndex in range(1, len(self.ass4SolidsNames)):
                subAss4SolidsObject = self.taskDocName.findObjects(Name="^" + self.ass4SolidsNames[assIndex] + "$")[0]
                # Find the relationship between the subAss4SolidsPlacement and the mainSolidObject.Placement
                # i.e. from LCS of solid A to the LCS of solid B (in terms of the local coordinates of A)
                pointNames.append(subAss4SolidsObject.Name + "-{" + self.ass4SolidsNames[assIndex] + "}")
                pointLabels.append(subAss4SolidsObject.Label + "-{" + self.ass4SolidsLabels[assIndex] + "}")
                POB_O = subAss4SolidsObject.Placement
                VAB_A = POA_O.toMatrix().inverse().multVec(POB_O.Base)
                pointLocals.append(VAB_A)

                if Debug:
                    DT.MessNoLF("Vector from origin to " +
                                subAss4SolidsObject.Label + " in world coordinates: ")
                    DT.PrintVec(POB_O.Base)
                    DT.MessNoLF("Local vector from " + mainSolidObject.Label +
                                " to " + subAss4SolidsObject.Label +
                                " in " + mainSolidObject.Label + " coordinates: ")
                    DT.PrintVec(VAB_A)

                # Now handle all the points which are inside Solid B
                for sub_member in subAss4SolidsObject.Group:
                    if hasattr(sub_member, 'MapMode'):
                        if not ('Wire' in str(sub_member.Shape)):
                            if not ('Sketch' in str(sub_member.Label)):
                                pointNames.append(subAss4SolidsObject.Name + "-{" + sub_member.Name + "}")
                                pointLabels.append(subAss4SolidsObject.Label + "-{" + sub_member.Label + "}")
                                VBb_B = sub_member.Placement.Base  # VBb_B: the local vector from the LCS of solid B to the point b
                                VOb_O = POB_O.toMatrix().multVec(
                                    VBb_B)  # VOb_O: the vector from the origin to the point b in solid B
                                VAb_A = POA_O.toMatrix().inverse().multVec(
                                    VOb_O)  # VAb_A: the local vector from solid A LCS to the point b in solid B
                                pointLocals.append(VAb_A)

                                if Debug:
                                    DT.Mess(" ")
                                    DT.MessNoLF("Vector from origin to " + subAss4SolidsObject.Label +
                                                " in world coordinates: ")
                                    DT.PrintVec(POB_O.Base)
                                    DT.MessNoLF("Relationship between the " + subAss4SolidsObject.Label +
                                                " Vector and the " + mainSolidObject.Label +
                                                " Vector in " + mainSolidObject.Label + " coordinates: ")
                                    DT.PrintVec(VAB_A)
                                    DT.MessNoLF("Local vector from " + subAss4SolidsObject.Label +
                                                " to the point " + sub_member.Label + ": ")
                                    DT.PrintVec(VBb_B)
                                    DT.MessNoLF("Vector from the origin to the point " + sub_member.Label +
                                                " in body " + subAss4SolidsObject.Label + ": ")
                                    DT.PrintVec(VOb_O)
                                    DT.MessNoLF("Local vector from " + mainSolidObject.Label +
                                                " to the point " + sub_member.Label +
                                                " in body " + subAss4SolidsObject.Label + ": ")
                                    DT.PrintVec(VAb_A)
        if Debug:
            DT.Mess("Names: ")
            DT.Mess(pointNames)
            DT.Mess("Labels: ")
            DT.Mess(pointLabels)
            DT.Mess("Locals: ")
            for vec in range(len(pointLocals)):
                DT.MessNoLF(pointLabels[vec])
                DT.PrintVec(pointLocals[vec])

        # Condense all the duplicate points into one
        # And save them in the bodyTaskObject
        DT.condensePoints(pointNames, pointLabels, pointLocals)
        self.bodyTaskObject.pointNames = pointNames
        self.bodyTaskObject.pointLabels = pointLabels
        self.bodyTaskObject.pointLocals = pointLocals

        # Recompute document to update view provider based on the shapes
        self.bodyTaskObject.recompute()

        # Switch off the Task panel
        GuiDocument = CADGui.getDocument(self.bodyTaskObject.Document)
        GuiDocument.resetEdit()
    #  -------------------------------------------------------------------------
    def selectedAss4SolidsToFormF(self):
        """The ass4Solids list is the list of all the parts which make up this body.
        Rebuild the ass4Solids list in the task panel dialog form from our copy of it"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-selectedAss4SolidsToFormF")
        self.form.partsList.clear()
        for subBody in self.ass4SolidsLabels:
            self.form.partsList.addItem(subBody)
    #  -------------------------------------------------------------------------
    def velocitiesToFormX_Callback(self):
        """Rebuild the velocities in the form when we have changed the X component"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesToFormF")
        # If we have checked m/s units then convert to meters per second
        if self.form.ms.isChecked():
            self.form.velocityX.setValue(self.bodyTaskObject.worldDot.x / 1000.0)
        else:
            self.form.velocityX.setValue(self.bodyTaskObject.worldDot.x)
    #  -------------------------------------------------------------------------
    def velocitiesToFormY_Callback(self):
        """Rebuild the velocities in the form when we have changed the Y component"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesToFormF")
        # If we have checked m/s units then convert to meters per second
        if self.form.ms.isChecked():
            self.form.velocityY.setValue(self.bodyTaskObject.worldDot.y / 1000.0)
        else:
            self.form.velocityY.setValue(self.bodyTaskObject.worldDot.y)
    #  -------------------------------------------------------------------------
    def velocitiesToFormZ_Callback(self):
        """Rebuild the velocities in the form when we have changed the Z component"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesToFormF")
        # If we have checked m/s units then convert to meters per second
        if self.form.ms.isChecked():
            self.form.velocityZ.setValue(self.bodyTaskObject.worldDot.z / 1000.0)
        else:
            self.form.velocityZ.setValue(self.bodyTaskObject.worldDot.z)
    #  -------------------------------------------------------------------------
    def angularVelToFormVal_Callback(self):
        """Rebuild the velocities in the form when we have changed the angular velocity"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesToFormF")
        # If we have checked degrees units then convert to deg/s from rad/s
        if self.form.degrees.isChecked():
            self.form.angularVelocity.setValue(self.bodyTaskObject.phiDot * 180.0 / math.pi)
        else:
            self.form.angularVelocity.setValue(self.bodyTaskObject.phiDot)
    #  -------------------------------------------------------------------------
    def velocitiesFromFormX_Callback(self):
        """Rebuild when we have changed something"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesFromFormF")
        if self.bodyTaskObject.Name == "DapBody":
            self.bodyTaskObject.worldDot.x = 0.0
            return
        # If we have checked m/s units then convert from meters per second
        if self.form.ms.isChecked():
            self.bodyTaskObject.worldDot.x = self.form.velocityX.value() * 1000.0
        else:
            self.bodyTaskObject.worldDot.x = self.form.velocityX.value()
    #  -------------------------------------------------------------------------
    def velocitiesFromFormY_Callback(self):
        """Rebuild when we have changed something"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesFromFormF")
        if self.bodyTaskObject.Name == "DapBody":
            self.bodyTaskObject.worldDot.y = 0.0
            return
        # If we have checked m/s units then convert from meters per second
        if self.form.ms.isChecked():
            self.bodyTaskObject.worldDot.y = self.form.velocityY.value() * 1000.0
        else:
            self.bodyTaskObject.worldDot.y = self.form.velocityY.value()
    #  -------------------------------------------------------------------------
    def velocitiesFromFormZ_Callback(self):
        """Rebuild when we have changed something"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesFromFormF")
        if self.bodyTaskObject.Name == "DapBody":
            self.bodyTaskObject.worldDot.z = 0.0
            return

        # If we have checked m/s units then convert from meters per second
        if self.form.ms.isChecked():
            self.bodyTaskObject.worldDot.z = self.form.velocityZ.value() * 1000.0
        else:
            self.bodyTaskObject.worldDot.z = self.form.velocityZ.value()
    #  -------------------------------------------------------------------------
    def angularVelFromFormVal_Callback(self):
        """Rebuild when we have changed something"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-velocitiesFromFormF")
        if self.bodyTaskObject.Name == "DapBody":
            self.bodyTaskObject.phiDot = 0.0
            return

        # If we have checked degrees units then convert to rad/s from deg/s
        if self.form.degrees.isChecked():
            self.bodyTaskObject.phiDot = self.form.angularVelocity.value() * math.pi / 180.0
        else:
            self.bodyTaskObject.phiDot = self.form.angularVelocity.value()
    #  -------------------------------------------------------------------------
    def PlaneNormal_Callback(self):
        """Rebuild when we have changed something to do with the plane normal
        The plane normal transforms are built in, but might still need debugging
        It is therefore temporarily commented out to avoid complaints
        from users at this stage"""
        if Debug:
            DT.Mess("PlaneNormal_Callback")

        if not self.form.definePlaneNormal.isChecked():
            # Hide the movementPlaneNormal tick boxes if the 'define' tickbox is unchecked
            # self.form.planeX.setEnabled(False)
            # self.form.planeY.setEnabled(False)
            # self.form.planeZ.setEnabled(False)
            # self.form.planeXdeci.setEnabled(False)
            # self.form.planeYdeci.setEnabled(False)
            # self.form.planeZdeci.setEnabled(False)
            self.form.planeGroup.setHidden(True)

            self.taskDocName.recompute()
            return

        # Show the tick boxes
        self.form.planeX.setEnabled(True)
        self.form.planeY.setEnabled(True)
        self.form.planeZ.setEnabled(True)
        self.form.planeXdeci.setEnabled(True)
        self.form.planeYdeci.setEnabled(True)
        self.form.planeZdeci.setEnabled(True)

        # All the following paraphanalia is to handle various methods of defining the plane vector
        if self.form.planeX.isChecked():
            self.movementPlaneNormal.x = self.form.planeXdeci.value()
            if self.movementPlaneNormal.x == 0:
                self.movementPlaneNormal.x = 1.0
                self.form.planeXdeci.setValue(1.0)
        else:
            self.movementPlaneNormal.x = 0.0
            self.form.planeXdeci.setValue(0.0)

        if self.form.planeY.isChecked():
            self.movementPlaneNormal.y = self.form.planeYdeci.value()
            if self.movementPlaneNormal.y == 0:
                self.movementPlaneNormal.y = 1.0
                self.form.planeYdeci.setValue(1.0)
        else:
            self.movementPlaneNormal.y = 0.0
            self.form.planeYdeci.setValue(0.0)

        if self.form.planeZ.isChecked():
            self.movementPlaneNormal.z = self.form.planeZdeci.value()
            if self.movementPlaneNormal.z == 0:
                self.movementPlaneNormal.z = 1.0
                self.form.planeZdeci.setValue(1.0)
        else:
            self.movementPlaneNormal.z = 0.0
            self.form.planeZdeci.setValue(0.0)

        if self.movementPlaneNormal == CAD.Vector(0, 0, 0):
            self.movementPlaneNormal.z = 1.0

        # Make a temporary plane and normal vector in the object view box to show the movement plane
        cylinder = Part.makeCylinder(5, 300, CAD.Vector(0, 0, 0), self.movementPlaneNormal)
        plane = Part.makeCylinder(500, 1, CAD.Vector(0, 0, 0), self.movementPlaneNormal)
        cone = Part.makeCone(10, 0, 20, CAD.Vector(self.movementPlaneNormal).multiply(300), self.movementPlaneNormal)
        planeNormal = Part.makeCompound([cylinder, plane, cone])

        self.bodyTaskObject.Shape = planeNormal
        self.bodyTaskObject.ViewObject.Transparency = 20
        self.bodyTaskObject.ViewObject.ShapeColor = (0.5, 1.0, 0.5, 1.0)

        self.taskDocName.recompute()
    #  -------------------------------------------------------------------------
    def buttonAddPart_Callback(self):
        """Run when we click the add part button"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-buttonAddPart_Callback")

        # Find the object for the part name we have selected
        partIndex = self.form.partLabel.currentIndex()
        addPartObject = self.modelAss4SolidObjectsList[partIndex]
        # Add it to the list of ass4SolidsLabels if it is not already there
        if addPartObject.Name not in self.ass4SolidsNames:
            self.ass4SolidsNames.append(self.modelAss4SolidsNames[partIndex])
            self.ass4SolidsLabels.append(self.modelAss4SolidsLabels[partIndex])

        # Highlight the current item
        CADGui.Selection.clearSelection()
        CADGui.Selection.addSelection(addPartObject)

        # Rebuild the subBody's List in the form
        self.selectedAss4SolidsToFormF()
    #  -------------------------------------------------------------------------
    def buttonRemovePart_Callback(self):
        """Run when we remove a body already added"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-buttonRemovePart_Callback")

        # Remove the current row
        if len(self.ass4SolidsNames) > 0:
            row = self.form.partsList.currentRow()
            self.ass4SolidsNames.pop(row)
            self.ass4SolidsLabels.pop(row)

        # Rebuild the subBodies in the form
        self.selectedAss4SolidsToFormF()
    #  -------------------------------------------------------------------------
    def partsListRowChanged_Callback(self, row):
        """Actively select the part in the requested row,
           to make it visible when viewing parts already in list"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-partsListRowChanged_Callback")

        if len(self.ass4SolidsNames) > 0:
            # Clear the highlight on the previous item selected
            CADGui.Selection.clearSelection()
            # Highlight the current item
            selection_object = self.taskDocName.findObjects(Name="^"+self.ass4SolidsNames[row]+"$")[0]
            CADGui.Selection.addSelection(selection_object)
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-getStandardButtons")
        return int(QtGui.QDialogButtonBox.Ok)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapBodyClass-loads")
        if state:
            self.Type = state
        return None
# ==============================================================================
