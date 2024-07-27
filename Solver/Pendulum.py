import numpy as np
np.set_printoptions(edgeitems=10,linewidth=1800)
import pandas as pd
#import openpyxl

from scipy.integrate import solve_ivp

from DAPClasses.Body import DAPBody
from DAPClasses.Joint import DAPJoint

#############
#############
# Vector function
def dapvec(x, y):
    return np.array([[x], [y]])

body0 = DAPBody('ground', 0, 0)
body0.parameters(dapvec(0, 0), 0)
body0.points = [dapvec(0, 0)]

body1 = DAPBody('pendulum', 0.80628, 0.0683180128)
body1.parameters(dapvec(0.5, 0), 0)
body1.points = [dapvec(-0.5, 0), dapvec(0.5, 0)]

solverBodies = [body0, body1]

jointO = DAPJoint('revolute')
jointO.parameters(0, 0, 1, 0)

solverJoints = [jointO]

from Solver import Solver
Solver(solverBodies, solverJoints, __file__.split('\\')[-1][0:-3], limit=[(-1.2, 1.2), (-1.2, 0.2)])