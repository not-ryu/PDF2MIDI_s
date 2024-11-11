#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  2 18:07:53 2024
@author: gabrielmiyazawa
"""


import warnings
import numpy as np
from sklearn.mixture import GaussianMixture
from scipy.stats import gaussian_kde, mode
import matplotlib.pyplot as plt
import cv2
import os
import ast

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)




# Load stave coordinates from a file
def load_stave_coordinates(filename):
    staves_coord = []
    with open(filename, 'r') as file:
        for line in file:
            tuple_staves_coord = ast.literal_eval(line.strip())
            staves_coord.append(tuple_staves_coord)
    return staves_coord[0]


# Measure the variance of spacing in a group
def spacing_variance(group):
    if len(group) < 2:
        return float('inf')  # Invalid group
    return np.var(np.diff(sorted(group)))


def adjust_group_lines_anchored(group, optimal_spacing):
    # Anchor the start of the new group at the position of the first line in the original group
    start_y = min(group)  # Use the minimum y-coordinate of the group as the start

    # Generate new positions for five lines starting from this anchor point
    new_positions = [start_y + i * optimal_spacing for i in range(5)]
    return new_positions


    
def main_lines(staves_txt, out_path):
    if __name__ == '__main__':    
        staves_coord = load_stave_coordinates(staves_txt)
    else:
        staves_coord = staves_txt
        
    
    # Extract y-coordinates and sort them in descending order
    y_coords = [y1 for (_, y1), _ in staves_coord]
    y_coords.sort(reverse=True)
    
    # Calculate differences and remove small gaps
    differences = np.diff(y_coords)
    to_del = np.where(differences > -3)[0]
    differences = np.delete(differences, to_del)
    staves_coord = [coord for i, coord in enumerate(staves_coord) if i not in to_del]
    
    # Prepare data for Gaussian Mixture Model (GMM)
    data = differences.reshape(-1, 1)
    gmm = GaussianMixture(n_components=4, covariance_type='full', random_state=0)
    gmm.fit(data)
    labels = gmm.predict(data)
    
    # Plot and visualize the clusters
    # indices = np.arange(len(data))
    # plt.scatter(indices, data, c=labels, cmap='viridis', edgecolor='k', s=50)
    # plt.colorbar()
    # plt.show()
    
    # # Determine the most representative point in each cluster
    # max_size = 0
    # for i in range(gmm.n_components):
    #     cluster_points = data[labels == i]
    #     kde = gaussian_kde(cluster_points.T)
    #     density = kde(cluster_points.T)
    #     most_representative = cluster_points[np.argmax(density)]
    #     print(f"Point with highest density for cluster {i} is {most_representative}")
    
    #     # Find the largest cluster
    #     if len(cluster_points) > max_size:
    #         max_size = len(cluster_points)
    
    # # Determine the most representative point in each cluster
    # max_size = 0
    # for i in range(gmm.n_components):
    #     cluster_points = data[labels == i]
    
    #     if cluster_points.shape[1] > 1 and len(cluster_points) > 1:
    #         # Proceed with KDE if there are enough points and the points vary
    #         try:
    #             kde = gaussian_kde(cluster_points.T)
    #             density = kde(cluster_points.T)
    #             most_representative = cluster_points[np.argmax(density)]
    #             print(f"Point with highest density for cluster {i} is {most_representative}")
    #         except ValueError:
    #             print("Not enough variance or points for KDE.")
    #     else:
    #         # Use an alternative metric - mean or median
    #         # Here we use the mean, which is a reasonable choice for representative purposes
    #         most_representative = np.mean(cluster_points, axis=0)
    #         print(f"Using mean as the representative point for cluster {i} because of insufficient data for KDE: {most_representative}")
    
    #     # Find the largest cluster
    #     if len(cluster_points) > max_size:
    #         max_size = len(cluster_points)
    

    # Determine the most representative point in each cluster
    max_size = 0
    for i in range(gmm.n_components):
        cluster_points = data[labels == i]
    
        if cluster_points.shape[1] > 1 and len(cluster_points) > 1:
            # Proceed with KDE if there are enough points and the points vary
            try:
                kde = gaussian_kde(cluster_points.T)
                density = kde(cluster_points.T)
                most_representative = cluster_points[np.argmax(density)]
                print(f"Point with highest density for cluster {i} is {most_representative}")
            except ValueError:
                print("Not enough variance or points for KDE.")
        else:
            # Use an alternative metric - median or mode
            median_point = np.median(cluster_points, axis=0)
            mode_point, _ = mode(cluster_points, axis=0, keepdims = False)
            most_representative = mode_point[0] if len(mode_point) > 0 else median_point
            print(f"Using mode/median as the representative point for cluster {i} because of insufficient data for KDE: {most_representative}")
    
        # Find the largest cluster
        if len(cluster_points) > max_size:
            max_size = len(cluster_points)

    # Process the image
    print("\nDEBUG (staff_lines.py) - Trying to read loc_std_staff.png:")
    print("DEBUG (staff_lines.py) - Output directory:", out_path)
    print("DEBUG (staff_lines.py) - File exists in output directory:", os.path.exists(os.path.join(out_path, 'loc_std_staff.png')))
    
    image = cv2.imread(os.path.join(out_path, 'loc_std_staff.png'))
    height, width = image.shape[:2]
    new_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    all_in_image = cv2.imread(os.path.join(out_path, 'loc_stems+bars.png'))
    
    # Get line coordinates
    line_indices = np.array(y_coords)[::-1]
    line_left, line_right = staves_coord[0][0][0], staves_coord[0][1][0]    # Should be the same for all lines
    
    # Find staff groupings
    group_threshold = 30  # Maximum pixel distance between lines to consider in same group
    groups = []
    current_group = []
    for line_index in line_indices:
        if not current_group or line_index - current_group[-1] <= group_threshold:
            current_group.append(line_index)
        else:
            groups.append(current_group)
            current_group = [line_index]
    if current_group:
        groups.append(current_group)

    # Finding candidate reference grouping
    perfect_groups = [i for i, sublist in enumerate(groups) if len(sublist) == 5]
    print('Perfect sets of staff lines (?):')
    for stacks in perfect_groups:
        print(f'\t {stacks}:', groups[stacks])
    
    groups_length = np.abs([(i[0] - i[-1]) for i in groups if (i[0] - i[-1]) != 0])
    
    # Identify groups that are outliers based on the width of each group
    Q1 = np.percentile(groups_length, 25)
    Q3 = np.percentile(groups_length, 75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 2 * IQR
    upper_bound = Q3 + 2 * IQR
    
    outliers = np.where((groups_length < lower_bound) | (groups_length > upper_bound))[0]
    non_outliers = np.where((groups_length >= lower_bound) & (groups_length <= upper_bound))[0]
    
    print('Outliers:', groups_length[outliers], '\n\t index:', outliers)
    print('Non-Outliers:', groups_length[non_outliers], '\n\t index:', non_outliers)
    
    # Display staff groupings only
    image = cv2.imread(os.path.join(out_path, 'loc_std_staff.png'), cv2.IMREAD_GRAYSCALE)
    color_image = cv2.imread(os.path.join(out_path, 'loc_std_staff.png'), cv2.IMREAD_COLOR)
    
    median_width = np.median(groups_length)
    threshold_width = median_width - 0.20 * median_width
    
    # Selecting groups that match requirements
    staff_groups = [i for i, g in enumerate(groups) if len(g) > 2 and (max(g) - min(g)) > threshold_width]
    grouping = []
    for i in staff_groups:
        grouping.append(groups[i])
    
    # Display selected groups
    for i in staff_groups:
        group = groups[i]
        top = min(group)
        bottom = max(group)
    
        cv2.rectangle(color_image, (line_left, top), (line_right, bottom), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(out_path, 'grouped_staves.png'), color_image)
    
    # Find the group with 5 lines and the smallest variance in spacing
    optimal_group = None
    min_variance = float('inf')
    
    for group in grouping:
        if len(group) == 5:
            variance = spacing_variance(group)
            if variance < min_variance:
                min_variance = variance
                optimal_group = group

    # If an optimal group is found, calculate its mean spacing
    if optimal_group:
        optimal_spacing = np.mean(np.diff(sorted(optimal_group)))
        print(f"Optimal Group Found: {optimal_group} with spacing {optimal_spacing}")
    else:
        optimal_spacing = median_width/4
        print("No optimal group found.")
    
    height, width = image.shape[:2]
    new_image = np.zeros((height, width, 3), dtype=np.uint8)

    # Recalculate adjusted groups using the new function
    adjusted_groups_anchored = [adjust_group_lines_anchored(group, optimal_spacing) for group in grouping]
    
    # Output the adjusted groups
    print("Adjusted Groups:")
    print(adjusted_groups_anchored)
    for index, group in enumerate(adjusted_groups_anchored):
        print(f"Group {index + 1}: {group}")
        
    # Display adjusted staff groups 
    new_image = np.zeros((height, width, 3), dtype=np.uint8)
    for group in adjusted_groups_anchored:
        for y in group:
            y = int(round(y))  # Convert float to int and round
            if 0 <= y < height:  # Check if y-coordinate is within the image bounds
                cv2.line(new_image, (line_left, y), (line_right, y), (0, 0, 255), 1)
                cv2.line(all_in_image, (line_left, y), (line_right, y), (255, 0, 0), 1)

    cv2.imwrite(os.path.join(out_path, 'adjusted_staves.png'), new_image)
    cv2.imwrite(os.path.join(out_path, 'all_so_far.png'), all_in_image)
    
    # Save standardized staff y-coordinates to txt file
    txt_outpath = os.path.join(out_path, 'std_staffs.txt')

    stded_staff = sorted(adjusted_groups_anchored, key=lambda x: x[0])
    staff_ideal = [[int(x) for x in inner] for inner in stded_staff]
        
    with open(txt_outpath, 'w') as file:
        staff_list = [list(map(int, staff)) for staff in staff_ideal]
        file.write(str(staff_list))
        print('Standardized staffs saved at:', txt_outpath)

    return staff_ideal

if __name__ == '__main__':
    test_set = '/Users/gabrielmiyazawa/Desktop/Cods/algs/lose/img_out/set_4/'
    os.chdir(test_set)
    print(f"Currently using logs from: {test_set}")
    
    staff_ideal = main_lines('staves.txt', test_set)
    
    matches_outpath = os.path.join(test_set, 'ideal_lines.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(staff_ideal))







