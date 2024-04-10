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
from materialtools import cardutils
from PySide import QtGui, QtCore
from pivy import coin

import DapToolsMod as DT

Debug = False
# =============================================================================
def makeDapMaterial(name="DapMaterial"):
    if Debug:
        CAD.Console.PrintMessage("makeDapMaterial\n")
    materialObject = CAD.ActiveDocument.addObject("Part::FeaturePython", name)
    # Instantiate a DapMaterial object
    DapMaterialClass(materialObject)
    # Instantiate the class to handle the Gui stuff
    ViewProviderDapMaterialClass(materialObject.ViewObject)
    return materialObject
# =============================================================================
class CommandDapMaterialClass:
    """The Dap Material command definition"""
    if Debug:
        CAD.Console.PrintMessage("CommandDapMaterialClass-CLASS\n")
    #  -------------------------------------------------------------------------
    def GetResources(self):
        """Called by FreeCAD when 'CADGui.addCommand' is run in InitGui.py
        Returns a dictionary defining the icon, the menu text and the tooltip"""
        if Debug:
            CAD.Console.PrintMessage("CommandDapMaterialClass-GetResources\n")
        return {
            "Pixmap": path.join(DT.getDapModulePath(), "icons", "Icon5n.png"),
            "MenuText": QtCore.QT_TRANSLATE_NOOP("Dap_Material_alias", "Add Material"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("Dap_Material_alias", "Define the material properties associated with each body part.")
        }
    #  -------------------------------------------------------------------------
    def IsActive(self):
        """Determine if the command/icon must be active or greyed out.
        Only activate it when there is at least one body defined"""
        if Debug:
            CAD.Console.PrintMessage("CommandDapMaterialClass-IsActive(query)\n")
        return (len(DT.getDictionary("DapBody")) > 0) and (DT.getMaterialObject() is None)
    #  -------------------------------------------------------------------------
    def Activated(self):
        """Called when the Material Selection command is run"""
        if Debug:
            CAD.Console.PrintMessage("CommandDapMaterialClass-Activated\n")
        # This is where we create a new empty Dap Material object
        DT.getActiveContainerObject().addObject(makeDapMaterial())
        # Switch on the Dap Material Task Panel
        CADGui.ActiveDocument.setEdit(CAD.ActiveDocument.ActiveObject.Name)
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapBodyClass-__getstate__\n")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapBodyClass-__setstate__\n")
# =============================================================================
class DapMaterialClass:
    """Defines the DAP material class"""
    if Debug:
        CAD.Console.PrintMessage("DapMaterialClass-CLASS\n")
    #  -------------------------------------------------------------------------
    def __init__(self, materialObject):
        """Initialise on instantiation of a new DAP Material object"""
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-__init__\n")
        materialObject.Proxy = self
        self.addPropertiesToObject(materialObject)
    #  -------------------------------------------------------------------------
    def onDocumentRestored(self, materialObject):
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-onDocumentRestored\n")
        self.addPropertiesToObject(materialObject)
    #  -------------------------------------------------------------------------
    def addPropertiesToObject(self, materialObject):
        """Called by __init__ and onDocumentRestored functions"""
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-addPropertiesToObject\n")

        DT.addObjectProperty(materialObject, "solidsNameList",       [],   "App::PropertyStringList", "", "List of Solid Part Names")
        DT.addObjectProperty(materialObject, "materialsNameList",    [],   "App::PropertyStringList", "", "List of matching Material Names")
        DT.addObjectProperty(materialObject, "materialsDensityList", [],   "App::PropertyFloatList",  "", "List of matching Density values")
        DT.addObjectProperty(materialObject, "kgm3ORgcm3",           True, "App::PropertyBool",       "", "Density units in the Dialog - kg/m^3 or g/cm^3")
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-__getstate__\n")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-__setstate__\n")
    # --------------------------------------------------------------------------
    def __str__(self):
        return str(self.__dict__)
