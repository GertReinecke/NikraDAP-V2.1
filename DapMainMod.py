import FreeCAD
import FreeCADGui

import os
import numpy as np
from scipy.integrate import solve_ivp
import math
import PySide

import DapToolsMod as DT
import DapFunctionMod

Debug = False

#  -------------------------------------------------------------------------
class DapMainC:
    """Instantiated when the 'solve' button is clicked in the task panel"""
    #  -------------------------------------------------------------------------
    def __init__(self, simEnd, simDelta, Accuracy, correctInitial):
        if Debug:
            DT.Mess("DapMainClass-__init__")

        # Save the parameters passed via the __init__ function
        self.simEnd = simEnd
        self.simDelta = simDelta
        self.correctInitial = correctInitial

        # Store the required accuracy figures
        self.relativeTolerance = 10**(-Accuracy-2)
        self.absoluteTolerance = 10**(-Accuracy-4)

        print("self.relativeTolerance", self.relativeTolerance)
        print("self.absoluteTolerance", self.absoluteTolerance)

        # Counter of function evaluations
        self.Counter = 0

        # We will need the solver object as well
        self.solverObj = FreeCAD.ActiveDocument.findObjects(Name="^DapSolver$")[0]
        
        # Set a variable to flag whether we have reached the end error-free
        # It will be available to DapSolverMod as an instance variable
        self.initialised = False

        # Dictionary of the pointers for Dynamic calling of the Acceleration functions
        self.dictAccelerationFunctions = {
            0: self.Revolute_Acc
        }
        # Dictionary of the pointers for Dynamic calling of the constraint functions
        self.dictconstraintFunctions = {
            0: self.Revolute_constraint
        }
        # Dictionary of the pointers for Dynamic calling of the Jacobian functions
        self.dictJacobianFunctions = {
            0: self.Revolute_Jacobian
        }

        # Convert joint object Dictionary to Joint Object List to ensure being ordered
        jointObjDict = DT.getDictionary("DapJoint")
        self.jointObjList = []
        for jointName in jointObjDict:
            self.jointObjList.append(jointObjDict[jointName])
        self.numJoints = len(self.jointObjList)
        # Tag each joint with its number so we know which one we are looking at later
        for jointNum in range(self.numJoints):
            self.jointObjList[jointNum].JointNumber = jointNum

        # Convert force object Dictionary to a Force Object List to ensure being ordered
        forceObjDict = DT.getDictionary("DapForce")
        self.forceObjList = []
        for forceName in forceObjDict:
            self.forceObjList.append(forceObjDict[forceName])
        self.numForces = len(self.forceObjList)

        # Convert body object Dictionary to a Body List to ensure being ordered
        bodyObjDict = DT.getDictionary("DapBody")
        self.bodyObjList = []
        # Get the dictionary of dictionary of Points
        # i.e. {<body name> : {<point name> : <its index in the body object's list of points>}}
        DictionaryOfPoints = DT.getDictionaryOfBodyPoints()
        # Convert to a list of point dictionaries at the same index as its parent body object
        self.pointDictList = []
        bodyIndex = 0
        for bodyName in bodyObjDict:
            self.bodyObjList.append(bodyObjDict[bodyName])
            self.pointDictList.append(DictionaryOfPoints[bodyName])
            # Make sure all indices point to the correct body in case a body
            # has been subsequently deleted after joint/force definition
            # This is done by matching the index to the Body Name
            self.cleanUpIndices(bodyName, bodyIndex)
            bodyIndex += 1
        self.numBodies = bodyIndex
        self.numMovBodiesx3 = (self.numBodies-1) * 3

        # Remove any non-existent body names which are still around
        # in case a body has been deleted after joint/force definition
        self.clearZombieBodies(bodyObjDict)

        # Get the plane normal rotation matrix from the main DAP container
        # This will rotate all the coordinates in the model, to be in the X-Y plane
        xyzToXYRotation = FreeCAD.Rotation(FreeCAD.Vector(0.0, 0.0, 1.0), DT.getActiveContainerObject().movementPlaneNormal)

        # Find the global maximum number of points in any of the bodies
        # We will need this so we can initialise large enough NumPy arrays
        maxNumberPoints = 0
        for bodyIndex in range(self.numBodies):
            if maxNumberPoints < len(self.pointDictList[bodyIndex]):
                maxNumberPoints = len(self.pointDictList[bodyIndex])
        # Initialise the size of all the NumPy arrays and fill with zeros
        self.initNumPyArrays(maxNumberPoints)

        # Transfer all the 3D stuff into the NumPy arrays while doing the projection onto the X-Y plane
        for bodyIndex in range(self.numBodies):
            bodyObj = self.bodyObjList[bodyIndex]
            # Bring the body Mass, CoG, MoI and Weight up-to-date
            # It was already calculated after the Materials definition
            # but do it again, just in case something has changed since
            DT.computeCoGAndMomentInertia(bodyObj)
            # All Mass and moment of inertia stuff
            self.MassNp[bodyIndex] = bodyObj.Mass
            self.momentInertiaNp[bodyIndex] = bodyObj.momentInertia
            npVec = DT.CADVecToNumPyF(xyzToXYRotation.toMatrix().multVec(bodyObj.weightVector))
            self.WeightNp[bodyIndex] = npVec

            # Change the local vectors to be relative to the CoG, rather than the body origin
            # The CoG in world coordinates are the world coordinates of the body
            # All points in the body are relative to this point

            # World
            CoG = xyzToXYRotation.toMatrix().multVec(bodyObj.centreOfGravity)
            npCoG = DT.CADVecToNumPyF(CoG)
            self.worldNp[bodyIndex, 0:2] = npCoG
            self.worldRotNp[bodyIndex, 0:2] = DT.Rot90NumPy(npCoG.copy())
            # WorldDot
            npWorldDot = DT.CADVecToNumPyF(xyzToXYRotation.toMatrix().multVec(bodyObj.worldDot))
            self.worldDotNp[bodyIndex, 0:2] = npWorldDot
            self.worldDotRotNp[bodyIndex, 0:2] = DT.Rot90NumPy(npWorldDot.copy())
            # WorldDotDot
            self.worldDotDotNp[bodyIndex, 0:2] = np.zeros((1, 2))

            # Transform the points from model Placement to World X-Y plane relative to the CoG
            vectorsRelativeCoG = bodyObj.pointLocals.copy()
            for localIndex in range(len(vectorsRelativeCoG)):
                vectorsRelativeCoG[localIndex] = xyzToXYRotation.toMatrix(). \
                    multiply(bodyObj.world.toMatrix()). \
                    multVec(vectorsRelativeCoG[localIndex]) - CoG

            # Take some trouble to make phi as nice an angle as possible
            # Because the user will maybe use it manually later and will appreciate more simplicity
            if bodyIndex == 0:
                self.phiNp[bodyIndex] = 0.0
            else:
                self.phiNp[bodyIndex] = DT.nicePhiPlease(vectorsRelativeCoG)

            # The phiDot axis vector is by definition perpendicular to the movement plane,
            # so we don't have to do any rotating from the phiDot value set in bodyObj
            self.phiDotNp[bodyIndex] = bodyObj.phiDot

            # We will now calculate the rotation matrix and use it to find the coordinates of the points
            self.RotMatPhiNp[bodyIndex] = DT.RotationMatrixNp(self.phiNp[bodyIndex])
            if Debug:
                DT.Np2D(vectorsRelativeCoG)
            for pointIndex in range(len(vectorsRelativeCoG)):
                # Point Local - vector from module body CoG to the point, in body LCS coordinates
                # [This is what we needed phi for, to fix the orientation of the body]
                npVec = DT.CADVecToNumPyF(vectorsRelativeCoG[pointIndex])
                self.pointXiEtaNp[bodyIndex, pointIndex, 0:2] = npVec @ self.RotMatPhiNp[bodyIndex]
                # Point Vector - vector from body CoG to the point in world coordinates
                self.pointXYrelCoGNp[bodyIndex, pointIndex, 0:2] = npVec
                self.pointXYrelCoGrotNp[bodyIndex][pointIndex] = DT.Rot90NumPy(npVec.copy())
                # Point Vector Dot
                self.pointXYrelCoGdotNp[bodyIndex][pointIndex] = np.zeros((1, 2))
                # Point World - coordinates of the point relative to the system origin - in world coordinates
                npVec += npCoG
                self.pointXYWorldNp[bodyIndex, pointIndex] = npVec
                self.pointWorldRotNp[bodyIndex, pointIndex] = DT.Rot90NumPy(npVec.copy())
                # Point World Dot
                self.pointWorldDotNp[bodyIndex][pointIndex] = np.zeros((1, 2))
            # Next pointIndex
        # Next bodyIndex

        # Print out what we have calculated for debugging
        if True:
            DT.Mess("Point Dictionary: ")
            for bodyIndex in range(self.numBodies):
                DT.Mess(self.pointDictList[bodyIndex])
            DT.Mess("Mass: [g]")
            DT.Np1D(True, self.MassNp * 1.0e3)
            DT.Mess("")
            DT.Mess("Mass: [kg]")
            DT.Np1D(True, self.MassNp)
            DT.Mess("")
            DT.Mess("Weight Vector: [kg mm /s^2 = mN]")
            DT.Np2D(self.WeightNp)
            DT.Mess("")
            DT.Mess("MomentInertia: [kg.mm^2]")
            DT.Mess(self.momentInertiaNp)
            DT.Mess("")
            DT.Mess("Forces: [kg.mm/s^2 = mN]")
            DT.Np2D(self.sumForcesNp)
            DT.Mess("")
            DT.Mess("Moments: [N.mm]")
            DT.Np1D(True, self.sumMomentsNp)
            DT.Mess("")
            DT.Mess("World [CoG]: [mm]")
            DT.Np2D(self.worldNp)
            DT.Mess("")
            DT.Mess("WorldDot: [mm/s]")
            DT.Np2D(self.worldDotNp)
            DT.Mess("")
            DT.MessNoLF("phi: [deg]")
            DT.Np1Ddeg(True, self.phiNp)
            DT.Mess("")
            DT.MessNoLF("phi: [rad]")
            DT.Np1D(True, self.phiNp)
            DT.Mess("")
            DT.MessNoLF("phiDot: [deg/sec]")
            DT.Np1Ddeg(True, self.phiDotNp)
            DT.Mess("")
            DT.MessNoLF("phiDot: [rad/sec]")
            DT.Np1D(True, self.phiDotNp)
            DT.Mess("")
            DT.MessNoLF("Number of Points: ")
            DT.Mess(len(self.pointDictList[bodyIndex]))
            DT.Mess("")
            DT.Mess("PointLocal: [mm]")
            DT.Np3D(self.pointXiEtaNp)
            DT.Mess("")
            DT.Mess("PointVector: [mm]")
            DT.Np3D(self.pointXYrelCoGNp)
            DT.Mess("")
            DT.Mess("PointWorld: [mm]")
            DT.Np3D(self.pointXYWorldNp)
            DT.Mess("")

        # Make an array with the respective body Mass and moment of inertia
        # do not add the body=0 to the list because it is ground
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        # % Mass (inertia) matrix as an array
        #    M_array = zeros(nB3,1); M_inv_array = zeros(nB3,1);
        #    for Bi = 1:nB
        #        is = 3*(Bi - 1) + 1;
        #        ie = is + 2;
        #        M_array(is:ie,1) = [Bodies(Bi).m; Bodies(Bi).m; Bodies(Bi).J];
        #        M_inv_array(is:ie,1) = [Bodies(Bi).m_inv; Bodies(Bi).m_inv; Bodies(Bi).J_inv];
        #    end
        # ==================================
        self.massArrayNp = np.zeros(self.numMovBodiesx3)
        for index in range(1, self.numBodies):
            bodyObj = self.bodyObjList[index]
            self.massArrayNp[(index-1)*3:index*3] = bodyObj.Mass, bodyObj.Mass, bodyObj.momentInertia

        # Transfer the joint unit vector coordinates to the NumPy arrays
        for jointIndex in range(self.numJoints):
            jointObj = self.jointObjList[jointIndex]
            # Unit vector on body I in body local coordinates
            self.jointUnit_I_XiEtaNp[jointIndex] = DT.NormalizeNpVec(self.pointXiEtaNp[jointObj.body_I_Index, jointObj.point_I_j_Index] -
                                                                     self.pointXiEtaNp[jointObj.body_I_Index, jointObj.point_I_i_Index])
            # Unit vector on body I in world coordinates
            self.jointUnit_I_WorldNp[jointIndex] = DT.NormalizeNpVec(self.pointXYWorldNp[jointObj.body_I_Index, jointObj.point_I_j_Index] -
                                                                     self.pointXYWorldNp[jointObj.body_I_Index, jointObj.point_I_i_Index])
            self.jointUnit_I_WorldRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_I_WorldNp[jointIndex].copy())
            self.jointUnit_I_WorldDotNp[jointIndex] = DT.NormalizeNpVec(self.pointWorldDotNp[jointObj.body_I_Index, jointObj.point_I_j_Index] -
                                                                        self.pointWorldDotNp[jointObj.body_I_Index, jointObj.point_I_i_Index])
            self.jointUnit_I_WorldDotRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_I_WorldDotNp[jointIndex].copy())
    
            # Unit vector on body J in body local coordinates
            self.jointUnit_J_XiEtaNp[jointIndex] = DT.NormalizeNpVec(self.pointXiEtaNp[jointObj.body_J_Index, jointObj.point_J_j_Index] -
                                                                     self.pointXiEtaNp[jointObj.body_J_Index, jointObj.point_J_i_Index])
            # Unit vector on body J in world coordinates
            self.jointUnit_J_WorldNp[jointIndex] = DT.NormalizeNpVec(self.pointXYWorldNp[jointObj.body_J_Index, jointObj.point_J_j_Index] -
                                                                     self.pointXYWorldNp[jointObj.body_J_Index, jointObj.point_J_i_Index])
            self.jointUnit_J_WorldRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_J_WorldNp[jointIndex].copy())
            self.jointUnit_J_WorldDotNp[jointIndex] = DT.NormalizeNpVec(self.pointWorldDotNp[jointObj.body_J_Index, jointObj.point_J_j_Index] -
                                                                        self.pointWorldDotNp[jointObj.body_J_Index, jointObj.point_J_i_Index])
            self.jointUnit_J_WorldDotRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_J_WorldDotNp[jointIndex].copy())

            # Find the length of the link between the first point on each body - signed scalar
            unitPinInSlot = self.pointXYWorldNp[jointObj.body_I_Index, jointObj.point_I_i_Index] - \
                            self.pointXYWorldNp[jointObj.body_J_Index, jointObj.point_J_i_Index]
            length = np.sqrt(unitPinInSlot[0]**2 + unitPinInSlot[1]**2)
            dotProduct = self.jointUnit_I_WorldNp[jointIndex].dot(unitPinInSlot)
            if dotProduct < 0.0:
                jointObj.lengthLink = -length
            else:
                jointObj.lengthLink = length

        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        # % Unit vectors
        #   nU = length(Uvectors);
        #    for Vi = 1:nU
        #        if Uvectors(Vi).Bindex == 0
        #            Uvectors(Vi).u = Uvectors(Vi).ulocal;
        #            Uvectors(Vi).u_r = s_rot(Uvectors(Vi).u);
        #        end
        #    end
        # ==================================
        for jointIndex in range(self.numJoints):
            jointObj = self.jointObjList[jointIndex]
            # If the body is attached to ground then its unit vector local coordinates are world coordinates
            if jointObj.body_I_Index == 0:
                self.jointUnit_I_WorldNp[jointIndex] = self.jointUnit_I_XiEtaNp[jointIndex]
                self.jointUnit_I_WorldRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_I_WorldNp[jointIndex].copy())
            if jointObj.body_J_Index == 0:
                self.jointUnit_J_WorldNp[jointIndex] = self.jointUnit_J_XiEtaNp[jointIndex]
                self.jointUnit_J_WorldRotNp[jointIndex] = DT.Rot90NumPy(self.jointUnit_J_WorldNp[jointIndex].copy())

        # Assign number of constraint and number of bodies to each defined joint according to its type
        for jointObj in self.jointObjList:
            if jointObj.JointType == DT.JOINT_TYPE_DICTIONARY["Revolute"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'rev'};
                #            Joints(Ji).mrows = 2;
                #            Joints(Ji).nbody = 2;
                #            Pi = Joints(Ji).iPindex;
                #            Pj = Joints(Ji).jPindex;
                #            Bi = Points(Pi).Bindex;
                #            Joints(Ji).iBindex = Bi;
                #            Bj = Points(Pj).Bindex;
                #            Joints(Ji).jBindex = Bj;
                #            if Joints(Ji).fix == 1
                #                Joints(Ji).mrows = 3;
                #                if Bi == 0
                #                    Joints(Ji).p0 = -Bodies(Bj).p;
                #                elseif Bj == 0
                #                    Joints(Ji).p0 = Bodies(Bi).p;
                #                else
                #                    Joints(Ji).p0 = Bodies(Bi).p - Bodies(Bj).p;
                #                end
                #            end
                # ==================================
                if jointObj.FunctType == -1:
                    jointObj.mConstraints = 2
                    jointObj.nMovBodies = 2
                    if jointObj.fixDof is True:
                        jointObj.mConstraints = 3
                        # Set the initial angle phi0 and handle the case where one is attached to ground
                        if jointObj.body_I_Index == 0:
                            jointObj.phi0 = -self.phiNp[jointObj.body_J_Index]
                        elif jointObj.body_J_Index == 0:
                            jointObj.phi0 = self.phiNp[jointObj.body_I_Index]
                        else:
                            jointObj.phi0 = self.phiNp[jointObj.body_I_Index] - self.phiNp[jointObj.body_J_Index]
                else:
                    # ==================================
                    # Matlab Code from Nikravesh: DAP_BC
                    # ==================================
                    #        case {'rel-rot'}                                       % revised August 2022
                    #            Joints(Ji).mrows = 1; Joints(Ji).nbody = 1;        % revised August 2022
                    # ==================================
                    jointObj.mConstraints = 1
                    jointObj.nMovBodies = 1
            else:
                FreeCAD.Console.PrintError("Unknown Joint Type - this should never occur"+str(jointObj.JointType)+"\n")
        # Next Joint Object

        # Run through the joints and find if any of them use a driver function
        # if so, then initialize the parameters for the driver function routine
        self.driverObjDict = {}
        for jointObj in self.jointObjList:
            # If there is a driver function, then
            # store an instance of the class in driverObjDict and initialize its parameters
            if jointObj.FunctType != -1:
                self.driverObjDict[jointObj.Name] = DapFunctionMod.FunctionC(
                    [jointObj.FunctType,
                     jointObj.startTimeDriveFunc, jointObj.endTimeDriveFunc,
                     jointObj.startValueDriveFunc, jointObj.endValueDriveFunc,
                     jointObj.endDerivativeDriveFunc,
                     jointObj.Coeff0, jointObj.Coeff1, jointObj.Coeff2, jointObj.Coeff3, jointObj.Coeff4, jointObj.Coeff5]
                )

        # Add up all the numbers of constraints and allocate row start and end pointers
        self.numConstraints = 0
        for jointObj in self.jointObjList:
            jointObj.rowStart = self.numConstraints
            jointObj.rowEnd = self.numConstraints + jointObj.mConstraints
            self.numConstraints = jointObj.rowEnd

        # Return with a flag to show we have reached the end of init error-free
        self.initialised = True
    #  -------------------------------------------------------------------------
    def MainSolve(self):
        if self.numConstraints != 0 and self.correctInitial:
            # Correct for initial conditions consistency
            if self.correctInitialConditions() is False:
                FreeCAD.Console.PrintError("Initial Conditions not successfully calculated")
                return

        # Determine any redundancy between constraints
        Jacobian = self.GetJacobianF()
        if True:
            DT.Mess("Jacobian calculated to determine rank of solution")
            DT.Np2D(Jacobian)
        redundant = np.linalg.matrix_rank(Jacobian)
        if redundant < self.numConstraints:
            FreeCAD.Console.PrintError('The constraints exhibit Redundancy\n')
            return

        # Velocity correction
        velCorrArrayNp = np.zeros((self.numMovBodiesx3,), dtype=np.float64)
        # Move velocities to the corrections array
        for bodyIndex in range(1, self.numBodies):
            velCorrArrayNp[(bodyIndex-1) * 3: bodyIndex*3] = \
                self.worldDotNp[bodyIndex, 0], \
                self.worldDotNp[bodyIndex, 1], \
                self.phiDotNp[bodyIndex]
        # Solve for velocity at time = 0
        # Unless the joint is Driven-Revolute or Driven-Translational
        # RHSVel = [0,0,...]   (i.e. a list of zeros)
        solution = np.linalg.solve(Jacobian @ Jacobian.T, (Jacobian @ velCorrArrayNp) - self.RHSVel(0))
        deltaVel = -Jacobian.T @ solution
        if True:
            DT.MessNoLF("Velocity Correction Array: ")
            DT.Np1D(True, velCorrArrayNp)
            DT.MessNoLF("Velocity Correction Solution: ")
            DT.Np1D(True, solution)
            DT.MessNoLF("Delta velocity: ")
            DT.Np1D(True, deltaVel)
        # Move corrected velocities back into the system
        for bodyIndex in range(1, self.numBodies):
            self.worldDotNp[bodyIndex, 0] += deltaVel[(bodyIndex-1)*3]
            self.worldDotNp[bodyIndex, 1] += deltaVel[(bodyIndex-1)*3+1]
            self.phiDotNp[bodyIndex] += deltaVel[(bodyIndex-1)*3+2]
        # Report corrected coordinates and velocities
        if Debug:
            DT.Mess("Corrected Positions: [mm]")
            DT.Np2D(self.worldNp)
            DT.Np1Ddeg(True, self.phiNp)
            DT.Mess("Corrected Velocities [mm/s]")
            DT.Np2D(self.worldDotNp)
            DT.Np1Ddeg(True, self.phiDotNp)

        ##############################
        # START OF THE SOLUTION PROPER
        ##############################
        # Pack coordinates and velocities into the NumPy uArray
        uArray = np.zeros((self.numMovBodiesx3 * 2,), dtype=np.float64)
        index1 = 0
        index2 = self.numMovBodiesx3
        for bodyIndex in range(1, self.numBodies):
            uArray[index1:index1+2] = self.worldNp[bodyIndex]
            uArray[index1+2] = self.phiNp[bodyIndex]
            uArray[index2:index2+2] = self.worldDotNp[bodyIndex]
            uArray[index2+2] = self.phiDotNp[bodyIndex]
            index1 += 3
            index2 += 3
        if Debug:
            DT.Mess("uArray:")
            DT.Np1D(True, uArray)
        # Set up the list of time intervals over which to integrate
        self.Tspan = np.arange(0.0, self.simEnd, self.simDelta)

        # ###################################################################################
        # Matrix Integration Function
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
        # ###################################################################################
        # scipy.integrate.solve_ivp
        # INPUTS:
        #       fun,                      Function name
        #       t_span,                   (startTime, endTime)
        #       y0,                       Initial values array [uArray]
        #       method='RK45',            RK45 | RK23 | DOP853 | Radau | BDF | LSODA
        #       t_eval=None,              times to evaluate at
        #       dense_output=False,       continuous solution or not
        #       events=None,              events to track
        #       vectorized=False,         whether fun is vectorized (i.e. parallelized)
        #       args=None,
        #       first_step=None,          none means algorithm chooses
        #       max_step=inf,             default is inf
        #       rtol=1e-3, atol=1e-6      relative and absolute tolerances
        #       jacobian,                 required for Radau, BDF and LSODA
        #       jac_sparsity=None,        to help algorithm when it is sparse
        #       lband=inf, uband=inf,     lower and upper bandwidth of Jacobian
        #       min_step=0                minimum step (required for LSODA)
        # RETURNS:
        #       t                         time array
        #       y                         values array
        #       sol                       instance of ODESolution (when dense_output=True)
        #       t_events                  array of event times
        #       y_events                  array of values at the event_times
        #       nfev                      number of times the rhs was evaluated
        #       njev                      number of times the Jacobian was evaluated
        #       nlu                       number of LU decompositions
        #       status                    -1 integration step failure | +1 termination event | 0 Successful
        #       message                   Human readable error message
        #       success                   True if 0 or +1 above
        # ###################################################################################

        # Solve the equations: <analysis function> (<start time>, <end time>) <pos & vel array> <times at which to evaluate>
        solution = solve_ivp(self.Analysis,
                             (0.0, self.simEnd),
                             uArray,
                             t_eval=self.Tspan,
                             rtol=self.relativeTolerance,
                             atol=self.absoluteTolerance)

        # Output the positions/angles results file
        self.PosFILE = open(os.path.join(self.solverObj.Directory, "DapAnimation.csv"), 'w')
        Sol = solution.y.T
        for tick in range(len(solution.t)):
            self.PosFILE.write(str(solution.t[tick])+" ")
            for body in range(self.numBodies-1):
                self.PosFILE.write(str(Sol[tick, body * 3]) + " ")
                self.PosFILE.write(str(Sol[tick, body * 3 + 1]) + " ")
                self.PosFILE.write(str(Sol[tick, body * 3 + 2]) + " ")
            self.PosFILE.write("\n")
        self.PosFILE.close()

        # Save the most important stuff into the solver object
        BodyNames = []
        BodyCoG = []
        for bodyIndex in range(1, len(self.bodyObjList)):
            BodyNames.append(self.bodyObjList[bodyIndex].Name)
            BodyCoG.append(self.bodyObjList[bodyIndex].centreOfGravity)
        self.solverObj.BodyNames = BodyNames
        self.solverObj.BodyCoG = BodyCoG
        self.solverObj.DeltaTime = self.simDelta
        # Flag that the results are valid
        self.solverObj.DapResultsValid = True

        if self.solverObj.FileName != "-":
            self.outputResults(solution.t, solution.y.T)
    ##########################################
    #   This is the end of the actual solution
    #    The rest are all called subroutines
    ##########################################
    #  -------------------------------------------------------------------------
    def Analysis(self, tick, uArray):
        """The Analysis function which takes a
        uArray consisting of a world 3vector and a velocity 3vector"""
        if Debug:
            DT.Mess("Input to 'Analysis'")
            DT.Np1D(True, uArray)

        # Unpack uArray into world coordinate and world velocity sub-arrays
        index1 = 0
        index2 = self.numMovBodiesx3
        for bodyIndex in range(1, self.numBodies):
            self.worldNp[bodyIndex, 0] = uArray[index1]
            self.worldNp[bodyIndex, 1] = uArray[index1+1]
            self.phiNp[bodyIndex] = uArray[index1+2]
            self.worldDotNp[bodyIndex, 0] = uArray[index2]
            self.worldDotNp[bodyIndex, 1] = uArray[index2+1]
            self.phiDotNp[bodyIndex] = uArray[index2+2]
            index1 += 3
            index2 += 3
        if Debug:
            DT.Np2D(self.worldNp)
            DT.Np1Ddeg(True, self.phiNp)
            DT.Np2D(self.worldDotNp)
            DT.Np1Ddeg(True, self.phiDotNp)

        # Update the point stuff accordingly
        self.updatePointPositions()
        self.updatePointVelocities()

        # array of applied forces
        self.makeForceArray()
        # find the accelerations ( a = F / m )
        accel = []
        if self.numConstraints == 0:
            for index in range(self.numMovBodiesx3):
                accel.append = self.massInvArray[index] * self.forceArrayNp[index]
        # We go through this if we have any constraints
        else:
            Jacobian = self.GetJacobianF()
            if Debug:
                DT.Mess("Jacobian")
                DT.Np2D(Jacobian)

            # Create the Jacobian-Mass-Jacobian matrix
            # [ diagonal masses ---- Jacobian transpose ]
            # [    |                        |           ]
            # [  Jacobian      ------     Zeros         ]
            numBodPlusConstr = self.numMovBodiesx3 + self.numConstraints
            JacMasJac = np.zeros((numBodPlusConstr, numBodPlusConstr), dtype=np.float64)
            JacMasJac[0: self.numMovBodiesx3, 0: self.numMovBodiesx3] = np.diag(self.massArrayNp)
            JacMasJac[self.numMovBodiesx3:, 0: self.numMovBodiesx3] = Jacobian
            JacMasJac[0: self.numMovBodiesx3, self.numMovBodiesx3:] = -Jacobian.T
            if Debug:
                DT.Mess("Jacobian-MassDiagonal-JacobianT Array")
                DT.Np2D(JacMasJac)

            # get r-h-s of acceleration constraints at this time
            rhsAccel = self.RHSAcc(tick)
            if Debug:
                DT.Mess("rhsAccel")
                DT.Np1D(True, rhsAccel)
            # Combine Force Array and rhs of Acceleration constraints into one array
            rhs = np.zeros((numBodPlusConstr,), dtype=np.float64)
            rhs[0: self.numMovBodiesx3] = self.forceArrayNp
            rhs[self.numMovBodiesx3:] = rhsAccel
            if Debug:
                DT.Mess("rhs")
                DT.Np1D(True, rhs)
            # Solve the JacMasJac augmented with the rhs
            solvedVector = np.linalg.solve(JacMasJac, rhs)
            # First half of solution are the acceleration values
            accel = solvedVector[: self.numMovBodiesx3]
            # Second half is Lambda which is reported in the output results routine
            self.Lambda = solvedVector[self.numMovBodiesx3:]
            if Debug:
                DT.MessNoLF("Accelerations: ")
                DT.Np1D(True, accel)
            if True:
                DT.MessNoLF("Lambda: ")
                DT.Np1D(True, self.Lambda)

        # Transfer the accelerations back into the worldDotDot/phiDotDot and uDot/uDotDot Arrays
        for bodyIndex in range(1, self.numBodies):
            accelIndex = (bodyIndex-1)*3
            self.worldDotDotNp[bodyIndex] = accel[accelIndex], accel[accelIndex+1]
            self.phiDotDotNp[bodyIndex] = accel[accelIndex+2]
        uDotArray = np.zeros((self.numMovBodiesx3 * 2), dtype=np.float64)
        index1 = 0
        index2 = self.numMovBodiesx3
        for bodyIndex in range(1, self.numBodies):
            uDotArray[index1:index1+2] = self.worldDotNp[bodyIndex]
            uDotArray[index1+2] = self.phiDotNp[bodyIndex]
            uDotArray[index2:index2+2] = self.worldDotDotNp[bodyIndex]
            uDotArray[index2+2] = self.phiDotDotNp[bodyIndex]
            index1 += 3
            index2 += 3

        # Increment number of function evaluations
        self.Counter += 1

        return uDotArray
    #  -------------------------------------------------------------------------
    def correctInitialConditions(self):
        """This function corrects the supplied initial conditions by making
        the body coordinates and velocities consistent with the constraints"""
        if Debug:
            DT.Mess("DapMainMod-correctInitialConditions")
        # Try Newton-Raphson iteration for n up to 20
        for n in range(20):
            # Update the points positions
            self.updatePointPositions()

            # Evaluate Deltaconstraint of the constraints at time=0
            Deltaconstraints = self.GetconstraintsF(0)
            if Debug:
                DT.Mess("Delta constraints Result:")
                DT.Np1D(True, Deltaconstraints)
                
            # Evaluate Jacobian
            Jacobian = self.GetJacobianF()
            if Debug:
                DT.Mess("Jacobian:")
                DT.Np2D(Jacobian)

            # Determine any redundancy between constraints
            redundant = np.linalg.matrix_rank(Jacobian) 
            if redundant < self.numConstraints:
                FreeCAD.Console.PrintError('The constraints exhibit Redundancy\n')
                return False

            # We have successfully converged if the ||Deltaconstraint|| is very small
            DeltaconstraintLengthSq = 0
            for index in range(self.numConstraints):
                DeltaconstraintLengthSq += Deltaconstraints[index] ** 2
            if Debug:
                DT.Mess("Total constraint Error: " + str(math.sqrt(DeltaconstraintLengthSq)))
            if DeltaconstraintLengthSq < 1.0e-16:
                return True

            # Solve for the new corrections
            solution = np.linalg.solve(Jacobian @ Jacobian.T, Deltaconstraints)
            delta = - Jacobian.T @ solution
            # Correct the estimates
            for bodyIndex in range(1, self.numBodies):
                self.worldNp[bodyIndex, 0] += delta[(bodyIndex-1)*3]
                self.worldNp[bodyIndex, 1] += delta[(bodyIndex-1)*3+1]
                self.phiNp[bodyIndex] += delta[(bodyIndex-1)*3+2]
                
        FreeCAD.Console.PrintError("Newton-Raphson Correction failed to converge\n\n")
        return False
    #  -------------------------------------------------------------------------
    def updatePointPositions(self):
        for bodyIndex in range(1, self.numBodies):
            # Compute the Rotation Matrix
            self.RotMatPhiNp[bodyIndex] = DT.RotationMatrixNp(self.phiNp[bodyIndex])

            if Debug:
                DT.MessNoLF("In Xi-Eta Coordinates           ")
                DT.MessNoLF("Relative to CoG                 ")
                DT.MessNoLF("Relative to CoG Rotated 90      ")
                DT.Mess("World Coordinates               ")
            for pointIndex in range(len(self.pointDictList[bodyIndex])):
                pointVector = self.RotMatPhiNp[bodyIndex] @ self.pointXiEtaNp[bodyIndex, pointIndex]
                self.pointXYrelCoGNp[bodyIndex, pointIndex] = pointVector
                self.pointXYWorldNp[bodyIndex, pointIndex] = self.worldNp[bodyIndex] + pointVector
                self.pointXYrelCoGrotNp[bodyIndex][pointIndex] = DT.Rot90NumPy(pointVector)
                if Debug:
                    DT.Np1D(False, self.pointXiEtaNp[bodyIndex][pointIndex])
                    DT.MessNoLF("   ")
                    DT.Np1D(False, self.pointXYrelCoGNp[bodyIndex][pointIndex])
                    DT.MessNoLF("   ")
                    DT.Np1D(False, self.pointXYrelCoGrotNp[bodyIndex][pointIndex])
                    DT.MessNoLF("   ")
                    DT.Np1D(True, self.pointXYWorldNp[bodyIndex][pointIndex])
    #  -------------------------------------------------------------------------
    def updatePointVelocities(self):
        if Debug:
            DT.Mess("DapMainMod-updatePointVelocities")
        for bodyIndex in range(1, self.numBodies):
            for pointIndex in range(len(self.pointDictList[bodyIndex])):
                velVector = self.pointXYrelCoGrotNp[bodyIndex, pointIndex] * self.phiDotNp[bodyIndex]
                self.pointXYrelCoGdotNp[bodyIndex, pointIndex] = velVector
                self.pointWorldDotNp[bodyIndex, pointIndex] = self.worldDotNp[bodyIndex] + velVector
        # for forceObj in self.forceObjList:
        #   if forceObj.actuatorType != 0:
        #        if forceObj.body_I_Index != 0:
        #            forceObj.FUnit_I_WorldDot = DT.Rot90NumPy(forceObj.FUnit_I_World) * self.phiDotNp[forceObj.body_I_Index]
    #  -------------------------------------------------------------------------
    def cleanUpIndices(self, bodyName, bodyIndex):
        # Clean up Joint Indices in case the body order has been altered
        for jointNum in range(self.numJoints):
            if self.jointObjList[jointNum].body_I_Name == bodyName:
                self.jointObjList[jointNum].body_I_Index = bodyIndex
            if self.jointObjList[jointNum].body_J_Name == bodyName:
                self.jointObjList[jointNum].body_J_Index = bodyIndex
        # Clean up force Indices in case the body order has been altered
        for forceNum in range(self.numForces):
            if self.forceObjList[forceNum].body_I_Name == bodyName:
                self.forceObjList[forceNum].body_I_Index = bodyIndex
            if self.forceObjList[forceNum].body_J_Name == bodyName:
                self.forceObjList[forceNum].body_J_Index = bodyIndex
    #  -------------------------------------------------------------------------
    def clearZombieBodies(self, bodyObjDict):
        # Clean up any zombie body names
        for jointNum in range(self.numJoints):
            if self.jointObjList[jointNum].body_I_Name not in bodyObjDict:
                self.jointObjList[jointNum].body_I_Name = ""
                self.jointObjList[jointNum].body_I_Label = ""
                self.jointObjList[jointNum].body_I_Index = 0
            if self.jointObjList[jointNum].body_J_Name not in bodyObjDict:
                self.jointObjList[jointNum].body_J_Name = ""
                self.jointObjList[jointNum].body_J_Label = ""
                self.jointObjList[jointNum].body_J_Index = 0
        for forceNum in range(self.numForces):
            if self.forceObjList[forceNum].body_I_Name not in bodyObjDict:
                self.forceObjList[forceNum].body_I_Name = ""
                self.forceObjList[forceNum].body_I_Label = ""
                self.forceObjList[forceNum].body_I_Index = 0
            if self.forceObjList[forceNum].body_J_Name not in bodyObjDict:
                self.forceObjList[forceNum].body_J_Name = ""
                self.forceObjList[forceNum].body_J_Label = ""
                self.forceObjList[forceNum].body_J_Index = 0
    #  =========================================================================
    def GetconstraintsF(self, tick):
        """Returns a numConstraints-long vector which contains the current deviation
        from the defined constraints"""
        if Debug:
            DT.Mess("DapMainMod-constraints")

        DeltaconstraintNp = np.zeros((self.numConstraints,), dtype=np.float64)
        
        # Call the applicable function which is pointed to by the constraint function dictionary
        for jointObj in self.jointObjList:
            if jointObj.JointType == DT.JOINT_TYPE_DICTIONARY['Revolute'] and jointObj.FunctType != -1:
                jointObj.JointType = DT.JOINT_TYPE_DICTIONARY['Driven-Revolute']
            constraintNp = self.dictconstraintFunctions[jointObj.JointType](jointObj, tick)
            DeltaconstraintNp[jointObj.rowStart: jointObj.rowEnd] = constraintNp


        return DeltaconstraintNp
    #  =========================================================================
    def GetJacobianF(self):
        """Returns the Jacobian matrix numConstraints X (3 x numMovBodies)"""
        if Debug:
            DT.Mess("DapMainMod-Jacobian")
        Jacobian = np.zeros((self.numConstraints, self.numMovBodiesx3,))
        for jointObj in self.jointObjList:
            # Call the applicable function which is pointed to by the Jacobian dictionary
            if jointObj.JointType == DT.JOINT_TYPE_DICTIONARY['Revolute'] and jointObj.FunctType != -1:
                jointObj.JointType = DT.JOINT_TYPE_DICTIONARY['Driven-Revolute']
            JacobianHead, JacobianTail = self.dictJacobianFunctions[jointObj.JointType](jointObj)
            # Fill in the values in the Jacobian
            if jointObj.body_I_Index != 0:
                columnHeadStart = (jointObj.body_I_Index-1) * 3
                columnHeadEnd = jointObj.body_I_Index * 3
                Jacobian[jointObj.rowStart: jointObj.rowEnd, columnHeadStart: columnHeadEnd] = JacobianHead
            if jointObj.body_J_Index != 0:
                columnTailStart = (jointObj.body_J_Index-1) * 3
                columnTailEnd = jointObj.body_J_Index * 3
                Jacobian[jointObj.rowStart: jointObj.rowEnd, columnTailStart: columnTailEnd] = JacobianTail
        return Jacobian
    #  =========================================================================
    def RHSAcc(self, tick):
        """Returns a numConstraints-long vector containing gamma"""
        if Debug:
            DT.Mess("DapMainMod-RHSAcc")
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        #    rhs = zeros(nConst,1);
        # for Ji = 1:nJ
        #    switch (Joints(Ji).type);
        #        case {'rev'}
        #            A_rev
        #        case {'tran'}
        #            A_tran
        #        case {'rev-rev'}
        #            A_rev_rev
        #        case {'rev-tran'}
        #            A_rev_tran
        #        case {'rigid'}
        #            A_rigid
        #        case {'disc'}
        #            A_disc
        #        case {'rel-rot'}
        #            A_rel_rot
        #        case {'rel-tran'}
        #            A_rel_tran
        #    end
        #        rs = Joints(Ji).rows;
        #        re = Joints(Ji).rowe;
        #        rhs(rs:re) = f;
        # end
        # ==================================
        # Determine the Right-Hand-Side of the acceleration equation (gamma)
        rhsAcc = np.zeros((self.numConstraints,), dtype=np.float64)
        # Call the applicable function which is pointed to by the Acceleration function dictionary
        for jointObj in self.jointObjList:
            if jointObj.JointType == DT.JOINT_TYPE_DICTIONARY['Revolute'] and jointObj.FunctType != -1:
                jointObj.JointType = DT.JOINT_TYPE_DICTIONARY['Driven-Revolute']
            gamma = self.dictAccelerationFunctions[jointObj.JointType](jointObj, tick)
            rhsAcc[jointObj.rowStart: jointObj.rowEnd] = gamma
        return rhsAcc
    #  -------------------------------------------------------------------------
    def RHSVel(self, tick):
        if Debug:
            DT.Mess("DapMainMod-RHSVel")
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        #     rhs = zeros(nConst,1);
        # for Ji = 1:nJ
        #    switch (Joints(Ji).type);
        #        case {'rel-rot'}
        #            [fun, fun_d, fun_dd] = functs(Joints(Ji).iFunct, t);
        #            f = fun_d;
        #            rhs(Joints(Ji).rows:Joints(Ji).rowe) = f;
        #        case {'rel-tran'}
        #            [fun, fun_d, fun_dd] = functs(Joints(Ji).iFunct, t);
        #            f = fun*fun_d;
        #            rhs(Joints(Ji).rows:Joints(Ji).rowe) = f;
        #    end
        # end
        # ==================================
        # Call the applicable Driven-Revolute or Driven-Translation function where applicable
        rhsVelNp = np.zeros((self.numConstraints,), dtype=np.float64)
        for jointObj in self.jointObjList:
            if jointObj.JointType == DT.JOINT_TYPE_DICTIONARY['Revolute'] and jointObj.FunctType != -1:
                jointObj.JointType = DT.JOINT_TYPE_DICTIONARY['Driven-Rotation']
                [func, funcDot, funcDotDot] = self.driverObjDict[jointObj.Name].getFofT(jointObj.FunctType, tick)
                rhsVelNp[jointObj.rowStart: jointObj.rowEnd] = func * funcDot
            elif jointObj.JointType == DT.JOINT_TYPE_DICTIONARY['Driven-Translation']:
                [func, funcDot, funcDotDot] = self.driverObjDict[jointObj.Name].getFofT(jointObj.FunctType, tick)
                rhsVelNp[jointObj.rowStart: jointObj.rowEnd] = funcDot
        return rhsVelNp
    #  =========================================================================
    def Revolute_constraint(self, jointObj, tick):
        """Evaluate the constraints for a Revolute joint"""
        if Debug:
            DT.Mess("DapMainMod-Revolute_constraint")
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        #    Pi = Joints(Ji).iPindex;
        #    Pj = Joints(Ji).jPindex;
        #
        #    f = Points(Pi).rP - Points(Pj).rP;
        #    if Joints(Ji).fix == 1
        #        Bi = Joints(Ji).iBindex;
        #        Bj = Joints(Ji).jBindex;
        #        if Bi == 0
        #        f = [f
        #            (- Bodies(Bj).p - Joints(Ji).p0)];
        #        elseif Bj == 0
        #            f = [f
        #            (Bodies(Bi).p - Joints(Ji).p0)];
        #        else
        #            f = [f
        #            (Bodies(Bi).p - Bodies(Bj).p - Joints(Ji).p0)];
        #        end
        #    end
        # ==================================
        constraintNp = self.pointXYWorldNp[jointObj.body_I_Index, jointObj.point_I_i_Index] - \
                       self.pointXYWorldNp[jointObj.body_J_Index, jointObj.point_J_i_Index]
        if Debug:
            DT.Mess('Revolute Constraint:')
            DT.MessNoLF('    Point I: ')
            DT.Np1D(True, self.pointXYWorldNp[jointObj.body_I_Index, jointObj.point_I_i_Index])
            DT.MessNoLF('    Point J: ')
            DT.Np1D(True, self.pointXYWorldNp[jointObj.body_J_Index, jointObj.point_J_i_Index])
            DT.MessNoLF('    Difference Vector: ')
            DT.Np1D(True, constraintNp)
        if jointObj.fixDof:
            if jointObj.body_I_Index == 0:
                constraintNp = np.array([constraintNp[0],
                                         constraintNp[1],
                                         (-self.phiNp[jointObj.body_J_Index] - jointObj.phi0)])
            elif jointObj.body_J_Index == 0:
                constraintNp = np.array([constraintNp[0],
                                         constraintNp[1],
                                         (self.phiNp[jointObj.body_I_Index] - jointObj.phi0)])
            else:
                constraintNp = np.array([constraintNp[0],
                                         constraintNp[1],
                                         (self.phiNp[jointObj.body_I_Index]
                                          - self.phiNp[jointObj.body_J_Index]
                                          - jointObj.phi0)])
        return constraintNp
    #  -------------------------------------------------------------------------
    def Revolute_Jacobian(self, jointObj):
        """Evaluate the Jacobian for a Revolute joint"""
        if Debug:
            DT.Mess("DapMainMod-Revolute_Jacobian")
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        # Pi = Joints(Ji).iPindex;
        # Pj = Joints(Ji).jPindex;
        #
        #    Di = [ eye(2)  Points(Pi).sP_r];
        #    Dj = [-eye(2) -Points(Pj).sP_r];
        #
        #    if Joints(Ji).fix == 1
        #        Di = [Di
        #              0  0  1];
        #        Dj = [Dj
        #              0  0 -1];
        #    end
        # ==================================
        if jointObj.fixDof is False:
            JacobianHead = np.array([
                [1.0, 0.0, self.pointXYrelCoGrotNp[jointObj.body_I_Index, jointObj.point_I_i_Index, 0]],
                [0.0, 1.0, self.pointXYrelCoGrotNp[jointObj.body_I_Index, jointObj.point_I_i_Index, 1]]])
            JacobianTail = np.array([
                [-1.0, 0.0, -self.pointXYrelCoGrotNp[jointObj.body_J_Index, jointObj.point_J_i_Index, 0]],
                [0.0, -1.0, -self.pointXYrelCoGrotNp[jointObj.body_J_Index, jointObj.point_J_i_Index, 1]]])
        else:
            JacobianHead = np.array([
                [1.0, 0.0, self.pointXYrelCoGrotNp[jointObj.body_I_Index, jointObj.point_I_i_Index, 0]],
                [0.0, 1.0, self.pointXYrelCoGrotNp[jointObj.body_I_Index, jointObj.point_I_i_Index, 1]],
                [0.0, 0.0, 1.0]])
            JacobianTail = np.array([
                [-1.0, 0.0, -self.pointXYrelCoGrotNp[jointObj.body_J_Index, jointObj.point_J_i_Index, 0]],
                [0.0, -1.0, -self.pointXYrelCoGrotNp[jointObj.body_J_Index, jointObj.point_J_i_Index, 1]],
                [0.0, 0.0, -1.0]])
        return JacobianHead, JacobianTail
    #  -------------------------------------------------------------------------
    def Revolute_Acc(self, jointObj, tick):
        """Evaluate gamma for a Revolute joint"""
        if Debug:
            DT.Mess("DapMainMod-Revolute_Acc")
        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        # Pi = Joints(Ji).iPindex;
        # Pj = Joints(Ji).jPindex;
        # Bi = Points(Pi).Bindex;
        # Bj = Points(Pj).Bindex;
        #
        # if Bi == 0
        #    f = s_rot(Points(Pj).sP_d)*Bodies(Bj).p_d;
        # elseif Bj == 0
        #    f = -s_rot(Points(Pi).sP_d)*Bodies(Bi).p_d;
        # else
        #    f = -s_rot(Points(Pi).sP_d)*Bodies(Bi).p_d + ...
        #         s_rot(Points(Pj).sP_d)*Bodies(Bj).p_d;
        # end
        #
        #    if Joints(Ji).fix == 1
        #       f = [f
        #            0];
        #    end
        # ==================================
        if jointObj.body_I_Index == 0:
            gammaNp = DT.Rot90NumPy(self.pointXYrelCoGdotNp[jointObj.body_J_Index, jointObj.point_J_i_Index]) * self.phiDotNp[jointObj.body_J_Index]
        elif jointObj.body_J_Index == 0:
            gammaNp = -DT.Rot90NumPy(self.pointXYrelCoGdotNp[jointObj.body_I_Index, jointObj.point_I_i_Index]) * self.phiDotNp[jointObj.body_I_Index]
        else:
            gammaNp = -DT.Rot90NumPy(self.pointXYrelCoGdotNp[jointObj.body_I_Index, jointObj.point_I_i_Index]) * self.phiDotNp[jointObj.body_I_Index] +\
                       DT.Rot90NumPy(self.pointXYrelCoGdotNp[jointObj.body_J_Index, jointObj.point_J_i_Index]) * self.phiDotNp[jointObj.body_J_Index]
        if jointObj.fixDof:
            gammaNp = np.array([gammaNp[0], gammaNp[1], 0.0])

        return gammaNp
    #  =========================================================================
    #  -------------------------------------------------------------------------
    def outputResults(self, timeValues, uResults):
        if Debug:
            DT.Mess("DapMainMod-outputResults")

        # Compute body accelerations, Lagrange multipliers, coordinates and
        #    velocity of all points, kinetic and potential energies,
        #             at every reporting time interval
        self.solverObj = FreeCAD.ActiveDocument.findObjects(Name="^DapSolver$")[0]
        fileName = self.solverObj.Directory+"/"+self.solverObj.FileName+".csv"
        DapResultsFILE = open(fileName, 'w')
        numTicks = len(timeValues)

        # Create the vertical headings list
        # To write each body name into the top row of the spreadsheet,
        # would make some columns very big by default
        # So body names and point names are also written vertically in
        # The column before the body/point data is written
        VerticalHeaders = []
        # Write the column headers horizontally
        for twice in range(2):
            ColumnCounter = 0
            DapResultsFILE.write("Time: ")
            # Bodies Headings
            for bodyIndex in range(1, self.numBodies):
                if twice == 0:
                    VerticalHeaders.append(self.bodyObjList[bodyIndex].Label)
                    DapResultsFILE.write("Body" + str(bodyIndex))
                    DapResultsFILE.write(" x y phi(r) phi(d) dx/dt dy/dt dphi/dt(r) dphi/dt(d) d2x/dt2 d2y/dt2 d2phi/dt2(r) d2phi/dt2(d) ")
                else:
                    DapResultsFILE.write(VerticalHeaders[ColumnCounter] + " -"*12 + " ")
                ColumnCounter += 1
                # Points Headings
                for index in range(len(self.pointDictList[bodyIndex])):
                    if twice == 0:
                        VerticalHeaders.append(self.bodyObjList[bodyIndex].pointLabels[index])
                        DapResultsFILE.write("Point" + str(index+1) + " x y dx/dt dy/dt ")
                    else:
                        DapResultsFILE.write(VerticalHeaders[ColumnCounter] + " -"*4 + " ")
                    ColumnCounter += 1
            # Lambda Headings
            if self.numConstraints > 0:
                for bodyIndex in range(1, self.numBodies):
                    if twice == 0:
                        VerticalHeaders.append(self.bodyObjList[bodyIndex].Label)
                        DapResultsFILE.write("Lam" + str(bodyIndex) + " x y ")
                    else:
                        DapResultsFILE.write(VerticalHeaders[ColumnCounter] + " - - ")
                    ColumnCounter += 1
            # Kinetic Energy Headings
            for bodyIndex in range(1, self.numBodies):
                if twice == 0:
                    VerticalHeaders.append(self.bodyObjList[bodyIndex].Label)
                    DapResultsFILE.write("Kin" + str(bodyIndex) + " - ")
                else:
                    DapResultsFILE.write(VerticalHeaders[ColumnCounter] + " - ")
                ColumnCounter += 1

            # Potential Energy Headings
            for forceIndex in range(self.numForces):
                forceObj = self.forceObjList[forceIndex]
                if forceObj.actuatorType == 0:
                    for bodyIndex in range(1, self.numBodies):
                        if twice == 0:
                            VerticalHeaders.append(self.bodyObjList[bodyIndex].Label)
                            DapResultsFILE.write("Pot" + str(bodyIndex) + " - ")
                        else:
                            DapResultsFILE.write(VerticalHeaders[ColumnCounter] + " - ")
                        ColumnCounter += 1

            # Energy Totals Headings
            if twice == 0:
                DapResultsFILE.write("TotKin TotPot Total\n")
            else:
                DapResultsFILE.write("\n")

        # Do the calculations for each point in time
        # Plus an extra one at time=0 (with no printing)
        VerticalCounter = 0
        TickRange = [0]
        TickRange += range(numTicks)
        for timeIndex in TickRange:
            tick = timeValues[timeIndex]
            ColumnCounter = 0
            potEnergy = 0

            # Do the analysis on the stored uResults
            self.Analysis(tick, uResults[timeIndex])

            # Write Time
            if timeIndex != 0:
                DapResultsFILE.write(str(tick) + " ")

            # Write All the Bodies position, positionDot, positionDotDot
            for bodyIndex in range(1, self.numBodies):
                if timeIndex != 0:
                    # Write Body Name vertically
                    if VerticalCounter < len(VerticalHeaders[ColumnCounter]):
                        character = VerticalHeaders[ColumnCounter][VerticalCounter]
                        if character in "0123456789":
                            DapResultsFILE.write("'" + character + "' ")
                        else:
                            DapResultsFILE.write(character + " ")
                    else:
                        DapResultsFILE.write("- ")

                    ColumnCounter += 1
                    # X Y
                    DapResultsFILE.write(str(self.worldNp[bodyIndex]*1e-3)[1:-1:] + " ")
                    # Phi (rad)
                    DapResultsFILE.write(str(self.phiNp[bodyIndex])[1:-1:] + " ")
                    # Phi (deg)
                    DapResultsFILE.write(str(self.phiNp[bodyIndex] * 180.0 / math.pi)[1:-1:] + " ")
                    # Xdot Ydot
                    DapResultsFILE.write(str(self.worldDotNp[bodyIndex]*1e-3)[1:-1:] + " ")
                    # PhiDot (rad)
                    DapResultsFILE.write(str(self.phiDotNp[bodyIndex])[1:-1:] + " ")
                    # PhiDot (deg)
                    DapResultsFILE.write(str(self.phiDotNp[bodyIndex] * 180.0 / math.pi)[1:-1:] + " ")
                    # Xdotdot Ydotdot
                    DapResultsFILE.write(str(self.worldDotDotNp[bodyIndex]*1e-3)[1:-1:] + " ")
                    # PhiDotDot (rad)
                    DapResultsFILE.write(str(self.phiDotDotNp[bodyIndex])[1:-1:] + " ")
                    # PhiDotDot (deg)
                    DapResultsFILE.write(str(self.phiDotDotNp[bodyIndex] * 180.0 / math.pi)[1:-1:] + " ")

                # Write all the points position and positionDot in the body
                for index in range(len(self.pointDictList[bodyIndex])):
                    if timeIndex != 0:
                        # Write Point Name vertically
                        if VerticalCounter < len(VerticalHeaders[ColumnCounter]):
                            character = VerticalHeaders[ColumnCounter][VerticalCounter]
                            if character in "0123456789":
                                DapResultsFILE.write("'" + character + "' ")
                            else:
                                DapResultsFILE.write(character + " ")
                        else:
                            DapResultsFILE.write("- ")

                        ColumnCounter += 1
                        # Point X Y
                        DapResultsFILE.write(str(self.pointXYWorldNp[bodyIndex, index]*1e-3)[1:-1:] + " ")
                        # Point Xdot Ydot
                        DapResultsFILE.write(str(self.pointWorldDotNp[bodyIndex, index]*1e-3)[1:-1:] + " ")

            # Write the Lambdas
            if self.numConstraints > 0:
                if timeIndex != 0:
                    # Lambda
                    for bodyIndex in range(self.numBodies-1):
                        # Write the Body Name vertically
                        if VerticalCounter < len(VerticalHeaders[ColumnCounter]):
                            character = VerticalHeaders[ColumnCounter][VerticalCounter]
                            if character in "0123456789":
                                DapResultsFILE.write("'" + character + "' ")
                            else:
                                DapResultsFILE.write(character + " ")
                        else:
                            DapResultsFILE.write("- ")

                        ColumnCounter += 1
                        DapResultsFILE.write(str(self.Lambda[bodyIndex*2] * 1e-3)[1:-1:] + " " + str(self.Lambda[bodyIndex*2 + 1] * 1e-3)[1:-1:] + " ")

            # Compute kinetic and potential energies in Joules
            totKinEnergy = 0
            for bodyIndex in range(1, self.numBodies):
                kinEnergy = 0.5e-6 * (
                        (self.massArrayNp[(bodyIndex-1) * 3] *
                         (self.worldDotNp[bodyIndex, 0] ** 2 + self.worldDotNp[bodyIndex, 1] ** 2)) +
                        (self.massArrayNp[(bodyIndex - 1) * 3 + 2] * (self.phiDotNp[bodyIndex] ** 2)))

                # Kinetic Energy (m^2 = mm^2 * 1e-6)
                if timeIndex != 0:
                    # Body Name vertically
                    if VerticalCounter < len(VerticalHeaders[ColumnCounter]):
                        character = VerticalHeaders[ColumnCounter][VerticalCounter]
                        if character in "0123456789":
                            DapResultsFILE.write("'" + character + "' ")
                        else:
                            DapResultsFILE.write(character + " ")
                    else:
                        DapResultsFILE.write("- ")
                    ColumnCounter += 1
                    DapResultsFILE.write(str(kinEnergy)[1:-1:] + " ")
                totKinEnergy += kinEnergy

            # Currently, calculate only gravitational potential energy
            totPotEnergy = 0
            for forceIndex in range(self.numForces):
                forceObj = self.forceObjList[forceIndex]
                # Potential Energy
                potEnergy = 0
                if forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Gravity"]:
                    for bodyIndex in range(1, self.numBodies):
                        potEnergy = -self.WeightNp[bodyIndex].dot(self.worldNp[bodyIndex]) * 1e-6 - self.potEnergyZeroPointNp[bodyIndex]
                        totPotEnergy += potEnergy
                        if timeIndex == 0:
                            self.potEnergyZeroPointNp[bodyIndex] = potEnergy
                        else:
                            # Body Name vertically
                            if VerticalCounter < len(VerticalHeaders[ColumnCounter]):
                                character = VerticalHeaders[ColumnCounter][VerticalCounter]
                                if character in "0123456789":
                                    DapResultsFILE.write("'" + character + "' ")
                                else:
                                    DapResultsFILE.write(character + " ")
                            else:
                                DapResultsFILE.write("- ")
                            ColumnCounter += 1
                            DapResultsFILE.write(str(potEnergy) + " ")

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Spring"] or \
                    forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Linear Spring Damper"]:
                    # potEnergy += 0.5 * forceObj.k * delta**2
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Rotational Spring"] or \
                        forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Rotational Spring Damper"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Force Local to Body"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Global Force"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Torque about a Point"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Contact Friction"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Unilateral Spring Damper"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Motor"]:
                    pass

                elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Motor with Air Friction"]:
                    pass

            if timeIndex == 0:
                VerticalCounter = 0
            else:
                DapResultsFILE.write(str(totKinEnergy) + " ")
                DapResultsFILE.write(str(totPotEnergy) + " ")
                DapResultsFILE.write(str(totKinEnergy + totPotEnergy) + " ")
                DapResultsFILE.write("\n")
                VerticalCounter += 1
        # Next timeIndex

        DapResultsFILE.close()
    #  -------------------------------------------------------------------------
    def makeForceArray(self):
        if Debug:
            DT.Mess("DapMainC - makeForceArray")

        # Reset all forces and moments to zero
        for bodyIndex in range(1, self.numBodies):
            self.sumForcesNp[bodyIndex] = np.zeros((2,), dtype=np.float64)
            self.sumMomentsNp[bodyIndex] = np.zeros((1,), dtype=np.float64)

        # Add up all the body force vectors for all the bodies
        for forceIndex in range(self.numForces):
            forceObj = self.forceObjList[forceIndex]
            if forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Gravity"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'weight'}
                #            for Bi=1:nB
                #                Bodies(Bi).f = Bodies(Bi).f + Bodies(Bi).wgt;
                #            end
                for bodyIndex in range(1, self.numBodies):
                    self.sumForcesNp[bodyIndex] += self.WeightNp[bodyIndex]

            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Spring"] or \
                    forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Linear Spring Damper"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'ptp'}
                # % Point-to-point spring-damper-actuator
                #  Pi = Forces(Fi).iPindex;
                #  Pj = Forces(Fi).jPindex;
                #  Bi = Forces(Fi).iBindex;
                #  Bj = Forces(Fi).jBindex;
                #  d  = Points(Pi).rP - Points(Pj).rP;
                #  d_dot = Points(Pi).rP_d - Points(Pj).rP_d;
                #  L  = sqrt(d'*d);
                #  L_dot = d'*d_dot/L;
                #  del = L - Forces(Fi).L0;
                #  u = d/L;
                #
                #  f = Forces(Fi).k*del + Forces(Fi).dc*L_dot + Forces(Fi).f_a;
                #  fi = f*u;
                #  if Bi ~= 0
                #    Bodies(Bi).f = Bodies(Bi).f - fi;
                #    Bodies(Bi).n = Bodies(Bi).n - Points(Pi).sP_r'*fi;
                #  end
                #  if Bj ~= 0
                #    Bodies(Bj).f = Bodies(Bj).f + fi;
                #    Bodies(Bj).n = Bodies(Bj).n + Points(Pj).sP_r'*fi;
                #  end

                diffNp = self.pointXYWorldNp[forceObj.body_I_Index, forceObj.point_i_Index] - \
                       self.pointXYWorldNp[forceObj.body_J_Index, forceObj.point_j_Index]
                diffDotNp = self.pointWorldDotNp[forceObj.body_I_Index, forceObj.point_i_Index] - \
                       self.pointWorldDotNp[forceObj.body_J_Index, forceObj.point_j_Index]
                length = np.sqrt(diffNp.dot(diffNp))
                lengthDot = (diffNp.dot(diffDotNp))/length
                delta = length - forceObj.LengthAngle0
                unitVecNp = diffNp/length
                # Find the component of the force in the direction of
                # the vector between the head and the tail of the force
                force = forceObj.Stiffness * delta + forceObj.DampingCoeff * lengthDot + forceObj.ForceMagnitude
                forceUnitNp = unitVecNp * force
                if forceObj.body_I_Index != 0:
                    self.sumForcesNp[forceObj.body_I_Index] -= forceUnitNp
                    self.sumMomentsNp[forceObj.body_I_Index] -= (self.pointXYrelCoGrotNp[forceObj.body_I_Index, forceObj.point_i_Index]).dot(forceUnitNp)
                if forceObj.body_J_Index != 0:
                    self.sumForcesNp[forceObj.body_J_Index] += forceUnitNp
                    self.sumMomentsNp[forceObj.body_J_Index] += self.pointXYrelCoGrotNp[forceObj.body_J_Index, forceObj.point_j_Index].dot(forceUnitNp)
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Rotational Spring"] or \
                    forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Rotational Spring Damper"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'rot-sda'}
                # % Rotational spring-damper-actuator
                #
                #  Bi = Forces(Fi).iBindex;
                #  Bj = Forces(Fi).jBindex;
                #
                #    if Bi == 0
                #        theta   = -Bodies(Bj).p;
                #        theta_d = -Bodies(Bj).p_d;
                #        T = Forces(Fi).k*(theta - Forces(Fi).theta0) + ...
                #            Forces(Fi).dc*theta_d + Forces(Fi).T_a;
                #        Bodies(Bj).n = Bodies(Bj).n + T;
                #    elseif Bj == 0
                #        theta   = Bodies(Bi).p;
                #        theta_d = Bodies(Bi).p_d;
                #        T = Forces(Fi).k*(theta - Forces(Fi).theta0) + ...
                #            Forces(Fi).dc*theta_d + Forces(Fi).T_a;
                #        Bodies(Bi).n = Bodies(Bi).n - T;
                #    else
                #        theta   = Bodies(Bi).p - Bodies(Bj).p;
                #        theta_d = Bodies(Bi).p_d - Bodies(Bj).p_d;
                #        T = Forces(Fi).k*(theta - Forces(Fi).theta0) + ...
                #            Forces(Fi).dc*theta_d + Forces(Fi).T_a;
                #        Bodies(Bi).n = Bodies(Bi).n - T;
                #        Bodies(Bj).n = Bodies(Bj).n + T;
                #    end
                if forceObj.body_I_Index == 0:
                    theta = -self.phiNp[forceObj.body_J_Index]
                    thetaDot = -self.phiDotNp[forceObj.body_J_Index]
                    Torque = forceObj.Stiffness * (theta - forceObj.LengthAngle0) + \
                             forceObj.DampingCoeff * thetaDot + \
                             forceObj.TorqueMagnitude
                    self.sumMomentsNp[forceObj.body_J_Index] += Torque
                elif forceObj.body_J_Index == 0:
                    theta = self.phiNp[forceObj.body_I_Index]
                    thetaDot = self.phiDotNp[forceObj.body_I_Index]
                    Torque = forceObj.Stiffness * (theta - forceObj.LengthAngle0) + \
                             forceObj.DampingCoeff * thetaDot + \
                             forceObj.TorqueMagnitude
                    self.sumMomentsNp[forceObj.body_I_Index] -= Torque
                else:
                    theta = self.phiNp[forceObj.body_I_Index] - self.phiNp[forceObj.body_J_Index]
                    thetaDot = self.phiDotNp[forceObj.body_I_Index] - self.phiDotNp[forceObj.body_J_Index]
                    Torque = forceObj.Stiffness * (theta - forceObj.LengthAngle0) + \
                             forceObj.DampingCoeff * thetaDot + \
                             forceObj.TorqueMagnitude
                    self.sumMomentsNp[forceObj.body_I_Index] -= Torque
                    self.sumMomentsNp[forceObj.body_J_Index] += Torque
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Unilateral Spring Damper"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                # TODO: Future implementation - not explicitly handled by Nikravesh
                DT.Console.PrintError("Still in development\n")
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Force Local to Body"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'flocal'}
                #            Bi = Forces(Fi).iBindex;
                #            Bodies(Bi).f = Bodies(Bi).f + Bodies(Bi).A*Forces(Fi).flocal;
                self.sumForcesNp[forceObj.body_I_Index] += self.RotMatPhiNp[forceObj.body_I_Index] @ forceObj.constLocalForce
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Global Force"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'f'}
                #            Bi = Forces(Fi).iBindex;
                #            Bodies(Bi).f = Bodies(Bi).f + Forces(Fi).f;
                self.sumForcesNp[forceObj.body_I_Index, 0] += forceObj.constWorldForce[0]
                self.sumForcesNp[forceObj.body_I_Index, 1] += forceObj.constWorldForce[1]
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Constant Torque about a Point"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                #        case {'T'}
                #            Bi = Forces(Fi).iBindex;
                #            Bodies(Bi).n = Bodies(Bi).n + Forces(Fi).T;
                self.sumMomentsNp[forceObj.body_I_Index] += forceObj.constTorque
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Contact Friction"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                # TODO: Future implementation - not explicitly handled by Nikravesh
                DT.Console.PrintError("Still in development\n")
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Motor"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                # TODO: Future implementation - not explicitly handled by Nikravesh
                DT.Console.PrintError("Still in development\n")
            elif forceObj.actuatorType == DT.FORCE_TYPE_DICTIONARY["Motor with Air Friction"]:
                # ==================================
                # Matlab Code from Nikravesh: DAP_BC
                # ==================================
                # TODO: Future implementation - not explicitly handled by Nikravesh
                FreeCAD.Console.PrintError("Still in development\n")
            else:
                FreeCAD.Console.PrintError("Unknown Force type - this should never occur\n")
        # Next forceIndex

        # ==================================
        # Matlab Code from Nikravesh: DAP_BC
        # ==================================
        # g = zeros(nB3,1);
        # for Bi = 1:nB
        #    ks = Bodies(Bi).irc; ke = ks + 2;
        #    g(ks:ke) = [Bodies(Bi).f; Bodies(Bi).n];
        # end
        # ==================================
        # The force array has three values for every body
        # x and y are the sum of forces and z is the sum of moments
        for bodyIndex in range(1, self.numBodies):
            self.forceArrayNp[(bodyIndex - 1) * 3: bodyIndex * 3 - 1] = self.sumForcesNp[bodyIndex]
            self.forceArrayNp[bodyIndex * 3 - 1] = self.sumMomentsNp[bodyIndex]
        if Debug:
            DT.MessNoLF("Force Array:  ")
            DT.Np1D(True, self.forceArrayNp)
    #  =========================================================================
    def initNumPyArrays(self, maxNumPoints):
        # Initialize all the NumPy arrays with zeros

        # Parameters for each body
        self.MassNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.WeightNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.momentInertiaNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.sumForcesNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.sumMomentsNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.worldNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.worldRotNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.worldDotNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.worldDotRotNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.worldDotDotNp = np.zeros((self.numBodies, 2,), dtype=np.float64)
        self.phiNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.phiDotNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.phiDotDotNp = np.zeros((self.numBodies,), dtype=np.float64)
        self.RotMatPhiNp = np.zeros((self.numBodies, 2, 2,), dtype=np.float64)
        self.potEnergyZeroPointNp = np.zeros((self.numBodies,), dtype=np.float64)

        # Parameters for each point within a body, for each body
        # Vector from CoG to the point in body local coordinates
        self.pointXiEtaNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        # Vector from CoG to the point in world coordinates
        self.pointXYrelCoGNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        self.pointXYrelCoGrotNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        self.pointXYrelCoGdotNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        # Vector from the origin to the point in world coordinates
        self.pointXYWorldNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        self.pointWorldRotNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)
        self.pointWorldDotNp = np.zeros((self.numBodies, maxNumPoints, 2,), dtype=np.float64)

        # Unit vector (if applicable) of the first body of the joint in body local coordinates
        self.jointUnit_I_XiEtaNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        # Unit vector (if applicable) of the first body of the joint in world coordinates
        self.jointUnit_I_WorldNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_I_WorldRotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_I_WorldDotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_I_WorldDotRotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        # Second unit vector (if applicable) of the second body of the joint in body local coordinates
        self.jointUnit_J_XiEtaNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        # second unit vector (if applicable) of the second body of the joint in world coordinates
        self.jointUnit_J_WorldNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_J_WorldRotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_J_WorldDotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)
        self.jointUnit_J_WorldDotRotNp = np.zeros((self.numJoints, 2,), dtype=np.float64)

        self.forceArrayNp = np.zeros((self.numMovBodiesx3,), dtype=np.float64)
    #  -------------------------------------------------------------------------
    def dumps(self):
        if Debug:
            DT.Mess("TaskPanelDapMainClass-dumps")
        return None
    #  -------------------------------------------------------------------------
    def loads(self, state):
        if Debug:
            DT.Mess("TaskPanelDapMainClass-loads")
        if state:
            self.Type = state
        return None
    #  =========================================================================