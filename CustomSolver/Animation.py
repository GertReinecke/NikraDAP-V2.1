from Body import DAPBody
from Joint import DAPJoint

import numpy as np
import pandas as pd

import matplotlib; matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def dapvec(x, y):
    return np.array([[x], [y]])


def A_matrix(phi):
    if type(phi) == np.ndarray:
        phi = phi[0]
    return np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])


def DAPPlot(solverBodies, dataframe, i):

    fig, ax = plt.subplots()

    for body in solverBodies:
        bodyPosition = [dataframe[f'x {body.name}'].iloc[i], dataframe[f'y {body.name}'].iloc[i]]
        bodyAngle = dataframe[f'phi {body.name}'].iloc[i]

        print(f'bodyAngle {body.name}', bodyAngle)
        print(f'bodyPosition {body.name}', bodyPosition)

        bodyPointsX = []
        bodyPointsY = []
        for point in body.getPoints():
            bodyPointsX.append((bodyPosition + A_matrix(bodyAngle) @ point)[0])
            bodyPointsY.append((bodyPosition + A_matrix(bodyAngle) @ point)[1])

        linestyle = 'solid'
        marker = 'o'
        if body.name == 'ground':
            linestyle = 'none'
            marker = 'x'

        ax.plot(bodyPointsX, bodyPointsY, label=body.name, linestyle=linestyle, marker=marker)

    plt.title(f'Pendulum at time {i}')
    plt.legend()
    plt.show()


def Animation(solverBodies, solverJoints, dataframe, T_eval, limit=None, speed=1):
    if limit is None:
        limit = [(-0.5, 0.5), (-0.5, 0.5)]

    fig, ax = plt.subplots()

    # Set the aspect of the plot to be equal
    ax.set_aspect('equal')

    lines = []

    for body in solverBodies:
        line, = ax.plot([], [], label=body.name)
        lines.append(line)

    # Text object for displaying the frame number
    frame_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

    def init():
        ax.set_xlim(limit[0])
        ax.set_ylim(limit[1])
        frame_text.set_text('')
        return lines + [frame_text]

    def animate(i):
        for body, line in zip(solverBodies, lines):
            bodyPosition = np.array([dataframe[f'x {body.name}'].iloc[i], dataframe[f'y {body.name}'].iloc[i]])
            bodyAngle = dataframe[f'phi {body.name}'].iloc[i]

            # Precompute the transformation matrix
            A = A_matrix(bodyAngle)

            bodyPoints = np.array(body.getPoints())
            transformed_points = bodyPosition + bodyPoints @ A.T

            line.set_data(transformed_points[:, 0], transformed_points[:, 1])
            if body.name == 'ground':
                line.set_linestyle('none')
                line.set_marker('x')
            else:
                line.set_linestyle('solid')
                line.set_marker('o')

        frame_text.set_text(f'Time: {T_eval[i]:.2f} s')
        plt.title(f'Pendulum at time {T_eval[i]:.2f} s')

        return lines + [frame_text]

    # Calculate interval in milliseconds (0.01 s = 10 ms)
    interval = int((T_eval[1] - T_eval[0]) * 1000 / speed)

    ani = animation.FuncAnimation(fig, animate, frames=len(dataframe), init_func=init,
                                  interval=interval, blit=True, repeat=False)
    plt.show()