import FreeCAD as App
import FreeCADGui as Gui
import Part
from pivy import coin
import numpy as np

def exists(active: list, obj: str):
    for l in active:
        if type(l) == InfoIcon and (l.object == obj):
            return True, l
    return False, None

class SelectionObserverClass:
    def __init__(self):
        self.counter = 1
        self.ActiveIcons = []
        self.sceneGraph = Gui.ActiveDocument.ActiveView.getSceneGraph()

    def addSelection(self, doc, obj, sub, pnt):
        # This method is called when an object is selected
        print(f"Icons count: {len(self.ActiveIcons)}")
        print(f"Object: {obj}")
        self.counter = self.counter + 1
        # Get the selected object to show its 
        body = App.getDocument(doc).getObject(obj)
        
        icon = None
        if obj == 'DapContainer':
            icon = InfoIcon.planeIcon(self.sceneGraph, obj, doc)
        elif (len(obj) > 7 and obj[:8] == 'DapJoint'):
            icon = InfoIcon.rotationIcon(self.sceneGraph, obj, doc)
        elif (len(obj) > 6 and obj[:7] == 'DapBody'):
            icon = InfoIcon.velocityIcon(self.sceneGraph, obj, doc)
        
        if icon != None:
            self.ActiveIcons.append(icon)	

    def clearSelection(self, doc):
        # This method is called when the selection is cleared
        print(f"Selection cleared {len(self.ActiveIcons)}")
        for i in self.ActiveIcons:
            self.sceneGraph.removeChild(i.root)
            del i
        self.ActiveIcons.clear()
        
    def removeSelection(self, doc, obj, sub):
        # This method is called when an object is deselected
        print(f"Deselected object: {obj}")

