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
    return np.linalg.norm(a - b)


def find_center(traces):
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
    return point + (point - center) * (factor - 1)


def resize(symbol):
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


def draw(symbol):
    grid = np.zeros((FRAME_SIZE, FRAME_SIZE))
    new_symbol = resize(symbol)
    for trace in new_symbol.traces:
        for i in range(1, len(trace)):
            # Start point always has smaller x
            start_point, end_point = sorted([trace[i - 1], trace[i]], key=lambda p: p[1])
            start_y, start_x = start_point
            end_y, end_x = end_point
            if int(start_x) == int(end_x):
                x = int(start_x)
                for y in range(int(start_y), int(end_y) + 1):
                    if x in range(FRAME_SIZE) and y in range(FRAME_SIZE):
                        grid[x][y] = 1
            else:
                gradient = (end_y - start_y) / (end_x - start_x)
                for x in range(int(start_x), int(end_x) + 1):
                    y = int((x + 0.5 - start_x) * gradient + start_y)
                    if x in range(FRAME_SIZE) and y in range(FRAME_SIZE):
                        grid[x][y] = 1

            # Start point always has smaller y
            start_point, end_point = sorted([trace[i - 1], trace[i]], key=lambda p: p[0])
            start_y, start_x = start_point
            end_y, end_x = end_point
            if int(start_y) == int(end_y):
                y = int(start_y)
                for x in range(int(start_x), int(end_x) + 1):
                    if x in range(FRAME_SIZE) and y in range(FRAME_SIZE):
                        grid[x][y] = 1
            else:
                gradient = (end_x - start_x) / (end_y - start_y)
                for y in range(int(start_y), int(end_y) + 1):
                    x = int((y + 0.5 - start_y) * gradient + start_x)
                    if x in range(FRAME_SIZE) and y in range(FRAME_SIZE):
                        grid[x][y] = 1
    return grid


if __name__ == '__main__':
    numbering = 1
    for filename in listdir(getcwd()):
        if filename.endswith('.inkml'):
            with open(filename, 'r') as f:
                inkml_str = f.read()
            expression = Expression(inkml_str)
            symbols = expression.symbols()
            for symbol in symbols:
                print(numbering, symbol.truth)
                array = draw(symbol)
                img = to_image(array)
                truth_string = symbol.truth.replace('\\', '')
                img.save(str(numbering) + '   ' + truth_string + '.png')
                numbering += 1
