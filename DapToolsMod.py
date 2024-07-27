import FreeCAD

import Part
from os import path
import math
import numpy as np

Debug = False
#  -------------------------------------------------------------------------
# These are the string constants used in various places throughout the code
# These options are included in the code,
# but limited until each has been more thoroughly tested
JOINT_TYPE = ["Revolute"
              ]
JOINT_TYPE_DICTIONARY = {"Revolute": 0
                         }
# These options are included in the code,
# but limited until each has been more thoroughly tested
FORCE_TYPE = ["Gravity",
              "Spring",
              "Rotational Spring",
              "Linear Spring Damper",
              "Rotational Spring Damper",
              "Unilateral Spring Damper",
              "Constant Force Local to Body",
               "Constant Global Force",
              "Constant Torque about a Point",
               "Contact Friction",
              "Motor",
              "Motor with Air Friction"
              ]
FORCE_TYPE_DICTIONARY = {"Gravity": 0,
                         "Spring": 1,
                         "Rotational Spring": 2,
                         "Linear Spring Damper": 3,
                         "Rotational Spring Damper": 4,
                         "Unilateral Spring Damper": 5,
                         "Constant Force Local to Body": 6,
                         "Constant Global Force": 7,
                         "Constant Torque about a Point": 8,
                         "Contact Friction": 9,
                         "Motor": 10,
                         "Motor with Air Friction": 11,
                         }
FORCE_TYPE_HELPER_TEXT = [
    "Universal force of attraction between all matter",
    "A device that stores energy when compressed or extended and exerts a force in the opposite direction",
    "A device that stores energy when twisted and exerts a torque in the opposite direction",
    "A device used to limit or retard linear vibration ",
    "Device used to limit movement and vibration caused by rotation",
    "A Device used to dampen vibration in only the one direction",
    "A constant force with direction relative to the Body coordinates",
    "A constant force in a specific global direction",
    "A constant torque about a point on a body",
    "Contact friction between two bodies",
    "A motor with characteristics defined by an equation",
    "A motor defined by an equation, but with air friction associated with body movement"]
NIKRAVESH_EXAMPLES = [
    'Double A-Arm Suspension',
    'MacPherson Suspension A',
    'MacPherson Suspension B',
    'MacPherson Suspension C',
    'Cart A',
    'Cart B',
    'Cart C',
    'Cart D',
    'Conveyor Belt and Friction',
    'Rod Impacting Ground',
    'Sliding Pendulum',
    'Generic Sliding Pendulum']
NIKRAVESH_EXAMPLES_DICTIONARY = {
    'Double A-Arm Suspension': 'II',
    'MacPherson Suspension A': 'MP_A',
    'MacPherson Suspension B': 'MP_B',
    'MacPherson Suspension C': 'MP_C',
    'Cart A': 'CART_A',
    'Cart B': 'CART_B',
    'Cart C': 'CART_C',
    'Cart D': 'CART_D',
    'Conveyor Belt and Friction': 'CB',
    'Rod Impacting Ground': 'Rod',
    'Sliding Pendulum': 'SP',
    'Generic Sliding Pendulum': 'GSP'}
NIKRAVESH_EXAMPLES_HELPER_TEXT = [
    'Double A-Arm Suspension - Nikravesh pp 170–173, 371–372',
    'MacPherson Suspension A - Nikravesh pp 173-175',
    'MacPherson Suspension B - Nikravesh pp 175-176',
    'MacPherson Suspension C - Nikravesh pp 176-177',
    'Cart_A - Nikravesh pp. 177–178',
    'Cart_B - Nikravesh pp. 178–179',
    'Cart_C - Nikravesh pp. 179-180',
    'Cart_D - Nikravesh pg. 180',
    'Conveyor Belt and Friction - Nikravesh 180–182, 358',
    'Rod Impacting Ground - Nikravesh pp. 176-177',
    'Sliding Pendulum - Nikravesh pp. 94, 118–120',
    'Generic Sliding Pendulum']
####################################################################
# HERE IS THE 'DICTIONARY' to the  DICTIONARIES in the DAP workbench
# ####################################################################
#
# bodyObjDict:          Dap Body Object Container Name --> Dap Body Object
# jointObjDict:         Dap Joint Container Name --> Dap Joint Container object
# forceObjDict:         Dap Force Container Name --> Dap Force Container object
# DictionaryOfPoints:   Dap Body Object Container Name -->
#                       Dict: FreeCAD point name --> index number in the point list in the Body container
# driverObjDict:        joint name --> initialised instance of function class
# cardID2cardData:      materialID --> cardData --> data on card
# cardID2cardName:      materiaID --> material name in the card

####################################################################
# List of available buttons in the task dialog
####################################################################
# NoButton        = 0x00000000,     Ok     = 0x00000400,     Save    = 0x00000800,
# SaveAll         = 0x00001000,     Open   = 0x00002000,     Yes     = 0x00004000,
# YesToAll        = 0x00008000,     No     = 0x00010000,     NoToAll = 0x00020000,
# Abort           = 0x00040000,     Retry  = 0x00080000,     Ignore  = 0x00100000,
# Close           = 0x00200000,     Cancel = 0x00400000,     Discard = 0x00800000,
# Help            = 0x01000000,     Apply  = 0x02000000,     Reset   = 0x04000000,
# RestoreDefaults = 0x08000000,

