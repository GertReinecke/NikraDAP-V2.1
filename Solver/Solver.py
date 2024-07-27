import numpy as np
np.set_printoptions(edgeitems=10,linewidth=1800)
import pandas as pd
#import openpyxl
from scipy.integrate import solve_ivp

def Solver(solverBodies, solverJoints, file, limit=None):
    g = 9.81
    uy = np.array([[0, 1]]).T

    from Analysis import analysis
    from Analysis import initial_conditions

    solverBodies = initial_conditions(solverBodies, solverJoints)
    #############
    #############
    # Generate the initial coordinates array
    C = []
    for body in solverBodies:
        C.append(body.position[0, 0])
        C.append(body.position[1, 0])
        C.append(body.angle)
    C = np.array([C]).T
    #############
    #############
    # Generate the initial velocity coordinates array
    Cd = []
    for body in solverBodies:
        Cd.append(body.position_d[0, 0])
        Cd.append(body.position_d[1, 0])
        Cd.append(body.angle_d)
    Cd = np.array([Cd]).T
    #############
    #############
    # Setup the integration array, initial conditions
    U = np.vstack([C, Cd])
    #############
    #############

    T_eval = np.arange(0, 1.01, 0.01)
    solution = solve_ivp(analysis, [0, 5], U.flatten(), t_eval=T_eval, method='RK45', rtol=1e-12, atol=1e-9,
                         args=(solverBodies, solverJoints, True))

    solution_df_name = []
    for body in solverBodies:
        solution_df_name.append(f'x {body.name}')
        solution_df_name.append(f'y {body.name}')
        solution_df_name.append(f'phi {body.name}')

    for body in solverBodies:
        solution_df_name.append(f'x_d {body.name}')
        solution_df_name.append(f'y_d {body.name}')
        solution_df_name.append(f'phi_d {body.name}')

    solution_df = pd.DataFrame(solution.y.T, index=solution.t, columns=solution_df_name)

    sol = solution_df.to_numpy()
    Lam = []
    Acc = []
    for i in range(len(sol)):
        acc, lam = analysis(T_eval[i], sol[i], solverBodies, solverJoints, False)

        Acc.append(acc.flatten())
        Lam.append(lam.flatten())

    lagrande_df_name = []
    for joint in solverJoints:
        if joint.joint_type == "revolute":
            lagrande_df_name.append(f'x {solverBodies[joint.body_i].name} {solverBodies[joint.body_j].name}')
            lagrande_df_name.append(f'y {solverBodies[joint.body_i].name} {solverBodies[joint.body_j].name}')

        if joint.joint_type == "translational":
            lagrande_df_name.append(f'x {solverBodies[joint.body_i].name} {solverBodies[joint.body_j].name}')
            lagrande_df_name.append(f'y {solverBodies[joint.body_i].name} {solverBodies[joint.body_j].name}')

        if joint.joint_type == "rel-rev":
            lagrande_df_name.append(f'rel-rev {solverBodies[joint.body_i].name} {solverBodies[joint.body_j].name}')

    lagrande_df = pd.DataFrame(Lam, columns=lagrande_df_name)

    acceleration_df_name = []
    for body in solverBodies:
        acceleration_df_name.append(f'x_dd {body.name}')
        acceleration_df_name.append(f'y_dd {body.name}')
        acceleration_df_name.append(f'phi_dd {body.name}')
    acceleration_df = pd.DataFrame(Acc, columns=acceleration_df_name)

    excel_file = f'Solutions/{file}.xlsx'
    import os
    if not os.path.exists(excel_file):
        solution_df.to_excel(excel_file, index=True, sheet_name="IVP Solution")

    with pd.ExcelWriter(excel_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        solution_df.to_excel(writer, index=True, sheet_name="IVP Solution")
        acceleration_df.to_excel(writer, index=False, sheet_name="Accelerations")
        lagrande_df.to_excel(writer, index=False, sheet_name="Lagrande Multipliers")

    print(lagrande_df.head(0))

    import matplotlib.pyplot as plt
    # plt.plot(lagrande_df['rel-rev short-arm ground'])
    # plt.show()

    from Animation import Animation
    Animation(solverBodies, solverJoints, solution_df, T_eval, limit=limit, speed=0.5)