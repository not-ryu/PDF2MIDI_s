#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 13:14:40 2024

@author: gabrielmiyazawa
"""

import math
import numpy as np
import cv2
import os

def line_length(line):
    x1, y1, x2, y2 = line
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def filter_lines_by_length(lines, min_length):
    return [line for line in lines if line_length(line) >= min_length]


def std_barlines(lines, min_length = 200, y_proximity_threshold=100):
    """
    Standardizes the size (length) of lines based on the vertical proximity of their midpoints.

    :param standardized_lines: List of line segments, where each line is represented as [x1, y1, x2, y2].
    :param y_proximity_threshold: Maximum allowed vertical distance between midpoints to consider lines as part of the same group (in pixels).
    :return: List of lines with standardized sizes.
    """
    
    standardized_lines = filter_lines_by_length(lines, min_length)

    if not standardized_lines:
        return []

    # Calculate the midpoint for each line and store it with the line
    lines_with_midpoints = []
    
    for line in standardized_lines:
        x1, y1, x2, y2 = line
        midpoint_y = (y1 + y2) / 2
        lines_with_midpoints.append((midpoint_y, line))

    # Sort lines by their midpoints
    lines_with_midpoints.sort(key=lambda x: x[0])

    standardized_size_lines = []
    current_batch = []

    for midpoint_y, line in lines_with_midpoints:
        if not current_batch:
            current_batch.append((midpoint_y, line))
            continue

        # Get the midpoint of the last line in the current batch
        last_midpoint_y = current_batch[-1][0]

        # Check if the current line's midpoint is within the y_proximity_threshold of the last line's midpoint
        if abs(midpoint_y - last_midpoint_y) <= y_proximity_threshold:
            current_batch.append((midpoint_y, line))
        else:
            # Standardize the size of the current batch
            min_y = int(min([min(l[1][1], l[1][3]) for l in current_batch]))
            max_y = int(max([max(l[1][1], l[1][3]) for l in current_batch]))
            for _, l in current_batch:
                x1, y1, x2, y2 = l
                standardized_size_lines.append([[x1, min_y, x2, max_y]])

            # Start a new batch
            current_batch = [(midpoint_y, line)]

    # Standardize the size of the final batch
    if current_batch:
        min_y = int(min([min(l[1][1], l[1][3]) for l in current_batch]))
        max_y = int(max([max(l[1][1], l[1][3]) for l in current_batch]))
        for _, l in current_batch:
            x1, y1, x2, y2 = l
            standardized_size_lines.append([[x1, min_y, x2, max_y]])

    return standardized_size_lines



def get_barline(stem_lines_var,image_path, out_path, min_length = 200):
    # Check if input is a string or file
    if isinstance(stem_lines_var, str) and stem_lines_var.endswith('.txt') and os.path.isfile(stem_lines_var):
        with open(stem_lines_var, 'r') as file:
            data = file.read().strip()
            stem_lines = ast.literal_eval(data)
    elif isinstance(stem_lines_var, list) and all(isinstance(item, tuple) and len(item) == 2 for item in stem_lines_var):
        stem_lines = stem_lines_var
    stem_lines = [[x1, y1, x2, y2] for ((x1, y1), (x2, y2)) in stem_lines]
        
    # Main processing function
    filtered_lines = std_barlines(stem_lines, min_length)
    
    # Save lines' coordinates in txt
    txt_outpath = os.path.join(out_path, 'measures.txt')
    fine_barlines = sorted(filtered_lines, key=lambda x: x[0][1])
    fine_barlines = [((x1, y1), (x2, y2)) for [[x1, y1, x2, y2]] in fine_barlines]
    with open(txt_outpath, 'w') as file:
        file.write(str(fine_barlines))
        print('Standardized barlines saved at:', txt_outpath)
        
    # Draw
    if isinstance(image_path, str):  # Check if image_input is a file path
        binary = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Read image from file path
    else:
        binary = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)  # Convert image array to grayscale
    contour_image = np.zeros_like(binary)
    contour_image_rgb = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
    for line in filtered_lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(contour_image_rgb, (x1, y1), (x2, y2), (0,0,255), 2)
    result_path = os.path.join(out_path, 'measures.png')
    cv2.imwrite(result_path, contour_image_rgb)


    return fine_barlines


if __name__ == '__main__':
    
    import ast
    
    out_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_2/'
    
    stems_txt = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_2/stems_lines.txt'
    image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_2/morph_stems.png'
    
    with open(stems_txt, 'r') as file:
        data = file.read().strip()
        stem_lines = ast.literal_eval(data)
    stem_lines = [[x1, y1, x2, y2] for ((x1, y1), (x2, y2)) in stem_lines]
    
    # Load the image
    if isinstance(image_path, str):  # Check if image_input is a file path
        binary = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Read image from file path
    else:
        binary = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)  # Convert image array to grayscale

    
    contour_image = np.zeros_like(binary)
    contour_image_rgb = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
        
    filtered_lines = std_barlines(stem_lines, min_length = 200)
    
    # Draw the long, refined lines on binary image
    for line in filtered_lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(contour_image_rgb, (x1, y1), (x2, y2), (0,0,255), 2)

    result_path = os.path.join(out_path, 'measures.png')
    cv2.imwrite(result_path, contour_image_rgb)