#--------------------------------
# Icons for the
class InfoIcon:
    def __init__(self):
        self.rotation = None
        self.position = None
        self.root = None
        self.object = None
        self.document = None
        self.switch = None

    def rotationIcon(sceneGraph, doc, obj):
        # Create a new icon object
        icon = InfoIcon()
        icon.document = doc
        icon.object = obj

        # Create the SoSeperator node for the rotation icon
        rotationRoot = coin.SoSeparator()
        icon.root = rotationRoot
        
        # Add a switch so this can be turned on or off
        rotationRootSwitch = coin.SoSwitch()
        rotationRootSwitch.whichChild.setValue(-3) # Enabled
        rotationRoot.addChild(rotationRootSwitch)
        icon.switch = rotationRootSwitch

        # Create an annotation so that it is always visable
        rotationRootAnnotation = coin.SoAnnotation()
        rotationRootSwitch.addChild(rotationRootAnnotation)

        # Add the translation and rotation nodes
        rotationRootTrans = coin.SoTranslation()
        rotationRootTrans.translation.setValue([0, 0, 0])
        rotationRootRotation = coin.SoRotation()
        rotationRootRotation.rotation.setValue(0, 0, 0, 1)
            
        rotationRootAnnotation.addChild(rotationRootTrans)
        rotationRootAnnotation.addChild(rotationRootRotation)
        icon.position = rotationRootTrans
        icon.rotation = rotationRootRotation

        # Add the colour node
        rotationRootCol = coin.SoPackedColor()
        rotationRootCol.orderedRGBA.setValue(0xAAAA00ff)
        rotationRootAnnotation.addChild(rotationRootCol)

        # Set the constants for the arrow
        innerRadius = 8
        outerRadius = 10
        arrowWidth = 2
        arrowHeight = 4

        angleStep = np.pi / 100

        # Inner line
        innerLine = coin.SoSeparator()
        angle = 0.0
        for i in range(100):
            startAngle = angle
            endAngle = angle + angleStep
            startPoint = coin.SbVec3f(innerRadius * np.cos(startAngle), innerRadius * np.sin(startAngle), 0)
            endPoint = coin.SbVec3f(innerRadius * np.cos(endAngle), innerRadius * np.sin(endAngle), 0)
                    
            line = coin.SoLineSet()
            vertices = coin.SoVertexProperty()
            vertices.vertex.set1Value(0, startPoint)
            vertices.vertex.set1Value(1, endPoint)
            line.vertexProperty = vertices
            innerLine.addChild(line)
                    
            angle = endAngle
        rotationRootAnnotation.addChild(innerLine)

        # Outer line
        outerLine = coin.SoSeparator()
        angle = 0.0
        for i in range(100):
            startAngle = angle
            endAngle = angle + angleStep
            startPoint = coin.SbVec3f(outerRadius * np.cos(startAngle), outerRadius * np.sin(startAngle), 0)
            endPoint = coin.SbVec3f(outerRadius * np.cos(endAngle), outerRadius * np.sin(endAngle), 0)
                    
            line = coin.SoLineSet()
            vertices = coin.SoVertexProperty()
            vertices.vertex.set1Value(0, startPoint)
            vertices.vertex.set1Value(1, endPoint)
            line.vertexProperty = vertices
            outerLine.addChild(line)
                    
            angle = endAngle
        rotationRootAnnotation.addChild(outerLine)

        # Left Arrow
        leftArrow = coin.SoSeparator()
        points = [[-outerRadius, 0, -outerRadius - arrowWidth, 0],
            [-outerRadius - arrowWidth, 0, (outerRadius + innerRadius) / -2, -arrowHeight],
            [(outerRadius + innerRadius) / -2, -arrowHeight, -innerRadius + arrowWidth, 0],
            [-innerRadius + arrowWidth, 0, -innerRadius, 0]]

        for point in points:
            startPoint = coin.SbVec3f(point[0], point[1], 0)
            endPoint = coin.SbVec3f(point[2], point[3], 0)
                
            line = coin.SoLineSet()
            vertices = coin.SoVertexProperty()
            vertices.vertex.set1Value(0, startPoint)
            vertices.vertex.set1Value(1, endPoint)
            line.vertexProperty = vertices
            leftArrow.addChild(line)     
        rotationRootAnnotation.addChild(leftArrow)

        # Right Arrow
        rightArrow = coin.SoSeparator()
        points = [[outerRadius, 0, outerRadius + arrowWidth, 0],
            [outerRadius + arrowWidth, 0, (outerRadius + innerRadius) / 2, -arrowHeight],
            [(outerRadius + innerRadius) / 2, -arrowHeight, innerRadius - arrowWidth, 0],
            [innerRadius - arrowWidth, 0, innerRadius, 0]]

        for point in points:
            startPoint = coin.SbVec3f(point[0], point[1], 0)
            endPoint = coin.SbVec3f(point[2], point[3], 0)
                
            line = coin.SoLineSet()
            vertices = coin.SoVertexProperty()
            vertices.vertex.set1Value(0, startPoint)
            vertices.vertex.set1Value(1, endPoint)
            line.vertexProperty = vertices
            rightArrow.addChild(line)     
        rotationRootAnnotation.addChild(rightArrow)

            # Display the nodes
        sceneGraph.addChild(rotationRoot)

        return icon
    

    def velocityIcon(sceneGraph, doc, obj):
        # Create a new icon object
        icon = InfoIcon()
        icon.document = doc
        icon.object = obj

        # Create the SoSeperator node for the rotation icon
        velocityRoot = coin.SoSeparator()
        icon.root = velocityRoot
        
        # Add a switch so this can be turned on or off
        velocityRootSwitch = coin.SoSwitch()
        velocityRootSwitch.whichChild.setValue(-3) # Enabled
        velocityRoot.addChild(velocityRootSwitch)
        icon.switch = velocityRootSwitch

        # Create an annotation so that it is always visable
        velocityRootAnnotation = coin.SoAnnotation()
        velocityRootSwitch.addChild(velocityRootAnnotation)

        # Add the translation and rotation nodes
        velocityRootTrans = coin.SoTranslation()
        velocityRootTrans.translation.setValue([0, 0, 0])
        velocityRootRotation = coin.SoRotation()
        velocityRootRotation.rotation.setValue(0, 0, 0, 1)
            
        velocityRootAnnotation.addChild(velocityRootTrans)
        velocityRootAnnotation.addChild(velocityRootRotation)
        icon.position = velocityRootTrans
        icon.rotation = velocityRootRotation

        # Add the colour node
        velocityRootCol = coin.SoPackedColor()
        velocityRootCol.orderedRGBA.setValue(0xAAAA00ff)
        velocityRootAnnotation.addChild(velocityRootCol)

        # Set the constants for the arrow
        shaftWidth = 4
        shaftHeight = 12
        arrowWidth = 4
        arrowHeight = shaftWidth + arrowWidth

        # Shaft
        shaft = coin.SoSeparator()
        points = [[-shaftWidth, 0, -shaftWidth, shaftHeight],
            [-shaftWidth, shaftHeight, shaftWidth, shaftHeight],
            [shaftWidth, shaftHeight, shaftWidth, 0]]

        for point in points:
            startPoint = coin.SbVec3f(point[0], point[1], 0)
            endPoint = coin.SbVec3f(point[2], point[3], 0)
                
            line = coin.SoLineSet()
            vertices = coin.SoVertexProperty()
            vertices.vertex.set1Value(0, startPoint)
            vertices.vertex.set1Value(1, endPoint)
            line.vertexProperty = vertices
            shaft.addChild(line)     
        velocityRootAnnotation.addChild(shaft)

        # Arrow
        arrow = coin.SoSeparator()
        #points = [[-shaftWidth, 0, -shaftWidth - arrowWidth, 0],
        #    [-shaftWidth - arrowWidth, 0, 0, -arrowHeight],
        #    [0, -arrowHeight, shaftWidth + arrowWidth, 0],
        #    [shaftWidth + arrowWidth, 0, shaftWidth, 0]]

        #for point in points:
        #    startPoint = coin.SbVec3f(point[0], point[1], 0)
        #    endPoint = coin.SbVec3f(point[2], point[3], 0)
                
        #    line = coin.SoLineSet()
        #    vertices = coin.SoVertexProperty()
        #    vertices.vertex.set1Value(0, startPoint)
        #    vertices.vertex.set1Value(1, endPoint)
        #    line.vertexProperty = vertices
        #    arrow.addChild(line)     

        # Define vertices for the arrow shape
        vertices = coin.SoVertexProperty()
        vertices.vertex.setValues(0, [
            coin.SbVec3f(-shaftWidth, 0, 0),  # Bottom-left of the shaft
            coin.SbVec3f(shaftWidth, 0, 0),   # Bottom-right of the shaft
            coin.SbVec3f(shaftWidth, shaftHeight, 0),    # Top-right of the shaft
            coin.SbVec3f(-shaftWidth, shaftHeight, 0),   # Top-left of the shaft
            coin.SbVec3f(-shaftWidth - arrowWidth, 0, 0),    # Left corner of the arrowhead
            coin.SbVec3f(shaftWidth + arrowWidth, 0, 0),     # Right corner of the arrowhead
            coin.SbVec3f(0, -arrowHeight, 0) # Tip of the arrowhead
        ])

        # Define the faces using the vertices
        faces = coin.SoIndexedFaceSet()
        faces.coordIndex.setValues(0, [
            0, 1, 2, 3, -1,  # Shaft
            0, 4, 6, 5, -1   # Arrowhead
        ])

        # Add the color, vertices, and faces to the scene graph
        arrow.addChild(vertices)
        arrow.addChild(faces)

        velocityRootAnnotation.addChild(arrow)

        # Display the nodes
        sceneGraph.addChild(velocityRoot)

        return icon
    
    def planeIcon(sceneGraph, doc, obj):
        # Create a new icon object
        icon = InfoIcon()
        icon.document = doc
        icon.object = obj

        # Create the SoSeperator node for the rotation icon
        planeRoot = coin.SoSeparator()
        icon.root = planeRoot
        
        # Add a switch so this can be turned on or off
        planeRootSwitch = coin.SoSwitch()
        planeRootSwitch.whichChild.setValue(-3) # Enabled
        planeRoot.addChild(planeRootSwitch)
        icon.switch = planeRootSwitch

        # Create an annotation so that it is always visable
        planeRootAnnotation = coin.SoAnnotation()
        planeRootSwitch.addChild(planeRootAnnotation)

        # Add the translation and rotation nodes
        planeRootTrans = coin.SoTranslation()
        planeRootTrans.translation.setValue([0, 0, 0])
        planeRootRotation = coin.SoRotation()
        planeRootRotation.rotation.setValue(0, 0, 0, 1)

        planeRootAnnotation.addChild(planeRootTrans)
        planeRootAnnotation.addChild(planeRootRotation)
        icon.position = planeRootTrans
        icon.rotation = planeRootRotation
            
        col_pz = coin.SoPackedColor()
        col_pz.orderedRGBA.setValue(0x00ff007f)
        coords_pz = coin.SoCoordinate3()
        coords_pz.point.set1Value(0, -600, 20, 0.00001)
        coords_pz.point.set1Value(1, -600, -20, 0.00001)
        coords_pz.point.set1Value(2, 600, -20, 0.00001)
        coords_pz.point.set1Value(3, 600, 20, 0.00001)
        normals_pz = coin.SoNormal()
        normals_pz.vector.set1Value(0, (0, 0, 1))
        normals_pz.vector.set1Value(1, (0, 0, 1))
        normals_pz.vector.set1Value(2, (0, 0, 1))
        normals_pz.vector.set1Value(3, (0, 0, 1))
        shapeHints_pz = coin.SoShapeHints()
        shapeHints_pz.vertexOrdering.setValue(coin.SoShapeHints.COUNTERCLOCKWISE)
        shapeHints_pz.shapeType.setValue(coin.SoShapeHints.SOLID)
        plane_pz = coin.SoFaceSet()
        planeRootAnnotation.addChild(col_pz)
        planeRootAnnotation.addChild(coords_pz)
        planeRootAnnotation.addChild(normals_pz)
        planeRootAnnotation.addChild(shapeHints_pz)
        planeRootAnnotation.addChild(plane_pz)

        col_nz = coin.SoPackedColor()
        col_nz.orderedRGBA.setValue(0xff00007f)
        coords_nz = coin.SoCoordinate3()
        coords_nz.point.set1Value(0, 600, 20, -0.00001)
        coords_nz.point.set1Value(1, 600, -20, -0.00001)
        coords_nz.point.set1Value(2, -600, -20, -0.00001)
        coords_nz.point.set1Value(3, -600, 20, -0.00001)
        normals_nz = coin.SoNormal()
        normals_nz.vector.set1Value(0, (0, 0, -1))
        normals_nz.vector.set1Value(1, (0, 0, -1))
        normals_nz.vector.set1Value(2, (0, 0, -1))
        normals_nz.vector.set1Value(3, (0, 0, -1))
        shapeHints_nz = coin.SoShapeHints()
        shapeHints_nz.vertexOrdering.setValue(coin.SoShapeHints.COUNTERCLOCKWISE)
        shapeHints_nz.shapeType.setValue(coin.SoShapeHints.SOLID)
        plane_nz = coin.SoFaceSet()
        planeRootAnnotation.addChild(col_nz)
        planeRootAnnotation.addChild(coords_nz)
        planeRootAnnotation.addChild(normals_nz)
        planeRootAnnotation.addChild(shapeHints_nz)
        planeRootAnnotation.addChild(plane_nz)

        sceneGraph.addChild(planeRoot)

        return icon