# =============================================================================
class ViewProviderDapMaterialClass:
    """Handle the screen interface stuff for the materials dialog"""
    if Debug:
        CAD.Console.PrintMessage("ViewProviderDapMaterialClass-CLASS\n")
    #  -------------------------------------------------------------------------
    def __init__(self, materialViewObject):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-__init__\n")
        materialViewObject.Proxy = self
    #  -------------------------------------------------------------------------
    def doubleClicked(self, materialViewObject):
        """Open up the TaskPanel if it is not open"""
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-doubleClicked\n")
        Document = CADGui.getDocument(materialViewObject.Object.Document)
        if not Document.getInEdit():
            Document.setEdit(materialViewObject.Object.Name)
        return True
    #  -------------------------------------------------------------------------
    def getIcon(self):
        """Returns the full path to the material icon (Icon5n.png)"""
        if Debug:
            DT.Mess("ViewProviderDapMaterialClass-getIcon")
        return path.join(DT.getDapModulePath(), "icons", "Icon5n.png")
    #  -------------------------------------------------------------------------
    def attach(self, materialViewObject):
        if Debug:
            DT.Mess("ViewProviderDapMaterialClass-attach")
        self.materialObject = materialViewObject.Object
        materialViewObject.addDisplayMode(coin.SoGroup(), "Standard")
    #  -------------------------------------------------------------------------
    def getDisplayModes(self, materialObject):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-getDisplayModes\n")
        return []
    #  -------------------------------------------------------------------------
    def getDefaultDisplayMode(self):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-getDefaultDisplayMode\n")
        return "Flat Lines"
    #  -------------------------------------------------------------------------
    def setDisplayMode(self, mode):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-setDisplayMode\n")
        return mode
    #  -------------------------------------------------------------------------
    def updateData(self, obj, prop):
        return
    #  -------------------------------------------------------------------------
    def setEdit(self, materialViewObject, mode):
        """Edit the parameters by calling the task dialog"""
        if Debug:
            DT.Mess("ViewProviderDapMaterialClass-setEdit")
        CADGui.Control.showDialog(TaskPanelDapMaterialClass(self.materialObject))
        return True
    #  -------------------------------------------------------------------------
    def unsetEdit(self, materialViewObject, mode):
        """Close the task dialog when we have finished using it"""
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-unsetEdit\n")
        CADGui.Control.closeDialog()
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-__getstate__\n")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            CAD.Console.PrintMessage("ViewProviderDapMaterialClass-__setstate__\n")
# =============================================================================
class TaskPanelDapMaterialClass:
    """Task panel for adding a Material for each solid Part"""
    if Debug:
        CAD.Console.PrintMessage("TaskPanelDapMaterialClass-CLASS\n")
    #  -------------------------------------------------------------------------
    def __init__(self, materialTaskObject):
        """Run on first instantiation of a TaskPanelDapMaterial class"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapMaterialClass-__init__\n")

        self.materialTaskObject = materialTaskObject
        materialTaskObject.Proxy = self

        # Get the materials data from the materials library
        cardID2cardData, cardID2cardName, DummyDict = cardutils.import_materials()

        # Set up a record for the default density value at the beginning of the density dictionary
        self.densityDict = {'Default': 1000.0}

        # Add all the cards to the densityDict except for specialised steels
        for materialID in sorted(cardID2cardData.keys()):
            # If the density option is 'None' set the density to a very small but non-zero value
            if cardID2cardName[materialID] == "None":
                self.densityDict[cardID2cardName[materialID]] = 0.000000001
            # We want to ignore all the gazillion types of steel - except the generic one
            elif 'Steel' not in cardID2cardName[materialID] or cardID2cardName[materialID] == 'Steel-Generic':
                # The density values are in various number formats on the cards, so
                # Get the density string from the card, and filter out the non-numeric characters
                # This is fancy python - don't alter at all if you don't understand it
                # Python Syntax:  f(x) if condition else g(x) for x in sequence
                densityStr = cardID2cardData[materialID]['Density'][0:-3]
                density = ''.join(x for x in densityStr if x.isdigit() or x in ['.', '-', ','])
                densityNoComma = ''.join(x if x.isdigit() or x in ['.', '-'] else '.' for x in density)
                self.densityDict[cardID2cardName[materialID]] = float(str(densityNoComma))

        # Last thing, add a custom density card at the end of the list
        self.densityDict['Custom'] = 1000

        # Get a list of all the names (and labels) of all the Solid parts
        self.modelSolidsNamesList, self.modelSolidsLabelsList, DummyList = DT.getAllSolidsLists()
        self.modelMaterialsNamesList = []
        self.modelMaterialsDensitiesList = []

        # Create a density entry for all the solid names in the model
        for index in range(len(self.modelSolidsNamesList)):
            # Search for the material for this solid in any pre-existing list of solids
            for preIndex in range(len(materialTaskObject.solidsNameList)):
                if self.modelSolidsNamesList[index] == materialTaskObject.solidsNameList[preIndex]:
                    self.modelMaterialsNamesList.append(materialTaskObject.materialsNameList[preIndex])
                    self.modelMaterialsDensitiesList.append(materialTaskObject.materialsDensityList[preIndex])
                    break
            else:
                # If we don't find it, then create a default material at this index
                self.modelMaterialsNamesList.append("Default")
                self.modelMaterialsDensitiesList.append(1000.0)

        # Set up the task dialog
        ui_path = path.join(path.dirname(__file__), "TaskPanelDapMaterials.ui")
        self.form = CADGui.PySideUic.loadUi(ui_path)

        # Set up kg/m3 according to the material object value
        if materialTaskObject.kgm3ORgcm3 is True:
            self.form.kgm3.setChecked(True)
        else:
            self.form.gcm3.setChecked(True)

        # Set up the table for the densities in the task dialog
        self.form.tableWidget.clearContents()
        self.form.tableWidget.setRowCount(0)
        self.form.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

        # Display a density table of all the solid parts in the dialog form
        for tableIndex in range(len(self.modelSolidsNamesList)):
            self.form.tableWidget.insertRow(tableIndex)
            # --------------------------------------
            # Column 0 -- Name of solid in the model
            # Add the solid LABEL to the form, not the solid NAME
            partName = QtGui.QTableWidgetItem(self.modelSolidsLabelsList[tableIndex])
            partName.setFlags(QtCore.Qt.ItemIsEnabled)
            self.form.tableWidget.setItem(tableIndex, 0, partName)

            # ----------------------------------
            # Column 1 - Material type selection
            # Create a separate new combobox of all material types in column 1 of each solid Part
            combo = QtGui.QComboBox()
            # If we don't find an entry, then the material will be default (item 0 in list)
            dictIndex = 0
            comboIndex = 0
            for materName in self.densityDict:
                # First add the material name to the list in the combo box
                combo.addItem(materName)
                # Now check if this one is the currently selected density
                if materName == self.modelMaterialsNamesList[tableIndex]:
                    comboIndex = dictIndex
                dictIndex += 1
            # Save the combo in the table cell and set the current index
            self.form.tableWidget.setCellWidget(tableIndex, 1, combo)
            combo.setCurrentIndex(comboIndex)

            # Set the connect function for the density index changed
            combo.currentIndexChanged.connect(self.MaterialComboChanged_Callback)

            # -------------------------
            # Column 2 - Density values
            # Insert the appropriate density into column 2
            if materialTaskObject.kgm3ORgcm3 is True:
                density = str(float(self.modelMaterialsDensitiesList[tableIndex]))
            else:
                density = str(float(self.modelMaterialsDensitiesList[tableIndex])/1000.0)

            self.form.tableWidget.setItem(
                tableIndex,
                2,
                QtGui.QTableWidgetItem(density))

            self.form.tableWidget.resizeColumnsToContents()
        # End of populating the table in the task dialog

        # Connect up changes in the form to the appropriate handler
        self.form.tableWidget.cellClicked.connect(self.showSelectionInGui_Callback)
        self.form.tableWidget.cellChanged.connect(self.manualDensityEntered_Callback)
        self.form.kgm3.toggled.connect(self.densityUnits_Callback)
        self.form.gcm3.toggled.connect(self.densityUnits_Callback)
    #  -------------------------------------------------------------------------
    def accept(self):
        """Run when we press the OK button"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapMaterialClass-accept\n")

        # Transfer the lists we have been working on, into the material Object
        self.materialTaskObject.solidsNameList = self.modelSolidsNamesList
        self.materialTaskObject.materialsNameList = self.modelMaterialsNamesList
        self.materialTaskObject.materialsDensityList = self.modelMaterialsDensitiesList

        # Get the body dictionary and calculate the new CoG and MoI
        # As any change in material will affect their CoG and MoI
        bodyObjDict = DT.getDictionary("DapBody")
        for bodyName in bodyObjDict:
            bodyObj = bodyObjDict[bodyName]
            DT.computeCoGAndMomentInertia(bodyObj)

        # Update all the stuff by asking for a re-compute
        self.materialTaskObject.recompute()
        CADGui.getDocument(self.materialTaskObject.Document).resetEdit()
    #  -------------------------------------------------------------------------
    def densityUnits_Callback(self):
        """Fix up the densities if we change between kg/m3 and g/cm3"""
        if self.form.kgm3.isChecked():
            self.materialTaskObject.kgm3ORgcm3 = True
        else:
            self.materialTaskObject.kgm3ORgcm3 = False

        for tableIndex in range(len(self.modelMaterialsDensitiesList)):
            if self.materialTaskObject.kgm3ORgcm3 is True:
                density = str(float(self.modelMaterialsDensitiesList[tableIndex]))
            else:
                density = str(float(self.modelMaterialsDensitiesList[tableIndex]) / 1000.0)
            self.form.tableWidget.setItem(
                tableIndex,
                2,
                QtGui.QTableWidgetItem(density))
    #  -------------------------------------------------------------------------
    def manualDensityEntered_Callback(self):
        """We have entered a density value manually"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapMaterialClass-manualDensityEntered_Callback\n")

        currentRow = self.form.tableWidget.currentRow()
        currentColumn = self.form.tableWidget.currentColumn()

        # Update if a Custom density has been entered in column 2
        if currentColumn == 2:
            densityStr = self.form.tableWidget.item(currentRow, 2).text()
            if len(densityStr) > 0:
                if 'e' in densityStr:
                    densityNoComma = densityStr
                else:
                    # The next few rows are fancy python
                    # Don't change them at all, unless you know what they mean
                    # Filter out any non-numerics
                    density = ''.join(x for x in densityStr if x.isdigit() or x in ['.', '-', ','])
                    # Replace any comma with a full-stop [period]
                    densityNoComma = ''.join(x if x.isdigit() or x in ['.', '-'] else '.' for x in density)
            else:
                densityNoComma = "1e-9"

            # Update the entry with the new custom value
            self.modelMaterialsNamesList[currentRow] = 'Custom'
            if self.materialTaskObject.kgm3ORgcm3 is True:
                self.modelMaterialsDensitiesList[currentRow] = float(str(densityNoComma))
            else:
                self.modelMaterialsDensitiesList[currentRow] = float(str(densityNoComma)) * 1000.0

            # Update the density to being a Custom one in the table
            # (the last density option in the list)
            combo = self.form.tableWidget.cellWidget(currentRow, 1)
            combo.setCurrentIndex(len(self.densityDict) - 1)
            self.form.tableWidget.setCellWidget(currentRow, 1, combo)
            # Write the new density value which was entered, back into column 2 of current Row
            # It was entered with the current units, so it should stay the same size as was entered
            self.form.tableWidget.item(currentRow, 2).setText(str(densityNoComma))
    #  -------------------------------------------------------------------------
    def MaterialComboChanged_Callback(self):
        """We have changed the type of material for this body"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapMaterialClass-MaterialComboChanged_Callback\n")

        # Find out where in the table our change occurred
        currentRow = self.form.tableWidget.currentRow()
        currentColumn = self.form.tableWidget.currentColumn()

        # Ignore false alarm calls to this callback function
        if currentRow < 0 and currentColumn < 0:
            return

        # Find the new material name we have selected
        MaterialClassombo = self.form.tableWidget.cellWidget(currentRow, 1)
        materialName = MaterialClassombo.currentText()

        # Update the entry with new material and density
        self.modelMaterialsNamesList[currentRow] = materialName
        self.modelMaterialsDensitiesList[currentRow] = float(self.densityDict[materialName])

        # Display the newly selected density in the table
        # NOTE: Density is stored internally as kg / m^3
        if self.materialTaskObject.kgm3ORgcm3 is True:
            self.form.tableWidget.setItem(currentRow, 2, QtGui.QTableWidgetItem(str(self.densityDict[materialName])))
        else:
            self.form.tableWidget.setItem(currentRow, 2, QtGui.QTableWidgetItem(str(self.densityDict[materialName] / 1000.0)))

        self.form.tableWidget.resizeColumnsToContents()
    #  -------------------------------------------------------------------------
    def showSelectionInGui_Callback(self, row, column):
        """Show the object in the Gui when we click on its name in the table"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapMaterialClass-showSelectionInGui_Callback\n")

        #  Select the object to make it highlighted
        if column == 0:
            # Find the object matching the solid item we have clicked on
            selectionObjectName = self.form.tableWidget.item(row, column).text()
            selection_object = CAD.ActiveDocument.findObjects(Label="^"+selectionObjectName+"$")[0]
            # Clear other possible visible selections and make this solid show in the "selected" colour
            CADGui.Selection.clearSelection()
            CADGui.Selection.addSelection(selection_object)
    #  -------------------------------------------------------------------------
    def getStandardButtons(self):
        """ Set which button will appear at the top of the TaskDialog [Called from FreeCAD]"""
        if Debug:
            CAD.Console.PrintMessage("TaskPanelDapAnimateClass-getStandardButtons\n")
        return int(QtGui.QDialogButtonBox.Ok)
    #  -------------------------------------------------------------------------
    def __getstate__(self):
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-__getstate__\n")
    #  -------------------------------------------------------------------------
    def __setstate__(self, state):
        if Debug:
            CAD.Console.PrintMessage("DapMaterialClass-__setstate__\n")
# =============================================================================