#  -------------------------------------------------------------------------
def getActiveContainerObject():
    """Return the container object which is currently active"""
    if Debug:
        Mess("DapTools-getActiveContainerObject")
    # The module must be imported here for "isinstance" to work below
    from DapContainerMod import DapContainerClass
    for container in FreeCAD.ActiveDocument.Objects:
        if hasattr(container, "Proxy") and isinstance(container.Proxy, DapContainerClass):
            if container.activeContainer is True:
                return container
    return None
#  -------------------------------------------------------------------------
def setActiveContainer(containerObj):
    """Sets the container object to activeContainer=True
       and makes all the other containers false"""
    if Debug:
        Mess("DapTools-setActiveContainer")
    # The module must be imported here for "isinstance" to work below
    from DapContainerMod import DapContainerClass
    Found = False
    for container in FreeCAD.ActiveDocument.Objects:
        if hasattr(container, "Proxy") and isinstance(container.Proxy, DapContainerClass):
            if container == containerObj:
                containerObj.activeContainer = True
                Found = True
            else:
                container.activeContainer = False
    
    # Return True/False if we found one or not
    return Found
#  -------------------------------------------------------------------------
def getPointsFromBodyName(bodyName, bodyObjDict):
    """Generate the Point Label list which corresponds to the given body name"""
    if Debug:
        Mess("DapTools-getPointsFromBodyName")

    ListNames = []
    ListLabels = []
    if bodyName != "":
        bodyObj = bodyObjDict[bodyName]
        return bodyObj.pointNames.copy(), bodyObj.pointLabels.copy()
    else:
        return [], []
# --------------------------------------------------------------------------
def condensePoints(pointNames, pointLabels, pointLocals):
    """Condense all the duplicate points into one"""
    if Debug:
        Mess("DapTools-condensePoints")

    # Condense all the duplicate points in this specific body into one
    numPoints = len(pointLocals)
    i = 0
    while i < numPoints:
        j = i + 1
        while j < numPoints:
            if abs(pointLocals[i].x - pointLocals[j].x) < 1.0e-10:
                if abs(pointLocals[i].y - pointLocals[j].y) < 1.0e-10:
                    if abs(pointLocals[i].z - pointLocals[j].z) < 1.0e-10:
                        # Compare the body names (i.e. the string from beginning to '{'
                        labeli = pointLabels[i][:pointLabels[i].index('{')]
                        labelj = pointLabels[j][:pointLabels[j].index('{')]
                        if labeli == labelj:
                            if Debug:
                                MessNoLF("Combining: ")
                                MessNoLF(pointLabels[i])
                                MessNoLF(" and ")
                                Mess(pointLabels[j])
                            pointNames[i] = pointNames[i] + "-" + pointNames[j][pointNames[j].index('{'):]
                            pointLabels[i] = pointLabels[i] + "-" + pointLabels[j][pointLabels[j].index('{'):]
                            # Shift the others up to remove the duplicate
                            k = j + 1
                            while k < numPoints:
                                pointNames[k - 1] = pointNames[k]
                                pointLabels[k - 1] = pointLabels[k]
                                pointLocals[k - 1] = pointLocals[k]
                                k += 1
                            # Pop the bottom item off the lists
                            pointNames.pop()
                            pointLabels.pop()
                            pointLocals.pop()
                            numPoints -= 1
            j += 1
        i += 1
    # Now, condense all the duplicate points into one, irrespective of body name
    numPoints = len(pointLocals)
    i = 0
    while i < numPoints:
        j = i + 1
        while j < numPoints:
            if abs(pointLocals[i].x - pointLocals[j].x) < 1.0e-10:
                if abs(pointLocals[i].y - pointLocals[j].y) < 1.0e-10:
                    if abs(pointLocals[i].z - pointLocals[j].z) < 1.0e-10:
                        if Debug:
                            MessNoLF("Combining: ")
                            MessNoLF(pointLabels[i])
                            MessNoLF(" and ")
                            Mess(pointLabels[j])
                        pointNames[i] = pointNames[i] + "-" + pointNames[j]
                        pointLabels[i] = pointLabels[i] + "-" + pointLabels[j]
                        if Debug:
                            Mess(pointLabels[i])
                        # Shift the others up to remove the duplicate
                        k = j + 1
                        while k < numPoints:
                            pointNames[k - 1] = pointNames[k]
                            pointLabels[k - 1] = pointLabels[k]
                            pointLocals[k - 1] = pointLocals[k]
                            k += 1
                        # Pop the bottom item off the lists
                        pointNames.pop()
                        pointLabels.pop()
                        pointLocals.pop()
                        numPoints -= 1
            j += 1
        i += 1

    # If we are debugging, Print out all the body's and point's placements etc
    if Debug:
        for index in range(len(pointNames)):
            Mess("-------------------------------------------------------------------")
            Mess("Point Name: " + str(pointNames[index]))
            Mess("Point Label:  " + str(pointLabels[index]))
            Mess("")
            MessNoLF("Point Local Vector:")
            PrintVec(pointLocals[index])
            MessNoLF("Point World Vector:")
            PrintVec(FreeCAD.Vector(BodyPlacementMatrix.multVec(pointLocals[index])))
            Mess("")
#  -------------------------------------------------------------------------
def parsePoint(pointString):
    """Split all the LCS points for this component into a tip string"""
    while True:
        try:
            a = pointString.index("}-{")
        except BaseException as e:
            break
        pointString = pointString[:a]+"\n  -->"+pointString[a+3:]
    while True:
        try:
            a = pointString.index("-{")
        except BaseException as e:
            break
        pointString = pointString[:a]+"\n  -->"+pointString[a+2:]
    while True:
        try:
            a = pointString.index("}-")
        except BaseException as e:
            break
        pointString = pointString[:a]+"\n"+pointString[a+2:]
    while True:
        try:
            a = pointString.index("}")
        except BaseException as e:
            break
        pointString = pointString[:a]
    return pointString
