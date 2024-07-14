import FreeCAD
import FreeCADGui

import numpy as np
from os import path
from math import degrees
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT

Debug = False
# =============================================================================
class CommandDapAnimationClass:
    """The Dap Animation command definition"""
    if Debug:
        DT.Mess("CommandDapAnimationClass-CLASS")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            DT.Mess("CommandDapAnimationClass-GetResourcesC")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "Icons", "Icon8n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("DapAnimationAlias", "Do Animation"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("DapAnimationAlias", "Animates the motion of the bodies."),
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if there are already some results stored in the solver object
        i.e. Determine if the animate command/icon must be active or greyed out"""
        if Debug:
            DT.Mess("CommandDapAnimationClass-IsActive")
        activeContainer = DT.getActiveContainerObject()
        # Return the valid results flag in the solver container
        for groupMember in activeContainer.Group:
            if "DapSolver" in groupMember.Name:
                self.solverObj = groupMember
                return groupMember.DapResultsValid
        # Return False if we didn't find a DapSolver object at all
        return False
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Animation command is run"""
        if Debug:
            DT.Mess("CommandDapAnimationClass-Activated")
        # Get the identity of the DAP document (which is the active document on entry)
        self.dapDocument = FreeCAD.ActiveDocument

        # Set an existing "Animation" document active or create it if it does not exist yet
        if "Animation" in FreeCAD.listDocuments():
            FreeCAD.setActiveDocument("Animation")
        else:
            FreeCAD.newDocument("Animation")
        self.animationDocument = FreeCAD.ActiveDocument

        # Add the ground object to the animation view (and forget about it)
        groundObj = self.dapDocument.findObjects(Name="DapBody")[0]
        animObj = self.animationDocument.addObject("Part::FeaturePython", ("Ani_DapBody"))
        animObj.Shape = groundObj.Shape
        ViewProviderDapAnimateClass(animObj.ViewObject)

        # Generate the list of bodies to be animated and
        # create an object for each, with their shapes, in the animationDocument
        animationIndex = 0
        for bodyName in self.solverObj.BodyNames:
            bodyObj = self.dapDocument.findObjects(Name="^"+bodyName+"$")[0]
            
            animObj = self.animationDocument.addObject("Part::FeaturePython", ("Ani_"+bodyName))
            # Add the shape to the newly created object
            animObj.Shape = bodyObj.Shape
            # Instantiate the class to handle the Gui stuff
            ViewProviderDapAnimateClass(animObj.ViewObject)

        # Request the animation window zoom to be set to fit the entire system
        FreeCADGui.SendMsgToActiveView("ViewFit")

        # Edit the parameters by calling the task dialog
        taskd = TaskPanelDapAnimateClass(
            self.solverObj,
            self.dapDocument,
            self.animationDocument,
        )
        FreeCADGui.Control.showDialog(taskd)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("CommandDapAnimClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("CommandDapAnimClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
class ViewProviderDapAnimateClass:
    """ A view provider for the DapAnimate container object """
    # -------------------------------------------------------------------------------------------------
    def __init__(self, animateViewObject):
        if Debug:
            DT.Mess("ViewProviderDapAnimateClass-__init__")
        animateViewObject.Proxy = self
    # -------------------------------------------------------------------------------------------------
    def doubleClicked(self, animateViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            DT.Mess("ViewProviderDapAnimateClass-doubleClicked")
        if not DT.getActiveAnalysis() == self.animateObject:
            if FreeCADGui.activeWorkbench().name() != 'DapWorkbench':
                FreeCADGui.activateWorkbench("DapWorkbench")
            DT.setActiveAnalysis(self.animateObject)
            return True
        return True
    # -------------------------------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the animation icon (Icon8n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapAnimateClass-getIcon")
        return path.join(DT.getDapModulePath(), "Gui", "Resources", "Icons", "Icon8n.png")
    # -------------------------------------------------------------------------------------------------
    def attach(self, animateViewObject):
        if Debug:
            DT.Mess("ViewProviderDapAnimateClass-attach")
        self.animateObject = animateViewObject.Object
        animateViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    # -------------------------------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    # -------------------------------------------------------------------------------------------------
    def dumps(self):
        return None
    # -------------------------------------------------------------------------------------------------
    def loads(self, state):
        if state:
            self.Type = state
        return None
# =============================================================================
class TaskPanelDapAnimateClass:
    """Taskpanel for Running an animation"""
    if Debug:
        DT.Mess("TaskPanelDapAnimateClass-CLASS")
    #  -------------------------------------------------------------------------
    def __init__(self, solverObj, dapDocument, animationDocument):
        """Run on first instantiation of a TaskPanelDapAnimate class"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-__init__")

        # Transfer the called parameters to the instance variables
        self.solverObj = solverObj
        self.dapDocument = dapDocument
        self.animationDocument = animationDocument

        # Here we get the list of objects from the animation document
        self.animationBodyObjects = FreeCAD.ActiveDocument.Objects

        # Set play back period to mid-range
        self.playBackPeriod = 100  # msec

        # Load the Dap Animate ui form
        uiPath = path.join(path.dirname(__file__), "TaskPanelDapAnimate.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiPath)

        # Define callback functions when changes are made in the dialog
        self.form.horizontalSlider.valueChanged.connect(self.moveObjects_Callback)
        self.form.startButton.clicked.connect(self.playStart_Callback)
        self.form.stopButton.clicked.connect(self.stopStop_Callback)
        self.form.playSpeed.valueChanged.connect(self.changePlaySpeed_Callback)

        # Fetch the animation object for all the bodies and place in a list
        self.animationBodyObj = []
        for animationBodyName in self.solverObj.BodyNames:
            self.animationBodyObj.append(self.animationDocument.findObjects(Name="^Ani_"+animationBodyName+"$")[0])

        # Load the calculated values of positions/angles from the results file
        self.Positions = np.loadtxt(path.join(self.solverObj.Directory, "DapAnimation.csv"))
        self.nTimeSteps = len(self.Positions.T[0])

        # Positions matrix is:
        # timeValue : body1X body1Y body1phi : body2X body2Y body2phi : ...
        # next time tick

        # Shift all the values relative to the starting position of each body
        startTick = self.Positions[0, :]
        self.startX = []
        self.startY = []
        self.startPhi = []
        for animationIndex in range(len(self.solverObj.BodyNames)):
            self.startX.append(startTick[animationIndex * 3 + 1])
            self.startY.append(startTick[animationIndex * 3 + 2])
            self.startPhi.append(startTick[animationIndex * 3 + 3])
        for tick in range(self.nTimeSteps):
            thisTick = self.Positions[tick, :]
            for animationIndex in range(len(self.solverObj.BodyNames)):
                thisTick[animationIndex * 3 + 1] -= self.startX[animationIndex]
                thisTick[animationIndex * 3 + 2] -= self.startY[animationIndex]
                thisTick[animationIndex * 3 + 3] -= self.startPhi[animationIndex]
            self.Positions[tick, :] = thisTick

        # Set up the timer parameters
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.playBackPeriod)
        self.timer.timeout.connect(self.onTimerTimeout_Callback)  # callback function after each tick

        # Set up the values displayed on the dialog
        self.form.horizontalSlider.setRange(0, self.nTimeSteps - 1)
        self.form.timeStepLabel.setText("0.000s of {0:5.3f}s".format(self.solverObj.TimeLength))
    #  -------------------------------------------------------------------------
    def reject(self):
        """Run when we press the Close button
        Closes document and sets the active document
        back to the solver document"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-reject")

        FreeCADGui.Control.closeDialog()
        FreeCAD.closeDocument(self.animationDocument.Name)
        FreeCAD.setActiveDocument(self.dapDocument.Name)
    #  -------------------------------------------------------------------------
    def playStart_Callback(self):
        """Start the Qt timer when the play button is pressed"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-playStart_Callback")

        self.timer.start()
    #  -------------------------------------------------------------------------
    def stopStop_Callback(self):
        """Stop the Qt timer when the stop button is pressed"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-stopStop_Callback")

        self.timer.stop()
    #  -------------------------------------------------------------------------
    def onTimerTimeout_Callback(self):
        """Increment the tick position in the player, looping, if requested"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-onTimerTimeout_Callback")

        tickPosition = self.form.horizontalSlider.value()
        tickPosition += 1
        if tickPosition >= self.nTimeSteps:
            if self.form.loopCheckBox.isChecked():
                tickPosition: int = 0
            else:
                self.timer.stop()

        # Update the slider in the dialog
        self.form.horizontalSlider.setValue(tickPosition)
    #  -------------------------------------------------------------------------
    def changePlaySpeed_Callback(self, newSpeed):
        """Alter the playback period by a factor of 1/newSpeed"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-changePlaySpeed_Callback")

        self.timer.setInterval(self.playBackPeriod * (1.0 / newSpeed))
    #  -------------------------------------------------------------------------
    def moveObjects_Callback(self, tick):
        """Move all the bodies to their pose at this clock tick"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-moveObjects_Callback")

        self.form.timeStepLabel.setText(
            "{0:5.3f}s of {1:5.3f}s".format(
                tick * self.solverObj.DeltaTime,
                self.solverObj.TimeLength
            )
        )

        thisTick = self.Positions[tick, :]
        for animationIndex in range(len(self.solverObj.BodyNames)):
            X = thisTick[animationIndex*3 + 1]
            Y = thisTick[animationIndex*3 + 2]
            Phi = thisTick[animationIndex*3 + 3]
            self.animationBodyObj[animationIndex].Placement = FreeCAD.Placement(FreeCAD.Vector(X, Y, 0.0),
                                                                            FreeCAD.Rotation(FreeCAD.Vector(0.0, 0.0, 1.0),degrees(Phi)),
                                                                            FreeCAD.Vector(self.startX[animationIndex],
                                                                                       self.startY[animationIndex],
                                                                                       0.0))
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            DT.Mess("TaskPanelDapAnimateClass-getStandardButtons")
        return int(QtGui.QDialogButtonBox.Close)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapAnimationClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapAnimationClass-loads")
        if state:
            self.Type = state
        return None
# =============================================================================
