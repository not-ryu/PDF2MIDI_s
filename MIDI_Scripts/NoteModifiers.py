#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 15:06:07 2024

@author: gabrielmiyazawa
"""


import numpy as np
import copy
import os
from pprint import pprint

import json
import re
from collections import defaultdict, Counter


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

def save_as_json(score, output_path):
    formatted_score = json.dumps(score, indent=4)
    
    out_path = os.path.join(output_path, 'score.json')
    with open(out_path, 'w') as file:
        file.write(formatted_score)
    print(f"Formatted score saved to: {out_path}")




class NoteMod:
    def __init__(self, notes, cleffs, rests, note_acc, key_sig):
        # Maps
        self.accident_map = {
            'as': + 1, 
            'an': 0, 
            'ab': - 1,
        }
        self.clef_map = {
            'cg': 0, 
            'cf': -21, 
            }
        self.type_map = {
            'f': 'note', 
            'o': 'note_whole', 
            }
        
        # Data
        self.notes = self._format_notes(notes)
        self.cleffs = self._format_matches(cleffs)
        self.rests = self._format_matches(rests)
        
        self.keys = self._format_keys(key_sig)
        self.accidents = note_acc
        
        # Midi Elemensts
        self.el_notes = copy.deepcopy(self.notes)


    def _format_matches(self, matches):
        formated_matches = []
        for i, arr in enumerate(matches):
            label = arr[3].split('_')[0]
            formated_matches.append({
                'loc': arr[0:2],
                'score': arr[2],
                ('clef' if label in self.clef_map else 'type'): label,
            })
        return formated_matches

    def _format_notes(self, notes):
        formated_notes = []
        for i, note in enumerate(notes):
            formated_notes.append({
                'loc': note[0:2],
                'score': note[2],
                'type': note[3].split('_')[0],
                'staff': note[5],
                'label': note[4],
                'val': self._midi_value(note[4]),
            })
        return formated_notes

    def _format_keys(self, keys):
        for key in keys:
            if 'label' in key:
                key['clef'] = key.pop('label')
            if 'key_sig' in key:
                key['key'] = key.pop('key_sig')
        return keys
        

    def _midi_value(self, note):
        notes = ['fa', 'mi', 're', 'do', 'si', 'la', 'sol']
        intervals = [1, 2, 2, 1, 2, 2]
        base_midi = 77
        
        a = note.split('_')
        if len(a) == 2:
            name, octave = a 
        else:
            name = a[0]
            octave = 0
        
        octave = int(octave)
        note_index = notes.index(name)
        
        midi_value = base_midi
        
        for i in range(note_index):
            midi_value -= intervals[i]
            
        midi_value -= octave * 12
        
        return midi_value
    
    
    def inv_map(self, fwd_map):
        return {v: k for k, v in fwd_map.items()}
            
    def circle_of_fifths(self, n):
        sharp_order = ['fa', 'do', 'sol', 're', 'la', 'mi']
        flat_order = ['si', 'mi', 'la', 're', 'sol', 'do']
        
        if abs(n) > 6:
            print(f'Bad key value: {n}')
            return None
         
        if n == 0:
            return 0
        elif n > 0:
            affected_notes = sharp_order[:n]
            return affected_notes
        else:
            n = 12 + n
            affected_notes = flat_order[:n]
            return affected_notes
    
    def change_to_keysig(self, val, affected_notes, direction):
        abs_val = val % 12
        base_midi2raise = [self._midi_value(aff_note) % 12 for aff_note in affected_notes]
        
        if abs_val in base_midi2raise:
            return val + direction
        else:
            return None
                        
    def assign_cleff(self, tolerance=0):
        el_note_locs = {el_note['loc'] for el_note in self.el_notes}
        el_note_dict = {el_note['loc']: el_note for el_note in self.el_notes}
        std_cleffs = []
        i = 0
        
        # Step 1: Find vertically aligned staff and cleffs
        for note in self.notes:
            staff_mid = central_point(note['staff'])
            staff_gap = note['staff'][1] - note['staff'][0]
            
            lower_bound = staff_mid - (staff_gap // 2 + tolerance)
            upper_bound = staff_mid + (staff_gap // 2 + tolerance)
            
            clefs_cand = []
            for clef in self.cleffs:
                cleff_x_mid, cleff_y_mid = central_point(clef['loc'])
                
                if lower_bound <= cleff_y_mid <= upper_bound:
                    
                    # Step 2: Decide if staf is before or after note
                    note_x_mid, _ = central_point(note['loc'])
                    if cleff_x_mid <= note_x_mid:
                        # all cleffs in a single staff
                        clefs_cand.append(clef)
            
            # get latest cleff for the current note
            central_x = central_point(note['loc'])[0]
            dists = [d for d in clefs_cand if (central_x - central_point(d['loc'])[0]) > 0]
            
            if dists:
                closest_dict = min(dists, key=lambda d: central_x - central_point(d['loc'])[0])
                last_clef = closest_dict['clef']

                   
            # Step 3: Modify the note value accordainly       
            if note['loc'] in el_note_locs:
                el_note = el_note_dict[note['loc']]
                el_note['clef'] = self.clef_map[last_clef]
                el_note['val'] += el_note['clef']
                            
            # Step 4: Assign the default clef at the beggining of each staff
            if len(clefs_cand) > 1:
                defaut_clef =  min(clefs_cand, key=lambda entry: central_point(entry['loc'])[0])
            else:
                defaut_clef = clefs_cand[0]
                
            if not std_cleffs or defaut_clef != std_cleffs[-1][1]:
                std_cleffs.append((i, defaut_clef))
                i += 1
            
        if std_cleffs: return std_cleffs
                
    # def assign_accident(self):
    #     accs = copy.deepcopy(self.accidents)
    #     i = 0
    #     for acc in accs:
    #         for note in self.el_notes:
    #             # Find matching reference 'f' value in acc with a 'loc' in note
    #             if acc[0]['ref'] == note['loc'] and acc[0]['label'] == note['type']:
    #                 note['acc'] = acc[1]['label']
    #                 i += 1
    #                 continue
    #             else:
    #                 note['acc'] = None

    def assign_accident(self):
        accs = copy.deepcopy(self.accidents)
        i = 0
    
        for note in self.el_notes:
            note['acc'] = None  # Default to None
            
            for acc in accs:
                # Find matching reference 'f' value in acc with a 'loc' in note
                if acc[0]['ref'] == note['loc'] and acc[0]['label'] == note['type']:
                    note['acc'] = acc[1]['label']
                    i += 1
                    break  # Stop after finding the first match
                    
        
        
        
    """
    add:
        do same as for the staff; save the defualt key sig per staff
    """
    def assign_keysig(self):
        # Count the occurrences of each 'key_sig' value
        key_sig_values = [d['key'] for d in self.keys]
        key_sig_counts = Counter(key_sig_values)
        key_sig_counts = np.transpose(list(key_sig_counts.items()))
        
        # Defauslt key signature
        std_keysig = []
        i = 0
        
        # Case 1: if the key is the same throughout, just update all val 
        if len(set(key_sig_counts[0])) == 1:
            for el_note in self.el_notes:
                el_note['key'] = key_sig_counts[0]
            std_keysig.append(copy.deepcopy(key_sig_counts[0]))
        
        # Case 2: small number of diferent key signatures
        elif max(key_sig_counts[1]) >= 0.96 * sum(key_sig_counts[1]):
            # Warn of possible mistake
            print('Possible missing accident from key signature;\n\tproceeding to assume missing match')
            
            max_index = np.argmax(key_sig_counts[1])
            assumed_val = key_sig_counts[0][max_index]
            for el_note in self.el_notes:
                el_note['key'] = assumed_val
            std_keysig.append(copy.deepcopy(assumed_val))
        
        # Case 3: use the key as it is are
        else:
            el_note_locs = {el_note['loc'] for el_note in self.el_notes}
            el_note_dict = {el_note['loc']: el_note for el_note in self.el_notes}
            
            # Step 1: Find vertically aligned staff and keys
            for note in self.notes:
                staff_mid = central_point(note['staff'])
                staff_gap = note['staff'][1] - note['staff'][0]
                
                lower_bound = staff_mid - (staff_gap // 2)
                upper_bound = staff_mid + (staff_gap // 2)
                
                keysig_cand = []
                
                for key in self.keys:
                    key_x_mid, key_y_mid = central_point(key['loc'])
                    
                    if lower_bound <= key_y_mid <= upper_bound:
                        
                        # Step 2: Decide if staf is before or after note
                        note_x_mid, _ = central_point(note['loc'])
                        if key_x_mid <= note_x_mid:
                            # Keep last key to the left of the note 
                            last_key = key['key']
                            keysig_cand.append(copy.deepcopy(key))
                                                
                # Step 4: Assign the default clef at the beggining of each staff
                if len(keysig_cand) > 1:
                    defaut_keysig =  min(keysig_cand, key=lambda entry: central_point(entry['loc'])[0])
                else:
                    defaut_keysig = keysig_cand[0]
                    
                    
                if not std_keysig or defaut_keysig != std_keysig[-1][1]:
                    std_keysig.append((i, defaut_keysig))
                    i += 1

                # Step 3: Modify the note value accordainly       
                if note['loc'] in el_note_locs:
                    el_note = el_note_dict[note['loc']]
                    el_note['key'] = last_key

                    # setp i: get notes affected by the key
                    direction = (last_key > 0) - (last_key < 0)
                    notes_to_raise = self.circle_of_fifths(last_key)
                    # step ii: change 'val' if is in the key
                    new_val = self.change_to_keysig(el_note['val'], notes_to_raise, direction)
                    if new_val: el_note['val'] = new_val

        if std_keysig: return std_keysig

    def find_chords(self, note1, note2, tolerance=10):
        # Calculate the x boundaries for both notes
        x1_start, x1_end = note1['loc'][0][0], note1['loc'][1][0]
        x2_start, x2_end = note2['loc'][0][0], note2['loc'][1][0]
    
        # Check if the x-centers are within the tolerance
        x1_center = (x1_start + x1_end) / 2
        x2_center = (x2_start + x2_end) / 2
        
        # Check if the notes are within the tolerance
        if abs(x1_center - x2_center) <= tolerance:
            return True
        
        # Check if the boundaries intersect
        if (x1_start <= x2_end and x1_end >= x2_start):
            return True
        
        return False    
        
    def order_notes(self, tolerance=10):
        # Step 1: Group by 'staff'
        grouped_by_staff = defaultdict(list)
        for note in self.el_notes:
            staff = note['staff']
            grouped_by_staff[staff].append(note)
        
        # Step 2: Create the final structured dictionary with index-based keys
        final_structure = defaultdict(lambda: {'notes': []})
        
        for index, (staff, notes) in enumerate(grouped_by_staff.items()):
            # Step 3: Sort notes by central x-coordinate
            sorted_notes = sorted(notes, key=lambda note: central_point(note['loc'])[0])
            
            # Step 4: Group notes by x-coordinate with tolerance and boundary intersection
            current_group = []
            for i, note in enumerate(sorted_notes):
                if current_group and not self.find_chords(current_group[-1], note, tolerance):
                    # Add the current group to the final structure
                    final_structure[index]['notes'].append({
                        'clef': self.inv_map(self.clef_map).get(current_group[0]['clef']),
                        'key': current_group[0]['key'],
                        'pos': len(final_structure[index]['notes']),
                        'type': [n['type'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                        'label': [n['label'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                        'val': [n['val'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                        'acc': [n['acc'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                    })
                    # Start a new group
                    current_group = []
                current_group.append(note)
            
            # Add the last group if it exists
            if current_group:
                final_structure[index]['notes'].append({
                    'clef': self.inv_map(self.clef_map).get(current_group[0]['clef']),
                    'key': current_group[0]['key'],
                    'pos': len(final_structure[index]['notes']),
                    'type': [n['type'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                    'label': [n['label'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                    'val': [n['val'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                    'acc': [n['acc'] for n in sorted(current_group, key=lambda n: central_point(n['loc'])[1])],
                })
        
        fin = dict(final_structure)
        return fin
    
    def track_presets(self, fin, std_clefs = None, std_keysig = None):
        if std_clefs and len(std_clefs) == len(fin):
            for key, dicts in fin.items():
                dicts['clef'] = std_clefs[key][1]['clef']
        
        # if std_keysig and len(std_keysig) == len(fin):
        #     for key, dicts in fin.items():
        #         dicts['key_signature'] = std_keysig[key][1]['key']  # """ why [1] """"
                
        if std_keysig:
            for key, dicts in fin.items():
                if len(std_keysig) == len(fin):
                    dicts['key_signature'] = std_keysig[key][1]['key']
                else:
                    dicts['key_signature'] = int(std_keysig[0][0])
        
        
        
    def formalize(self, already = None, tracks = None):
        al = copy.deepcopy(already if already else self.el_note)
        
        # Default values for keys that might be missing
        default_clef = "fa"
        default_key_signature = 'cg'
        default_pitch = "C4"
        default_type = "note"
        default_duration = 1/2
    
        score = []
    
        for i, part in enumerate(al.values(), start= -1):
            
            # Add presets of the part
            score_part = {"staf": i + 1}
            if 'clef' in part:
                score_part['clef'] = part['clef']
            if 'key_signature' in part:
                score_part['key_signature'] = part['key_signature']
                
            # Load the notes
            score_part['notes'] = []
            last_clef = None
            for note in part['notes']:
                
                # Check for cleff change
                if note['clef'] != score_part['clef'] and note['clef'] != last_clef:
                    note_entry = {'clef_change': note['clef']}
                    score_part["notes"].append(note_entry)
                    last_clef = note['clef']
                    
                # Handle the 'type' mapping
                note_type = note.get('type', default_type)
                note_type = [self.type_map.get(t, default_type) for t in note_type]
                if len(note_type) > 1:
                    note_type = 'chord'
    
                note_entry = {
                    "pitch": note.get('val', [default_pitch]),
                    "type": note_type,
                    "duration": note.get('duration', default_duration)
                }
                
                if 'acc' in note and note.get('acc') is not None:
                    note_entry["acc"] = [acc.split('_')[0] if acc is not None else None for acc in note.get('acc')]
                    
                
                # Remove brackets if there's only one value in any key
                for key in ['pitch', 'acc', 'type', 'duration']:
                    if key in note_entry and isinstance(note_entry[key], list) and len(note_entry[key]) == 1:
                        note_entry[key] = note_entry[key][0]
                
                score_part["notes"].append(note_entry)
            score.append(score_part)

        return score


def process_midi(out_path):
    import ast
    from collections import ChainMap
    
    file_paths = [
        'to_midi_notes.txt',
        'matches_cleffs.txt',
        'matches_rests.txt',
        # 'barlines.txt',
    ]
    
    # Original version
    # matches_data = {}
    # for file_path in file_paths:
    #     key = os.path.splitext(os.path.basename(file_path))[0].split('_')[-1]
    #     with open(file_path, 'r') as file:
    #         data = file.read().strip()
    #         matches_data[key] = ast.literal_eval(data)

    # New version with error handling
    matches_data = {}
    for file_path in file_paths:
        try:
            key = os.path.splitext(os.path.basename(file_path))[0].split('_')[-1]
            full_path = os.path.join(out_path, file_path)
            with open(full_path, 'r') as file:
                data = file.read().strip()
                matches_data[key] = ast.literal_eval(data)
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Continuing without this data.")
            matches_data[key] = []  # or some other appropriate default value
            
    # from match_accidents
    file_paths = [
        'note_acc.txt',
        'key_sig.txt',
    ]
    
    # Original version
    # acc_data = {}
    # for file_path in file_paths:
    #     key = os. path.splitext(os.path.basename(file_path))[0]
    #     with open(file_path, 'r') as file:
    #         data = file.read().strip()
    #         acc_data[key] = ast.literal_eval(data)
    
    acc_data = {}
    for file_path in file_paths:
        try:
            key = os.path.splitext(os.path.basename(file_path))[0]
            full_path = os.path.join(out_path, file_path)
            with open(full_path, 'r') as file:
                data = file.read().strip()
                acc_data[key] = ast.literal_eval(data)
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Continuing without this data.")
            acc_data[key] = []  # or some other appropriate default value

    all_data = dict(ChainMap(acc_data, matches_data))

    # Initialize
    nm = NoteMod(*all_data.values())
    
    # Add elements
    std_clefs = nm.assign_cleff()
    std_keysig = nm.assign_keysig()
    nm.assign_accident()    # Does not modify 'val'
    
    # Format 
    al = nm.order_notes()
    nm.track_presets(al,
                    std_clefs = std_clefs,
                    std_keysig = std_keysig,
                    )
    score = nm.formalize(already = al)
    
    # MIDI!!!
    save_as_json(score, out_path)


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, 'out')
    process_midi(out_path)