#  -------------------------------------------------------------------------
def addObjectProperty(newobject, newproperty, initVal, newtype, *args):
    """Call addObjectProperty on the object if it does not yet exist"""
    if Debug:
        Mess("DapTools-addObjectProperty")
    # Only add it if the property does not exist there already
    added = False
    if newproperty not in newobject.PropertiesList:
        added = newobject.addProperty(newtype, newproperty, *args)
    if added:
        setattr(newobject, newproperty, initVal)
        return True
    else:
        return False
#  -------------------------------------------------------------------------
def getDictionary(DAPName):
    """Run through the Active Container group and
    return a dictionary with 'DAPName', vs objects"""
    if Debug:
        Mess("DapToolsClass-getDictionary")
    DAPDictionary = {}
    activeContainer = getActiveContainerObject()
    for groupMember in activeContainer.Group:
        if DAPName in groupMember.Name:
            DAPDictionary[groupMember.Name] = groupMember
    return DAPDictionary
#  -------------------------------------------------------------------------
def getAllSolidsLists():
    """Run through the Solids and return lists of Names / Labels
    and a list of all the actual assembly objects"""
    allSolidsNames = []
    allSolidsLabels = []
    allSolidsObjects = []

    # Run through all the whole document's objects, looking for the Solids
    objects = FreeCAD.ActiveDocument.Objects
    for obj in objects:
        if hasattr(obj, "Type") and obj.Type == 'Assembly':
            if Debug:
                Mess(obj.Name)
            SolidsObject = obj
            break
    else:
        Mess("No Assembly 4 object found")
        return allSolidsNames, allSolidsLabels, allSolidsObjects
        
    # Find all the parts
    # A part is searched for as something which is attached to something,
    # by means of something, and which has a shape
    for groupMember in SolidsObject.Group:
        if hasattr(groupMember, 'AttachedTo') and \
           hasattr(groupMember, 'AttachedBy') and \
           hasattr(groupMember, 'Shape'):
            if "^"+groupMember.Name+"$" in allSolidsNames:
                FreeCAD.Console.PrintError("Duplicate Shape Name found: " + groupMember.Name + "\n")

            allSolidsNames.append(groupMember.Name)
            allSolidsLabels.append(groupMember.Label)
            allSolidsObjects.append(groupMember)

    return allSolidsNames, allSolidsLabels, allSolidsObjects
#  -------------------------------------------------------------------------
def getDictionaryOfBodyPoints():
    """Run through the active document and return a dictionary of a dictionary of
    point names in each bodyObject """
    # i.e. {<body name> : {<point name> : <its index in the body's list of points>}}
    if Debug:
        Mess("DapToolsClass-getDictionaryOfBodyPoints")
    dictionaryOfBodyPoints = {}
    activeContainer = getActiveContainerObject()
    for groupMember in activeContainer.Group:
        if "DapBody" in groupMember.Name:
            PointDict = {}
            for index in range(len(groupMember.pointNames)):
                PointDict[groupMember.pointNames[index]] = index
            dictionaryOfBodyPoints[groupMember.Name] = PointDict.copy()
            
    return dictionaryOfBodyPoints
#  -------------------------------------------------------------------------
def getMaterialObject():
    """Return the Material object if a Material Object container is contained in the active container"""
    if Debug:
        Mess("DapToolsMod-getMaterialObject")
    activeContainer = getActiveContainerObject()
    for groupMember in activeContainer.Group:
        if "DapMaterial" in groupMember.Name:
            return groupMember
    return None
#  -------------------------------------------------------------------------
def getDapModulePath():
    """Returns the path where the current DAP module is stored
    Determines where this file is running from, so DAP workbench works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)"""
    if Debug:
        Mess("DapTools-getDapModulePath")
    return path.dirname(__file__)
