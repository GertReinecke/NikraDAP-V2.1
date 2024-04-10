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
# *   See the GNU Library General Public License for more details.               *
# *                                                                              *
# *   You should have received a copy of the GNU Library General Public          *
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
from PySide import QtCore

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapContainer(name="DapContainer"):
    """Create Dap Container FreeCAD group object"""
    if Debug:
        DT.Mess("makeDapContainer")
    containerObject = CAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
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
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon2n.png"),
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
        if CAD.ActiveDocument is None:
            CAD.Console.PrintErrorMessage("No active document is loaded into FreeCAD for NikraDAP to use")
            return False

        for obj in CAD.ActiveDocument.Objects:
            if hasattr(obj, "Type") and obj.Type == 'Assembly':
                return True

        CAD.Console.PrintErrorMessage("No Assembly4 Model found for NikraDAP to use")
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
            CAD.Console.PrintError("Failed to create DAP container")
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-__setstate__")
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
        DT.addObjectProperty(containerObject, "movementPlaneNormal", CAD.Vector(0, 0, 1),            "App::PropertyVector", "", "Defines the movement plane in this NikraDAP run")
        DT.addObjectProperty(containerObject, "gravityVector",       CAD.Vector(0.0, -9810.0, 0.0),  "App::PropertyVector", "", "Gravitational acceleration Components")
        DT.addObjectProperty(containerObject, "gravityValid",        False,                          "App::PropertyBool",   "", "Flag to verify that the gravity Vector is applicable")

        DT.setActiveContainer(containerObject)
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("DapContainerClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("DapContainerClass-__setstate__")
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
        return path.join(DT.getDapModulePath(), "icons", "Icon2n.png")
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-__getstate__")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            DT.Mess("TaskPanelDapContainerClass-__setstate__")
# =============================================================================
