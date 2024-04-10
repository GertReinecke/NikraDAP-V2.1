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
import FreeCAD
import FreeCADGui

import os

import DapToolsMod as DT

global Debug
Debug = False
# =============================================================================
# InitGui.py
# 1. Connects the workbench to FreeCAD and FreeCADGui
# 2. Builds the graphical interface between the workbench and FreeCAD
# 3. Couples the graphical interface of FreeCAD with the functions of the workbench
# =============================================================================
class DapWorkbench21C(Workbench):
    """This class encompasses the whole NikraDAP workbench"""
    if Debug:
        FreeCAD.Console.PrintMessage("DapWorkbenchClass-CLASS\n")
    #  -------------------------------------------------------------------------
    def __init__(self):
        """Called on startup of FreeCAD"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-__init__\n")

        import os
        import DapToolsMod as DT

        # Set up the text for the DAP workbench option, the NikraDAP icon, and the tooltip
        self.__class__.Icon = os.path.join(DT.getDapModulePath(), "icons", "Icon1n.png")
        self.__class__.MenuText = "NikraDAP-2.1"
        self.__class__.ToolTip = "Planar multibody dynamics workbench based on Prof. Nikravesh's DAP solver"
    #  -------------------------------------------------------------------------
    def Initialize(self):
        """Called on the first selection of the DapWorkbench
        and couples the main NikraDAP functions to the FreeCAD interface"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-Initialize\n")

        # Define which commands will be called with each command alias
        from DapContainerMod import CommandDapContainerClass
        from DapBodyMod import CommandDapBodyClass
        from DapMaterialMod import CommandDapMaterialClass
        from DapForceMod import CommandDapForceClass
        from DapJointMod import CommandDapJointClass
        from DapSolverMod import CommandDapSolverClass
        from DapAnimationMod import CommandDapAnimationClass

        # Add the command to FreeCAD's list of functions
        FreeCADGui.addCommand("DapContainerAlias", CommandDapContainerClass())
        FreeCADGui.addCommand("DapBodyAlias", CommandDapBodyClass())
        FreeCADGui.addCommand("DapMaterialAlias", CommandDapMaterialClass())
        FreeCADGui.addCommand("DapJointAlias", CommandDapJointClass())
        FreeCADGui.addCommand("DapForceAlias", CommandDapForceClass())
        FreeCADGui.addCommand("DapSolverAlias", CommandDapSolverClass())
        FreeCADGui.addCommand("DapAnimationAlias", CommandDapAnimationClass())

        # Create a toolbar with the DAP commands (icons)
        self.appendToolbar("NikraDAP Commands", self.MakeCommandList())

        # Create a drop-down menu item for the menu bar
        self.appendMenu("NikraDAP-2.1Beta", self.MakeCommandList())
    #  -------------------------------------------------------------------------
    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen
        'recipient'=='view' when mouse is in the VIEW window
        'recipient'=='tree' when mouse is in the TREE window
        We currently do no use either flag"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-ContextMenu\n")

        # Append the DAP commands to the existing context menu
        self.appendContextMenu("NikraDAP Commands", self.MakeCommandList())
    #  -------------------------------------------------------------------------
    def MakeCommandList(self):
        """Define a list of our aliases for all the DAP main functions"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-MakeCommandList\n")

        return [
            "DapContainerAlias",
            "Separator",
            "DapBodyAlias",
            "DapMaterialAlias",
            "DapForceAlias",
            "DapJointAlias",
            "Separator",
            "DapSolverAlias",
            "Separator",
            "DapAnimationAlias"
        ]
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the NikraDAP workbench is run"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-Activated\n")
    #  -------------------------------------------------------------------------
    def Deactivated(self):
        """This function is executed each time the DAP workbench is stopped"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-Deactivated\n")
    #  -------------------------------------------------------------------------
    def GetClassName(self):
        """This function is mandatory if this is a full FreeCAD workbench
        The returned string should be exactly 'Gui::PythonWorkbench'
        This enables FreeCAD to ensure that the stuff in its 'Mod' folder
        is a valid workbench and not just rubbish"""
        if Debug:
            FreeCAD.Console.PrintMessage("DapWorkbenchClass-GetClassName\n")

        return "Gui::PythonWorkbench"
    # --------------------------------------------------------------------------
    def __str__(self):
        return str(self.__dict__)
# =============================================================================
# Run when FreeCAD detects a workbench folder in its 'Mod' folder
# Add the workbench to the list of workbenches and initialize it
# =============================================================================
Gui.addWorkbench(DapWorkbench21C())