#  -------------------------------------------------------------------------
def computeCoGAndMomentInertia(bodyObj):
    """ Computes:
    1. The world centre of mass of each body based on the weighted sum
    of each solid's centre of mass
    2. The moment of inertia of the whole body, based on the moment of Inertia for the
    solid through its CoG axis + solid mass * (perpendicular distance
    between the axis through the solid's CoG and the axis through the whole body's
    CoG) squared.   Both axes should be normal to the plane of movement and
    will hence be parallel if everything is OK.
    *************************************************************************
    IMPORTANT:  FreeCAD and NikraDAP work internally with a mm-kg-s system
    *************************************************************************
    """

    # Get the Material object (i.e. list of densities) which has been defined in the appropriate DAP routine
    theMaterialObject = getMaterialObject()

    # Determine the vectors and matrices to convert movement in the selected base plane to the X-Y plane
    MovePlaneNormal = getActiveContainerObject().movementPlaneNormal
    xyzToXYRotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), MovePlaneNormal)

    # Clear the variables and lists for filling
    totalBodyMass = 0
    CoGWholeBody = FreeCAD.Vector()
    massList = []
    solidMoIThroughCoGNormalToMovePlaneList = []
    solidCentreOfGravityXYPlaneList = []

    # Run through all the solids in the assemblyObjectList
    for assemblyPartName in bodyObj.ass4SolidsNames:
        assemblyObj = bodyObj.Document.findObjects(Name="^" + assemblyPartName + "$")[0]
        if Debug:
            Mess(str("assembly4 Part Name:  ")+str(assemblyPartName))

        # Translate this assemblyObj to where assembly4 put it
        # assemblyObj.applyRotation(assemblyObj.Placement.Rotation)
        # assemblyObj.applyTranslation(assemblyObj.Placement.Base)

        # Volume of this assemblyObj in cubic mm
        volume = assemblyObj.Shape.Volume
        # Density of this assemblyObj in kg per cubic mm
        index = theMaterialObject.solidsNameList.index(assemblyPartName)
        density = theMaterialObject.materialsDensityList[index] * 1e-9
        # Calculate the mass in kg
        mass = density * volume
        massList.append(mass)
        if Debug:
            Mess(str("Volume [mm^3]:  ") + str(volume))
            Mess("Density [kg/mm^3]:  "+str(density))
            Mess("Mass [kg]:  "+str(mass))

        # Add the Centre of gravities to the list to use in parallel axis theorem
        solidCentreOfGravityXYPlaneList.append(xyzToXYRotation.toMatrix().multVec(assemblyObj.Shape.CenterOfGravity))
        solidCentreOfGravityXYPlaneList[-1].z = 0.0

        # MatrixOfInertia[MoI] around an axis through the CoG of the Placed assemblyObj
        # and normal to the MovePlaneNormal
        MoIVec = assemblyObj.Shape.MatrixOfInertia.multVec(MovePlaneNormal)
        # MoIVecLength = MoIVec.Length * 1e-6
        MoIVecLength = MoIVec.Length
        # solidMoIThroughCoGNormalToMovePlaneList.append(MoIVecLength * mass)
        # MoI calculated in [kg*mm^2]
        solidMoIThroughCoGNormalToMovePlaneList.append(MoIVecLength * density)

        totalBodyMass += mass
        CoGWholeBody += mass * solidCentreOfGravityXYPlaneList[-1]
    # Next assemblyIndex

    bodyObj.Mass = totalBodyMass
    CoGWholeBody /= totalBodyMass
    bodyObj.centreOfGravity = CoGWholeBody
    bodyCentreOfGravityXYPlane = xyzToXYRotation.toMatrix().multVec(bodyObj.centreOfGravity)
    bodyCentreOfGravityXYPlane.z = 0.0

    # Using parallel axis theorem to compute the moment of inertia through the CoG
    # of the full body comprised of multiple shapes
    momentInertiaWholeBody = 0
    for MoIIndex in range(len(solidMoIThroughCoGNormalToMovePlaneList)):
        if Debug:
            Mess("Sub-Body MoI: "+str(solidMoIThroughCoGNormalToMovePlaneList[MoIIndex]))
        distanceBetweenAxes = (bodyCentreOfGravityXYPlane - solidCentreOfGravityXYPlaneList[MoIIndex]).Length
        momentInertiaWholeBody += solidMoIThroughCoGNormalToMovePlaneList[MoIIndex] + massList[MoIIndex] * (distanceBetweenAxes ** 2)
    bodyObj.momentInertia = momentInertiaWholeBody

    # Gravity vector is acceleration of gravity in mm / s^2 - weight vector is force of gravity in kg mm / s^2
    bodyObj.weightVector = getActiveContainerObject().gravityVector * totalBodyMass
    if Debug:
        Mess("Body Total Mass [kg]:  "+str(totalBodyMass))
        MessNoLF("Body Centre of Gravity [mm]:  ")
        PrintVec(CoGWholeBody)
        Mess("Body moment of inertia [kg mm^2):  "+str(momentInertiaWholeBody))
        Mess("")

    #
    return True
#  -------------------------------------------------------------------------
def DrawRotArrow(Point, LeftRight, diameter):
    """Draw a yellow circle arrow around a Revolute point
    We first draw it relative to the X-Y plane
    and then rotate it relative to the defined movement plane"""
    radiusRing = diameter
    thicknessRing = diameter / 5
    torus_direction = FreeCAD.Vector(0, 0, 1)
    cone_direction = FreeCAD.Vector(0, 1, 0)

    # Make either a left half or a right half of the torus
    if LeftRight:
        torus = Part.makeTorus(radiusRing, thicknessRing, FreeCAD.Vector(0, 0, radiusRing), torus_direction, -180, 180, 90)
        cone_position = FreeCAD.Vector(radiusRing, -5 * thicknessRing, radiusRing)
        cone = Part.makeCone(0, 2 * thicknessRing, 5 * thicknessRing, cone_position, cone_direction)
    else:
        torus = Part.makeTorus(radiusRing, thicknessRing, FreeCAD.Vector(0, 0, radiusRing), -torus_direction, -180, 180, 90)
        cone_position = FreeCAD.Vector(-radiusRing, -5 * thicknessRing, radiusRing)
        cone = Part.makeCone(0, 2 * thicknessRing, 5 * thicknessRing, cone_position, cone_direction)
    # Make a cone to act as an arrow on the end of the half torus
    torus_w_arrows = Part.makeCompound([torus, cone])
    # Rotate torus to be relative to the defined movement plane
    rotationToMovementPlane = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), getActiveContainerObject().movementPlaneNormal)
    torus_w_arrows.applyRotation(rotationToMovementPlane)
    # Translate the torus to be located at the point
    torus_w_arrows.applyTranslation(Point)

    return torus_w_arrows
