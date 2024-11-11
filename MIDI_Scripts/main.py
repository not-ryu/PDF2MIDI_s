#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Someday

@author: gabrielmiyazawa
"""

# Basic packadges
import os
import numpy as np
import cv2

# CV based functions
from template_match_last import multi_template_match
from rm_rect import remove_rectangles
from morph_map import morphologyex
from get_shaft import contour_notebar, contour_stem
from almost_lines import std_staff
from staff_lines import main_lines
from get_barlines_v3 import get_barline
from ledger_centroids import find_centroids

# MIDI building functions
from NoteMapper import Notes_Mapper
from match_accidents import match_acc

def process_sheet_music(main_image_path, output_directory, templates_directory):
    """
    Process sheet music image and generate MIDI data
    
    Args:
        main_image_path (str): Path to input sheet music image
        output_directory (str): Path to output directory for generated files
        templates_directory (str): Path to directory containing template images
    """
    print("\nDEBUGDEBUGDEBUGDEBUGDEBUGDEBUG (main.py) - Processing output directory:", output_directory)
    # Load main image
    try:
        main_image = cv2.imread(main_image_path)
        if main_image is None:
            raise FileNotFoundError(f"Could not load image at path: {main_image_path}")
    except FileNotFoundError as e:
        print(e)
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    if not os.path.isdir(templates_directory):
        os.chdir(templates_directory)
        
    templates_dirs = [
        {'path': 'Core/Notes_Full/', 'thresholds': 0.75, 'min_distance': 10}, 
        {'path': 'Core/Claves/Cleff_Fa/', 'thresholds': 0.65, 'min_distance': 15},
        {'path': 'Core/Claves/Cleff_Sol/', 'thresholds': 0.65, 'min_distance': 15},
        {'path': 'Core/Accidents/Sharp/', 'thresholds': 0.7, 'min_distance': 10},
        {'path': 'Core/Accidents/Flat/', 'thresholds': 0.75, 'min_distance': 10}, 
        {'path': 'Core/Accidents/Natural/', 'thresholds': 0.75, 'min_distance': 10},
        {'path': 'Core/Rests/Rest_Semiquaver/', 'thresholds': 0.7, 'min_distance': 15},
        {'path': 'Core/Rests/Rest_Quaver/', 'thresholds': 0.7, 'min_distance': 15},
    ]

    # Manually selected templates to skip
    skip_templates = None

    # Store all matches
    matches_to_txt = []

    # Specific storage for each component
    matches_notes = []
    matches_cleffs = []
    matches_accidents = []
    matches_rests = []

    match_categories = [
        (matches_notes, 'matches_notes.txt'),
        (matches_cleffs, 'matches_cleffs.txt'), 
        (matches_accidents, 'matches_accidents.txt'),
        (matches_rests, 'matches_rests.txt'),
    ]

    # Basic templates matching
    for templates in templates_dirs:
        matches_full, _, _ = multi_template_match(
            main_image_path, templates['path'], output_directory, templates['thresholds'],
            templates['min_distance'], skip_templates = skip_templates)
        
        # Save all templates matches
        if matches_to_txt:
            matches_to_txt.extend(matches_full)
        else:
            matches_to_txt = matches_full
        
        # Display matches counter
        template_dir_name = [p for p in templates['path'].split('/') if p][-1]
        print(template_dir_name +':', len(matches_full), 'matches')
        
        # Save specific classes of templates
        if 'Notes_Full' in templates.get('path', ''):
            matches_notes.extend(matches_full)
        elif 'Claves' in templates.get('path', ''):
            matches_cleffs.extend(matches_full)
        elif 'Accidents' in templates.get('path', ''):
            matches_accidents.extend(matches_full)
        elif 'Rests' in templates.get('path', ''):
            matches_rests.extend(matches_full)

    # Save matches per categories
    for matches, filename in match_categories:
        if matches:
            matches_outpath = os.path.join(output_directory, filename)
            print(f'Saving {filename} to: {matches_outpath}')
            with open(matches_outpath, 'w') as file:
                file.write(str(matches))

    # Save templates matches and scores
    matches_outpath = os.path.join(output_directory, 'matches_all.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(matches_to_txt))
    print('All matches saved to:', output_directory)

    # Reformat matches log
    matches = [tup[0] + tup[1] for tup in matches_to_txt]

    # Draw all rectangles on clean image
    clean_image = cv2.imread(main_image_path)
    for (x_initial, y_initial, x_final, y_final) in matches:
        cv2.rectangle(clean_image, (x_initial, y_initial), (x_final, y_final), (0, 255, 0), 2)

    # Save original image with matched rectangles 
    result_path = os.path.join(output_directory, 'matches.png')
    cv2.imwrite(result_path, clean_image)

    # Remove matched templates from main image
    cleaned_image = remove_rectangles(main_image_path, matches, output_directory)
    output_path = os.path.join(output_directory, 'rmrect.png')
    _ = cv2.imwrite(output_path, cleaned_image)

    # Phase 2 - Other
    # Get note bar
    bars_image = morphologyex(cleaned_image, output_directory, ker = (8, 10))
    output_path = os.path.join(output_directory, 'morph_bar.png')
    cv2.imwrite(output_path, bars_image)
    image, bar_contours, bar_coords = contour_notebar(bars_image, output_directory)

    # Get note stem
    stems_image = morphologyex(cleaned_image, output_directory, ker = (1, 50))
    output_path = os.path.join(output_directory, 'morph_stems.png')
    cv2.imwrite(output_path, stems_image)
    image, stem_contours, stem_coords = contour_stem(stems_image, output_directory)

    matches_outpath = os.path.join(output_directory, 'stems_lines.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(stem_coords))

    # Get bar lines
    barlines = get_barline(stem_coords, stems_image, output_directory, min_length = 50)

    # Draw location of note stems and bars
    contour_image = np.zeros_like(image)
    contour_image_rgb = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
    cv2.drawContours(contour_image_rgb, bar_contours, -1, (255), 1)
    cv2.drawContours(contour_image_rgb, stem_contours, -1, (0, 255, 0), 1)
    output_path = os.path.join(output_directory, 'contours.png')
    cv2.imwrite(output_path, contour_image_rgb)

    # All finds this far on original image
    shaft_coords = bar_coords + stem_coords
    for coords in shaft_coords:
        cv2.line(clean_image, coords[0], coords[1], (0, 0, 255), 2)
    output_path = os.path.join(output_directory, 'loc_stems+bars.png')
    cv2.imwrite(output_path, clean_image)

    # Phase 3 - Staffs
    # os.chdir(output_directory)

    print("\nDEBUG (main.py) - Current working directory:", os.getcwd())
    print("DEBUG (main.py) - Output directory:", output_directory)

    # Morphological map for horizontal lines
    morph_img = morphologyex(main_image, output_directory, ker = (20, 1))
    cv2.imwrite(os.path.join(output_directory, 'morph_staff.png'), morph_img)

    # Standardized (Ideal) staff
    print("\nDEBUG (main.py) - std_staff() called with output_directory:", output_directory)
    adjusted_lines = std_staff(morph_img, output_directory)
    staff_ideal = main_lines(adjusted_lines, output_directory)

    # Find centroids for ledger notes
    centroids = find_centroids(morph_img, staff_ideal, output_directory)

    # Phase 4 - Piece components together
    # os.chdir(output_directory)

    Notes_Mapper(output_directory, output_directory)

    matched_acc, unmatched, key_sig = match_acc(output_directory, group_max_dist=50, y_threshold=20, x_limit=30, plot=False)

    matches_outpath = os.path.join(output_directory, 'note_acc.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(matched_acc))
    matches_outpath = os.path.join(output_directory, 'key_sig.txt')
    with open(matches_outpath, 'w') as file:
        file.write(str(key_sig))
