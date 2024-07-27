# This is the analyte function from Nikravesh
import numpy as np
from scipy.integrate import solve_ivp

def dapvec(x, y):
    return np.array([[x], [y]])


def A_matrix(phi):
    if type(phi) == np.ndarray:
        phi = phi[0]
    return np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])


def s_rot(u):
    return np.array([[0, -1], [1, 0]]) @ u


g = 9.81
uy = np.array([[0, 1]]).T


def jacobian(solverBodies, solverJoints):
    D = np.empty((0, len(solverBodies) * 3))

    for joint in solverJoints:
        if joint.joint_type == 'revolute':
            body_i = solverBodies[joint.body_i]
            body_j = solverBodies[joint.body_j]

            phi_i = body_i.angle
            A_i = A_matrix(phi_i)

            phi_j = body_j.angle
            A_j = A_matrix(phi_j)

            s_i = A_i @ body_i.points[joint.point_i]
            s_j = A_j @ body_j.points[joint.point_j]

            D_i = np.hstack([np.eye(2, 2), s_rot(s_i)])
            D_i = np.hstack(
                    [np.zeros((2, joint.body_i * 3)), D_i, np.zeros((2, (len(solverBodies) - joint.body_i - 1) * 3))])
            D_j = np.hstack([-np.eye(2, 2), -s_rot(s_j)])
            D_j = np.hstack(
                    [np.zeros((2, joint.body_j * 3)), D_j, np.zeros((2, (len(solverBodies) - joint.body_j - 1) * 3))])
            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

        if joint.joint_type == "translational":
            body_i = solverBodies[joint.body_i]
            body_j = solverBodies[joint.body_j]

            phi_i = body_i.angle
            A_i = A_matrix(phi_i)

            phi_j = body_j.angle
            A_j = A_matrix(phi_j)

            s_i = A_i @ body_i.points[joint.point_i]
            s_j = A_j @ body_j.points[joint.point_j]

            u_i = joint.unit_i
            u_j = joint.unit_j

            D_i = np.hstack([s_rot(u_i).T, u_i.T @ s_i])
            D_i = np.vstack([D_i, np.array([0, 0, 1])])
            D_i = np.hstack([np.zeros((2, joint.body_i * 3)), D_i, np.zeros((2, (len(solverBodies) - joint.body_i - 1) * 3))])

            d =  (body_i.position + s_i) - (body_j.position + s_j)

            D_j = np.hstack([-s_rot(u_i).T, -u_i.T @ (s_j + d)])
            D_j = np.vstack([D_j, np.array([0, 0, -1])])
            D_j = np.hstack([np.zeros((2, joint.body_j * 3)), D_j, np.zeros((2, (len(solverBodies) - joint.body_j - 1) * 3))])

            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

        if joint.joint_type == "rel-rev":
            D_i = np.array([[0, 0, 1]])
            D_i = np.hstack([np.zeros((1, joint.body_i * 3)), D_i, np.zeros((1, (len(solverBodies) - joint.body_i - 1) * 3))])

            D_j = np.array([[0, 0, -1]])
            D_j = np.hstack([np.zeros((1, joint.body_j * 3)), D_j, np.zeros((1, (len(solverBodies) - joint.body_j - 1) * 3))])

            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

    D = np.delete(D, [0, 1, 2], axis=1)

    return D


def initial_conditions(solverBodies, solverJoints):
    Phi = np.empty([0, 1])

    for Bi in range(len(solverBodies)):
        ir = 1 + (Bi - 1)*3
        Phi = np.vstack([Phi, solverBodies[Bi].position_d, solverBodies[Bi].angle_d])

    Phi = np.delete(Phi, [0, 1, 2], axis=0)

    # Set the initail velocities, need the rel-ref to be the function value
    rhs = np.empty((0, 1))
    for joint in solverJoints:
        if joint.joint_type == 'revolute':
            rhs = np.vstack([rhs, 0, 0])
        if joint.joint_type == 'translational':
            rhs = np.vstack([rhs, 0, 0])
        if joint.joint_type == "rel-rev":
            f_d = joint.func[1] + joint.func[3] * 0
            rhs = np.vstack([rhs, f_d])

    D = jacobian(solverBodies, solverJoints)
    delta_v = -D.T @ np.linalg.solve((D@D.T), ((D @ Phi) - rhs))

    for Bi in range(len(solverBodies) - 1):
        ir = 1 + (Bi)*3
        solverBodies[Bi + 1].position_d = solverBodies[Bi+1].position_d + delta_v[ir-1:ir+1]
        solverBodies[Bi + 1].angle_d = solverBodies[Bi+1].angle_d + delta_v[ir+1, 0]

    return solverBodies

