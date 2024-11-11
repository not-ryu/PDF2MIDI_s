#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 20:32:54 2024

@author: gabrielmiyazawa
"""

import cv2
import os 
import ast
import numpy as np

    
    
def biIn_cvtOut(image_path, verb = False):
    # Initialize binary_image to None to handle cases where conditions fail
    binary_image = None
    
    # Check if image_input is a file path or an already-loaded image
    if isinstance(image_path, str):
        # Load the image as grayscale if the input is a path
        binary_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    else:
        # Assign directly if it's already an image array
        binary_image = image_path
        if verb: print('Provided image input directly')
    
    # Check if the image has been successfully loaded or assigned
    if binary_image is not None:
        # Further checks for image processing
        if binary_image.ndim == 3 and binary_image.shape[2] == 3:
            if verb: print("Image is colored BGR. Converting to grayscale...")
            binary_image = cv2.cvtColor(binary_image, cv2.COLOR_BGR2GRAY)
        elif binary_image.dtype != np.uint8:
            if verb: print("Image is not 8-bit grayscale. Converting...")
            binary_image = cv2.normalize(binary_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Check if image already colored
    if binary_image.ndim == 3 and binary_image.shape[2] == 3:
        if verb: print("Image is already a colored BGR image.")
        output_image = binary_image
    else:
        # Convert grayscale to BGR if it's not already a colored image
        if verb: print("Converting grayscale image to BGR.")
        output_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
        
    return binary_image, output_image



def find_centroids(image, y_ranges, out_path):

    binary_image, output_image = biIn_cvtOut(image)
    
    # Prepare to check against the y-ranges, excluding the exact boundary values
    roi_limits = []
    for range_pair in y_ranges:
        if len(range_pair) > 1:
            roi_limits.extend([(range_pair[i], range_pair[i + 1]) for i in range(len(range_pair) - 1)])

    # Find contours in the image
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours and calculate centroids
    centroids = []
    for contour in contours:
        if not is_in_roi(contour, roi_limits):
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroids.append((cx, cy))

    # Draw centroids on the image
    for (cx, cy) in centroids:
        cv2.circle(output_image, (cx, cy), 5, (0, 255, 0), -1)
    output_path = os.path.join(out_path, 'centroids.png')
    cv2.imwrite(output_path, output_image)
    
    # Save coordinates of centroids to txt
    txt_out = os.path.join(out_path, 'centroids.txt')
    centroids = sorted(centroids, key=lambda x: x[1])
    with open(txt_out, 'w') as file:
        file.write(str(centroids))
    print('Centroids saved at:', txt_out)

    return centroids



def is_in_roi(contour, roi_limits):
    x, y, w, h = cv2.boundingRect(contour)
    return any(lower < y + h and upper > y for (lower, upper) in roi_limits)


# def centre(rect):
#     return ((rect[0]+rect[2])/2, (rect[1]+rect[3])/2) 


# def ledge_centroid(centroid, note_rect):
#     for (xi, yi), (xf, yf), _, _ in note_rect:
#         rect_centre = centre([(xi, yi), (xf, yf)])
        
#         if is_in_roi(rect_centre, roi_limits):
            
            


#%%


if __name__ == '__main__':
    
    out_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_1/'
    image_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_1/morph_staff.png'
    staff_std_txt = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_1/std_staffs.txt'
    matches_txt = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_1/matches_notes.txt'

    os.chdir(out_path)
    
    staves_coord = []
    with open(staff_std_txt, 'r') as file:
        for line in file:
            tuple_staves_coord = ast.literal_eval(line.strip())
            staves_coord.append(tuple_staves_coord)
    staff_std = staves_coord[0]

    centroids = find_centroids(image_path, staff_std, out_path)

