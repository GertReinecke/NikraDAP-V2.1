import numpy as np

def quaternion_from_euler(roll, pitch, yaw):
    """
    Convert an Euler angle to a quaternion.
  
    Input
        :param roll: The roll (rotation around x-axis) angle in radians.
        :param pitch: The pitch (rotation around y-axis) angle in radians.
        :param yaw: The yaw (rotation around z-axis) angle in radians.

    Output
        :return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
    """
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)

    return [qx, qy, qz, qw]

def calculate_rotation(target_vector):
    import numpy as np
    from scipy.spatial.transform import Rotation as R

    # Reference vector (0, 0, 1)
    reference_vector = np.array([0, 0, 1])
    
    # Normalize the target vector
    target_vector = target_vector / np.linalg.norm(target_vector)
    
    # Compute the rotation axis (cross product of reference and target vectors)
    rotation_axis = np.cross(reference_vector, target_vector)
    
    # Compute the angle between the vectors (dot product)
    angle = np.arccos(np.dot(reference_vector, target_vector))
    
    # Handle the case where the target vector is exactly opposite to the reference vector
    if np.linalg.norm(rotation_axis) == 0:
        if np.dot(reference_vector, target_vector) < 0:
            rotation_axis = np.array([1, 0, 0])  # Arbitrary axis
            angle = np.pi
        else:
            return np.array([0, 0, 0])  # No rotation needed
    
    # Normalize the rotation axis
    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
    
    # Create the rotation object
    rotation = R.from_rotvec(rotation_axis * angle)
    
    # Get the Euler angles (in radians)
    euler_angles = rotation.as_euler('xyz')
    
    return euler_angles

angels = calculate_rotation([0, 0, 1])
print(quaternion_from_euler(*angels))