#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 10:46:05 2024

@author: gabrielmiyazawa
"""


import numpy as np
import copy
import os


# Save whatever for debugging
def show_results(var, name):
    txt_out = os.path.join(os.getcwd(), '{}.txt'.format(name))
    if type(var[0]) != int:
        var_out = sorted(var, key=lambda x: x[0])
    else:
        var_out = var
    with open(txt_out, 'w') as file:
        file.write(str(var_out))
    print('{} saved at:'.format(name), txt_out)


class NoteMapper:
    def __init__(self, staff_groups):
        self.staff_groups = staff_groups
        self.labels = ['fa', 'mi', 're', 'do', 'si', 'la', 'sol']
        self.label_map = self.Staff_Map()



    def get_label(self, index):
        label_index = index % len(self.labels)
        cycle_count = index // len(self.labels)
        label = self.labels[label_index]
        return f'{label}_{cycle_count}'
    
    
    
    def get_note_label(self, note_centre):
        min_distance = float('inf')
        closest_label = None
    
        # Iterate over each subgroup's label_map
        for group_map in self.label_map:
            for y in group_map:
                distance = abs(y - note_centre)
                if distance < min_distance:
                    min_distance = distance
                    closest_label = group_map[y]
        
        return closest_label
    
    
    
    def get_ledger_label(self, note_centre, group):
        differences = [(group[i+1] - group[i]) for i in range(len(group) - 1)]
        mean_difference = np.mean(differences) if differences else 0
    
        label_up = note_centre > max(group)
        label_down = note_centre < min(group)
    
        # Calculate the label based on extrapolation
        # Sums and subtractions by 1 to adjust for index counter starting point
        if label_up:
            steps = round((note_centre - max(group)) / mean_difference) - 1
            extrapolated_index = (len(group) - 1) + steps

        elif label_down:
            steps = round((min(group) - note_centre) / mean_difference)
            extrapolated_index = -steps - 1
            
        else:
            print('Error in get_ledger_label. Input not a ledger note.', '\n',\
                  len(group)+'elements in single staff. Expected 11')
    
        # Return the label corresponding to the extrapolated index for the ledger note
        return self.get_label(extrapolated_index)

    


    def mean_staff_halfspace(self, group):
        differences = [(group[i+1] - group[i]) / 2 for i in range(len(group) - 1)]
        mean_difference = np.mean(differences) if differences else 0
        return mean_difference
    
    

    def staff_padding(self, group, label_map):
        mean_difference = self.mean_staff_halfspace(group)
        
        # Calculate padding values
        lower_padding = round(group[0] - mean_difference)
        upper_padding = round(group[-1] + mean_difference)

        # Identify labels and cycles for padding
        first_label, first_cycle = label_map[group[0]].split('_')
        last_label, last_cycle = label_map[group[-1]].split('_')

        first_label_index = self.labels.index(first_label)
        last_label_index = self.labels.index(last_label)

        # Calculate new labels and cycles for padding
        lower_label_index = (first_label_index - 1) % len(self.labels)
        upper_label_index = (last_label_index + 1) % len(self.labels)

        lower_cycle = int(first_cycle) - 1 if first_label_index == 0 else int(first_cycle)
        upper_cycle = int(last_cycle) + 1 if last_label_index == len(self.labels) - 1 else int(last_cycle)

        lower_label = self.labels[lower_label_index]
        upper_label = self.labels[upper_label_index]

        # Assign new labels to padding values
        label_map[lower_padding] = f"{lower_label}_{lower_cycle}"
        label_map[upper_padding] = f"{upper_label}_{upper_cycle}"



    def Staff_Map(self):
        all_maps = []  # List to hold each group's mapping dictionary
        
        for group in self.staff_groups:
            label_map = {}
            index = 0  # Reset label index for each subgroup
            extended_group = []
    
            # Calculate and append midpoints, rounding them to the nearest integer
            for i in range(len(group) - 1):
                extended_group.append(group[i])
                midpoint = round((group[i] + group[i+1]) / 2)
                extended_group.append(midpoint)
            extended_group.append(group[-1])  # Append the last element
    
            # Assign labels to the coordinates and midpoints using the get_label method
            for y in extended_group:
                label_map[y] = self.get_label(index)
                index += 1
                
            # Add padding to label map
            self.staff_padding(group, label_map)
            label_map = dict(sorted(label_map.items()))
            all_maps.append(label_map)
    
        return all_maps
    


    def Label_Notes(self, Notes):
        # Create a shallow copy of the Notes list. This is enough since tuples are immutable and you're adding not modifying tuples.
        notes = copy.copy(Notes)
        
        for i in range(len(notes)):
            rect = notes[i]
            y_mid = (rect[0][1] + rect[1][1]) / 2  # Calculate the midpoint of the y-coordinates
    
            # Iterate over each group's mappings in label_map
            for label_map in self.label_map:
                group_keys = list(label_map.keys())
                mean_difference = self.mean_staff_halfspace(group_keys)
                tolerance = mean_difference * (2/3)  # Two-thirds of the mean distance to the next gap-space
    
                # Check using the keys of the current label_map dictionary
                if (min(group_keys) - tolerance) <= y_mid <= (max(group_keys) + tolerance):
                    # Find the closest label to this midpoint
                    label = self.get_note_label(y_mid)
                    
                    y_start, y_end = group_keys[1], group_keys[-2]
                    
                    new_rect = rect + (label,) + ((y_start, y_end),)
                    notes[i] = new_rect
                    break  # Break the loop once a matching group is found
    
        return notes


    
    
    def check_linked_staff(self, centroids, y_range):
        # Check if there are centroids aligned vertically towards the y-range
        start_y, end_y = y_range[0], y_range[-1]
        return any(c[1] <= start_y or c[1] >= end_y for c in centroids)
    
    
    def find_associated_y_ranges(self, centroids, rectangles, y_ranges):
        # Convert y_ranges to more accessible format, each as a tuple of min and max y
        processed_y_ranges = [list(d.keys()) for d in y_ranges]
        
        rectangle_associations = []
    
        for rect in rectangles:
            x1, y1, x2, y2 = rect[0][0], rect[0][1], rect[1][0], rect[1][1]
            # x1, y1, x2, y2 = rect[0], rect[1], rect[2], rect[3] 
            y_mid = (y1 + y2) / 2
            
            # Find centroids within this rectangle
            contained_centroids = [c for c in centroids if x1 <= c[0] <= x2 and y1 <= c[1] <= y2]
    
            if not contained_centroids:
                continue
    
            # Identify the nearest y-range based on the rectangle's vertical position
            closest_y_range = None
            min_distance = float('inf')
    
            for y_range in processed_y_ranges:
                distance = min(abs(y_range[0] - y_mid), abs(y_range[1] - y_mid))
                if distance < min_distance:
                    min_distance = distance
                    closest_y_range = y_range
    
            # Validate the closest y-range by checking for a succession of centroids
            if self.check_linked_staff(centroids, closest_y_range):
                rectangle_associations.append((rect, closest_y_range))
    
        return sorted(rectangle_associations, key=lambda x: x[0][0][1])



    def Label_Ledger_Notes(self, Notes, centroids):
        staff_maps = self.Staff_Map()
        
        # Save a sorted copy of the full array of notes and a simplified array containing only the coordinates
        maped_notes = copy.copy(Notes)
        maped_notes = sorted(maped_notes, key=lambda x: x[0][1])
        
        # map_notes = [(rect[0][0], rect[0][1], rect[1][0], rect[1][1]) for rect in maped_notes]
        # map_notes = sorted(map_notes, key=lambda x: x[1])
        
        ind = [index for index, note in enumerate(maped_notes) if len(note) < 5]

        # Find related staff to each ledger note
        associated_staff = self.find_associated_y_ranges(centroids, maped_notes, staff_maps)
        # for lin in associated_staff:
        #     print(lin)
        
        j = 0
        for i in ind:
            # (x1, y1, x2, y2) = map_notes[i]
            (x1, y1), (x2, y2), _, _ = maped_notes[i]

            y_mid = (y1 + y2) / 2
            
            # Find centroids within this rectangle
            contained_centroids = [c for c in centroids if x1 <= c[0] <= x2 and y1 <= c[1] <= y2]
            
            if not contained_centroids:
                # j += 1
                continue
            
            associated_y_range = associated_staff[j][1]
            y_start, y_end = associated_y_range[1], associated_y_range[-2]
            
            label = self.get_ledger_label(y_mid, associated_y_range)  # Get the label based on y_mid
            maped_notes[i] = maped_notes[i] + (label,) + ((y_start, y_end),) # Append the label to the rectangle
            
            j += 1
            
        return maped_notes
    
    

def Notes_Mapper(base_path, out_path):
    
    import ast
    import cv2
    from collections import Counter
    
    # os.chdir(out_path)

    staff_std_txt = os.path.join(out_path,'std_staffs.txt')
    matches_txt = os.path.join(out_path, 'matches_notes.txt')
    centroids_txt = os.path.join(out_path,'centroids.txt')
    
    print('Staff standard path:', staff_std_txt)
    print('Note matches path:', matches_txt) 
    print('Centroids path:', centroids_txt)
    
    staves_coord = []
    with open(staff_std_txt, 'r') as file:
        for line in file:
            tuple_staves_coord = ast.literal_eval(line.strip())
            staves_coord.append(tuple_staves_coord)
    staff_groups = staves_coord[0]

    with open(matches_txt, 'r') as file:
        data = file.read().strip()
        rect_list = sorted(ast.literal_eval(data), key=lambda x: x[0][1])
    
    with open(centroids_txt, 'r') as file:
        data = file.read().strip()
        centroids = ast.literal_eval(data)

    

    mapper = NoteMapper(staff_groups)
    notes_map = mapper.label_map    # Just checking
    
    labeled_notes = mapper.Label_Notes(rect_list)
    
    notes_mapped_count = []
    for i in range(len(labeled_notes)):
        if len(labeled_notes[i]) > 4:
            notes_mapped_count.append(labeled_notes[i][4])
    label_counts = Counter(label for label in notes_mapped_count)
    for label, count in label_counts.items():
        print(f"'{label}': {count} times.")
    
    
    # Manual centroids aka mid point
    'Corrected unlabled notes, missmatch with wrong staff'
    pseud_centroids = []
    for item in labeled_notes:
        if len(item) < 5:
            (x1, y1), (x2, y2) = item[:2]
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2
            pseud_centroids.append((x_mid, y_mid))
    
    
    all_notes_labeled = mapper.Label_Ledger_Notes(labeled_notes, pseud_centroids)
    
    
    # Order labelled notes
    to_midi = [note for note in all_notes_labeled if len(note) == 6]
    to_midi.sort(key=lambda x: x[0][0])
    to_midi.sort(key=lambda x: x[-1][0])
    
    matches_outpath = os.path.join(out_path, 'to_midi_notes.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(to_midi))
        
        
    image_path = os.path.join(out_path, 'all_so_far.png')
    img = cv2.imread(image_path)
    for item in all_notes_labeled:
        if len(item) > 4:
            start_point, end_point, label = item[0], item[1], item[4]
            text_position = (start_point[0]+35, (start_point[1]+end_point[1])//2)
    
            # Font settings
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_color = (0)
            line_type = 2
            
            cv2.putText(img, label, text_position, font, font_scale, font_color, line_type)

    new_image_path = os.path.join(out_path,'labeled_notes.png')
    cv2.imwrite(new_image_path, img)

    matches_outpath = os.path.join(out_path, 'labeled_notes.txt')
    all_labeled = sorted(all_notes_labeled, key=lambda x: x[0][1])
    with open(matches_outpath, 'w') as file:
        file.write(str(all_labeled))
        print('Cleffs matches saved to:', matches_outpath)
    
 
    
    
    
    
if __name__ == '__main__':
    
    
    out_path = '/Users/gabrielmiyazawa/Desktop/Cods/algs/MIDI_Scripts/out/'

    Notes_Mapper(out_path, out_path)
    
 
    
    
    
    
    
    
    
    
    
    