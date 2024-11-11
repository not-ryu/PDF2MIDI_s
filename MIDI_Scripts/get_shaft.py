import cv2
import numpy as np
import matplotlib.pyplot as plt
import os


def merge_bars(lines, x_threshold, y_threshold):
    # Initial sorting by y-coord, then x-coord
    lines.sort(key=lambda line: ((line[0][1] + line[1][1]) / 2, line[0][0]))

    merged_lines = []
    while lines:
        base_line = lines.pop(0)
        merged = False

        for i, target_line in enumerate(merged_lines):
            if check_merge(base_line, target_line, y_threshold, x_threshold):
                merged_lines[i] = merge_pair(base_line, target_line)
                merged = True
                break

        if not merged:
            merged_lines.append(base_line)

    return merged_lines

def check_merge(line1, line2, vertical_threshold, horizontal_gap_threshold):
    # Calculate vertical and horizontal differences
    avg_y1 = (line1[0][1] + line1[1][1]) / 2
    avg_y2 = (line2[0][1] + line2[1][1]) / 2
    vertical_diff = abs(avg_y1 - avg_y2)

    # Check for horizontal overlap or closeness
    max_left = max(line1[0][0], line2[0][0])
    min_right = min(line1[1][0], line2[1][0])
    horizontal_overlap = min_right - max_left

    # Lines are considered mergeable if they are close vertically and either
    # overlap horizontally or are within a gap threshold
    return vertical_diff <= vertical_threshold and (horizontal_overlap > 0 or abs(horizontal_overlap) <= horizontal_gap_threshold)

def merge_pair(line1, line2):
    # Merging by taking outermost x-coord and averaging y-coord
    new_x_initial = min(line1[0][0], line2[0][0])
    new_x_final = max(line1[1][0], line2[1][0])
    new_y_initial = round((line1[0][1] + line1[1][1] + line2[0][1] + line2[1][1]) / 4)
    new_y_final = new_y_initial

    return ((new_x_initial, new_y_initial), (new_x_final, new_y_final))




def contour_notebar(image_path, output_path, separate_kernel = (7,7), blur_threshold = 200, \
                    x_threshold=10, y_threshold=5):
    
    if __name__ == '__main__':
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    else: 
        image = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)
    
    ### Improve (NO MORE KERNELS PLEASE)
    # Remove edges
    blurred = cv2.GaussianBlur(image, separate_kernel, 0)
    _, binary_image = cv2.threshold(blurred, blur_threshold, 255, cv2.THRESH_BINARY)

    # Remove smaller objects
    kernel = np.ones((4, 20), np.uint8)
    binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
    ###


    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by size (area)
    size_threshold = 80 
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > size_threshold]    
    
    line_coords = []
    # Calculate line coordinates
    for cnt in contours:
        # Get bounding box coordinates for each contour
        x, y, width, height = cv2.boundingRect(cnt)
        leftmost = x
        rightmost = x + width
        midpoint_y = y + height // 2
    
        line_coords.append(((leftmost, midpoint_y), (rightmost, midpoint_y)))
        
    bar_coords = merge_bars(line_coords, x_threshold, y_threshold)
        
    return binary_image, large_contours, bar_coords


def contour_stem(image_path, output_path):
    
    if __name__ == '__main__':
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    else: 
        image = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)
                
    # Ensure image is binary
    _, binary_image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    line_coords = []
    # Calculate line coordinates
    for cnt in contours:
        x, y, width, height = cv2.boundingRect(cnt)
        topmost = y
        bottommost = y + height
        midpoint_x = x + width // 2
    
        line_coords.append(((midpoint_x, topmost), (midpoint_x, bottommost)))
    
    return image, contours, line_coords