#  -------------------------------------------------------------------------
def DrawRigidBolt(Point, diam, length):
    bolt = Part.makeCylinder(
        diam,
        length * 2,
        Point - FreeCAD.Vector(0, 0, length),
        FreeCAD.Vector(0, 0, 1)
    )

    # FORMAT OF MAKE WEDGE:
    # ====================
    # makeWedge (xbotleftbase, basey, zbotleftbase,
    #            zbotleftroof,xbotleftroof,
    #            xtoprightbase,roofy,ztoprightbase,
    #            ztoprightroof,xtoprightroof

    sin = math.sin(math.pi / 3)
    cos = math.cos(math.pi / 3)

    nuta = Part.makeWedge(-diam, -diam * 2 * sin, -length * 2 / 9,
                          -length * 2 / 9, 0,
                          diam, 0, length * 2 / 9,
                          length * 2 / 9, 0)
    nutb = nuta.copy().mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(sin, cos, 0))
    nutc = nuta.copy().mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(sin, -cos, 0))
    nutd = nuta.fuse([nutb, nutc])
    nute = nutd.copy().mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
    nutf = nutd.fuse([nute])
    nutg = nutf.copy()
    nutf.translate(Point - FreeCAD.Vector(0, 0, length * 0.7))
    nutg.translate(Point + FreeCAD.Vector(0, 0, length * 0.7))

    return bolt.fuse([nutf, nutg])
#  -------------------------------------------------------------------------
def DrawTransArrow(Point1, Point2, diameter):
    # Draw an arrow as long as the distance of the vector between the points
    llen = (Point1 - Point2).Length
    if llen > 1e-6:
        # Direction of the arrow is the direction of the vector between the two points
        lin_move_dir = (Point2 - Point1).normalize()
        cylinder = Part.makeCylinder(
            diameter * 0.3,
            0.60 * llen,
            Point1 + 0.2 * llen * lin_move_dir,
            lin_move_dir,
        )
        # Draw the two arrow heads
        cone1 = Part.makeCone(0, diameter, 0.2 * llen, Point1, lin_move_dir)
        cone2 = Part.makeCone(0, diameter, 0.2 * llen, Point2, -lin_move_dir)
        return Part.makeCompound([cylinder, cone1, cone2])
    return Part.Shape()
#  -------------------------------------------------------------------------
def minMidMax3(x, y, z, minMidMax):
    """Given three numbers, return the minimum, or the middle or the maximum one
        minimum: if minMidMax == 1
        middle:  if minMidMax == 2
        maximum: if minMidMax == 3
    """
    x = abs(x)
    y = abs(y)
    z = abs(z)
    if x >= y:
        if y >= z:
            # x >= y >= z
            if minMidMax == 1:
                return z
            elif minMidMax == 2:
                return y
            else:
                return x
        elif x >= z:
            # x >= z > y
            if minMidMax == 1:
                return y
            elif minMidMax == 2:
                return z
            else:
                return x
        # z > x >= y
        elif minMidMax == 1:
            return y
        elif minMidMax == 2:
            return x
        else:
            return z
    # y > x
    elif x >= z:
        # y >= x >= z
        if minMidMax == 1:
            return z
        elif minMidMax == 2:
            return x
        else:
            return y
    # y > x and z > x
    elif y >= z:
        # y >= z > x
        if minMidMax == 1:
            return x
        elif minMidMax == 2:
            return z
        else:
            return y
    # z > y > x
    elif minMidMax == 1:
        return x
    elif minMidMax == 2:
        return y
    else:
        return z
#  -------------------------------------------------------------------------
def minMidMaxVec(Vector, minMidMax):
    """Given coordinates in a vector, return the minimum, or the middle or the maximum one
        minimum: if minMidMax == 1
        middle:  if minMidMax == 2
        maximum: if minMidMax == 3
    """
    Vec = FreeCAD.Vector(Vector)
    Vec.x = abs(Vec.x)
    Vec.y = abs(Vec.y)
    Vec.z = abs(Vec.z)
    if Vec.x >= Vec.y:
        if Vec.y >= Vec.z:
            # Vec.x >= Vec.y >= Vec.z
            if minMidMax == 1:
                return Vec.z
            elif minMidMax == 2:
                return Vec.y
            else:
                return Vec.x
        if Vec.x >= Vec.z:
            # Vec.x >= Vec.z > Vec.y
            if minMidMax == 1:
                return Vec.y
            elif minMidMax == 2:
                return Vec.z
            else:
                return Vec.x
        # Vec.z > Vec.x >= Vec.y
        if minMidMax == 1:
            return Vec.y
        elif minMidMax == 2:
            return Vec.x
        else:
            return Vec.z
    # y > x
    if Vec.x >= Vec.z:
        # Vec.y >= Vec.x >= Vec.z
        if minMidMax == 1:
            return Vec.z
        elif minMidMax == 2:
            return Vec.x
        else:
            return Vec.y
    # y > x and z > x
    if Vec.y >= Vec.z:
        # Vec.y >= Vec.z > Vec.x
        if minMidMax == 1:
            return Vec.x
        elif minMidMax == 2:
            return Vec.z
        else:
            return Vec.y
    # Vec.z > Vec.y > Vec.x
    if minMidMax == 1:
        return Vec.x
    elif minMidMax == 2:
        return Vec.y
    else:
        return Vec.z
#  -------------------------------------------------------------------------
def RotationMatrixNp(phi):
    """ This function computes the rotational transformation matrix
    in the format of a 2X2 NumPy array"""
    return np.array([[math.cos(phi), -math.sin(phi)],
                     [math.sin(phi),  math.cos(phi)]])
#  -------------------------------------------------------------------------
def Mess(string):
    FreeCAD.Console.PrintMessage(str(string)+"\n")