def analysis(t, u, solverBodies, solverJoints, integrate):

    print('uArray', u, 'tick', t)

    # Make the arrays vertical to be easier to work with
    c = np.array([u[:int(len(u) / 2)]]).T
    c_d = np.array([u[int(len(u) / 2):]]).T

    # Set the bodies' variables to the new stuff
    for i in range(len(solverBodies)):
        solverBodies[i].position = dapvec(c[i * 3, 0], c[i * 3 + 1, 0])
        solverBodies[i].angle = c[i * 3 + 2, 0]

        solverBodies[i].position_d = dapvec(c_d[i * 3, 0], c_d[i * 3 + 1, 0])
        solverBodies[i].angle_d = c_d[i * 3 + 2, 0]

    M = []
    for body in solverBodies:
        M.append(body.mass)
        M.append(body.mass)
        M.append(body.inertia)
    M = np.diag(M)

    rhs = np.empty((0, 1))
    D = np.empty((0, len(solverBodies) * 3))

    for body in solverBodies:
        # Add the forces
        w = -body.mass * g * uy
        f = np.array([[0], [0]])  # N

        f_a = np.vstack([w + f, 0])
        rhs = np.vstack([rhs, f_a])

    for joint in solverJoints:

        if joint.joint_type == 'revolute':
            body_i = solverBodies[joint.body_i]
            body_j = solverBodies[joint.body_j]

            phi_i = body_i.angle
            A_i = A_matrix(phi_i)

            phi_j = body_j.angle
            A_j = A_matrix(phi_j)

            s_i = A_i @ body_i.points[joint.point_i]
            s_j = A_j @ body_j.points[joint.point_j]

            D_i = np.hstack([np.eye(2, 2), s_rot(s_i)])
            D_i = np.hstack(
                    [np.zeros((2, joint.body_i * 3)), D_i, np.zeros((2, (len(solverBodies) - joint.body_i - 1) * 3))])
            D_j = np.hstack([-np.eye(2, 2), -s_rot(s_j)])
            D_j = np.hstack(
                    [np.zeros((2, joint.body_j * 3)), D_j, np.zeros((2, (len(solverBodies) - joint.body_j - 1) * 3))])
            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

            gamma = s_i * body_i.angle_d ** 2 - s_j * body_j.angle_d ** 2

            rhs = np.vstack([rhs, gamma])

        if joint.joint_type == "translational":
            body_i = solverBodies[joint.body_i]
            body_j = solverBodies[joint.body_j]

            phi_i = body_i.angle
            A_i = A_matrix(phi_i)

            phi_j = body_j.angle
            A_j = A_matrix(phi_j)

            s_i = A_i @ body_i.points[joint.point_i]
            s_j = A_j @ body_j.points[joint.point_j]

            u_i = joint.unit_i
            u_j = joint.unit_j

            D_i = np.hstack([s_rot(u_i).T, u_i.T @ s_i])
            D_i = np.vstack([D_i, np.array([0, 0, 1])])
            D_i = np.hstack([np.zeros((2, joint.body_i * 3)), D_i, np.zeros((2, (len(solverBodies) - joint.body_i - 1) * 3))])

            d =  (body_i.position + s_i) - (body_j.position + s_j)

            D_j = np.hstack([-s_rot(u_i).T, -u_i.T @ (s_j + d)])
            D_j = np.vstack([D_j, np.array([0, 0, -1])])
            D_j = np.hstack([np.zeros((2, joint.body_j * 3)), D_j, np.zeros((2, (len(solverBodies) - joint.body_j - 1) * 3))])

            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

            gamma_top = ((s_rot(u_j).T @ (body_i.position - body_j.position) * body_i.angle_d +
                    2 * s_rot(u_j).T @ (body_i.position_d - body_j.position_d)) * body_i.angle_d)
            gamma = np.vstack([gamma_top, 0])

            rhs = np.vstack([rhs, gamma])

        if joint.joint_type == "rel-rev":
            f = joint.func[0] + joint.func[1]*t + joint.func[2]*(t**2)
            f_d = joint.func[1] + joint.func[3] * t
            f_dd = joint.func[3]

            D_i = np.array([[0, 0, 1]])
            D_i = np.hstack([np.zeros((1, joint.body_i * 3)), D_i, np.zeros((1, (len(solverBodies) - joint.body_i - 1) * 3))])

            D_j = np.array([[0, 0, -1]])
            D_j = np.hstack([np.zeros((1, joint.body_j * 3)), D_j, np.zeros((1, (len(solverBodies) - joint.body_j - 1) * 3))])

            D_joint = D_i + D_j
            D = np.vstack([D, D_joint])

            gamma = f_dd

            rhs = np.vstack([rhs, gamma])



    DMD_row1 = np.hstack([M, -D.T])
    DMD_row2 = np.hstack([D, np.zeros([D.shape[0], D.shape[0]])])
    DMD = np.vstack([DMD_row1, DMD_row2])

    # Delete the ground body associated parameters else the solution will fail
    DMD = np.delete(DMD, [0, 1, 2], axis=0)
    DMD = np.delete(DMD, [0, 1, 2], axis=1)
    rhs = np.delete(rhs, [0, 1, 2], axis=0)

    solution = np.linalg.solve(DMD, rhs)

    c_dd = np.vstack([np.zeros((3, 1)), solution[:len(solverBodies) * 3 - 3]])
    ud = np.vstack([c_d, c_dd])

    if integrate:
        return ud.flatten()

    lagrange = solution[len(solverBodies) * 3 - 3:]
    return c_dd, lagrange