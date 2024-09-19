import numpy as np
np.set_printoptions(edgeitems=10,linewidth=1800)
import pandas as pd
#import openpyxl

from scipy.integrate import solve_ivp

class DAPBody:
    def __init__(self, name, mass, inertia):
        self.name = name
        self.mass = mass
        self.inertia = inertia
        self.position = []
        self.angle = 0
        self.points = []

    def parameters(self, position, angle):
        self.position = position
        self.position_d = dapvec(0, 0)
        self.position_dd = dapvec(0, 0)
        self.angle = angle
        self.angle_d = 0
        self.angle_dd = 0

    def getPoints(self):
        # Convert points to 2x1 column vectors
        return np.hstack([point for point in self.points]).T

class DAPJoint:
    def __init__(self, joint_type):
        self.joint_type = joint_type
    def parameters(self, bodyI, pointI, bodyJ, pointJ):
        self.body_i = bodyI
        self.point_i = pointI
        self.body_j = bodyJ
        self.point_j = pointJ

#############
#############
# Vector function
def dapvec(x, y):
    return np.array([[x], [y]])

body0 = DAPBody('ground', 0, 0)
body0.parameters(dapvec(0, 0), 0)
body0.points = [dapvec(0, 0)]

body1 = DAPBody('First', 0.88099, 0.0259291853)
body1.parameters(dapvec(-0.293373894, 0), 0)
body1.points = [dapvec(-0.3, 0), dapvec(0.3, 0)]

body2 = DAPBody('Second', 0.88099, 0.0259291853)
body2.parameters(dapvec(-0.293373894 - 0.6, 0), 0)
body2.points = [dapvec(0.3, 0), dapvec(-0.3, 0)]

solverBodies = [body0, body1, body2]

jointO = DAPJoint('revolute')
jointO.parameters(0, 0, 1, 1)

jointA = DAPJoint('revolute')
jointA.parameters(1, 0, 2, 0)

solverJoints = [jointO, jointA]

from Solver import Solver
Solver(solverBodies, solverJoints, __file__.split('\\')[-1][0:-3], limit=[(-1.8, 1.8), (-1.8, 0.2)])