#  -------------------------------------------------------------------------
def MessNoLF(string):
    FreeCAD.Console.PrintMessage(str(string))
#  -------------------------------------------------------------------------
def PrintVec(vec):
    FreeCAD.Console.PrintMessage("[" + str(Round(vec.x)) + ":" + str(Round(vec.y)) + ":" + str(Round(vec.z)) + "]\n")
#  -------------------------------------------------------------------------
def Np3D(arr):
    for x in arr:
        for y in x:
            s = "[ "
            for z in y:
                ss = str(Round(z))+"                 "
                s = s + ss[:12]
            s = s + " ]"
            FreeCAD.Console.PrintMessage(s+"\n")
        FreeCAD.Console.PrintMessage("\n")
#  -------------------------------------------------------------------------
def Np2D(arr):
    for x in arr:
        s = "[ "
        for y in x:
            ss = str(Round(y))+"                 "
            s = s + ss[:12]
        s = s + " ]"
        FreeCAD.Console.PrintMessage(s+"\n")
#  -------------------------------------------------------------------------
def Np1D(LF, arr):
    s = "[ "
    for y in arr:
        ss = str(Round(y))+"                 "
        s = s + ss[:12]
    s = s + " ]"
    if LF:
        FreeCAD.Console.PrintMessage(s+"\n")
    else:
        FreeCAD.Console.PrintMessage(s+" ")
#  -------------------------------------------------------------------------
def Np1Ddeg(LF, arr):
    s = "[ "
    for y in arr:
        ss = str(Round(y*180.0/math.pi))+"                 "
        s = s + ss[:12]
    s = s + " ]"
    if LF:
        FreeCAD.Console.PrintMessage(s+"\n")
    else:
        FreeCAD.Console.PrintMessage(s+" ")
#  -------------------------------------------------------------------------
def Round(num):
    if num >= 0.0:
        return int((100.0 * num + 0.5))/100.0
    else:
        return int((100.0 * num - 0.5))/100.0
