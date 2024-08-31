import numpy as np

# Normalize the normal vector
def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
        return v
    return v / norm

# Example usage
normal = np.array([1, 1, 1])
normal = normalize(normal)
print('Normal:', normal)

# First Vector
if normal[0] != 0 or normal[1] != 0:
    plane_x = np.array([-normal[1], normal[0], 0])
else:
    # If the normal vector is along z-axis, choose vectors along x and y axis
    plane_x = np.array([1, 0, 0])
plane_x = normalize(plane_x)
print('Plane X:', plane_x)

# Compute Plane Y ensuring orthogonality
plane_y = np.cross(normal, plane_x)
plane_y = normalize(plane_y)
print('Plane Y:', plane_y)

# Projecting a point onto the plane defined by the normal
point = np.array([1, 2, 1])
dot_product = np.dot(point, normal)
projected_point = point - dot_product * normal

# Coordinates in the plane
x_coord = np.dot(projected_point, plane_x)
y_coord = np.dot(projected_point, plane_y)

print('Projected Point:', projected_point)
print('X Coord:', x_coord)
print('Y Coord:', y_coord)