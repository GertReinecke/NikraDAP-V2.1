# Class definition for the DAPBody

class DAPJoint:
    def __init__(self):
        # Speficy the type of joint
        self.JointType = 'Revolute'

        # The type of driver constraint
        self.FunctType = -1

        # The number of constraints
        self.mConstraints = -1

        # The number of moving bodies
        self.nMovBodies = -1

        self.fixDof = False

        self.body_I_Index = -1
        self.point_I_i_Index = -1
        self.point_I_j_Index = -1

        self.body_J_Index = -1
        self.point_J_i_Index = -1
        self.point_J_j_Index = -1

        self.phi0 = 0.0

        self.rowStart = -1
        self.rowEnd = -1