# --------------------------------------------------------------------------
def decorateObject(objectToDecorate, body_I_object, body_J_object):
    # Get the world coordinates etc. of the A point
    solidNameAList = []
    solidPlacementAList = []
    solidBoxAList = []
    worldPointA = FreeCAD.Vector()
    if objectToDecorate.point_I_i_Name != "":
        # Find the bounding boxes of the component solids
        # solidNameList - names of the solids
        # solidPlacementList - The Placement.Base are the world coordinates of the solid origin
        # solidBoxList - The BoundBox values are the rectangular cartesian world coordinates of the bounding box
        Document = FreeCAD.ActiveDocument
        for solidName in body_I_object.ass4SolidsNames:
            solidObj = Document.findObjects(Name="^" + solidName + "$")[0]
            solidNameAList.append(solidName)
            solidPlacementAList.append(solidObj.Placement)
            solidBoxAList.append(solidObj.Shape.BoundBox)

        # Get the A world Placement of the compound DAP body
        worldAPlacement = body_I_object.world
        if Debug:
            MessNoLF("Main Body World A Placement: ")
            Mess(worldAPlacement)
        pointIndex = body_I_object.pointNames.index(objectToDecorate.point_I_i_Name)
        point_I_i_Local = body_I_object.pointLocals[pointIndex]
        worldPointA = worldAPlacement.toMatrix().multVec(point_I_i_Local)

    # Get the world coordinates etc. of the B of the point
    solidNameBList = []
    solidPlacementBList = []
    solidBoxBList = []
    worldPointB = FreeCAD.Vector()
    if objectToDecorate.point_J_i_Name != "":
        # Find the bounding boxes of the component solids
        Document = FreeCAD.ActiveDocument
        for solidName in body_J_object.ass4SolidsNames:
            solidObj = Document.findObjects(Name="^" + solidName + "$")[0]
            solidNameBList.append(solidName)
            solidPlacementBList.append(solidObj.Placement)
            solidBoxBList.append(solidObj.Shape.BoundBox)

        # Get the B world Placement of the compound DAP body
        worldBPlacement = body_J_object.world
        if Debug:
            MessNoLF("Main Body World B Placement: ")
            Mess(worldBPlacement)
        pointIndex = body_J_object.pointNames.index(objectToDecorate.point_J_i_Name)
        point_J_i_Local = body_J_object.pointLocals[pointIndex]
        worldPointB = worldBPlacement.toMatrix().multVec(point_J_i_Local)

    if Debug:
        Mess("Solid lists:")
        for i in range(len(solidNameAList)):
            MessNoLF(solidNameAList[i])
            MessNoLF(" -- ")
            MessNoLF(solidPlacementAList[i])
            MessNoLF(" -- ")
            Mess(solidBoxAList[i])
        for i in range(len(solidNameBList)):
            MessNoLF(solidNameBList[i])
            MessNoLF(" -- ")
            MessNoLF(solidPlacementBList[i])
            MessNoLF(" -- ")
            Mess(solidBoxBList[i])
        MessNoLF("World A point: ")
        PrintVec(worldPointA)
        MessNoLF("World B point: ")
        PrintVec(worldPointB)

    # Identify in which solid bounding box, the A and B points are
    ASolidIndex = BSolidIndex = 1
    for boxIndex in range(len(solidBoxAList)):
        if solidBoxAList[boxIndex].isInside(worldPointA):
            if Debug:
                MessNoLF("A point inside: ")
                Mess(solidNameAList[boxIndex])
            ASolidIndex = boxIndex
    for boxIndex in range(len(solidBoxBList)):
        if solidBoxBList[boxIndex].isInside(worldPointB):
            if Debug:
                MessNoLF("B point inside: ")
                Mess(solidNameBList[boxIndex])
            BSolidIndex = boxIndex

    if objectToDecorate.point_I_i_Name != "" and objectToDecorate.point_J_i_Name != "":
        # Draw some shapes in the gui, to show the point positions
        CurrentJointType = objectToDecorate.JointType
        planeNormal = getActiveContainerObject().movementPlaneNormal
        point_I_i_ = FreeCAD.Vector(worldPointA)
        point_J_i_ = FreeCAD.Vector(worldPointB)

        # Do some calculation of the torus sizes for Rev and Rev-Rev points
        if CurrentJointType == 0 or CurrentJointType == 2:
            # Depending on the plane normal:
            # Move the two thickness coordinates to their average,
            # Squash the thickness to zero, and
            # Set the point Diameter to the middle value of the Intersection box's xlength ylength zlength
            if planeNormal.x > 1e-6:
                point_I_i_.x = (worldPointA.x + worldPointB.x) / 2.0
                point_J_i_.x = point_I_i_.x
            elif planeNormal.y > 1e-6:
                point_I_i_.y = (worldPointA.y + worldPointB.y) / 2.0
                point_J_i_.y = point_I_i_.y
            elif planeNormal.z > 1e-6:
                point_I_i_.z = (worldPointA.z + worldPointB.z) / 2.0
                point_J_i_.z = point_I_i_.z

        # Draw the yellow circular arrow in the case of 'Rev' point
        if CurrentJointType == 0 \
                and objectToDecorate.point_I_iName != "" \
                and objectToDecorate.point_J_i_Name != "":
            pointDiam = minMidMax3(boxIntersection.XLength,
                                   boxIntersection.YLength,
                                   boxIntersection.ZLength,
                                   2)
            # Only draw if the diameter non-zero
            if pointDiam > 1e-6:
                # Draw the Left side
                # False == Left side
                Shape1 = DrawRotArrow(point_I_i_, False, pointDiam)
                # Draw the Right side
                # True == Right side
                Shape2 = DrawRotArrow(point_J_i_, True, pointDiam)
                Shape = Part.makeCompound([Shape1, Shape2])
                objectToDecorate.Shape = Shape
                objectToDecorate.ViewObject.ShapeColor = (1.0, 1.0, 0.5, 1.0)
                objectToDecorate.ViewObject.Transparency = 20

        # Draw a straight red arrow in the case of 'trans' point
        elif CurrentJointType == 1:
            Shape = DrawTransArrow(worldPointB, worldPointA, 15)
            objectToDecorate.Shape = Shape
            objectToDecorate.ViewObject.ShapeColor = (1.0, 0.5, 0.5, 1.0)
            objectToDecorate.ViewObject.Transparency = 20

        # Draw the two circular arrows and a line in the case of 'Revolute-Revolute' point
        elif CurrentJointType == 2:
            point_I_iDiam = minMidMax3(solidBoxAList[ASolidIndex].XLength,
                                       solidBoxAList[ASolidIndex].YLength,
                                       solidBoxAList[ASolidIndex].ZLength,
                                       2)
            point_J_i_Diam = minMidMax3(solidBoxBList[BSolidIndex].XLength,
                                        solidBoxBList[BSolidIndex].YLength,
                                        solidBoxBList[BSolidIndex].ZLength,
                                        2)
            # Draw both left and right sides of the torus
            Shape1 = DrawRotArrow(point_I_i_, True, point_I_iDiam / 2)
            Shape2 = DrawRotArrow(point_I_i_, False, point_I_iDiam / 2)
            Shape3 = DrawRotArrow(point_J_i_, True, point_J_i_Diam / 2)
            Shape4 = DrawRotArrow(point_J_i_, False, point_J_i_Diam / 2)
            # Draw the arrow
            Shape5 = DrawTransArrow(point_I_i_, point_J_i_, point_I_iDiam / 2)
            Shape = Part.makeCompound([Shape1, Shape2, Shape3, Shape4, Shape5])
            objectToDecorate.Shape = Shape
            objectToDecorate.ViewObject.ShapeColor = (1.0, 0.5, 1.0, 1.0)
            objectToDecorate.ViewObject.Transparency = 20
            objectToDecorate.lengthLink = (point_I_i_ - point_J_i_).Length

        # Draw a circular arrow and a line in the case of 'Revolute-Translation' point
        elif CurrentJointType == 3:
            Shape1 = DrawRotArrow(worldPointA, True, 3)
            Shape2 = DrawRotArrow(worldPointA, False, 3)
            Shape3 = DrawTransArrow(worldPointA, worldPointB, 15)
            Shape = Part.makeCompound([Shape1, Shape2, Shape3])
            objectToDecorate.Shape = Shape
            objectToDecorate.ViewObject.ShapeColor = (0.5, 1.0, 1.0, 1.0)
            objectToDecorate.ViewObject.Transparency = 20

        # Draw a Bolt in the case of 'Rigid' point
        elif CurrentJointType == 7:
            point_I_ilen = minMidMax3(boxIntersection.XLength,
                                      boxIntersection.YLength,
                                      boxIntersection.ZLength,
                                      3)
            point_I_idiam = minMidMax3(boxIntersection.XLength,
                                       boxIntersection.YLength,
                                       boxIntersection.ZLength,
                                       2)
            objectToDecorate.Shape = DrawRigidBolt(worldPointA, point_I_idiam / 3, point_I_ilen / 3)
            objectToDecorate.ViewObject.ShapeColor = (1.0, 0.5, 0.5, 1.0)
            objectToDecorate.ViewObject.Transparency = 20

        else:
            # Add a null shape to the object for the other more fancy types
            # TODO: The appropriate shapes may be added at a later time
            objectToDecorate.Shape = Part.Shape()
