#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 16:59:24 2024

@author: gabrielmiyazawa
"""


import os
import ast
import copy
from scipy.spatial import distance

def central_point(start, end=None):
    if end:
        if isinstance(start, int):
            return (start + end) // 2
        elif isinstance(start, tuple) and len(start) == 2:
            (xi, yi), (xf, yf) = start, end
            return (xi + xf) // 2, (yi + yf) // 2
    else:
        if isinstance(start[0], tuple):
            (xi, yi), (xf, yf) = start
            return (xi + xf) // 2, (yi + yf) // 2
        else:
            return (start[0] + start[1]) // 2


def group_points_by_proximity(accs, distance_threshold):
    groups = []
    
    for acc in accs:
        point = acc['loc']
        added = False

        # Attempt to add the point to an existing group
        for group in groups:
            if any(distance.euclidean(point, g['loc']) < distance_threshold for g in group):
                group.append(acc)
                added = True
                break
        
        # If the point was not added to any group, create a new group
        if not added:
            groups.append([acc])
    
    # Repeat the grouping process to ensure all points are grouped correctly
    merged = True
    while merged:
        merged = False
        new_groups = []

        while groups:
            # Take the first group
            current_group = groups.pop(0)
            
            # Check against all other groups to see if they should be merged
            for i in range(len(groups)):
                other_group = groups[i]
                
                if any(distance.euclidean(g1['loc'], g2['loc']) < distance_threshold for g1 in current_group for g2 in other_group):
                    current_group.extend(groups.pop(i))
                    merged = True
                    break
            
            # Add the current group to the new groups list
            new_groups.append(current_group)
        
        # Update groups with new merged groups
        groups = new_groups
    
    return groups

# Step 1: Group points by proximity
def find_closest_horizontally(group, lists_of_points, y_threshold=20, x_limit=50):
    closest_points = []

    for points in lists_of_points:
        bijective_match = check_bijective_match(group, points, y_threshold, x_limit)
        
        if bijective_match:
            closest_points.extend(bijective_match)
        else:
            return []  # If the group is not bijectively matched, return an empty list
    
    return closest_points

def check_bijective_match(group, candidates, y_threshold, x_limit):
    group_x_max = max(g['loc'][0] for g in group)
    group_y_min = min(g['loc'][1] for g in group)
    group_y_max = max(g['loc'][1] for g in group)

    # Filter candidates that are valid based on y-range and x-distance
    valid_candidates = [
        (i, p) for i, p in enumerate(candidates)
        if (group_x_max < p['loc'][0] <= group_x_max + x_limit and
            group_y_min - y_threshold <= p['loc'][1] <= group_y_max + y_threshold)
    ]
    
    # If the number of valid candidates doesn't match the group size, return None
    if len(valid_candidates) < len(group):
        return None

    # Try to create a bijective mapping
    closest_points = []
    used_candidate_indices = set()

    for g in group:
        best_match = None
        min_distance = float('inf')
        
        for i, p in valid_candidates:
            if i not in used_candidate_indices:  # Ensure this candidate has not been used
                distance_x = abs(p['loc'][0] - g['loc'][0])
                if distance_x < min_distance:
                    min_distance = distance_x
                    best_match = (i, p)
        
        if best_match:
            closest_points.append(best_match[1])
            used_candidate_indices.add(best_match[0])
        else:
            return None  # If no unique match found, return None
    
    return closest_points


# Step 3: Associate closest points with each group
def associate_closest_points(accs, lists_of_points, distance_threshold):
    groups = group_points_by_proximity(accs, distance_threshold)
    associated_groups = []
    for group in groups:
        closest_points = find_closest_horizontally(group, lists_of_points)
        associated_groups.append((group, closest_points))
    return associated_groups


# Step 4: Associate unmatched accidents to a clef
def find_key(matchings, clefs, y_threshold, x_limit):
    # Extract acc groups that had no matches
    unmatched_groups = [group for group, matches in matchings if not matches]
    key_matches = []

    for group in unmatched_groups:
        leftmost_acc = min(group, key=lambda g: g['loc'][0])  # Find the leftmost member of the group
        best_match = None
        min_distance = float('inf')

        # Search directly to the left
        for clef in clefs:
            clef_x_max = clef['loc'][1][0]
            clef_y_min = clef['loc'][0][1]
            clef_y_max = clef['loc'][1][1]

            # Check if the clef is directly to the left of the acc group and within the y-range
            if (clef_x_max < leftmost_acc['loc'][0] and
                clef_y_min - y_threshold <= leftmost_acc['loc'][1] <= clef_y_max + y_threshold):
                
                distance_x = leftmost_acc['loc'][0] - clef_x_max
                if distance_x < min_distance and distance_x <= x_limit:
                    min_distance = distance_x
                    best_match = clef

        # If no match found directly to the left, search using closest point within bounds
        if not best_match:
            for clef in clefs:
                clef_x_min, clef_y_min = clef['loc'][0]
                clef_x_max, clef_y_max = clef['loc'][1]

                # Determine the closest point on the clef's rectangle to the leftmost_acc
                closest_clef_x = max(clef_x_min, min(leftmost_acc['loc'][0], clef_x_max))
                closest_clef_y = max(clef_y_min, min(leftmost_acc['loc'][1], clef_y_max))

                # Calculate the distance between the leftmost_acc and the closest point on the clef
                distance_x = leftmost_acc['loc'][0] - closest_clef_x
                distance_y = abs(leftmost_acc['loc'][1] - closest_clef_y)

                # Check if the clef is to the left and within the y-range and x-distance
                if distance_x >= 0 and distance_y <= y_threshold and distance_x <= x_limit:
                    if distance_x < min_distance:
                        min_distance = distance_x
                        best_match = clef

        if best_match:
            key_matches.append((group, best_match))
    
    return key_matches


# Step 4.5: Associate unmatched accidents to a measure. Possible key change


# Step 5: For still unmacthed accidents, search individualy
def match_acc_to_notes(accs_dic, notes_dic, x_threshold=30, y_threshold=20): # accs_dic = unmatched
    matches = []

    for acc_group, _ in accs_dic:
        for acc in acc_group:
            acc_x, acc_y = acc['loc']
            closest_note = None
            min_y_distance = float('inf')

            for note in notes_dic:
                note_x, note_y = note['loc']

                y_distance = abs(acc_y - note_y)
                if y_distance <= y_threshold:
                    if acc_x < note_x and (note_x - acc_x) <= x_threshold:
                        # Check if this note is closer in y-distance than the previous closest
                        if y_distance < min_y_distance:
                            closest_note = note
                            min_y_distance = y_distance
            
            if closest_note:
                matches.append([acc, closest_note])

    return matches

# Step 6: For each element of each acc group, assign vertically ordered the note matched
def match_by_height(acc_matches):    
    matched_acc = []

    for acc_group, f_group in acc_matches:
        # Sort both groups by the y-coordinate of their 'loc' (height)
        acc_sorted = sorted(acc_group, key=lambda x: x['loc'][1])
        f_sorted = sorted(f_group, key=lambda x: x['loc'][1])

        # Pair each element from acc_sorted with the corresponding element from f_sorted
        matched_pairs = []
        for acc, f in zip(acc_sorted, f_sorted):
            # Create a new dictionary with the additional 'acc' field
            # f_with_acc = f.copy()
            # f_with_acc['acc'] = acc['label']
            # matched_pairs.append(f_with_acc)

            matched_pairs.append([f, acc])

        matched_acc.extend(matched_pairs)
    return matched_acc

# Step 7: Find key signature
def get_key_sig(key_matches):
    accident_map = {
        'as': + 1, 
        'an': 0, 
        'ab': - 1,
    }
    
    key_sig = []
    for clef in key_matches:
        cp = copy.deepcopy(clef)
        
        acc_count = len(cp[0])
        
        label = cp[0][0]['label']
        # val = accident_map[clef[0]['label']]
        val =  accident_map.get(label, 0)
        
        cp[1]['key_sig'] = val * acc_count if val !=0 else print('Invalid key signature:', val)
        raise_error = 1/val
        
        key_sig_dict = {k: v for k, v in cp[1].items() if k != 'ref'}
        key_sig.append(key_sig_dict)
        
        key_sig = sorted(key_sig, key=lambda item: item['loc'][0][1])

    return key_sig




import matplotlib.pyplot as plt
import matplotlib.patches as patches

def display_matchings(out_path, matchings, key_matches=None):
    # plt.figure(figsize=(25.6, 35.65), dpi=100)
    plt.figure(figsize=(25.95, 7.57), dpi=100)
    
    i = 0
    # Define colors, excluding red for matched groups
    # colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    colors = ['green']

    # Track groups matched by clefs to avoid coloring them red
    groups_matched_by_clef = {id(group): clef for group, clef in (key_matches or [])}

    for i, (group, closest_points) in enumerate(matchings):
        if id(group) in groups_matched_by_clef:
            color = 'cyan'
        elif closest_points:
            color = colors[i % len(colors)]
        else:
            color = 'red'

        # Plot the points in the acc group with their respective colors
        for item in group:
            plt.scatter(item['loc'][0], item['loc'][1], color=color, s = 100)
            plt.text(item['loc'][0] - 15, item['loc'][1] - 10, item['label']+','+str(len(group)),\
                     fontsize=12, color=color)

        # Plot the closest points from other lists in black
        if closest_points:
            for item in closest_points:
                plt.scatter(item['loc'][0], item['loc'][1], color='blue', s = 100)
                plt.text(item['loc'][0] + 10, item['loc'][1], item['label'], fontsize=12, color='blue')

            # Draw lines connecting group points to their closest points
            for group_point in group:
                for closest_point in closest_points:
                    plt.plot([group_point['loc'][0], closest_point['loc'][0]], 
                             [group_point['loc'][1], closest_point['loc'][1]], 
                             color=color, linestyle='dashed')

    # Draw rectangles for key matches (clefs)
    if key_matches:
        for group, clef in key_matches:
            # Draw rectangle for the clef
            clef_rect = patches.Rectangle(
                (clef['loc'][0][0], clef['loc'][0][1]),  # Bottom-left corner
                clef['loc'][1][0] - clef['loc'][0][0],   # Width
                clef['loc'][1][1] - clef['loc'][0][1],   # Height
                linewidth=2, edgecolor='cyan', facecolor='none'
            )
            plt.gca().add_patch(clef_rect)
            
            # # Draw line from the clef to the leftmost point in the acc group
            # leftmost_acc = min(group, key=lambda g: g['loc'][0])
            # plt.plot([clef['loc'][1][0], leftmost_acc['loc'][0]],
            #          [clef['loc'][1][1], leftmost_acc['loc'][1]],
            #          color='cyan', linestyle='dashed')

    plt.grid(True)
    plt.gca().invert_yaxis()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    output_path = os.path.join(out_path, 'acc_map.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()



def match_acc(out_path, group_max_dist=50, y_threshold=20, x_limit=30, plot = False):

    # os.chdir(out_path)
        
    file_paths = [
        os.path.join(out_path, 'to_midi_notes.txt'),
        os.path.join(out_path, 'matches_cleffs.txt'), 
        os.path.join(out_path, 'matches_accidents.txt')
    ]
    
    print('Classifying accidents using:\n' , file_paths)
    
    matches_data = {}
    for file_path in file_paths:
        key = os.path.splitext(file_path)[0].split('_')[-1]
        with open(file_path, 'r') as file:
            data = file.read().strip()
            matches_data[key] = ast.literal_eval(data)
            
    accs = matches_data['accidents']
    notes = matches_data['notes']
    clefs = matches_data['cleffs']
    
    accs_dic = []
    for arr in accs:
        label = arr[3].split('_')[0]
        # For flats, centre around the 2/3-of-the-way-y
        loc = ( central_point(arr[0][0], arr[1][0]),
               arr[0][1] + 2 * (arr[1][1] - arr[0][1]) // 3
               ) if label == 'ab' else central_point(arr[0:2])
        
        accs_dic.append({
            'ref': arr[0:2],
            'loc': loc,
            'label': label,
        })
        
    notes_dic = []
    for arr in notes:
        notes_dic.append({
            'ref': arr[0:2],
            'loc': central_point(arr[0:2]),
            'label': arr[3].split('_')[0],
        })
    
    clefs_dic = []
    for arr in clefs:
        clefs_dic.append({
            'ref': arr[0:2],
            'loc': arr[0:2],
            'label': arr[3].split('_')[0],
        })
     

    
    result = associate_closest_points(accs_dic, [notes_dic], group_max_dist)
    # display_matchings(out_path, result)
    
    key_matches = find_key(result, clefs_dic, x_limit=30, y_threshold=20)
    if plot: 
        display_matchings(out_path, result, key_matches)
    
    inter = [x for x in result if x[0] not in [y[0] for y in key_matches]]
    acc_matches = [k for k in inter if k[1]]
    unmatched = [k for k in inter if not k[1]]
    
    # For non-bijective groups, match closer by acc-note
    leftover_acc = match_acc_to_notes(unmatched, notes_dic, x_threshold=50, y_threshold=10)
    
    # For grouped accs with bijctive match to note's groups, sort by hight
    matched_acc = match_by_height(acc_matches)
    
    # Add key signature value to cleff
    key_sig = get_key_sig(key_matches)
    
    
    
    
    
    # Check
    all_accs = leftover_acc+matched_acc
    
    clef_acc_count = [k for j in [i[0] for i in key_matches] for k in j]
    note_acc_count = [i[1] for i in all_accs]
    acc_count = clef_acc_count + note_acc_count
    
    not_acc_note = [i for i in accs_dic if i not in acc_count]

    
    # not_acc_clef = [i for i in accs_dic if i not in (clef_acc_count + not_acc_note)]
    # print(len(not_acc_note))
    # print(f'Left uncategorized accidents: {len(not_acc_clef)}')
    
    return matched_acc, leftover_acc, key_sig
    # return result, key_matches, acc_matches, unmatched, matched_acc, key_sig, leftover_acc, all_accs, accs_dic

    

if __name__ == '__main__':
    out_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/MIDI_Scripts/out/'
    
    matched_acc, unmatched, key_sig = \
        match_acc(out_path, group_max_dist=50, y_threshold=20, x_limit=30, plot = 0)
        
    matches_outpath = os.path.join(out_path, 'note_acc.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(matched_acc))
    matches_outpath = os.path.join(out_path, 'key_sig.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(key_sig))
    
    
    
    
    
    
    
    
    
    
    
    
