"""Orthographic mesh previews and an explicit section outline for visual QA."""

import math
from pathlib import Path

from PIL import Image, ImageDraw


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(vector):
    length = math.sqrt(dot(vector, vector))
    return tuple(value / length for value in vector)


def canvas(points, title):
    width, height = 900, 700
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = min((width - 80) / max(xmax - xmin, 1e-8), (height - 100) / max(ymax - ymin, 1e-8))
    def pixel(point):
        return (width / 2 + (point[0] - (xmin + xmax) / 2) * scale,
                (height + 40) / 2 - (point[1] - (ymin + ymax) / 2) * scale)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 15), title, fill="black")
    draw.text((20, 35), f"Envelope: {xmax-xmin:.2f} x {ymax-ymin:.2f} mm", fill="black")
    return image, draw, pixel


def render_mesh(triangles, output: Path, axis="y", position=0.0):
    output.mkdir(parents=True, exist_ok=True)
    cameras = {"top": (0, 0, 1), "front": (0, -1, 0), "right": (1, 0, 0),
               "underside": (0, 0, -1), "isometric": (1, -1, 1)}
    paths = []
    for name, direction in cameras.items():
        look = normalize(direction)
        world_up = (0, 1, 0) if abs(look[2]) > 0.98 else (0, 0, 1)
        right = normalize(cross(world_up, look))
        up = cross(look, right)
        projected = [[(dot(vertex, right), dot(vertex, up)) for vertex in triangle] for triangle in triangles]
        image, draw, pixel = canvas([point for triangle in projected for point in triangle], f"{name} | mesh projection | camera {direction}")
        order = sorted(range(len(triangles)), key=lambda index: sum(dot(vertex, look) for vertex in triangles[index]))
        for index in order:
            a, b, c = triangles[index]
            normal = cross(tuple(b[i] - a[i] for i in range(3)), tuple(c[i] - a[i] for i in range(3)))
            length = math.sqrt(dot(normal, normal))
            shade = 0.55 + 0.4 * abs(dot(normal, look)) / length if length else 0.55
            color = tuple(int(value * shade) for value in (117, 166, 194))
            draw.polygon([pixel(point) for point in projected[index]], fill=color)
        path = output / f"{name}.png"
        image.save(path)
        paths.append(path)
    cut_axis = "xyz".index(axis)
    visible_axes = [index for index in range(3) if index != cut_axis]
    segments = []
    for triangle in triangles:
        distances = [vertex[cut_axis] - position for vertex in triangle]
        if all(abs(value) < 1e-7 for value in distances):
            continue
        hits = []
        for index in range(3):
            a, b = triangle[index], triangle[(index + 1) % 3]
            da, db = distances[index], distances[(index + 1) % 3]
            if abs(da) < 1e-7:
                hits.append(a)
            if da * db < 0:
                ratio = da / (da - db)
                hits.append(tuple(a[i] + ratio * (b[i] - a[i]) for i in range(3)))
        unique = {tuple(round(value, 6) for value in point) for point in hits}
        if len(unique) == 2:
            segments.append([tuple(point[index] for index in visible_axes) for point in unique])
    if not segments:
        raise ValueError("section plane does not cross the mesh")
    image, draw, pixel = canvas([point for segment in segments for point in segment], f"section {axis}={position:g} mm | triangle-plane intersection")
    for segment in segments:
        draw.line([pixel(point) for point in segment], fill="black", width=2)
    path = output / f"section-{axis}-{position:g}.png"
    image.save(path)
    paths.append(path)
    return paths
