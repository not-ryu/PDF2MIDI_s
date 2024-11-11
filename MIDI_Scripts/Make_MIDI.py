#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 12:14:30 2024

@author: gabrielmiyazawa
"""


import music21 as m21
import os
import json


accidental_map = {
    "as": m21.pitch.Accidental("sharp"),
    "ab": m21.pitch.Accidental("flat"),
    "an": m21.pitch.Accidental("natural"),
    None: None
}



def load_staff_data(staff_data):

    part = m21.stream.Part()
    
    # Map clef codes to music21 Clef objects
    clef_map = {
        "cg": m21.clef.TrebleClef(),
        "cf": m21.clef.BassClef()
    }
    
    # Set the clef for the staff
    clef = clef_map.get(staff_data["clef"], m21.clef.TrebleClef())
    part.append(clef)
    
    # Set the key signature for the staff
    key_signature = m21.key.KeySignature(staff_data["key_signature"])
    part.append(key_signature)
    
    measure = m21.stream.Measure()
    
    # Add notes to the staff
    for note_data in staff_data["notes"]:
        if "clef_change" in note_data:
            # Complete the current measure before changing the clef
            if measure.duration.quarterLength > 0:
                part.append(measure)
                measure = m21.stream.Measure()
            new_clef = clef_map.get(note_data["clef_change"], m21.clef.TrebleClef())
            measure.append(new_clef)
        else:
            # Create note or chord considering the key signature
            if isinstance(note_data["pitch"], list):
                chord_pitches = [m21.pitch.Pitch(p) for p in note_data["pitch"]]
                n = m21.chord.Chord(chord_pitches, quarterLength=note_data["duration"])
            else:
                pitch = m21.pitch.Pitch(note_data["pitch"])
                # pitch.transpose(key_signature.sharps, inPlace=True)  # Apply key signature
                n = m21.note.Note(pitch, quarterLength=note_data["duration"])
            measure.append(n)
    
    # Add the last measure if it has content
    if measure.duration.quarterLength > 0:
        part.append(measure)
    
    return part




def check_enharmonic(part, midi_values, accidentals, key_signature_fifths):
    if isinstance(midi_values, int):
        # Convert to a list if a single MIDI value is provided
        midi_values = [midi_values]
        accidentals = [accidentals]
    
    pitches = []
    
    for midi_value, accidental in zip(midi_values, accidentals):
        # Create the pitch from the MIDI value
        pitch = m21.pitch.Pitch(midi_value)
        
        # Apply the provided accidental, if any
        if accidental == "as":
            pitch.accidental = m21.pitch.Accidental("sharp")
        elif accidental == "ab":
            pitch.accidental = m21.pitch.Accidental("flat")
        elif accidental == "an":
            pitch.accidental = m21.pitch.Accidental("natural")
        
        # Determine the automatically assigned accidental by music21 after applying the key signature
        automatic_accidental = pitch.accidental
        
        # Only adjust if the note has an automatically assigned accidental and no explicit accidental was provided
        if automatic_accidental is not None and accidental is None:
            # Check if the pitch accidental is opposite to what the key signature would naturally assign
            if (key_signature_fifths < 0 and automatic_accidental.name == "sharp") or \
               (key_signature_fifths > 0 and automatic_accidental.name == "flat"):
                # Switch to the enharmonic equivalent that follows the key signature's direction
                pitch = pitch.getEnharmonic(inPlace=False)
                print(f"Note adjusted to: {pitch.nameWithOctave}.")
        
        # Add the pitch to the list of pitches for the chord or single note
        pitches.append(pitch)
    
    # Create the chord or note with the adjusted pitches and add it to the part
    if len(pitches) > 1:
        chord = m21.chord.Chord(pitches, quarterLength=1.0)
        part.append(chord)
    else:
        note = m21.note.Note(pitches[0], quarterLength=1.0)
        part.append(note)



def process_notes_data(part, notes_data, key_signature_fifths):
    for note_data in notes_data:
        pitches = note_data["pitch"]
        accidentals = note_data["acc"]
        duration = note_data["duration"]
        
        # Ensure that pitches and accidentals are lists for uniform processing
        if isinstance(pitches, int):
            pitches = [pitches]
            accidentals = [accidentals]
        
        # Process the note or chord through check_enharmonic function
        check_enharmonic(part, pitches, accidentals, key_signature_fifths)
        
        # If needed, adjust the duration of the last note or chord added
        if part[-1].duration.quarterLength != duration:
            part[-1].duration.quarterLength = duration
            

def run_example_with_data(notes_data, key_signature_fifths):
    # Set up the staff with Treble Clef and specified Key Signature
    part = m21.stream.Part()
    
    # Treble (G) Clef
    clef = m21.clef.TrebleClef()
    part.append(clef)
    
    # Set up the key signature
    key_signature = m21.key.KeySignature(key_signature_fifths)
    part.append(key_signature)
    
    # Process the notes data
    process_notes_data(part, notes_data, key_signature_fifths)
    
    # Create a score to hold the part
    score = m21.stream.Score()
    score.append(part)
    
    # Display the score as an image
    score.show('musicxml.png')







#%%
def load_score(data, tracks = None):
    score = m21.stream.Score()
    
    for staff_data in data:
        part = load_staff_data(staff_data)
        score.append(part)
    
    return score

def make_midi(out_path, final_output_path, name='score'):
    # Load the JSON data from the file
    score_json = os.path.join(out_path, f'{name}.json')
    with open(score_json, 'r') as file:
        data = json.load(file)
        
    score = load_score(data)
    score.write('musicxml.png', fp=os.path.join(final_output_path, f'{name}.png'))

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, 'out')
    final_output_path = os.path.join(script_dir, 'final_output')
    make_midi(out_path, final_output_path)

