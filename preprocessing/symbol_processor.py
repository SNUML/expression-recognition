from PIL import Image
import numpy as np
from expression_loader import Expression
from copy import deepcopy
from os import listdir, getcwd

COLOR_MAX = 255
FRAME_SIZE = 40
IMAGE_SIZE = 50

assert FRAME_SIZE % 2 == 0
assert IMAGE_SIZE % 2 == 0
assert FRAME_SIZE <= IMAGE_SIZE


def to_image(binary_list, invert=True):
    """Receives image in 2d binary list form and returns Image."""
    assert all([all(x in (0, 1) for x in line) for line in binary_list])
    binary_array = np.asarray(binary_list, dtype='uint8')
    borderless_png_array = binary_array * COLOR_MAX
    png_array = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype='uint8')
    padding = (IMAGE_SIZE - FRAME_SIZE) // 2
    for i in range(FRAME_SIZE):
        for j in range(FRAME_SIZE):
            png_array[i + padding][j + padding] = borderless_png_array[i][j]

    if invert:
        full_white = np.full((IMAGE_SIZE, IMAGE_SIZE), COLOR_MAX, dtype='uint8')
        png_array = full_white - png_array
    # padding

    return Image.fromarray(png_array)


def distance(a, b):
    """Returns euclidean distance between two points."""
    return np.linalg.norm(a - b)


def find_center(traces):
    """Receives list of traces and returns center of mass."""
    point_sum = np.asarray([0, 0], dtype=np.float32)
    weight_sum = 0
    for trace in traces:
        for i in range(len(trace)):
            weight = 0
            for j in (i - 1, i + 1):
                if j in range(len(trace)):
                    weight += distance(trace[j], trace[i])
            point_sum += trace[i] * weight
            weight_sum += weight
    return point_sum / weight_sum


def find_limiting_point(measured_from, points):
    """Finds the point which will lie on box's border."""
    radius = 0
    limiting_point = points[0]
    for point in points:
        dst = max([abs(x) for x in point - measured_from])
        if dst > radius:
            radius = dst
            limiting_point = point
    return limiting_point, radius


def rescale(point, center, factor):
    """Shifts point away from center by multiplying distance by factor."""
    return point + (point - center) * (factor - 1)


def resize(symbol):
    """Resizes symbol to FRAME_SIZE."""
    new_symbol = deepcopy(symbol)
    center = find_center(symbol.traces)
    limiting_point, radius = find_limiting_point(center, symbol.points())
    factor = FRAME_SIZE / 2 / radius
    factor *= 0.8  # Just in case it 'overflows' the box borders
    for trace in new_symbol.traces:
        for i in range(len(trace)):
            # rescaling
            trace[i] = rescale(trace[i], center, factor)
            # re-centering
            trace[i] = np.asarray([FRAME_SIZE / 2, FRAME_SIZE / 2]) + (trace[i] - center)

    return new_symbol


def rasterized_line(start_point, end_point, axis):
    """Returns array of coordinates to represent line segment speified by arguments.

    The axis parameter determines by which axis to rasterize the line.
    The axis parameter should be 0 for x or 1 for y."""
    assert axis in (0, 1)
    axis_inv = (axis + 1) % 2

    # makes sure that start_point has smaller rel_x value.
    start_point, end_point = sorted([start_point, end_point], key=lambda p: p[axis])

    # sets relative x and y depending on the axis argument
    start_rel_x, start_rel_y = start_point[axis], start_point[axis_inv]
    end_rel_x, end_rel_y = end_point[axis], end_point[axis_inv]

    coordinates = set()
    if int(start_rel_x) == int(end_rel_x):
        rel_x = int(start_rel_x)
        for rel_y in range(int(start_rel_y), int(end_rel_y) + 1):
            if rel_x in range(FRAME_SIZE) and rel_y in range(FRAME_SIZE):
                rel_coordinate = [rel_x, rel_y]
                x, y = rel_coordinate[axis], rel_coordinate[axis_inv]
                coordinates.add((x, y))
    else:
        gradient = (end_rel_y - start_rel_y) / (end_rel_x - start_rel_x)
        for rel_x in range(int(start_rel_x), int(end_rel_x) + 1):
            rel_y = int((rel_x + 0.5 - start_rel_x) * gradient + start_rel_y)
            if rel_x in range(FRAME_SIZE) and rel_y in range(FRAME_SIZE):
                rel_coordinate = [rel_x, rel_y]
                x, y = rel_coordinate[axis], rel_coordinate[axis_inv]
                coordinates.add((x, y))

    return coordinates


def draw(symbol):
    """Rasterizes symbol to B&W image."""
    grid = np.zeros((FRAME_SIZE, FRAME_SIZE))
    new_symbol = resize(symbol)
    for trace in new_symbol.traces:
        for i in range(1, len(trace)):
            start_point, end_point = trace[i - 1], trace[i]
            coordinates_by_x = rasterized_line(start_point, end_point, 0)
            coordinates_by_y = rasterized_line(start_point, end_point, 1)
            coordinates = coordinates_by_x.union(coordinates_by_y)
            for coordinate in coordinates:
                x, y = coordinate
                grid[y][x] = 1

    return grid


resource_path = '../data/resources/'
image_save_path = '../data/train/'

if __name__ == '__main__':
    numbering = 1
    for filename in listdir(resource_path):
        if filename.endswith('.inkml'):
            with open(resource_path + filename, 'r') as f:
                inkml_str = f.read()
            expression = Expression(inkml_str)
            symbols = expression.symbols()
            for symbol in symbols:
                print(numbering, symbol.truth)
                array = draw(symbol)
                img = to_image(array)
                truth_string = symbol.truth
                #truth_string = symbol.truth.replace('\\', '')
                img.save(image_save_path + str(numbering) + '   ' + truth_string + '.png')
                numbering += 1
