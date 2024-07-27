# Class definition for the DAPBody

class DAPBody:
    def __init__(self):
        self.mass = 0
        self.inertia = 0

        self.phiDot = 0

        # List of Vectors, relative to CoG, in local coordinates (x, y, z)
        self.pointLocals = []

        # Vector, position of the body, (x, y, z)
        self.centreOfGravity = 0

        # Body LCS relative to origin
        # Is a base.placement
        self.world = None

        self.worldDot = 0

        # Vector, direction of gravity in local coordinates, (x, y, z)
        self.weightVector = None