# --------------------------------------------------------------------------
#  -------------------------------------------------------------------------
def NormalizeNpVec(vecNp):
    if Debug:
        Mess("DapMainC - NormalizeNpVec")
    mag = np.sqrt(vecNp[0]**2 + vecNp[1]**2)
    if mag > 1.0e-10:
        vecNp /= mag
    else:
        vecNp *= 0.0
    return vecNp
#  -------------------------------------------------------------------------
def Rot90NumPy(a):
    b = np.zeros((2,))
    b[0], b[1] = -a[1], a[0]
    return b
#  -------------------------------------------------------------------------
def CADVecToNumPyF(CADVec):
    if Debug:
        Mess("CADvecToNumPyF")
    a = np.zeros((2,))
    a[0] = CADVec.x
    a[1] = CADVec.y
    return a
#  -------------------------------------------------------------------------
def nicePhiPlease(vectorsRelativeCoG):
    if Debug:
        Mess("nicePhiPlease")

    # Start off with a big phi to check when a good one hasn't been found yet
    phi = 1e6

    # Approximate phi from the longest local point vector
    maxLength = 0
    maxVectorIndex = 0
    if Debug:
        Mess("---")
        for i in range(len(vectorsRelativeCoG)):
            PrintVec(vectorsRelativeCoG[i])
        Mess("===")
    for localIndex in range(len(vectorsRelativeCoG)):
        if Debug:
            Mess(math.sqrt(vectorsRelativeCoG[localIndex].dot(vectorsRelativeCoG[localIndex])))
        L = vectorsRelativeCoG[localIndex].dot(vectorsRelativeCoG[localIndex])
        if L > maxLength:
            maxLength = L
            maxVectorIndex = localIndex
    x = vectorsRelativeCoG[maxVectorIndex].x
    y = vectorsRelativeCoG[maxVectorIndex].y
    if abs(x) < 1e-8:
        phi = math.pi / 2.0
    elif abs(y) < 1e-8:
        phi = 0
    elif abs(1.0 - abs(y / x)) < 1e-8:
        if y / x >= 0.0:
            phi = math.pi / 4.0
        else:
            phi = -math.pi / 4.0
    elif abs(0.57735026919 - abs(y / x)) < 1e-8:
        if y / x >= 0.0:
            phi = math.pi / 6.0
        else:
            phi = -math.pi / 6.0
    elif abs(1.73205080757 - abs(y / x)) < 1e-8:
        if y / x >= 0:
            phi = math.pi / 3.0
        else:
            phi = -math.pi / 3.0

    # If not, be satisfied with any other nice phi
    # of any other local point vector longer than 1/10 of the max one

    # Try for a multiple of 90 degrees
    if phi == 1e6:
        for localIndex in range(len(vectorsRelativeCoG) - 1):
            length = vectorsRelativeCoG[localIndex].Length
            if length > maxLength / 10.0:
                x = vectorsRelativeCoG[maxVectorIndex].x
                y = vectorsRelativeCoG[maxVectorIndex].y
                if abs(x) < 1e-8:
                    phi = math.pi / 2.0
                    break
                elif abs(y) < 1e-8:
                    phi = 0.0
                    break
    # If not found, try for a multiple of 45 degrees
    if phi == 1e6:
        for localIndex in range(len(vectorsRelativeCoG) - 1):
            length = vectorsRelativeCoG[localIndex].Length
            if length > maxLength / 10.0:
                x = vectorsRelativeCoG[maxVectorIndex].x
                y = vectorsRelativeCoG[maxVectorIndex].y
                if abs(1.0 - abs(y / x)) < 1e-8:
                    if y / x >= 0.0:
                        phi = math.pi / 4.0
                        break
                    else:
                        phi = -math.pi / 4.0
                        break
    # Next try for a multiple of 30 degrees
    if phi == 1e6:
        for localIndex in range(len(vectorsRelativeCoG) - 1):
            length = vectorsRelativeCoG[localIndex].Length
            if length > maxLength / 10.0:
                x = vectorsRelativeCoG[maxVectorIndex].x
                y = vectorsRelativeCoG[maxVectorIndex].y
                if abs(0.57735026919 - abs(y / x)) < 1e-8:
                    if y / x >= 0.0:
                        phi = math.pi / 6.0
                        break
                    else:
                        phi = -math.pi / 6.0
                        break
                if abs(1.73205080757 - abs(y / x)) < 1e-8:
                    if y / x >= 0:
                        phi = math.pi / 3.0
                        break
                    else:
                        phi = -math.pi / 3.0
                        break
    # Give up trying to find a nice one - at least we tried!
    if phi == 1e6:
        phi = math.atan2(vectorsRelativeCoG[maxVectorIndex].y, vectorsRelativeCoG[maxVectorIndex].x)

    # Make -90 < phi < 90
    if abs(phi) > math.pi:
        if phi < 0.0:
            phi += math.pi
        else:
            phi -= math.pi
    if abs(phi) > math.pi / 2.0:
        if phi < 0.0:
            phi += math.pi
        else:
            phi -= math.pi

    return phi
#  ------------------------------------------------------------------------